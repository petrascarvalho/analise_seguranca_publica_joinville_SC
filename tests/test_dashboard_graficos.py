"""Testes das figuras do dashboard Sinesp: valores plotados = valores aprovados (Etapa 10) e regras visuais."""

import pandas as pd
import pytest

from dashboard import calculos, graficos
from dashboard import dados_publicos as dp


@pytest.fixture(scope="module")
def sinesp():
    return dp.carregar_sinesp()


def _texto_da_figura(figura) -> str:
    eixo = figura.axes[0]
    textos = [t.get_text() for t in figura.texts] + [figura.get_suptitle(), eixo.get_title(), eixo.get_xlabel(), eixo.get_ylabel()]
    return " | ".join(t for t in textos if t)


def test_quatro_figuras_da_etapa_10_preservam_valores_aprovados(sinesp):
    figuras = graficos.figuras_sinesp_etapa10(sinesp)
    assert list(figuras) == ["fig_homicidio_anual_sinesp", "fig_mulher_anual_sinesp", "fig_homicidios_jan_ago_sinesp", "fig_mulher_jan_ago_sinesp"]
    linhas = figuras["fig_homicidio_anual_sinesp"].axes[0].lines
    assert list(linhas[0].get_xdata()) == [2020, 2021, 2022, 2023, 2024, 2025] and list(linhas[0].get_ydata()) == [62, 62, 49, 55, 36, 29]
    barras = figuras["fig_mulher_anual_sinesp"].axes[0].containers
    assert [b.get_height() for b in barras[0]] == [3, 6, 2, 2, 3, 2]       # Feminicídio
    assert [b.get_height() for b in barras[1]] == [10, 4, 7, 7, 10, 9]     # Tentativa de feminicídio
    linhas = figuras["fig_homicidios_jan_ago_sinesp"].axes[0].lines
    assert list(linhas[0].get_xdata()) == [2020, 2021, 2022, 2023, 2024, 2025, 2026]
    assert list(linhas[0].get_ydata()) == [50, 40, 29, 40, 21, 18, 22]      # janeiro–agosto, mesmo com setembro/2026 publicado
    assert list(linhas[1].get_ydata()) == [74, 53, 60, 62, 57, 37, 68]
    barras = figuras["fig_mulher_jan_ago_sinesp"].axes[0].containers
    assert [b.get_height() for b in barras[0]] == [0, 0] and [b.get_height() for b in barras[1]] == [4, 10]
    for nome, figura in figuras.items():
        assert figura.axes[0].get_ylim()[0] == 0, nome
        texto = _texto_da_figura(figura)
        assert "MJSP / Sinesp VDE" in texto and "Joinville/SC" in texto and "Estadual" in texto and "vítimas" in texto.lower(), nome


def test_figura_anual_recusa_periodo_parcial(sinesp):
    with pytest.raises(ValueError, match="parcial"):
        graficos.quadro_eventos(sinesp, ["Homicídio doloso"], list(range(2020, 2027)), mes_final=None)


def test_valor_ausente_nao_vira_zero_nem_soma_parcial_nas_figuras(sinesp):
    ausente = sinesp.copy()
    ausente.loc[(ausente["evento"] == "Homicídio doloso") & (ausente["ano"] == 2021) & (ausente["mes"] == 3), "valor"] = pd.NA
    with pytest.raises(ValueError, match="ausente"):
        graficos.quadro_eventos(ausente, ["Homicídio doloso"], [2020, 2021], mes_final=None)
    assert graficos.figura_serie_anual_sinesp(ausente, "Homicídio doloso", "Estadual", [2021]) is None


def test_figuras_filtraveis_usam_cores_por_ano_e_eixo_em_zero(sinesp):
    figura = graficos.figura_periodo_sinesp(sinesp, "Homicídio doloso", "Estadual", list(range(2020, 2027)), 8)
    assert [b.get_height() for b in figura.axes[0].patches] == [50, 40, 29, 40, 21, 18, 22] and figura.axes[0].get_ylim()[0] == 0
    setembro = graficos.figura_periodo_sinesp(sinesp, "Homicídio doloso", "Estadual", list(range(2020, 2027)), 9)
    esperado = [int(sinesp[(sinesp["evento"] == "Homicídio doloso") & (sinesp["ano"] == a) & (sinesp["mes"] <= 9)]["valor"].sum()) for a in range(2020, 2027)]
    assert [b.get_height() for b in setembro.axes[0].patches] == esperado and esperado[-1] == 25  # janeiro–setembro: 2026 já comparável
    mensal = graficos.figura_mensal_sinesp(sinesp, "Tentativa de homicídio", "Estadual", [2025, 2026])
    assert [len([b for b in mensal.axes[0].patches if b.get_gid() == f"mensal_{a}"]) for a in (2025, 2026)] == [12, 9]  # 2026 tem 9 meses (até setembro)
    assert graficos.cor_ano(2023) == "#2A73B8" and graficos.cor_ano(2024) == "#074EA2"  # tons de azul; anos continuam distintos
    cores = list(graficos.COR_ANO.values()) + list(graficos.COR_EVENTO.values())
    assert len(set(graficos.COR_ANO.values())) == 7  # um tom por ano, sem repetição
    for cor in cores + [graficos.cor_ano(2031)]:  # identidade azul e branca: nenhum ano ou indicador usa roxo, verde, laranja ou vermelho
        r, g, b = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
        assert b > g > r, cor
    assert graficos.cor_ano(2031) == graficos.cor_ano(2031) and graficos.cor_ano(2031).startswith("#")  # ano futuro: cor de reserva estável
    assert graficos.figura_periodo_sinesp(sinesp, "Mandado de prisão cumprido", "Polícia Federal", [2020, 2021]) is None
    prf = graficos.figura_mensal_sinesp(sinesp, "Mortes no trânsito", "Polícia Rodoviária Federal", [2026])
    assert len([b for b in prf.axes[0].patches if b.get_gid() == "mensal_2026"]) == 8  # série PRF termina em agosto: sem barra nem preenchimento


def test_figura_serie_anual_apenas_anos_completos(sinesp):
    figura = graficos.figura_serie_anual_sinesp(sinesp, "Suicídio", "Estadual", list(range(2020, 2027)))
    barras = [b for b in figura.axes[0].patches if b.get_gid() == "barra_anual"]
    assert [t.get_text() for t in figura.axes[0].get_xticklabels()] == ["2020", "2021", "2022", "2023", "2024", "2025"]  # 2026 parcial fora da série anual
    assert [b.get_height() for b in barras] == [43, 52, 67, 44, 48, 39]
    assert graficos.figura_serie_anual_sinesp(sinesp, "Suicídio", "Estadual", [2026]) is None


def test_figura_ranking_respeita_unidade_e_valores(sinesp):
    ranking = calculos.ranking_por_unidade(sinesp, 2025, dp.UNIDADE_VITIMAS)
    figura = graficos.figura_ranking_sinesp(ranking, 2025)
    eixo = figura.axes[0]
    alturas = sorted((b.get_width() for b in eixo.patches), reverse=True)
    assert alturas == [int(v) for v in ranking["soma"]] and eixo.get_xlim()[0] == 0
    texto = _texto_da_figura(figura)
    assert "MJSP / Sinesp VDE" in texto and "nenhum total entre indicadores" in texto and "2025" in texto
    misturado = pd.concat([ranking.iloc[:1], calculos.ranking_por_unidade(sinesp, 2025, dp.UNIDADE_MANDADOS).iloc[:1]], ignore_index=True)
    with pytest.raises(ValueError, match="unidades diferentes"):
        graficos.figura_ranking_sinesp(misturado, 2025)
    assert graficos.figura_ranking_sinesp(ranking.iloc[0:0], 2025) is None
