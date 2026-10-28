"""Testes automatizados da interface Streamlit (``streamlit.testing.v1.AppTest``).

Verificam carregamento, filtros e mensagens da página única e de cada uma das suas quatro seções (Apresentação, Indicadores Sinesp,
Violência doméstica SSP/SC e Qualidade/metodologia). Não substituem a inspeção visual no navegador, que não é executada por estes testes.
"""

import os
import shutil
import subprocess
import sys
import textwrap

import pytest
from streamlit.testing.v1 import AppTest

from dashboard import dados_publicos as dp
from apoio_painel import cartoes, escolher_serie, texto_dos_cartoes
from src.pipeline.utils import project_path

PAGINAS = ("home", "sinesp", "violencia_domestica", "quality")


def _pagina(nome: str) -> AppTest:
    return AppTest.from_file(str(project_path("dashboard", "pages", f"{nome}.py")), default_timeout=120).run()


def _sem_erros(app: AppTest):
    assert not app.exception, [e.value for e in app.exception]
    assert not app.error, [e.value for e in app.error]


def _texto(app: AppTest) -> str:
    return " ".join([m.value for m in app.markdown] + [i.value for i in app.info] + [c.value for c in app.caption] + [w.value for w in app.warning]
                    + [texto_dos_cartoes(app)])


# ----------------------------------------------------------------------------- entrada: página única
def test_entrada_e_uma_unica_pagina_com_as_quatro_secoes_em_ordem():
    app = AppTest.from_file(str(project_path("scripts", "painel_streamlit.py")), default_timeout=180).run()
    _sem_erros(app)
    assert [t.value for t in app.title] == ["DADOS DA SEGURANÇA PÚBLICA DE JOINVILLE/SC"]
    assert [h.value for h in app.header] == ["Apresentação", "Indicadores Sinesp — Joinville/SC", "VIOLÊNCIA DOMÉSTICA — SSP/SC",
                                             "Qualidade dos dados", "Fontes, metodologia e limitações"]  # ordem vertical obrigatória
    texto = project_path("scripts", "painel_streamlit.py").read_text(encoding="utf-8")
    assert 'TITULO = "DADOS DA SEGURANÇA PÚBLICA DE JOINVILLE/SC"' in texto and "page_title=TITULO" in texto and 'layout="wide"' in texto
    assert "st.navigation(" not in texto and "st.Page(" not in texto  # sem navegação entre páginas
    for secao in ("home.py", "sinesp.py", "violencia_domestica.py", "quality.py"):
        assert f'"{secao}"' in texto and project_path("dashboard", "pages", secao).is_file()
    assert sorted(p.name for p in project_path("dashboard", "pages").glob("*.py")) == ["home.py", "quality.py", "sinesp.py", "violencia_domestica.py"]
    # a página única reúne todos os filtros: Indicador (série com abrangência), anos, meses e a categoria própria da SSP/SC
    assert [s.label for s in app.selectbox] == ["Indicador", "Categoria (SSP/SC)"]
    assert [s.label for s in app.select_slider] == ["Período (anos)", "Meses"]
    assert "Abrangência" not in [s.label for s in app.selectbox] and "Categoria" not in [s.label for s in app.selectbox]


@pytest.mark.parametrize("nome", PAGINAS)
def test_cada_pagina_executa_sem_excecoes(nome):
    _sem_erros(_pagina(nome))


def test_apresentacao_mostra_fonte_periodo_real_e_destaques_calculados():
    app = _pagina("home")
    texto = _texto(app)
    assert "deploy" not in texto and "streamlit.app" not in texto  # a seção não trata de publicação
    assert "janeiro/2020 a setembro/2026" in texto and "2026 é parcial" in texto
    assert "Sinesp/MJSP" in texto and "Mortes no trânsito (Polícia Rodoviária Federal) até 2026-08" in texto
    # fonte e período (4 números da base) e os destaques calculados (homicídio 2025, homicídio e tentativa em janeiro–setembro de 2026)
    lista = cartoes(app)
    assert [c.value for c in lista] == ["2020–2026", "911", "12", "2026-09", "29", "25", "77"]
    destaques = lista[4:]
    assert "−7 vs 2024" in destaques[0].delta and "+4 vs janeiro–setembro de 2025" in destaques[1].delta
    assert "+34 vs janeiro–setembro de 2025" in destaques[2].delta
    assert [c.direction for c in destaques] == ["DOWN", "UP", "UP"]  # a seta acompanha o sinal da diferença
    # cada card identifica indicador, abrangência, unidade, período e base de comparação em texto que não é cortado
    for trecho in ("Estadual · vítimas · ano completo", "Estadual · vítimas · ano parcial",
                   "Comparado com o ano completo de 2024.", "Comparado com janeiro–setembro de 2025 (mesma duração)."):
        assert trecho in texto, trecho
    for ausente in ("Prefeitura", "Fato Comunicado"):
        assert ausente not in texto, ausente
    assert [s.value for s in app.subheader] == ["Destaques (não mudam com os filtros)", "Principais achados"]
    assert "Pergunta, unidades e limites da leitura" in [e.label for e in app.expander]


# ------------------------------------------------------------------------------------------- Sinesp
def test_filtros_dependentes_e_restauracao_preservam_modo_compacto():
    app = _pagina("sinesp")
    assert [s.label for s in app.selectbox] == ["Indicador"]  # sem Categoria e sem Abrangência
    assert [s.label for s in app.select_slider] == ["Período (anos)", "Meses"]
    assert [b.label for b in app.button] == ["Restaurar filtros"]
    app.select_slider(key="periodo_anos").set_value((2022, 2024)).run()
    escolher_serie(app, "Mandado de prisão cumprido", "Polícia Federal")  # a PF só existe desde 2025: o período volta a ser o da série
    _sem_erros(app)
    assert app.select_slider(key="periodo_anos").options == ["2025", "2026"]
    assert app.select_slider(key="periodo_anos").value == (2025, 2026)
    app.select_slider(key="periodo_meses").set_value((1, 3)).run()
    app.toggle(key="modo_compacto").set_value(True).run()
    next(b for b in app.button if b.label == "Restaurar filtros").click().run()
    _sem_erros(app)
    assert app.selectbox(key="serie").value == "Homicídio doloso — Estadual"
    assert app.select_slider(key="periodo_anos").value == (2020, 2026)
    assert app.select_slider(key="periodo_meses").value == (1, 12)
    assert app.toggle(key="modo_compacto").value is True
    assert [c.value for c in cartoes(app)] == ["29", "25", "81 de 81"]


def test_sinesp_valores_padrao_e_filtros():
    app = _pagina("sinesp")
    _sem_erros(app)
    assert app.selectbox(key="serie").value == "Homicídio doloso — Estadual"
    lista = cartoes(app)
    assert [c.value for c in lista][:2] == ["29", "25"]  # último ano completo (2025) e janeiro–setembro de 2026
    assert "+4 vs janeiro–setembro de 2025" in lista[1].delta and "−7 vs 2024" in lista[0].delta
    assert "Janeiro–setembro de 2026" in lista[1].label and "Homicídio doloso · Estadual" in lista[1].detalhe  # abrangência explícita no card
    assert any("2026 contém apenas janeiro a setembro" in i.value for i in app.info)
    assert len(app.tabs) == 5

    app.select_slider[0].set_value((2020, 2025)).run()  # sem 2026: o aviso de ano parcial desaparece
    _sem_erros(app)
    assert not any("2026 contém apenas" in i.value for i in app.info)
    assert [c.value for c in cartoes(app)][:2] == ["29", "21"]  # janeiro–setembro passa a ser 2025

    opcoes = app.selectbox(key="serie").options  # todas as abrangências continuam disponíveis, dentro do nome do indicador
    assert "Mandado de prisão cumprido — Polícia Federal" in opcoes and "Mandado de prisão cumprido — Estadual" in opcoes
    escolher_serie(app, "Mandado de prisão cumprido", "Polícia Federal")
    _sem_erros(app)
    assert any("a partir de janeiro/2025" in w.value for w in app.warning)  # ausência de cobertura explícita, não zero
    assert "mandados cumpridos" in " ".join(m.value for m in app.markdown)  # unidade distinta de vítimas


def test_sinesp_serie_prf_vai_ate_agosto_sem_preenchimento():
    app = _pagina("sinesp")
    escolher_serie(app, "Mortes no trânsito", "Polícia Rodoviária Federal")
    _sem_erros(app)
    assert any("2026 contém apenas janeiro a agosto" in i.value for i in app.info)
    assert "Janeiro–agosto de 2026" in cartoes(app)[1].label and "vs janeiro–agosto de 2025" in cartoes(app)[1].delta
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
    assert len(app.selectbox(key="serie").options) == len(catalogo) == 12  # nenhuma série (nem PF/PRF) some ao remover o filtro de abrangência
    for linha in catalogo.itertuples():
        escolher_serie(app, linha.evento, linha.abrangencia)
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
    escolher_serie(app, "Roubo seguido de morte (latrocínio)")
    _sem_erros(app)
    assert any("Método IQR não informativo" in w.value and "IQR igual a zero" in w.value for w in app.warning)
    assert not any("Método informativo" in i.value for i in app.info)
    escolher_serie(app, "Mandado de prisão cumprido", "Polícia Federal")
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
    assert "Prefeitura" not in corpo
    assert "fonte separada e em validação" in corpo and "não tem definição oficial confirmada" in corpo  # a SSP/SC aparece só como limitação
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
        [dp.ARQ_SINESP, dp.ARQ_SINESP_CATALOGO, dp.ARQ_MANIFESTO])
    resultado = _executar_no_clone(tmp_path, """
        from streamlit.testing.v1 import AppTest
        for pagina in ("home", "sinesp", "violencia_domestica", "quality"):
            app = AppTest.from_file(f"dashboard/pages/{pagina}.py", default_timeout=120).run()
            assert not app.exception and not app.error, (pagina, [e.value for e in app.exception], [e.value for e in app.error])
        vd = AppTest.from_file("dashboard/pages/violencia_domestica.py", default_timeout=120).run()
        assert any("não são distribuídos" in i.value for i in vd.info), "esperado o aviso de que a SSP/SC não é distribuída (sem o CSV local)"
        assert not vd.selectbox  # sem dados, não há filtro nem número da SSP/SC
        entrada = AppTest.from_file("scripts/painel_streamlit.py", default_timeout=180).run()
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
        entrada = AppTest.from_file("scripts/painel_streamlit.py", default_timeout=180).run()  # a página única também falha de forma explícita
        assert not entrada.exception and entrada.error and "Dados indisponíveis" in entrada.error[0].value
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
    assert "janeiro/2020 a setembro/2026" in " ".join(c.value for c in sinesp.caption)  # período na legenda da fonte, derivado dos dados
    qualidade = _pagina("quality")
    legendas = " ".join(c.value for c in qualidade.caption)
    assert manifesto["versao"] in legendas and "última competência disponível: 2026-09" in legendas and "2026 é parcial" in legendas
    corpo = " ".join(m.value for m in qualidade.markdown) + " ".join(m.value for e in qualidade.expander for m in e.markdown)
    assert "MJSP" in corpo
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
    resultado = _executar_no_clone(clone, f"""
        import sys
        sys.path.insert(0, r"{project_path('tests')}")
        from apoio_painel import cartoes, texto_dos_cartoes
        from streamlit.testing.v1 import AppTest
        for pagina in ("home", "sinesp", "quality"):
            app = AppTest.from_file(f"dashboard/pages/{{pagina}}.py", default_timeout=120).run()
            assert not app.exception and not app.error, (pagina, [e.value for e in app.exception], [e.value for e in app.error])
        sinesp = AppTest.from_file("dashboard/pages/sinesp.py", default_timeout=120).run()
        sinesp.selectbox(key="serie").select("Suicídio — Estadual").run()
        assert any("2026 contém apenas janeiro a outubro" in i.value for i in sinesp.info), [i.value for i in sinesp.info]
        assert "Janeiro–outubro de 2026" in cartoes(sinesp)[1].label, cartoes(sinesp)[1].label
        assert "vs janeiro–outubro de 2025" in cartoes(sinesp)[1].delta
        sinesp.selectbox(key="serie").select("Mortes no trânsito — Polícia Rodoviária Federal").run()  # série PRF: ainda até setembro
        assert any("2026 contém apenas janeiro a setembro" in i.value for i in sinesp.info), [i.value for i in sinesp.info]
        assert "Janeiro–setembro de 2026" in cartoes(sinesp)[1].label, cartoes(sinesp)[1].label
        home = AppTest.from_file("dashboard/pages/home.py", default_timeout=120).run()
        assert "outubro/2026" in texto_dos_cartoes(home)  # período lido do manifesto (agora nos cards)
        quality = AppTest.from_file("dashboard/pages/quality.py", default_timeout=120).run()
        assert any("2026-10" in m.value for m in quality.markdown)
        print("OK")
    """)
    assert resultado.returncode == 0 and "OK" in resultado.stdout, resultado.stdout[-800:] + resultado.stderr[-1500:]


# ------------------------------------------------------------------ seta do delta e filtros
def test_seta_do_delta_acompanha_o_sinal_da_diferenca():
    app = _pagina("sinesp")
    _sem_erros(app)
    anual, periodo = cartoes(app)[0], cartoes(app)[1]
    assert anual.value == "29" and anual.delta == "−7 vs 2024"  # 2025 (29) − 2024 (36) = −7, valor preservado
    assert anual.direction == "DOWN"  # antes aparecia seta para cima ao lado do −7
    assert periodo.delta.startswith("+4") and periodo.direction == "UP"
    escolher_serie(app, "Mortes a esclarecer (sem indício de crime)")
    assert cartoes(app)[0].delta == "0 vs 2024" and cartoes(app)[0].direction == "NONE"  # sem diferença: sem seta


def test_filtros_na_ordem_indicador_depois_anos_e_meses_sem_abrangencia_redundante():
    app = _pagina("sinesp")
    assert [s.label for s in app.selectbox] == ["Indicador"]
    assert [s.label for s in app.select_slider][:2] == ["Período (anos)", "Meses"]
    assert app.selectbox(key="serie").value == "Homicídio doloso — Estadual"
    opcoes = app.selectbox(key="serie").options
    assert all(" — " in o for o in opcoes)  # toda opção traz a sua abrangência no nome
    assert {o.split(" — ")[1] for o in opcoes} == {"Estadual", "Polícia Federal", "Polícia Rodoviária Federal"}


# ------------------------------------------------------------------ seção SSP/SC
def test_violencia_domestica_ssp_sc_com_filtro_proprio_e_separacao_metodologica():
    from dashboard import dados_ssp

    if dados_ssp.caminho_disponivel() is None:
        pytest.skip("CSV local da SSP/SC ausente (clone limpo): a seção mostra a limitação, testada no teste do clone limpo")
    app = _pagina("violencia_domestica")
    _sem_erros(app)
    assert [h.value for h in app.header] == ["VIOLÊNCIA DOMÉSTICA — SSP/SC"]
    assert any("Fonte em validação" in w.value and "Fato Comunicado" in w.value for w in app.warning)
    assert [c.value for c in cartoes(app)] == ["2023–2024", "216", "27", "Em validação"]  # 216 observações e 27 zeros publicados
    assert app.selectbox(key="vd_categoria").value == "Todas as categorias" and len(app.selectbox(key="vd_categoria").options) == 10  # Todas + 9
    app.selectbox(key="vd_categoria").select("Ameaça").run()
    _sem_erros(app)
    assert [c.value for c in cartoes(app)][:2] == ["1.957", "2.085"]  # totais de 2023 e 2024: valores oficiais conferidos
    assert cartoes(app)[1].delta == "+128 vs 2023" and cartoes(app)[1].direction == "UP"
    texto = _texto(app)
    for proibido in ("vítimas de violência doméstica", "total geral", "Sinesp e SSP/SC somados"):
        assert proibido not in texto, proibido
    # o filtro da SSP/SC não herda nem altera o do Sinesp: a seção sozinha não tem os filtros do Sinesp
    assert not app.select_slider


def test_pagina_unica_ssp_sc_nao_muda_os_numeros_do_sinesp():
    app = AppTest.from_file(str(project_path("scripts", "painel_streamlit.py")), default_timeout=180).run()
    _sem_erros(app)
    antes = [c.value for c in cartoes(app)]
    from dashboard import dados_ssp

    if dados_ssp.caminho_disponivel() is not None:
        app.selectbox(key="vd_categoria").select("Injúria").run()
        _sem_erros(app)
        assert app.selectbox(key="serie").value == "Homicídio doloso — Estadual"  # o filtro da SSP/SC não mexe no do Sinesp
        assert [c.value for c in cartoes(app)][4:10] == antes[4:10]  # destaques e cards do Sinesp inalterados
