"""Testes automatizados da interface Streamlit (``streamlit.testing.v1.AppTest``).

Verificam carregamento, navegação, filtros e mensagens das quatro páginas. Não substituem a
inspeção visual no navegador, que não é executada por estes testes.
"""

import os
import shutil
import subprocess
import sys
import textwrap

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard import dados_publicos as dp
from scripts.utils import project_path

PAGINAS = ("home", "sinesp", "violencia_domestica", "quality")


def _pagina(nome: str) -> AppTest:
    return AppTest.from_file(str(project_path("dashboard", "pages", f"{nome}.py")), default_timeout=120).run()


def _sem_erros(app: AppTest):
    assert not app.exception, [e.value for e in app.exception]
    assert not app.error, [e.value for e in app.error]


# ----------------------------------------------------------------------------- entrada e navegação
def test_entrada_carrega_com_navegacao_das_quatro_paginas():
    app = AppTest.from_file(str(project_path("scripts", "painel_streamlit.py")), default_timeout=120).run()
    _sem_erros(app)
    assert [t.value for t in app.title] == ["Segurança Pública de Joinville/SC"]  # página padrão: Projeto
    texto = project_path("scripts", "painel_streamlit.py").read_text(encoding="utf-8")
    for pagina in ("home.py", "sinesp.py", "violencia_domestica.py", "quality.py"):
        assert f'project_path("dashboard", "pages", "{pagina}")' in texto
        assert project_path("dashboard", "pages", pagina).is_file()
    assert texto.count("st.Page(") == 4 and "st.navigation(" in texto and 'layout="wide"' in texto


@pytest.mark.parametrize("nome", PAGINAS)
def test_cada_pagina_executa_sem_excecoes(nome):
    _sem_erros(_pagina(nome))


def test_projeto_nao_afirma_deploy_nem_analise_pendente():
    app = _pagina("home")
    texto = " ".join(m.value for m in app.markdown) + " ".join(i.value for i in app.info) + " ".join(c.value for c in app.caption)
    assert "Não há deploy público confirmado" in texto
    assert "pendentes de validação" not in texto and "streamlit.app" not in texto
    assert [m.value for m in app.metric] == ["900", "216", "4"]


# ------------------------------------------------------------------------------------------- Sinesp
def test_sinesp_valores_padrao_e_filtros():
    app = _pagina("sinesp")
    _sem_erros(app)
    assert app.selectbox[0].value == "Homicídio doloso" and app.selectbox[1].value == "Estadual"
    assert [m.value for m in app.metric][:2] == ["29", "22"]  # último ano completo (2025) e janeiro–agosto de 2026
    assert "+4 vs janeiro–agosto de 2025" in app.metric[1].delta and "−7 vs 2024" in app.metric[0].delta
    assert any("2026 contém apenas janeiro a agosto" in i.value for i in app.info)
    assert len(app.tabs) == 5

    app.select_slider[0].set_value((2020, 2025)).run()  # sem 2026: o aviso de ano parcial desaparece
    _sem_erros(app)
    assert not any("2026 contém apenas" in i.value for i in app.info)
    assert [m.value for m in app.metric][:2] == ["29", "18"]  # janeiro–agosto passa a ser 2025

    app.selectbox[0].select("Mandado de prisão cumprido").run()
    assert "Polícia Federal" in app.selectbox[1].options and "Estadual" in app.selectbox[1].options
    app.selectbox[1].select("Polícia Federal").run()
    _sem_erros(app)
    assert any("a partir de janeiro/2025" in w.value for w in app.warning)  # ausência de cobertura explícita, não zero
    assert "mandados cumpridos" in " ".join(m.value for m in app.markdown)  # unidade distinta de vítimas


def test_sinesp_todos_os_indicadores_e_abrangencias_executam():
    catalogo = dp.carregar_catalogo_sinesp()
    app = _pagina("sinesp")
    for linha in catalogo.itertuples():
        app.selectbox[0].select(linha.evento).run()
        app.selectbox[1].select(linha.abrangencia).run()
        _sem_erros(app)


# ---------------------------------------------------------------------------- violência doméstica
def test_violencia_domestica_valores_padrao_e_avisos():
    app = _pagina("violencia_domestica")
    _sem_erros(app)
    avisos = " ".join(w.value for w in app.warning)
    assert "Fato Comunicado" in avisos and "vítimas, pessoas únicas ou boletins" in avisos
    assert len(app.tabs) == 6 and len(app.metric) == 0  # várias categorias: tabela por categoria, sem KPI único nem total
    assert len(app.multiselect[0].value) == 9 and app.multiselect[1].value == [2023, 2024]
    corpo = " ".join(m.value for m in app.markdown)
    assert "decisão metodológica" in corpo and "estrutura contínua" in corpo and "Não há total geral" in corpo


def test_violencia_domestica_filtros_alteram_a_apresentacao_sem_mudar_definicoes():
    vd = dp.carregar_violencia_domestica()
    app = _pagina("violencia_domestica")
    app.multiselect[0].set_value(["Ameaça"]).run()
    _sem_erros(app)
    assert [m.value for m in app.metric] == ["1.957", "2.085"] and "+128 vs 2023" in app.metric[1].delta

    app.select_slider[0].set_value((1, 6)).run()  # janeiro a junho nos dois anos
    _sem_erros(app)
    esperado = [int(vd[(vd.categoria == "Ameaça") & (vd.ano == a) & (vd.mes <= 6)].fatos_comunicados.sum()) for a in (2023, 2024)]
    assert [m.value for m in app.metric] == [f"{v:,}".replace(",", ".") for v in esperado]

    app.multiselect[1].set_value([2024]).run()
    _sem_erros(app)
    assert len(app.metric) == 1
    app.multiselect[1].set_value([2023, 2024]).run()
    app.multiselect[0].set_value([]).run()
    assert any("Selecione ao menos uma categoria" in i.value for i in app.info) and not app.exception


def test_violencia_domestica_comparacao_exige_dois_anos():
    app = _pagina("violencia_domestica")
    app.multiselect[1].set_value([2023]).run()
    _sem_erros(app)
    assert any("exige os dois anos" in i.value for i in app.info)


# ------------------------------------------------------------------------------------------ qualidade
def test_qualidade_mostra_integridade_cobertura_fontes_e_limitacoes():
    app = _pagina("quality")
    _sem_erros(app)
    corpo = " ".join(m.value for m in app.markdown)
    assert "Todos os Direitos Reservados" in corpo and "Creative Commons" in corpo  # condições de uso das fontes
    assert "Fato Comunicado" in corpo and "não** estão publicados no repositório" in corpo
    arquivos = app.dataframe[0].value
    assert len(arquivos) == 4 and arquivos["Integridade (SHA-256)"].str.contains("confere").all()
    assert not app.error


# -------------------------------------------------------------------------- clone limpo e falhas
def _copiar_projeto_minimo(destino, *, com_dados: bool = True):
    raiz = project_path()
    shutil.copytree(raiz / "dashboard", destino / "dashboard", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (destino / "scripts").mkdir()
    for nome in ("__init__.py", "utils.py", "painel_streamlit.py"):
        shutil.copy(raiz / "scripts" / nome, destino / "scripts" / nome)
    if not com_dados:
        shutil.rmtree(destino / "dashboard" / "data_publica")


def _executar_no_clone(destino, codigo: str) -> subprocess.CompletedProcess:
    ambiente = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, "-c", textwrap.dedent(codigo)], cwd=destino, capture_output=True, text=True, encoding="utf-8",
                          timeout=300, env=ambiente)


def test_funciona_em_clone_limpo_sem_dados_e_sem_dados_processados(tmp_path):
    _copiar_projeto_minimo(tmp_path)
    assert not (tmp_path / "dados").exists()
    resultado = _executar_no_clone(tmp_path, """
        from streamlit.testing.v1 import AppTest
        for pagina in ("home", "sinesp", "violencia_domestica", "quality"):
            app = AppTest.from_file(f"dashboard/pages/{pagina}.py", default_timeout=120).run()
            assert not app.exception and not app.error, (pagina, [e.value for e in app.exception], [e.value for e in app.error])
        entrada = AppTest.from_file("scripts/painel_streamlit.py", default_timeout=120).run()
        assert not entrada.exception
        quality = AppTest.from_file("dashboard/pages/quality.py", default_timeout=120).run()
        assert any("não está presente" in m.value for m in quality.markdown), "esperado aviso de acervo ausente"
        print("OK")
    """)
    assert resultado.returncode == 0 and "OK" in resultado.stdout, resultado.stderr[-1500:]


def test_ausencia_dos_arquivos_de_dados_mostra_erro_explicito_sem_derrubar_a_aplicacao(tmp_path):
    _copiar_projeto_minimo(tmp_path, com_dados=False)
    resultado = _executar_no_clone(tmp_path, """
        from streamlit.testing.v1 import AppTest
        for pagina in ("sinesp", "violencia_domestica", "quality", "home"):
            app = AppTest.from_file(f"dashboard/pages/{pagina}.py", default_timeout=120).run()
            assert not app.exception, (pagina, [e.value for e in app.exception])
            if pagina != "home":
                assert app.error and "Dados indisponíveis" in app.error[0].value, pagina
                assert any("Nenhum valor foi preenchido" in i.value for i in app.info), pagina
        print("OK")
    """)
    assert resultado.returncode == 0 and "OK" in resultado.stdout, resultado.stderr[-1500:]


def test_esquema_invalido_mostra_erro_explicito(tmp_path):
    _copiar_projeto_minimo(tmp_path)
    caminho = tmp_path / "dashboard" / "data_publica" / dp.ARQ_VD
    caminho.write_text(caminho.read_text(encoding="utf-8").replace("fatos_comunicados", "contagem", 1), encoding="utf-8", newline="\n")
    resultado = _executar_no_clone(tmp_path, """
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file("dashboard/pages/violencia_domestica.py", default_timeout=120).run()
        assert not app.exception and app.error and "Esquema inesperado" in app.error[0].value, [e.value for e in app.error]
        print("OK")
    """)
    assert resultado.returncode == 0 and "OK" in resultado.stdout, resultado.stderr[-1500:]


def test_integridade_divergente_e_sinalizada_na_pagina_de_qualidade(tmp_path):
    _copiar_projeto_minimo(tmp_path)
    caminho = tmp_path / "dashboard" / "data_publica" / dp.ARQ_VD
    caminho.write_text(caminho.read_text(encoding="utf-8").replace("JOINVILLE,2023,1,Ameaça,199", "JOINVILLE,2023,1,Ameaça,198", 1), encoding="utf-8", newline="\n")
    resultado = _executar_no_clone(tmp_path, """
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file("dashboard/pages/quality.py", default_timeout=120).run()
        assert not app.exception and any("não coincidem com o manifesto" in e.value for e in app.error), [e.value for e in app.error]
        print("OK")
    """)
    assert resultado.returncode == 0 and "OK" in resultado.stdout, resultado.stderr[-1500:]


# ------------------------------------------------------------------ versão dos dados e atualização
def test_paginas_mostram_versao_fonte_ultima_competencia_e_como_se_atualiza():
    manifesto = dp.carregar_manifesto()
    sinesp = _pagina("sinesp")
    legendas = " ".join(c.value for c in sinesp.caption)
    assert manifesto["versao"] in legendas and "última competência disponível: 2026-08" in legendas and "2026 é parcial" in legendas
    assert "agosto/2026" in legendas  # período na legenda da fonte, derivado dos dados
    corpo = " ".join(m.value for m in sinesp.markdown)
    assert "versão histórica validada" in corpo and "O painel **não** baixa dados" in corpo and "MJSP" in corpo
    assert "manual e controlada" in corpo and "verificar → preparar → aprovar" in corpo
    vd = _pagina("violencia_domestica")
    assert "última competência disponível: 2024-12" in " ".join(c.value for c in vd.caption)
    qualidade = _pagina("quality")
    texto = " ".join(m.value for m in qualidade.markdown) + " ".join(i.value for i in qualidade.info) + " ".join(c.value for c in qualidade.caption)
    assert "Última competência nos dados" in texto and "Sinesp 2026-08" in texto and "2024-12" in texto
    assert "ATUALIZACAO_DE_DADOS.md" in texto and "Licenças verificadas" in " ".join(e.label for e in qualidade.expander)


def test_painel_funciona_com_dados_de_setembro_e_serie_defasada(tmp_path):
    """Dados de uma atualização (aprovada) com 2026-09 e a série PRF ainda em 2026-08: cobertura por série, sem 'agosto' fixo no código."""
    from test_atualizacao_fluxo import _com_setembro, _entradas  # fixtures sintéticas
    from scripts import atualizacao_dados as au

    ativa = tmp_path / "ativa"
    shutil.copytree(dp.DIRETORIO_DADOS, ativa)
    mensal = _com_setembro(dp.carregar_sinesp(ativa), ignorar=["Mortes no trânsito"])
    candidato = au.preparar(ativa=ativa, staging_root=tmp_path / "staging", entradas_sinesp=_entradas(tmp_path / "entradas", mensal))
    assert candidato.validacao.erros == []
    clone = tmp_path / "clone"
    clone.mkdir()
    _copiar_projeto_minimo(clone)
    shutil.rmtree(clone / "dashboard" / "data_publica")
    shutil.copytree(candidato.diretorio / "dados", clone / "dashboard" / "data_publica")
    resultado = _executar_no_clone(clone, """
        from streamlit.testing.v1 import AppTest
        for pagina in ("home", "sinesp", "violencia_domestica", "quality"):
            app = AppTest.from_file(f"dashboard/pages/{pagina}.py", default_timeout=120).run()
            assert not app.exception and not app.error, (pagina, [e.value for e in app.exception], [e.value for e in app.error])
        sinesp = AppTest.from_file("dashboard/pages/sinesp.py", default_timeout=120).run()
        sinesp.selectbox[0].select("Suicídio").run()
        assert any("2026 contém apenas janeiro a setembro" in i.value for i in sinesp.info), [i.value for i in sinesp.info]
        assert "Janeiro–setembro de 2026" in sinesp.metric[1].label, sinesp.metric[1].label
        assert "vs janeiro–setembro de 2025" in sinesp.metric[1].delta
        sinesp.selectbox[0].select("Mortes no trânsito").run()  # série PRF: ainda até agosto
        assert any("2026 contém apenas janeiro a agosto" in i.value for i in sinesp.info), [i.value for i in sinesp.info]
        assert "Janeiro–agosto de 2026" in sinesp.metric[1].label, sinesp.metric[1].label
        home = AppTest.from_file("dashboard/pages/home.py", default_timeout=120).run()
        assert any("setembro/2026" in m.value for m in home.markdown)
        quality = AppTest.from_file("dashboard/pages/quality.py", default_timeout=120).run()
        assert any("Sinesp 2026-09" in m.value for m in quality.markdown)
        print("OK")
    """)
    assert resultado.returncode == 0 and "OK" in resultado.stdout, resultado.stdout[-800:] + resultado.stderr[-1500:]
