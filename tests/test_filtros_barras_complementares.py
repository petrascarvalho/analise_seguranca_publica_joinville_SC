"""Etapa 20.4 — filtros (categoria, indicador, ano, mês), gráficos de barras e protótipo separado dos indicadores complementares."""

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard import calculos, graficos
from dashboard import dados_publicos as dp
from apoio_painel import cartoes, escolher_serie
from src.pipeline.utils import project_path

ANOS = list(range(2020, 2027))
PROTOTIPO = project_path("dados", "processados", "complementares", "indicadores_complementares_joinville.csv")  # acervo local, fora do Git
precisa_prototipo = pytest.mark.skipif(not PROTOTIPO.is_file(), reason="protótipo complementar local ausente (fora do Git)")


@pytest.fixture(scope="module")
def sinesp():
    return dp.carregar_sinesp()


def _aba(app, nome):
    """A página executa só a aba selecionada (st.tabs com on_change="rerun"): seleciona a aba e executa de novo."""
    app.session_state["aba_analise"] = nome
    return app.run()


def _em_cada_aba(app):
    """Percorre as quatro abas de análise e devolve, a cada uma, o app já executado com ela selecionada."""
    for nome in ("Evolução", "Comparações", "Meses e tendência", "Estatísticas e meses incomuns"):
        yield nome, _aba(app, nome)


def _pagina():
    return AppTest.from_file(str(project_path("dashboard", "pages", "sinesp.py")), default_timeout=180).run()


# ------------------------------------------------------------------------------------------------ soma por meses
def test_soma_no_periodo_exige_todos_os_meses_publicados(sinesp):
    hom = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    r = calculos.soma_no_periodo(hom, 1, 3).set_index("ano")["soma"]
    for ano in ANOS:
        esperado = int(hom[(hom["ano"] == ano) & (hom["mes"] <= 3)]["valor"].sum())
        assert int(r[ano]) == esperado, ano
    assert int(r[2026]) == 11  # jan–mar/2026: 8 + 1 + 2
    assert calculos.soma_no_periodo(hom, 10, 12).set_index("ano")["soma"].isna()[2026]  # out–dez/2026 ainda não publicados: sem soma (não é zero)
    prf = calculos.serie_sinesp(sinesp, "Mortes no trânsito", "Polícia Rodoviária Federal")
    assert int(calculos.soma_no_periodo(prf, 1, 8).set_index("ano")["soma"][2026]) == 6
    assert pd.isna(calculos.soma_no_periodo(prf, 1, 9).set_index("ano")["soma"][2026])  # PRF termina em agosto
    with pytest.raises(ValueError, match="única série"):
        calculos.soma_no_periodo(pd.concat([hom, prf]), 1, 3)


# ---------------------------------------------------------------------------------------------------- filtros
def test_filtros_visiveis_indicador_com_abrangencia_anos_e_meses():
    app = _pagina()
    assert not app.exception and not app.error
    assert [s.label for s in app.selectbox] == ["Indicador"]  # sem Categoria e sem Abrangência como filtros separados
    assert [s.label for s in app.select_slider][:2] == ["Período (anos)", "Meses"]
    opcoes = app.selectbox(key="indicador").options
    assert len(opcoes) == 11 and not [o for o in opcoes if "—" in o]  # os 11 indicadores do Sinesp para Joinville, só com o nome principal
    app.selectbox(key="indicador").select("Mandado de prisão cumprido").run()
    assert app.selectbox(key="abrangencia").options == ["Estadual", "Polícia Federal"]  # PF preservada como segunda escolha
    assert "Mortes no trânsito" in opcoes  # a série da PRF continua disponível
    app.selectbox(key="indicador").select("Homicídio doloso").run()
    assert app.selectbox(key="indicador").value == "Homicídio doloso" and "abrangencia" not in [s.key for s in app.selectbox]


def test_filtro_de_meses_chega_aos_kpis_e_aos_resultados_mensais():
    app = _pagina()
    app.select_slider[1].set_value((1, 3)).run()
    assert not app.exception and not app.error
    rotulos = {m.label: m for m in cartoes(app)}
    kpi = next(m for r, m in rotulos.items() if r.startswith("Jan–Mar de 2026"))
    assert kpi.value == "11" and "vs 2025" in kpi.delta  # 8 + 1 + 2 em jan–mar/2026
    assert rotulos["Meses filtrados"].value == "3 de 12" and rotulos["Meses com valor publicado"].value == "21 de 21"  # 7 anos × 3 meses
    assert any("Filtro de meses ativo: Jan–Mar" in c.value for c in app.caption)
    app.select_slider[1].set_value((10, 12)).run()  # meses ainda não publicados em 2026: o KPI usa o último ano que os tem
    assert not app.exception and any(m.label.startswith("Out–Dez de 2025") for m in cartoes(app))
    app.select_slider[1].set_value((1, 12)).run()
    assert [m.value for m in cartoes(app)][:2] == ["29", "25"]  # sem filtro: os resultados aprovados


def test_filtro_de_meses_preserva_o_modo_compacto_e_funciona_na_prf():
    app = _pagina()
    app.toggle[0].set_value(True).run()
    escolher_serie(app, "Mortes no trânsito", "Polícia Rodoviária Federal")
    app.select_slider[1].set_value((1, 9)).run()
    assert app.toggle[0].value is True and not app.exception and not app.error
    assert any(m.label.startswith("Jan–Set de 2025") for m in cartoes(app))  # PRF 2026 só vai até agosto: o último ano com jan–set é 2025


def test_etapa_10_e_identificada_como_material_historico_independente_dos_filtros():
    app = _pagina()
    assert not any("Etapa 10" in t.label for t in app.tabs)  # fora das abas de análise
    assert "Quatro gráficos de referência (fixos, não mudam com os filtros)" in [e.label for e in app.expander]  # seção expansível
    assert any("Estes quatro gráficos são fixos" in w.value for w in app.warning)


# --------------------------------------------------------------------------------------------------- barras
def test_evolucao_anual_e_linha_com_marcadores_e_mensal_e_barras_com_os_valores_da_tabela(sinesp):
    anual = graficos.figura_serie_anual_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    linha = [l for l in anual.axes[0].lines if l.get_gid() == "linha_anual"]
    assert len(linha) == 1 and [int(v) for v in linha[0].get_ydata()] == [62, 62, 49, 55, 36, 29] and linha[0].get_marker() == "o"  # poucos pontos: linha com marcadores
    assert [t.get_text() for t in anual.axes[0].texts if t.get_text().isdigit()] == ["62", "62", "49", "55", "36", "29"]  # valor escrito UMA vez, acima de cada ponto
    assert [b.get_height() for b in anual.axes[0].patches if b.get_gid() == "barra_anual"] == [62, 62, 49, 55, 36, 29]  # gráfico combinado: barras na mesma escala
    mensal = graficos.figura_mensal_sinesp(sinesp, "Homicídio doloso", "Estadual", [2025, 2026])
    assert not mensal.axes[0].lines
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    for ano in (2025, 2026):
        valores = [int(v) for v in serie[serie["ano"] == ano]["valor"]]
        assert [int(b.get_height()) for b in mensal.axes[0].patches if b.get_gid() == f"mensal_{ano}"] == valores
    with graficos.modo_compacto():
        compacta = graficos.figura_mensal_sinesp(sinesp, "Homicídio doloso", "Estadual", [2024, 2025, 2026])
    assert [int(b.get_height()) for b in compacta.axes[0].patches if b.get_gid() == "mensal_2026"] == [int(v) for v in serie[serie["ano"] == 2026]["valor"]]
    assert compacta.axes[0].get_ylim()[0] == 0


# ------------------------------------------------------------------------------- indicadores complementares
def test_sinesp_continua_com_os_11_eventos_911_observacoes_e_manifesto_integro(sinesp):
    assert sinesp.shape == (911, 6) and sinesp["evento"].nunique() == 11
    assert not any(t in " ".join(sinesp["evento"].unique()).lower() for t in ("furto", "estupro", "tráfico", "trafico"))
    assert dp.verificar_integridade()["integro"].all() and dp.carregar_manifesto()["versao"] == "20261027T114400Z"
    assert sorted(p.name for p in dp.DIRETORIO_DADOS.iterdir()) == sorted([dp.ARQ_SINESP, dp.ARQ_SINESP_CATALOGO, dp.ARQ_MANIFESTO])  # nada complementar nos dados do painel


@precisa_prototipo
def test_prototipo_complementar_e_separado_explicita_fonte_e_nao_valida_divergentes():
    quadro = pd.read_csv(PROTOTIPO, dtype=str, keep_default_na=False)
    assert list(quadro.columns) == ["fonte", "publicador", "data_publicacao", "municipio", "ano", "indicador", "unidade", "valor", "url_evidencia", "situacao", "observacao"]
    assert quadro["municipio"].eq("Joinville").all() and quadro["url_evidencia"].str.startswith(("https://www.joinville.sc.gov.br/", "https://portalelegis.alesc.sc.gov.br/")).all()
    assert not quadro["situacao"].str.contains("^validado", regex=True).any()  # nenhum dado complementar está validado
    d = quadro[(quadro["ano"] == "2023") & quadro["indicador"].isin(["Furtos", "Roubos"])]
    assert sorted(zip(d["indicador"], d["valor"])) == [("Furtos", "1351"), ("Furtos", "8865"), ("Roubos", "361"), ("Roubos", "933")]
    assert d["situacao"].eq("divergente").all()  # os dois pares ficam divergentes, sem escolher um
    vazios = quadro[quadro["valor"] == ""]
    assert len(vazios) == 2 and vazios["situacao"].eq("não localizado").all() and vazios["ano"].eq("2023").all()  # ausência = vazio, nunca zero
    assert not quadro["indicador"].str.contains("Estupro|Tráfico", case=False).any()  # só havia variação %: nenhuma contagem foi estimada
    anual = quadro.assign(v=pd.to_numeric(quadro["valor"], errors="coerce")).pivot_table(index="indicador", columns="ano", values="v", aggfunc="first")
    for ano in ("2024", "2025"):  # subconjuntos não excedem o total (e não são somados a ele)
        assert anual.loc["Furtos de veículos", ano] + anual.loc["Furtos de residência", ano] < anual.loc["Furtos", ano]
        assert anual.loc["Roubos de veículos", ano] + anual.loc["Roubos de residência", ano] < anual.loc["Roubos", ano]
    latrocinio = quadro[quadro["indicador"] == "Latrocínio"].iloc[0]
    sinesp_latrocinio = dp.carregar_sinesp().query("evento == 'Roubo seguido de morte (latrocínio)' and ano == 2023")["valor"].sum()
    assert latrocinio["valor"] == "0" and int(sinesp_latrocinio) == 0  # coerente com o Sinesp


def test_documentacao_das_fontes_complementares_registra_matriz_e_divergencia():
    texto = project_path("README.md").read_text(encoding="utf-8")  # a investigação está consolidada no README (seção 4.4)
    for esperado in ("11 eventos", "8.865", "1.351", "933", "361", "divergente", "Estupro", "Tráfico de drogas", "não foram convertidas variações percentuais",
                     "nada disso foi incorporado ao painel", "https://dados.sc.gov.br/", "joinville-cidade-em-dados"):
        assert esperado.lower() in texto.lower(), esperado


# ===================================================================================== Etapa 20.5
def test_filtros_ativos_ficam_visiveis_e_analises_de_ano_completo_sao_identificadas():
    app = _pagina()
    ativos = next(m.value for m in app.markdown if m.value.startswith("**Recorte ativo:**"))
    assert "indicador **Homicídio doloso**" in ativos and "categoria" not in ativos and "Estadual" not in ativos  # o recorte mostra só o nome principal do indicador
    assert "anos **2020–2026**" in ativos and "janeiro–dezembro (12 meses)" in ativos and "visualização **completa**" in ativos
    assert not any("Análise de ano completo" in c.value for c in app.caption)  # sem filtro de meses não há o que avisar
    app.select_slider[1].set_value((4, 6)).run()
    app.toggle[0].set_value(True).run()
    ativos = next(m.value for m in app.markdown if m.value.startswith("**Recorte ativo:**"))
    assert "abril–junho (3 meses)" in ativos and "visualização **compacta**" in ativos
    avisos = []
    for nome, aba in _em_cada_aba(app):  # cada aba só executa quando selecionada
        avisos += [c.value for c in aba.caption if "Análise de ano completo (12 meses)" in c.value]
    assert len(avisos) >= 6 and all("não usa o filtro de meses" in a for a in avisos)  # anos completos, períodos, variações, anual, média móvel, acumulado, sazonalidade
    assert any(m.label.startswith("Abr–Jun de 2026") and m.value == "7" for m in cartoes(app))  # 4 + 0 + 3: soma só dos meses escolhidos, rotulada com o intervalo
    escolher_serie(app, "Suicídio")
    ativos = next(m.value for m in app.markdown if m.value.startswith("**Recorte ativo:**"))
    assert "indicador **Suicídio**" in ativos and not app.exception


def test_soma_de_alguns_meses_nunca_vira_total_anual():
    app = _pagina()
    app.select_slider[1].set_value((1, 3)).run()
    _aba(app, "Comparações")
    anual = [m for m in cartoes(app) if m.label.startswith("Último ano completo")]
    assert not anual  # com filtro de meses o KPI é rotulado pelo intervalo, nunca como "ano completo"
    assert any(m.label.startswith("Jan–Mar de 2026") for m in cartoes(app))
    tabelas = [d.value for d in app.dataframe]
    anos_completos = next(t for t in tabelas if "Cobertura" in t.columns and "Meses presentes" in t.columns)
    assert int(anos_completos.set_index("Ano").loc[2025, "Soma (vítimas)"].replace(".", "")) == 29  # total anual = 12 meses, não jan–mar


def test_perfil_mensal_em_barras_usa_mediana_e_so_anos_completos(sinesp):
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    perfil = calculos.perfil_sazonal(serie)
    for compacto in (False, True):
        with graficos.modo_compacto(compacto):
            figura = graficos.figura_sazonalidade_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
        barras = [b.get_height() for b in figura.axes[0].patches if b.get_gid() == "mediana_mensal"]
        assert barras == pytest.approx(perfil["mediana"].astype(float).tolist()) and len(barras) == 12
        assert not figura.axes[0].lines  # sem linhas
    assert any("2020–2025" in t.get_text() for t in figura.texts) or "2020–2025" in figura.sinesp_notas["interpretacao"]
    alterada = sinesp.copy()
    alterada.loc[(alterada["evento"] == "Homicídio doloso") & (alterada["ano"] == 2026) & (alterada["mes"] == 1), "valor"] = 500  # ano parcial não entra
    outra = graficos.figura_sazonalidade_sinesp(alterada, "Homicídio doloso", "Estadual", ANOS)
    assert [b.get_height() for b in outra.axes[0].patches if b.get_gid() == "mediana_mensal"] == barras
    assert graficos.figura_sazonalidade_sinesp(sinesp, "Mandado de prisão cumprido", "Polícia Federal", ANOS) is None  # 1 ano completo: sem figura


def test_documentacao_registra_o_relatorio_da_ssp_e_o_pedido_de_esclarecimento():
    texto = project_path("README.md").read_text(encoding="utf-8")
    for esperado in ("061/2024/GEAC/DINE/SSP/SC", "15/03/2024", "https://portalelegis.alesc.sc.gov.br/documentos/z1LZ8", "669", "Tabela 03", "Tabela 04",
                     "possível inconsistência editorial", "não usar 669 como total de furtos", "SEPROT", "2020 a 2026"):
        assert esperado.lower() in texto.lower(), esperado


@precisa_prototipo
def test_prototipo_registra_669_so_como_roubo_divergente():
    quadro = pd.read_csv(PROTOTIPO, dtype=str, keep_default_na=False)
    assert "669" in set(quadro["valor"]) and quadro.loc[quadro["valor"] == "669", "situacao"].eq("divergente").all()
    assert quadro.loc[quadro["valor"] == "669", "indicador"].eq("Roubos (ocorrências)").all()  # 669 só como roubo, nunca como furto
