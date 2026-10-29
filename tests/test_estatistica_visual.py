"""Etapa 20 — testes numéricos de quartis, IQR, outliers, períodos parciais, zeros, filtros e correspondência figura × tabela.

Os valores esperados são calculados de forma independente (NumPy ou contas manuais) e comparados com ``dashboard/calculos.py`` e com os
elementos desenhados pelas figuras de ``dashboard/graficos.py`` (identificados por ``gid``).
"""

import numpy as np
import pandas as pd
import pytest

from dashboard import calculos, graficos
from dashboard import dados_publicos as dp

ANOS = list(range(2020, 2027))


@pytest.fixture(scope="module")
def sinesp():
    return dp.carregar_sinesp()


def _serie(valores, evento="Evento sintético", abrangencia="Estadual", unidade="vítimas", ano_inicial=2020):
    """Série mensal sintética (meses consecutivos); ``None`` vira ausência (<NA>)."""
    linhas = [{"ano": ano_inicial + i // 12, "mes": i % 12 + 1, "evento": evento, "abrangencia": abrangencia, "unidade": unidade, "valor": v}
              for i, v in enumerate(valores)]
    quadro = pd.DataFrame(linhas)
    quadro["valor"] = quadro["valor"].astype("Int64")
    return quadro


def _linhas_por_gid(figura, gid):
    return [l for l in figura.axes[0].lines if l.get_gid() == gid]


def _ydata(linha):
    return np.array(linha.get_ydata(), dtype="float64")


# ------------------------------------------------------------------------------------------------ quartis e IQR
def test_quartis_iqr_e_limites_de_tukey_com_valores_conhecidos():
    q = calculos.quartis_iqr(list(range(1, 9)))  # 1..8: interpolação linear → Q1 = 2,75; Q3 = 6,25
    assert (q["n"], q["minimo"], q["maximo"]) == (8, 1.0, 8.0)
    assert q["q1"] == pytest.approx(2.75) and q["mediana"] == pytest.approx(4.5) and q["q3"] == pytest.approx(6.25)
    assert q["iqr"] == pytest.approx(3.5) and q["limite_inferior"] == pytest.approx(-2.5) and q["limite_superior"] == pytest.approx(11.5)
    com_ausencia = calculos.quartis_iqr(pd.array([1, 2, 3, 4, None, 5, 6, 7, 8], dtype="Int64"))
    assert com_ausencia["n"] == 8 and com_ausencia["q1"] == pytest.approx(2.75)  # ausência não vira zero nem entra na conta
    assert calculos.quartis_iqr(pd.array([None, None], dtype="Int64"))["n"] == 0


def test_quartis_dos_dados_reais_batem_com_numpy(sinesp):
    for evento, abrangencia in [("Homicídio doloso", "Estadual"), ("Suicídio", "Estadual"), ("Mandado de prisão cumprido", "Estadual"),
                                ("Mortes no trânsito", "Polícia Rodoviária Federal")]:
        serie = calculos.serie_sinesp(sinesp, evento, abrangencia)
        valores = serie["valor"].astype("float64").to_numpy()
        q1, med, q3 = np.percentile(valores, [25, 50, 75])
        q = calculos.quartis_iqr(serie["valor"])
        assert (q["q1"], q["mediana"], q["q3"]) == pytest.approx((q1, med, q3)), (evento, abrangencia)
        assert q["limite_superior"] == pytest.approx(q3 + 1.5 * (q3 - q1)) and q["n"] == len(valores)
    homicidio = calculos.quartis_iqr(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")["valor"])
    assert (homicidio["q1"], homicidio["mediana"], homicidio["q3"], homicidio["limite_superior"]) == (2.0, 3.0, 5.0, 9.5)


def test_iqr_informativo_aponta_apenas_os_pontos_fora_dos_limites():
    base = [3, 4, 5, 4, 3, 4, 5, 4, 3, 4, 5, 4] * 2
    valores = base[:-1] + [20]
    d = calculos.diagnostico_outliers_iqr(_serie(valores))
    q1, q3 = np.percentile(np.array(valores, dtype=float), [25, 75])
    assert d["classificacao"] == "informativo" and d["interpretavel"]
    assert d["limite_superior"] == pytest.approx(q3 + 1.5 * (q3 - q1)) and d["limite_inferior"] == pytest.approx(q1 - 1.5 * (q3 - q1))
    assert d["n_fora"] == 1 and int(d["fora"].iloc[0]["valor"]) == 20 and d["fora"].iloc[0]["direcao"] == "acima"
    assert (int(d["fora"].iloc[0]["ano"]), int(d["fora"].iloc[0]["mes"])) == (2021, 12)


@pytest.mark.parametrize("valores, classificacao", [
    ([4] * 24, "distribuicao_degenerada"),                          # todos iguais
    ([0] * 20 + [1] * 1, "iqr_zero"),                               # Q1 = Q3 = 0
    ([0] * 14 + [2, 3, 4, 5, 6, 7, 8, 9, 10, 11], "maioria_zeros"),  # 58% de zeros, IQR > 0
    ([0] * 8 + [1] * 15 + [3], "contagens_baixas"),                 # Q3 = 1: valor 3 é oscilação comum
    ([5, 6, 7, 5, 6, 7, 5, 6, 7, 5, 6], "dados_insuficientes"),    # 11 meses
])
def test_metodo_iqr_nao_informativo_nao_apresenta_anomalia(valores, classificacao):
    d = calculos.diagnostico_outliers_iqr(_serie(valores))
    assert d["classificacao"] == classificacao and d["interpretavel"] is False
    assert any(frase in d["mensagem"] for frase in ("não é informativo", "não é aplicado", "nenhum ponto", "não se conclui", "não são informativos")), d["mensagem"]
    if classificacao in ("distribuicao_degenerada", "dados_insuficientes"):
        assert d["n_fora"] == 0  # nem calcula pontos fora


def test_zero_publicado_conta_como_valor_e_ausencia_nao():
    valores = [0, 1, 2] * 8
    valores[5] = None
    d = calculos.diagnostico_outliers_iqr(_serie(valores))
    assert d["n"] == 23 and d["zeros"] == 8 and d["proporcao_zeros"] == pytest.approx(8 / 23)  # a ausência saiu do denominador e não virou zero


def test_diagnostico_dos_dados_reais_por_serie(sinesp):
    quadro = calculos.diagnostico_outliers_todas_as_series(sinesp).set_index(["evento", "abrangencia"])["classificacao"]
    esperado = {
        ("Mortes a esclarecer (sem indício de crime)", "Estadual"): "distribuição degenerada",
        ("Roubo seguido de morte (latrocínio)", "Estadual"): "IQR igual a zero",
        ("Feminicídio", "Estadual"): "IQR igual a zero",
        ("Lesão corporal seguida de morte", "Estadual"): "IQR igual a zero",
        ("Mandado de prisão cumprido", "Polícia Federal"): "maioria de zeros publicados",
        ("Tentativa de feminicídio", "Estadual"): "maioria de zeros publicados",
        ("Mortes no trânsito", "Polícia Rodoviária Federal"): "contagens muito baixas",
        ("Homicídio doloso", "Estadual"): "método informativo",
        ("Suicídio", "Estadual"): "método informativo",
    }
    for chave, rotulo in esperado.items():
        assert quadro[chave] == rotulo, chave
    homicidio = calculos.diagnostico_outliers_iqr(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual"))
    assert [(int(r.ano), int(r.mes), int(r.valor)) for r in homicidio["fora"].itertuples()] == [(2020, 1, 10), (2023, 1, 19)]


def test_quartis_por_ano_incluindo_ano_parcial_e_iqr_zero(sinesp):
    anual = calculos.quartis_por_ano(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")).set_index("ano")
    a2023, a2026 = anual.loc[2023], anual.loc[2026]
    assert (a2023["n"], a2023["q1"], a2023["mediana"], a2023["q3"]) == (12, 1.75, 3.5, 5.25)
    assert a2023["limite_superior"] == pytest.approx(10.5) and a2023["valores_fora"] == [19.0] and a2023["bigode_superior"] == 7.0 and a2023["bigode_inferior"] == 0.0
    assert a2026["cobertura"] == "parcial janeiro–setembro" and a2026["n"] == 9 and a2026["valores_fora"] == [0.0, 8.0]
    for ano, grupo in calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual").groupby("ano"):  # confere todos os anos com NumPy
        q1, q3 = np.percentile(grupo["valor"].astype("float64"), [25, 75])
        assert (anual.loc[ano, "q1"], anual.loc[ano, "q3"]) == pytest.approx((q1, q3))
    latrocinio = calculos.quartis_por_ano(calculos.serie_sinesp(sinesp, "Roubo seguido de morte (latrocínio)", "Estadual"))
    assert latrocinio["iqr_zero"].all()  # todos os anos degenerados: nenhum ponto será interpretado


# ----------------------------------------------------------------------------------- períodos parciais e sazonalidade
def test_sazonalidade_usa_somente_anos_completos_e_ignora_2026(sinesp):
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    assert calculos.anos_completos_da_serie(serie) == [2020, 2021, 2022, 2023, 2024, 2025]
    perfil = calculos.perfil_sazonal(serie)
    assert perfil.attrs["anos_usados"] == [2020, 2021, 2022, 2023, 2024, 2025] and perfil["n_anos"].eq(6).all()
    janeiro = [10, 5, 2, 19, 2, 2]
    assert perfil.loc[0, "media"] == pytest.approx(np.mean(janeiro)) and perfil.loc[0, "mediana"] == pytest.approx(np.median(janeiro))
    assert (perfil.loc[0, "minimo"], perfil.loc[0, "maximo"]) == (2, 19)
    alterada = serie.copy()
    alterada.loc[(alterada["ano"] == 2026) & (alterada["mes"] == 1), "valor"] = 999  # mexer no ano parcial não pode mudar o perfil
    pd.testing.assert_frame_equal(calculos.perfil_sazonal(alterada), perfil)
    assert calculos.perfil_sazonal(serie, [2020, 2021]).attrs["anos_usados"] == [2020, 2021]
    assert perfil["indice"].mean() == pytest.approx(1.0)  # média dos índices mensais = 1 (cada mês ÷ média geral)


def test_series_com_poucos_anos_completos_nao_geram_perfil_enganoso(sinesp):
    pf = calculos.serie_sinesp(sinesp, "Mandado de prisão cumprido", "Polícia Federal")
    assert calculos.anos_completos_da_serie(pf) == [2025]  # 2026 parcial; antes de 2025 não há cobertura
    assert calculos.perfil_sazonal(pf)["n_anos"].eq(1).all()
    assert graficos.figura_sazonalidade_sinesp(sinesp, "Mandado de prisão cumprido", "Polícia Federal", ANOS) is None  # menos de 2 anos: sem figura
    assert calculos.perfil_sazonal(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual"), [2026]).empty
    prf = calculos.serie_sinesp(sinesp, "Mortes no trânsito", "Polícia Rodoviária Federal")
    assert 2026 not in calculos.anos_completos_da_serie(prf)  # a PRF termina em agosto


def test_ano_parcial_nao_vira_ano_completo_em_acumulado_e_media_movel(sinesp):
    acumulado = calculos.acumulado_no_ano(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual"))
    ultimo = acumulado[acumulado["ano"] == 2026]
    assert ultimo["mes"].tolist() == list(range(1, 10)) and int(ultimo["acumulado"].iloc[-1]) == 25  # termina em setembro; 25 = jan–set
    assert acumulado[(acumulado["ano"] == 2025) & (acumulado["mes"] == 12)]["acumulado"].iloc[0] == 29
    prf = calculos.acumulado_no_ano(calculos.serie_sinesp(sinesp, "Mortes no trânsito", "Polícia Rodoviária Federal"))
    assert prf[prf["ano"] == 2026]["mes"].max() == 8 and int(prf[prf["ano"] == 2026]["acumulado"].iloc[-1]) == 6


def test_media_movel_exige_janela_completa_e_nao_interpola():
    movel = calculos.media_movel(_serie(list(range(1, 15))))
    assert movel["media_movel"].iloc[:11].isna().all() and movel["media_movel"].iloc[11] == pytest.approx(6.5)
    assert movel["media_movel"].iloc[13] == pytest.approx(np.mean(range(3, 15)))
    com_ausencia = calculos.media_movel(_serie([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, None, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25]))
    assert com_ausencia["media_movel"].iloc[11] == pytest.approx(6.5)
    assert com_ausencia["media_movel"].iloc[12:24].isna().all()  # toda janela que contém o mês sem valor fica sem média
    assert com_ausencia["media_movel"].iloc[24] == pytest.approx(np.mean(range(14, 26)))


def test_acumulado_para_no_mes_sem_valor():
    acumulado = calculos.acumulado_no_ano(_serie([1, 2, None, 4, 5]))
    assert acumulado["acumulado"].tolist()[:2] == [1, 3] and acumulado["acumulado"].iloc[2:].isna().all()
    with pytest.raises(ValueError, match="consecutivos"):
        calculos.acumulado_no_ano(_serie([1, 2, 3]).drop(index=1))


# --------------------------------------------------------------------------------------------- zeros, ausências, filtros
def test_grade_ano_mes_preserva_zeros_e_marca_meses_nao_observados(sinesp):
    grade = calculos.quadro_ano_mes(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual"))
    assert grade.loc[2022, 10] == 0 and grade.loc[2023, 1] == 19  # zero publicado é valor
    assert grade.loc[2026, [10, 11, 12]].isna().all() and grade.loc[2026, 9] == 3  # mês futuro: ausente, não zero
    assert grade.shape == (7, 12) and str(grade.dtypes.iloc[0]) == "Int64"
    frequencia = calculos.distribuicao_frequencias(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual"))
    assert int(frequencia.loc[frequencia["inicio"] == 0, "n_meses"].iloc[0]) == 4 and int(frequencia["n_meses"].sum()) == 81
    larga = calculos.distribuicao_frequencias(calculos.serie_sinesp(sinesp, "Mandado de prisão cumprido", "Estadual"))
    assert int(larga["n_meses"].sum()) == 81 and len(larga) <= 14 and larga["fim"].iloc[-1] >= 160  # classes de largura igual cobrem 0–160


def test_calculos_recusam_misturar_series_e_unidades(sinesp):
    mistura = pd.concat([calculos.serie_sinesp(sinesp, "Mandado de prisão cumprido", "Estadual"), calculos.serie_sinesp(sinesp, "Mandado de prisão cumprido", "Polícia Federal")])
    for funcao in (calculos.diagnostico_outliers_iqr, calculos.quartis_por_ano, calculos.quadro_ano_mes, calculos.perfil_sazonal, calculos.media_movel,
                   calculos.acumulado_no_ano, calculos.distribuicao_frequencias):
        with pytest.raises(ValueError, match="única série"):
            funcao(mistura)
    vitimas = pd.concat([calculos.serie_sinesp(sinesp, "Suicídio", "Estadual"), calculos.serie_sinesp(sinesp, "Mandado de prisão cumprido", "Estadual")])
    with pytest.raises(ValueError, match="única série"):
        calculos.diagnostico_outliers_iqr(vitimas)


def test_filtros_de_indicador_abrangencia_e_periodo_chegam_as_figuras(sinesp):
    figura = graficos.figura_mapa_calor_sinesp(sinesp, "Mandado de prisão cumprido", "Polícia Federal", [2025, 2026])
    matriz = figura.axes[0].images[0].get_array()
    assert matriz.shape == (2, 12) and matriz[0, 0] == 1  # PF: só 2025–2026; janeiro/2025 = 1 mandado
    assert "Polícia Federal" in " ".join(t.get_text() for t in figura.texts) and "mandados cumpridos" in " ".join(t.get_text() for t in figura.texts)
    assert graficos.figura_mapa_calor_sinesp(sinesp, "Mandado de prisão cumprido", "Polícia Federal", [2020, 2021]) is None  # sem cobertura: sem figura
    pf_estadual = graficos.figura_boxplot_anual_sinesp(sinesp, "Mandado de prisão cumprido", "Estadual", [2024, 2025])
    medianas = [float(l.get_ydata()[0]) for l in _linhas_por_gid(pf_estadual, "mediana")]
    esperado = calculos.quartis_por_ano(calculos.serie_sinesp(sinesp, "Mandado de prisão cumprido", "Estadual").query("ano in [2024, 2025]"))["mediana"].tolist()
    assert medianas == pytest.approx(esperado) and len(medianas) == 2


# ------------------------------------------------------------------------------------------- figura × tabela
def test_mapa_de_calor_desenha_a_grade_da_tabela(sinesp):
    figura = graficos.figura_mapa_calor_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    tabela = calculos.quadro_ano_mes(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual"))
    matriz = figura.axes[0].images[0].get_array()
    assert np.ma.getmaskarray(matriz).tolist() == tabela.isna().to_numpy().tolist()
    assert np.ma.filled(matriz, -1).astype(int).tolist() == tabela.astype("float64").fillna(-1).astype(int).to_numpy().tolist()
    textos = sorted(t.get_text() for t in figura.axes[0].texts)
    assert textos == sorted(str(int(v)) for v in tabela.to_numpy().ravel() if pd.notna(v))  # o número escrito em cada célula é o da tabela


def test_boxplot_desenha_os_numeros_da_tabela(sinesp):
    figura = graficos.figura_boxplot_anual_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    tabela = calculos.quartis_por_ano(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual"))
    assert [float(l.get_ydata()[0]) for l in _linhas_por_gid(figura, "mediana")] == pytest.approx(tabela["mediana"].tolist())
    assert [float(l.get_ydata()[0]) for l in _linhas_por_gid(figura, "bigode_inferior")] == pytest.approx(tabela["bigode_inferior"].tolist())
    assert [float(l.get_ydata()[0]) for l in _linhas_por_gid(figura, "bigode_superior")] == pytest.approx(tabela["bigode_superior"].tolist())
    caixas = _linhas_por_gid(figura, "caixa")
    assert [(float(_ydata(c).min()), float(_ydata(c).max())) for c in caixas] == pytest.approx(list(zip(tabela["q1"], tabela["q3"])))
    assert [sorted(_ydata(l).tolist()) for l in _linhas_por_gid(figura, "atipicos")] == [sorted(v) for v in tabela["valores_fora"]]
    assert figura.axes[0].get_ylim()[0] == 0
    degenerada = graficos.figura_boxplot_anual_sinesp(sinesp, "Roubo seguido de morte (latrocínio)", "Estadual", ANOS)
    assert all(len(_ydata(l)) == 0 for l in _linhas_por_gid(degenerada, "atipicos"))  # IQR = 0: nenhum ponto interpretado
    assert any("IQR = 0" in t.get_text() for t in degenerada.axes[0].texts)


def test_histograma_sazonalidade_media_movel_e_acumulado_desenham_as_tabelas(sinesp):
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    frequencia = calculos.distribuicao_frequencias(serie)
    barras = graficos.figura_distribuicao_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS).axes[0].patches
    assert [int(b.get_height()) for b in barras if b.get_gid() == "frequencia"] == frequencia["n_meses"].tolist()
    assert any(b.get_hatch() for b in barras if b.get_gid() == "frequencia")  # a classe do zero publicado é hachurada

    perfil = calculos.perfil_sazonal(serie)
    sazonal = graficos.figura_sazonalidade_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    barras = [b for b in sazonal.axes[0].patches if b.get_gid() == "mediana_mensal"]
    assert [b.get_height() for b in barras] == pytest.approx(perfil["mediana"].astype(float).tolist()) and len(barras) == 12  # mediana por mês, nenhum mês inventado
    assert not sazonal.axes[0].lines and "2020–2025" in " ".join(t.get_text() for t in sazonal.texts)  # anos usados identificados; 2026 fora

    movel = calculos.media_movel(serie)
    figura = graficos.figura_media_movel_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    np.testing.assert_allclose(_ydata(_linhas_por_gid(figura, "media_movel")[0]), movel["media_movel"].astype("float64").to_numpy(), equal_nan=True)
    np.testing.assert_allclose(_ydata(_linhas_por_gid(figura, "serie_mensal")[0]), movel["valor"].astype("float64").to_numpy(), equal_nan=True)
    assert np.isnan(_ydata(_linhas_por_gid(figura, "media_movel")[0])[:11]).all()  # sem janela completa: sem ponto

    acumulado = calculos.acumulado_no_ano(serie)
    figura = graficos.figura_acumulado_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    for ano, parte in acumulado.groupby("ano"):
        np.testing.assert_allclose(_ydata(_linhas_por_gid(figura, f"acumulado_{ano}")[0]), parte["acumulado"].astype("float64").to_numpy())
    assert len(_linhas_por_gid(figura, "acumulado_2026")[0].get_xdata()) == 9  # o ano parcial termina em setembro


def test_figura_de_outliers_destaca_so_quando_o_metodo_e_informativo(sinesp):
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    d = calculos.diagnostico_outliers_iqr(serie)
    figura = graficos.figura_outliers_iqr_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    assert _ydata(_linhas_por_gid(figura, "pontos")[0]).tolist() == serie["valor"].astype(float).tolist()
    assert _ydata(_linhas_por_gid(figura, "pontos_atipicos")[0]).tolist() == [10.0, 19.0]
    assert _ydata(_linhas_por_gid(figura, "limite_superior")[0]).tolist() == [d["limite_superior"]] * 2
    assert not _linhas_por_gid(figura, "limite_inferior")  # limite inferior negativo: nenhuma contagem pode ficar abaixo dele
    for estavel in (("Roubo seguido de morte (latrocínio)", "Estadual"), ("Mortes no trânsito", "Polícia Rodoviária Federal"),
                    ("Mandado de prisão cumprido", "Polícia Federal"), ("Mortes a esclarecer (sem indício de crime)", "Estadual")):
        sem_metodo = graficos.figura_outliers_iqr_sinesp(sinesp, *estavel, ANOS)
        assert not _linhas_por_gid(sem_metodo, "pontos_atipicos") and not _linhas_por_gid(sem_metodo, "limite_superior"), estavel
        assert any("pouco úteis" in t.get_text() for t in sem_metodo.axes[0].texts), estavel


def test_ranking_destaca_a_serie_selecionada_sem_mudar_valores(sinesp):
    ranking = calculos.ranking_por_unidade(sinesp, 2025, dp.UNIDADE_VITIMAS)
    figura = graficos.figura_ranking_sinesp(ranking, 2025, destaque=("Homicídio doloso", "Estadual"))
    barras = [b for b in figura.axes[0].patches if b.get_gid() == "ranking"]
    assert sorted(int(b.get_width()) for b in barras) == sorted(ranking["soma"].astype(int).tolist())
    cores = [b.get_facecolor() for b in barras]
    assert sum(1 for c in cores if c[:3] == pytest.approx((10 / 255, 52 / 255, 112 / 255), abs=1e-3)) == 1  # exatamente uma barra de destaque (azul mais escuro)


@pytest.mark.parametrize("evento, abrangencia", [("Homicídio doloso", "Estadual"), ("Mandado de prisão cumprido", "Polícia Federal"),
                                                 ("Mortes no trânsito", "Polícia Rodoviária Federal")])
def test_todas_as_figuras_novas_trazem_fonte_unidade_abrangencia_e_eixo_em_zero(sinesp, evento, abrangencia):
    unidade = sinesp.loc[sinesp["evento"].eq(evento) & sinesp["abrangencia"].eq(abrangencia), "unidade"].iloc[0]
    construidas = 0
    for nome in ("mapa_calor", "media_movel", "acumulado", "boxplot_anual", "distribuicao", "sazonalidade", "outliers_iqr"):
        figura = getattr(graficos, f"figura_{nome}_sinesp")(sinesp, evento, abrangencia, ANOS)
        if figura is None:  # só a sazonalidade da PF (1 ano completo) pode faltar
            assert nome == "sazonalidade" and abrangencia == "Polícia Federal"
            continue
        construidas += 1
        texto = " ".join(t.get_text() for t in figura.texts)
        assert "MJSP / Sinesp VDE" in texto and f"Abrangência: {abrangencia}" in texto and f"Unidade: {unidade}" in texto, nome
        if nome != "mapa_calor":
            assert figura.axes[0].get_ylim()[0] == 0, nome
        assert figura.get_figwidth() == 10  # mesma largura e identidade das demais figuras do painel
    assert construidas >= 6


# ===================================================================================================================
# Etapa 20.1 — regressão visual: histograma, acumulado sem colisão, textos dentro da figura, outliers recalculados
# ===================================================================================================================
def _caixas_dos_textos(figura):
    """Retângulos (em pixels) de todos os textos visíveis da figura, já renderizada."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    FigureCanvasAgg(figura)
    figura.canvas.draw()
    renderizador = figura.canvas.get_renderer()
    eixo = figura.axes[0]
    xmin, xmax = sorted(eixo.get_xlim())
    ymin, ymax = sorted(eixo.get_ylim())
    marcas_visiveis = [r for p, r in zip(eixo.get_xticks(), eixo.get_xticklabels()) if xmin <= p <= xmax] + [r for p, r in zip(eixo.get_yticks(), eixo.get_yticklabels()) if ymin <= p <= ymax]
    artistas = list(figura.texts) + list(eixo.texts) + [eixo.xaxis.label, eixo.yaxis.label] + marcas_visiveis  # marcas fora dos limites do eixo não são desenhadas
    legenda = eixo.get_legend()
    if legenda is not None:
        artistas += list(legenda.get_texts())
    if figura._suptitle is not None:
        artistas.append(figura._suptitle)
    from matplotlib.text import Text

    return [(a, Text.get_window_extent(a, renderizador)) for a in artistas if a.get_visible() and a.get_text().strip()]  # só o texto (sem a seta da anotação)


def _sem_sobreposicao(caixas) -> bool:
    return not any(a.overlaps(b) for i, (_, a) in enumerate(caixas) for _, b in caixas[i + 1:])


SERIES_REAIS = [("Homicídio doloso", "Estadual"), ("Tentativa de homicídio", "Estadual"), ("Feminicídio", "Estadual"), ("Roubo seguido de morte (latrocínio)", "Estadual"),
                ("Mandado de prisão cumprido", "Estadual"), ("Mandado de prisão cumprido", "Polícia Federal"), ("Mortes no trânsito", "Polícia Rodoviária Federal"),
                ("Mortes a esclarecer (sem indício de crime)", "Estadual"), ("Suicídio", "Estadual"), ("Tentativa de feminicídio", "Estadual"),
                ("Lesão corporal seguida de morte", "Estadual"), ("Morte no trânsito ou em decorrência dele (exceto homicídio doloso)", "Estadual")]


@pytest.mark.parametrize("evento, abrangencia", SERIES_REAIS)
def test_histograma_contabiliza_todos_os_meses_em_faixas_contiguas_com_zero_proprio(sinesp, evento, abrangencia):
    serie = calculos.serie_sinesp(sinesp, evento, abrangencia)
    for anos in (ANOS, [2023, 2024, 2025], [2026]):  # a regra vale para qualquer período selecionado
        recorte = serie[serie["ano"].isin(anos)]
        if recorte.empty:
            continue
        tabela = calculos.distribuicao_frequencias(recorte)
        valores = recorte["valor"].dropna().astype(int)
        assert int(tabela["n_meses"].sum()) == len(valores), (anos, "soma das frequências ≠ meses analisados")
        assert tabela["percentual"].sum() == pytest.approx(100.0, abs=0.05 * len(tabela))
        # cada valor cai em exatamente uma faixa, e a contagem independente confere faixa a faixa
        for faixa in tabela.itertuples():
            assert int(((valores >= faixa.inicio) & (valores <= faixa.fim)).sum()) == faixa.n_meses
        positivas = tabela[tabela["inicio"] > 0]
        assert (positivas["inicio"].iloc[1:].to_numpy() == positivas["fim"].iloc[:-1].to_numpy() + 1).all()  # faixas positivas contíguas, sem lacuna nem sobreposição
        assert tabela["inicio"].iloc[0] == valores.min() and tabela["fim"].iloc[-1] == valores.max()  # o valor extremo não é removido
        if len(positivas):
            assert positivas["inicio"].iloc[0] == valores[valores > 0].min()  # sem faixa vazia entre o zero e o menor valor positivo
            assert positivas["n_meses"].iloc[0] > 0
        zeros = int((valores == 0).sum())
        if zeros:
            zero = tabela[tabela["inicio"] == 0]
            assert len(zero) == 1 and int(zero["fim"].iloc[0]) == 0 and int(zero["n_meses"].iloc[0]) == zeros  # zero publicado: faixa própria
        assert len(tabela) <= calculos.numero_de_faixas(len(valores)) + 1


def test_histograma_com_valor_extremo_nao_gera_dezenas_de_faixas_vazias(sinesp):
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    tabela = calculos.distribuicao_frequencias(serie)
    assert tabela["rotulo"].tolist() == ["0", "1–3", "4–6", "7–9", "10–12", "13–15", "16–18", "19"]  # antes: 20 classes unitárias, 8 vazias
    assert tabela["n_meses"].tolist() == [4, 38, 27, 10, 1, 0, 0, 1] and tabela.attrs["largura"] == 3
    assert calculos.numero_de_faixas(81) == 8 and calculos.numero_de_faixas(21) == 6
    sintetica = _serie([3, 4, 5, 4, 3, 4, 5, 4, 3, 4, 5, 4] * 2 + [100])
    extremo = calculos.distribuicao_frequencias(sintetica)
    assert int(extremo["n_meses"].sum()) == 25 and int(extremo["fim"].iloc[-1]) == 100 and int(extremo["n_meses"].iloc[-1]) == 1  # o 100 está contado
    assert calculos.distribuicao_frequencias(_serie([0, 0, 0, 0]))["n_meses"].tolist() == [4]  # só zeros: uma faixa
    assert calculos.distribuicao_frequencias(_serie([None, None])).empty and calculos.distribuicao_frequencias(_serie([1, None, 2]))["n_meses"].sum() == 2


def test_figura_do_histograma_desenha_as_faixas_da_tabela_e_cita_a_regra(sinesp):
    figura = graficos.figura_distribuicao_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    tabela = calculos.distribuicao_frequencias(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual"))
    barras = [b for b in figura.axes[0].patches if b.get_gid() == "frequencia"]
    assert [int(b.get_height()) for b in barras] == tabela["n_meses"].tolist() and sum(int(b.get_height()) for b in barras) == 81
    assert [t.get_text() for t in figura.axes[0].get_xticklabels()] == tabela["rotulo"].tolist()
    texto = " ".join(t.get_text() for t in figura.texts)
    assert "intervalos de 3" in texto and "a última faixa pode ser menor" in texto and "n = 81" in texto and "faixa própria" in texto and "faixas vazias são mantidas" in texto


def test_acumulado_rotulos_finais_sem_colisao_e_com_ano_parcial_identificado(sinesp):
    for evento, abrangencia in [("Homicídio doloso", "Estadual"), ("Roubo seguido de morte (latrocínio)", "Estadual"), ("Feminicídio", "Estadual"),
                                ("Mortes a esclarecer (sem indício de crime)", "Estadual"), ("Mandado de prisão cumprido", "Estadual")]:
        figura = graficos.figura_acumulado_sinesp(sinesp, evento, abrangencia, ANOS)
        rotulos = [(a, c) for a, c in _caixas_dos_textos(figura) if a.get_gid() == "rotulo_final"]
        assert rotulos and _sem_sobreposicao(rotulos), (evento, "rótulos finais se sobrepõem")
        textos = [a.get_text() for a, _ in rotulos]
        assert any("2026 (jan–set)" in t for t in textos), textos  # ano parcial identificado no rótulo
        assert "2026 (parcial, até set)" in [t.get_text() for t in figura.axes[0].get_legend().get_texts()]  # e na legenda
    figura = graficos.figura_acumulado_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    textos = [a.get_text() for a in figura.axes[0].texts if a.get_gid() == "rotulo_final"]
    assert "2020, 2021: 62" in textos  # anos completos com o mesmo valor final dividem um rótulo (não se perde nenhum valor)
    finais = {ano: float(_ydata(_linhas_por_gid(figura, f"acumulado_{ano}")[0])[-1]) for ano in range(2020, 2027)}  # e a posição dos pontos não foi tocada
    assert finais == {2020: 62.0, 2021: 62.0, 2022: 49.0, 2023: 55.0, 2024: 36.0, 2025: 29.0, 2026: 25.0}
    prf = graficos.figura_acumulado_sinesp(sinesp, "Mortes no trânsito", "Polícia Rodoviária Federal", ANOS)
    assert any("2026 (jan–ago)" in a.get_text() for a in prf.axes[0].texts)  # a PRF termina em agosto


def test_series_sem_variacao_trazem_aviso_e_series_normais_nao(sinesp):
    funcoes = {"serie_anual": graficos.figura_serie_anual_sinesp, "periodo": graficos.figura_periodo_sinesp, "mensal": graficos.figura_mensal_sinesp,
               "mapa_calor": graficos.figura_mapa_calor_sinesp, "media_movel": graficos.figura_media_movel_sinesp, "acumulado": graficos.figura_acumulado_sinesp,
               "sazonalidade": graficos.figura_sazonalidade_sinesp}
    for nome, funcao in funcoes.items():
        figura = funcao(sinesp, "Mortes a esclarecer (sem indício de crime)", "Estadual", ANOS)
        assert any("Série sem variação" in t.get_text() for t in figura.axes[0].texts), nome
        normal = funcao(sinesp, "Homicídio doloso", "Estadual", ANOS)
        assert not any("Série sem variação" in t.get_text() for t in normal.axes[0].texts), nome


@pytest.mark.parametrize("evento, abrangencia", SERIES_REAIS)
def test_nenhum_titulo_eixo_legenda_ou_rotulo_sai_da_figura(sinesp, evento, abrangencia):
    for nome in ("mapa_calor", "media_movel", "acumulado", "boxplot_anual", "distribuicao", "sazonalidade", "outliers_iqr"):
        figura = getattr(graficos, f"figura_{nome}_sinesp")(sinesp, evento, abrangencia, ANOS)
        if figura is None:
            continue
        caixa = figura.bbox
        for artista, retangulo in _caixas_dos_textos(figura):
            assert retangulo.x0 >= -1 and retangulo.y0 >= -1 and retangulo.x1 <= caixa.x1 + 1 and retangulo.y1 <= caixa.y1 + 1, (nome, evento, artista.get_text()[:50])


def test_figura_de_outliers_mostra_estatisticas_e_recalcula_pelo_periodo_selecionado(sinesp):
    anos = [2021, 2022, 2023, 2024, 2025]
    figura = graficos.figura_outliers_iqr_sinesp(sinesp, "Homicídio doloso", "Estadual", anos)
    recorte = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual").query("ano in @anos")
    valores = recorte["valor"].astype("float64").to_numpy()
    q1, med, q3 = np.percentile(valores, [25, 50, 75])  # conjunto de referência = apenas o período selecionado
    limite = q3 + 1.5 * (q3 - q1)
    assert _ydata(_linhas_por_gid(figura, "limite_superior")[0]).tolist() == [limite] * 2
    assert _ydata(_linhas_por_gid(figura, "mediana")[0]).tolist() == [med] * 2
    assert sorted(_ydata(_linhas_por_gid(figura, "pontos_atipicos")[0]).tolist()) == sorted(valores[valores > limite].tolist())
    legenda = " ".join(t.get_text() for t in figura.axes[0].get_legend().get_texts())
    for item in ("Mediana", "Q1 a Q3", "IQR", "Limite superior", "Limite inferior", "Fora dos limites"):
        assert item in legenda, item
    assert "Conjunto de referência: 60 meses, jan/2021 a dez/2025" in " ".join(t.get_text() for t in figura.texts)
    recente = graficos.figura_outliers_iqr_sinesp(sinesp, "Homicídio doloso", "Estadual", [2024, 2025, 2026])  # outro conjunto de referência → outros limites
    q1r, q3r = np.percentile(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual").query("ano >= 2024")["valor"].astype("float64"), [25, 75])
    assert _ydata(_linhas_por_gid(recente, "limite_superior")[0]).tolist() == [q3r + 1.5 * (q3r - q1r)] * 2 and q3r + 1.5 * (q3r - q1r) != limite


def test_rotulos_dos_pontos_atipicos_nao_se_sobrepoem(sinesp):
    for evento in ("Tentativa de homicídio", "Homicídio doloso", "Mandado de prisão cumprido", "Suicídio"):
        figura = graficos.figura_outliers_iqr_sinesp(sinesp, evento, "Estadual", ANOS)
        rotulos = [(a, c) for a, c in _caixas_dos_textos(figura) if a.get_gid() == "rotulo_atipico"]
        assert _sem_sobreposicao(rotulos), evento


def test_tabela_de_pontos_atipicos_acompanha_o_diagnostico(sinesp):
    d = calculos.diagnostico_outliers_iqr(calculos.serie_sinesp(sinesp, "Tentativa de homicídio", "Estadual"))
    assert d["interpretavel"] and d["n_fora"] == 4 and set(d["fora"]["direcao"]) == {"abaixo", "acima"}
    assert (d["fora"].loc[d["fora"]["direcao"] == "abaixo", "valor"].astype(float) < d["limite_inferior"]).all()
    assert (d["fora"].loc[d["fora"]["direcao"] == "acima", "valor"].astype(float) > d["limite_superior"]).all()


# ---------------------------------------------------------------- conferências que antes ficavam no roteiro de ETL (agora, no notebook e aqui)
def test_mapa_de_calor_desenha_exatamente_a_tabela_ano_por_mes(sinesp):
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    figura = graficos.figura_mapa_calor_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    matriz = figura.axes[0].images[0].get_array()
    desenhado = [[None if matriz[i, j] is np.ma.masked else int(matriz[i, j]) for j in range(matriz.shape[1])] for i in range(matriz.shape[0])]
    esperado = [[None if pd.isna(v) else int(v) for v in linha] for linha in calculos.quadro_ano_mes(serie).to_numpy()]
    assert desenhado == esperado  # as células coloridas são os números da tabela; mês sem valor continua em branco


def test_media_movel_desenhada_e_a_da_tabela(sinesp):
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    figura = graficos.figura_media_movel_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    linha = {l.get_gid(): l for l in figura.axes[0].lines}["media_movel"]
    esperado = calculos.media_movel(serie)["media_movel"].astype("float64").to_numpy()
    assert np.allclose(np.array(linha.get_ydata(), dtype="float64"), esperado, equal_nan=True)


def test_criterio_iqr_e_informativo_em_5_das_12_series(sinesp):
    diagnosticos = calculos.diagnostico_outliers_todas_as_series(sinesp)
    assert len(diagnosticos) == 12 and int(diagnosticos["classificacao"].eq("método informativo").sum()) == 5
