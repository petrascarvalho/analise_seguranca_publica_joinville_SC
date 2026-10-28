"""Testes automatizados da interface Streamlit (``streamlit.testing.v1.AppTest``).

Verificam carregamento, navegação, filtros e mensagens das três páginas (Projeto, Indicadores Sinesp, Qualidade e
metodologia). Não substituem a inspeção visual no navegador, que não é executada por estes testes.
"""

import os
import shutil
import subprocess
import sys
import textwrap

import pytest
from streamlit.proto.Metric_pb2 import Metric
from streamlit.testing.v1 import AppTest

from dashboard import dados_publicos as dp
from src.pipeline.utils import project_path

PAGINAS = ("home", "sinesp", "quality")


def _pagina(nome: str) -> AppTest:
    return AppTest.from_file(str(project_path("dashboard", "pages", f"{nome}.py")), default_timeout=120).run()


def _sem_erros(app: AppTest):
    assert not app.exception, [e.value for e in app.exception]
    assert not app.error, [e.value for e in app.error]


def _texto(app: AppTest) -> str:
    return " ".join([m.value for m in app.markdown] + [i.value for i in app.info] + [c.value for c in app.caption] + [w.value for w in app.warning])


# ----------------------------------------------------------------------------- entrada e navegação
def test_entrada_carrega_com_navegacao_das_tres_paginas():
    app = AppTest.from_file(str(project_path("scripts", "painel_streamlit.py")), default_timeout=120).run()
    _sem_erros(app)
    assert [t.value for t in app.title] == ["Segurança Pública de Joinville/SC"]  # página padrão: Projeto
    texto = project_path("scripts", "painel_streamlit.py").read_text(encoding="utf-8")
    for pagina in ("home.py", "sinesp.py", "quality.py"):
        assert f'_RAIZ / "dashboard" / "pages" / "{pagina}"' in texto
        assert project_path("dashboard", "pages", pagina).is_file()
    for url in ('url_path="projeto"', 'url_path="sinesp"', 'url_path="qualidade"'):
        assert url in texto
    assert texto.count("st.Page(") == 3 and "st.navigation(" in texto and 'layout="wide"' in texto
    assert "violencia_domestica" not in texto and not project_path("dashboard", "pages", "violencia_domestica.py").exists()
    assert sorted(p.name for p in project_path("dashboard", "pages").glob("*.py")) == ["home.py", "quality.py", "sinesp.py"]


@pytest.mark.parametrize("nome", PAGINAS)
def test_cada_pagina_executa_sem_excecoes(nome):
    _sem_erros(_pagina(nome))


def test_projeto_apresenta_fonte_unica_periodo_real_destaques_e_um_grafico():
    app = _pagina("home")
    texto = _texto(app)
    assert "deploy" not in texto and "streamlit.app" not in texto  # a página não trata de publicação
    assert "janeiro/2020 a setembro/2026" in texto and "2026 é parcial" in texto
    assert "única fonte deste painel" in texto and "Mortes no trânsito (Polícia Rodoviária Federal) até 2026-08" in texto
    # fonte e período (4 números da base) e os destaques calculados (homicídio 2025, homicídio e tentativa em janeiro–setembro de 2026)
    assert [m.value for m in app.metric] == ["2020–2026", "911", "12", "2026-09", "29", "25", "77"]
    destaques = app.metric[4:]
    assert "−7 vs 2024" in destaques[0].delta and "+4 vs janeiro–setembro de 2025" in destaques[1].delta
    assert "+34 vs janeiro–setembro de 2025" in destaques[2].delta
    direcoes = [Metric.MetricDirection.Name(m.proto.direction) for m in destaques]
    assert direcoes == ["DOWN", "UP", "UP"]  # a seta acompanha o sinal da diferença
    # cada cartão identifica indicador, abrangência, unidade, período e base de comparação em texto que não é cortado
    legendas = " ".join(c.value for c in app.caption)
    for trecho in ("Estadual · vítimas · ano completo de 2025", "Estadual · vítimas · janeiro–setembro de 2026 (ano parcial)",
                   "Comparado com o ano completo de 2024.", "Comparado com janeiro–setembro de 2025 (mesma duração)."):
        assert trecho in legendas, trecho
    for ausente in ("SSP", "Prefeitura", "violência doméstica", "Fato Comunicado"):
        assert ausente not in texto, ausente
    assert [s.value for s in app.subheader] == ["Indicadores de destaque", "Evolução do homicídio doloso", "Principais achados", "Explore as análises"]
    assert sum(1 for e in app.expander if e.label == "Valores usados neste gráfico (tabela)") == 1  # um único gráfico, com a tabela de apoio
    assert "Pergunta, unidades e limites da leitura" in [e.label for e in app.expander]


# ------------------------------------------------------------------------------------------- Sinesp
def test_sinesp_valores_padrao_e_filtros():
    app = _pagina("sinesp")
    _sem_erros(app)
    assert app.selectbox(key="indicador").value == "Homicídio doloso" and app.selectbox(key="abrangencia").value == "Estadual"
    assert [m.value for m in app.metric][:2] == ["29", "25"]  # último ano completo (2025) e janeiro–setembro de 2026
    assert "+4 vs janeiro–setembro de 2025" in app.metric[1].delta and "−7 vs 2024" in app.metric[0].delta
    assert "Janeiro–setembro de 2026" in app.metric[1].label
    assert any("2026 contém apenas janeiro a setembro" in i.value for i in app.info)
    assert len(app.tabs) == 5

    app.select_slider[0].set_value((2020, 2025)).run()  # sem 2026: o aviso de ano parcial desaparece
    _sem_erros(app)
    assert not any("2026 contém apenas" in i.value for i in app.info)
    assert [m.value for m in app.metric][:2] == ["29", "21"]  # janeiro–setembro passa a ser 2025

    app.selectbox(key="indicador").select("Mandado de prisão cumprido").run()
    assert "Polícia Federal" in app.selectbox(key="abrangencia").options and "Estadual" in app.selectbox(key="abrangencia").options
    app.selectbox(key="abrangencia").select("Polícia Federal").run()
    _sem_erros(app)
    assert any("a partir de janeiro/2025" in w.value for w in app.warning)  # ausência de cobertura explícita, não zero
    assert "mandados cumpridos" in " ".join(m.value for m in app.markdown)  # unidade distinta de vítimas


def test_sinesp_serie_prf_vai_ate_agosto_sem_preenchimento():
    app = _pagina("sinesp")
    app.selectbox(key="indicador").select("Mortes no trânsito").run()
    app.selectbox(key="abrangencia").select("Polícia Rodoviária Federal").run()
    _sem_erros(app)
    assert any("2026 contém apenas janeiro a agosto" in i.value for i in app.info)
    assert "Janeiro–agosto de 2026" in app.metric[1].label and "vs janeiro–agosto de 2025" in app.metric[1].delta
    assert any("PRF pode terminar em competência diferente" in i.value for i in app.info)


def _aba(app, nome):
    """A página executa só a aba selecionada (st.tabs com on_change="rerun"): seleciona a aba e executa de novo."""
    app.session_state["aba_analise"] = nome
    return app.run()


def _em_cada_aba(app):
    """Percorre as quatro abas de análise e devolve, a cada uma, o app já executado com ela selecionada."""
    for nome in ("Evolução", "Comparações", "Padrões e tendência", "Estatística e outliers"):
        yield nome, _aba(app, nome)


def test_sinesp_todos_os_indicadores_e_abrangencias_executam():
    catalogo = dp.carregar_catalogo_sinesp()
    app = _pagina("sinesp")
    for linha in catalogo.itertuples():
        app.selectbox(key="indicador").select(linha.evento).run()
        app.selectbox(key="abrangencia").select(linha.abrangencia).run()
        _sem_erros(app)


def test_sinesp_organiza_a_analise_em_quatro_grupos_com_tabela_por_grafico():
    app = _pagina("sinesp")
    _sem_erros(app)
    assert [t.label for t in app.tabs] == ["Evolução", "Comparações", "Padrões e tendência", "Estatística e outliers", "Indicadores e interpretação"]
    tabelas, informativos, sazonalidade = 0, False, False
    for nome, aba in _em_cada_aba(app):  # cada aba só executa quando selecionada
        _sem_erros(aba)
        tabelas += sum(1 for e in aba.expander if e.label == "Valores usados neste gráfico (tabela)")
        informativos |= any("Método informativo" in i.value for i in aba.info)  # homicídio doloso: limites de Tukey informativos
        sazonalidade |= any("Sazonalidade (exploratória)" in m.value for m in aba.markdown)
    assert tabelas >= 9  # mapa de calor, períodos, ranking, anual, mensal, média móvel, acumulado, boxplot, distribuição, sazonalidade, outliers
    assert informativos and sazonalidade


def test_sinesp_outliers_nao_conclui_anomalia_quando_o_metodo_nao_e_informativo():
    app = _pagina("sinesp")
    _aba(app, "Estatística e outliers")
    app.selectbox(key="indicador").select("Roubo seguido de morte (latrocínio)").run()
    _sem_erros(app)
    assert any("Método IQR não informativo" in w.value and "IQR igual a zero" in w.value for w in app.warning)
    assert not any("Método informativo" in i.value for i in app.info)
    app.selectbox(key="indicador").select("Mandado de prisão cumprido").run()
    app.selectbox(key="abrangencia").select("Polícia Federal").run()
    _sem_erros(app)
    assert any("maioria de zeros publicados" in w.value for w in app.warning)
    assert any("Sazonalidade não avaliada" in i.value for i in _aba(app, "Padrões e tendência").info)  # PF: um único ano completo


def test_sinesp_comparacao_de_anos_completos_e_ranking_por_unidade():
    app = _pagina("sinesp")
    _aba(app, "Comparações")
    app.selectbox(key="ano_a").select(2020).run()
    app.selectbox(key="ano_b").select(2025).run()
    _sem_erros(app)
    assert "2020 × 2025:" in " ".join(m.value for m in app.markdown)
    assert "62 × 29" in " ".join(m.value for m in app.markdown)

    app.selectbox(key="ano_rank").select(2025).run()
    for unidade in app.radio(key="unidade_rank").options:
        app.radio(key="unidade_rank").set_value(unidade).run()
        _sem_erros(app)
    corpo = " ".join(c.value for c in app.caption)
    assert "Sem total entre indicadores" in corpo or "Não há total entre indicadores" in corpo or "nem entre abrangências" in corpo


# ------------------------------------------------------------------------------------------ qualidade
def test_qualidade_mostra_integridade_cobertura_fonte_e_limitacoes():
    app = _pagina("quality")
    _sem_erros(app)
    corpo = _texto(app)
    assert "Creative Commons" in corpo and "não confirmada" in corpo.lower() or "NÃO confirmada" in corpo or "não** foi confirmada" in corpo or "confirmada na consulta" in corpo
    assert "Última competência disponível:** **2026-09**" in corpo and "2026 parcial" in corpo
    arquivos = app.dataframe[0].value
    assert len(arquivos) == 2 and arquivos["Integridade"].str.contains("confere").all()
    assert set(arquivos["Arquivo"]) == {dp.ARQ_SINESP, dp.ARQ_SINESP_CATALOGO}
    cobertura = app.dataframe[2].value  # catálogo com cobertura por indicador
    assert len(cobertura) == 12 and cobertura["Última competência"].isin(["2026-09", "2026-08"]).all()
    assert cobertura.loc[cobertura["Última competência"].eq("2026-08"), "Abrangência"].tolist() == ["Polícia Rodoviária Federal"]
    assert "Regras do ETL" in [s.value for s in app.subheader] and "Procedimento de atualização dos dados" in [s.value for s in app.subheader]
    assert "README.md" in corpo and "não** baixa dados" in corpo
    for ausente in ("SSP", "Fato Comunicado", "Prefeitura"):
        assert ausente not in corpo, ausente
    assert not app.error


# -------------------------------------------------------------------------- clone limpo e falhas
def _copiar_projeto_minimo(destino, *, com_dados: bool = True):
    raiz = project_path()
    shutil.copytree(raiz / "dashboard", destino / "dashboard", ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    (destino / "scripts").mkdir()
    shutil.copy(raiz / "scripts" / "painel_streamlit.py", destino / "scripts" / "painel_streamlit.py")  # a entrada só precisa do pacote dashboard
    if not com_dados:
        shutil.rmtree(destino / "dashboard" / "data_publica")


def _executar_no_clone(destino, codigo: str) -> subprocess.CompletedProcess:
    ambiente = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8"}
    return subprocess.run([sys.executable, "-c", textwrap.dedent(codigo)], cwd=destino, capture_output=True, text=True, encoding="utf-8",
                          timeout=300, env=ambiente)


def test_funciona_em_clone_limpo_sem_dados_brutos_nem_ssp(tmp_path):
    _copiar_projeto_minimo(tmp_path)
    assert not (tmp_path / "dados").exists() and not (tmp_path / "atualizacao").exists()
    assert sorted(p.name for p in (tmp_path / "dashboard" / "data_publica").iterdir()) == sorted(
        [dp.ARQ_SINESP, dp.ARQ_SINESP_CATALOGO, dp.ARQ_MANIFESTO, "LEIAME.md"])
    resultado = _executar_no_clone(tmp_path, """
        from streamlit.testing.v1 import AppTest
        for pagina in ("home", "sinesp", "quality"):
            app = AppTest.from_file(f"dashboard/pages/{pagina}.py", default_timeout=120).run()
            assert not app.exception and not app.error, (pagina, [e.value for e in app.exception], [e.value for e in app.error])
        entrada = AppTest.from_file("scripts/painel_streamlit.py", default_timeout=120).run()
        assert not entrada.exception and not entrada.error
        quality = AppTest.from_file("dashboard/pages/quality.py", default_timeout=120).run()
        assert any("não está presente" in m.value for m in quality.markdown), "esperado aviso de acervo ausente"
        print("OK")
    """)
    assert resultado.returncode == 0 and "OK" in resultado.stdout, resultado.stderr[-1500:]


def test_ausencia_dos_arquivos_de_dados_mostra_erro_explicito_sem_derrubar_a_aplicacao(tmp_path):
    _copiar_projeto_minimo(tmp_path, com_dados=False)
    resultado = _executar_no_clone(tmp_path, """
        from streamlit.testing.v1 import AppTest
        for pagina in ("sinesp", "quality", "home"):
            app = AppTest.from_file(f"dashboard/pages/{pagina}.py", default_timeout=120).run()
            assert not app.exception, (pagina, [e.value for e in app.exception])
            assert app.error and "Dados indisponíveis" in app.error[0].value, pagina
            assert any("Nenhum valor foi preenchido" in i.value for i in app.info), pagina
        print("OK")
    """)
    assert resultado.returncode == 0 and "OK" in resultado.stdout, resultado.stderr[-1500:]


def test_esquema_invalido_mostra_erro_explicito(tmp_path):
    _copiar_projeto_minimo(tmp_path)
    caminho = tmp_path / "dashboard" / "data_publica" / dp.ARQ_SINESP
    caminho.write_text(caminho.read_text(encoding="utf-8").replace("ano,mes,evento", "ano,mes,indicador", 1), encoding="utf-8", newline="\n")
    resultado = _executar_no_clone(tmp_path, """
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file("dashboard/pages/sinesp.py", default_timeout=120).run()
        assert not app.exception and app.error and "Dados indisponíveis" in app.error[0].value, [e.value for e in app.error]
        assert "squema" in app.error[0].value, app.error[0].value
        print("OK")
    """)
    assert resultado.returncode == 0 and "OK" in resultado.stdout, resultado.stderr[-1500:]


def test_integridade_divergente_e_sinalizada_na_pagina_de_qualidade(tmp_path):
    _copiar_projeto_minimo(tmp_path)
    caminho = tmp_path / "dashboard" / "data_publica" / dp.ARQ_SINESP
    conteudo = caminho.read_text(encoding="utf-8")
    linhas = conteudo.splitlines()
    alvo = next(i for i, l in enumerate(linhas) if l.startswith("2023,5,Homicídio doloso,Estadual"))
    partes = linhas[alvo].split(",")
    partes[-1] = str(int(partes[-1]) + 1)  # altera um valor sem tocar no esquema: o hash deixa de conferir
    linhas[alvo] = ",".join(partes)
    caminho.write_text("\n".join(linhas) + "\n", encoding="utf-8", newline="\n")
    resultado = _executar_no_clone(tmp_path, """
        from streamlit.testing.v1 import AppTest
        app = AppTest.from_file("dashboard/pages/quality.py", default_timeout=120).run()
        assert not app.exception and any("não coincidem com o manifesto" in e.value for e in app.error), [e.value for e in app.error]
        print("OK")
    """)
    assert resultado.returncode == 0 and "OK" in resultado.stdout, resultado.stdout[-500:] + resultado.stderr[-1500:]


# ------------------------------------------------------------------ versão dos dados e atualização
def test_paginas_mostram_versao_fonte_ultima_competencia_e_como_se_atualiza():
    manifesto = dp.carregar_manifesto()
    sinesp = _pagina("sinesp")
    legendas = " ".join(c.value for c in sinesp.caption)
    assert manifesto["versao"] in legendas and "última competência disponível: 2026-09" in legendas and "2026 é parcial" in legendas
    assert "janeiro/2020 a setembro/2026" in legendas  # período na legenda da fonte, derivado dos dados
    corpo = " ".join(m.value for m in sinesp.markdown) + " ".join(m.value for e in sinesp.expander for m in e.markdown)
    assert "MJSP" in corpo
    qualidade = _pagina("quality")
    texto = _texto(qualidade) + " ".join(e.label for e in qualidade.expander)
    assert manifesto["versao"] in texto and "Aprovação" in texto and "aprovada em" in texto
    assert "verificar" in texto and "preparar" in texto and "aprovar" in texto and "README.md" in texto


def test_painel_funciona_apos_nova_competencia_aprovada_sem_mes_fixo_no_codigo(tmp_path):
    """Dados de uma atualização (candidata) com 2026-10 e a PRF em 2026-09: cobertura por série, sem mês fixo no código."""
    from test_atualizacao_fluxo import _com_proxima_competencia, _entradas  # fixtures sintéticas
    from src.pipeline import atualizacao_dados as au

    ativa = tmp_path / "ativa"
    shutil.copytree(dp.DIRETORIO_DADOS, ativa)
    mensal = _com_proxima_competencia(dp.carregar_sinesp(ativa))
    candidato = au.preparar(ativa=ativa, staging_root=tmp_path / "staging", entradas_sinesp=_entradas(tmp_path / "entradas", mensal))
    assert candidato.validacao.erros == []
    clone = tmp_path / "clone"
    clone.mkdir()
    _copiar_projeto_minimo(clone)
    shutil.rmtree(clone / "dashboard" / "data_publica")
    shutil.copytree(candidato.diretorio / "dados", clone / "dashboard" / "data_publica")
    resultado = _executar_no_clone(clone, """
        from streamlit.testing.v1 import AppTest
        for pagina in ("home", "sinesp", "quality"):
            app = AppTest.from_file(f"dashboard/pages/{pagina}.py", default_timeout=120).run()
            assert not app.exception and not app.error, (pagina, [e.value for e in app.exception], [e.value for e in app.error])
        sinesp = AppTest.from_file("dashboard/pages/sinesp.py", default_timeout=120).run()
        sinesp.selectbox(key="indicador").select("Suicídio").run()
        assert any("2026 contém apenas janeiro a outubro" in i.value for i in sinesp.info), [i.value for i in sinesp.info]
        assert "Janeiro–outubro de 2026" in sinesp.metric[1].label, sinesp.metric[1].label
        assert "vs janeiro–outubro de 2025" in sinesp.metric[1].delta
        sinesp.selectbox(key="indicador").select("Mortes no trânsito").run()
        sinesp.selectbox(key="abrangencia").select("Polícia Rodoviária Federal").run()  # série PRF: ainda até setembro
        assert any("2026 contém apenas janeiro a setembro" in i.value for i in sinesp.info), [i.value for i in sinesp.info]
        assert "Janeiro–setembro de 2026" in sinesp.metric[1].label, sinesp.metric[1].label
        home = AppTest.from_file("dashboard/pages/home.py", default_timeout=120).run()
        assert any("outubro/2026" in m.value for m in list(home.markdown) + list(home.caption))  # período lido do manifesto
        quality = AppTest.from_file("dashboard/pages/quality.py", default_timeout=120).run()
        assert any("2026-10" in m.value for m in quality.markdown)
        print("OK")
    """)
    assert resultado.returncode == 0 and "OK" in resultado.stdout, resultado.stdout[-800:] + resultado.stderr[-1500:]


# ------------------------------------------------------------------ Etapa 21: seta do delta e ordem dos filtros
def test_seta_do_delta_acompanha_o_sinal_da_diferenca():
    from streamlit.proto.Metric_pb2 import Metric

    app = _pagina("sinesp")
    _sem_erros(app)
    anual, periodo = app.metric[0], app.metric[1]
    assert anual.value == "29" and anual.delta == "−7 vs 2024"  # 2025 (29) − 2024 (36) = −7, valor preservado
    assert Metric.MetricDirection.Name(anual.proto.direction) == "DOWN"  # antes aparecia seta para cima ao lado do −7
    assert periodo.delta.startswith("+4") and Metric.MetricDirection.Name(periodo.proto.direction) == "UP"
    app.selectbox(key="indicador").select("Mortes a esclarecer (sem indício de crime)").run()
    assert app.metric[0].delta == "0 vs 2024" and Metric.MetricDirection.Name(app.metric[0].proto.direction) == "NONE"  # sem diferença: sem seta


def test_filtros_na_ordem_categoria_indicador_abrangencia_e_depois_anos_e_meses():
    app = _pagina("sinesp")
    assert [s.label for s in app.selectbox][:3] == ["Categoria", "Indicador", "Abrangência"]
    assert [s.label for s in app.select_slider][:2] == ["Período (anos)", "Meses"]
    assert app.selectbox(key="categoria").value == "Todas" and app.selectbox(key="indicador").value == "Homicídio doloso"
