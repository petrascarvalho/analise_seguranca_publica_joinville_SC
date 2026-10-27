"""Testes das figuras do dashboard: valores plotados = valores aprovados (Etapas 10 e 14.2)."""

import pandas as pd
import pytest

from dashboard import calculos, graficos
from dashboard import dados_publicos as dp


@pytest.fixture(scope="module")
def sinesp():
    return dp.carregar_sinesp()


@pytest.fixture(scope="module")
def vd():
    return dp.carregar_violencia_domestica()


def _texto_da_figura(figura) -> str:
    eixo = figura.axes[0]
    textos = [t.get_text() for t in figura.texts] + [figura.get_suptitle(), eixo.get_title(), eixo.get_xlabel(), eixo.get_ylabel()]
    return " | ".join(t for t in textos if t)


# ------------------------------------------------------------------------------- Etapa 10 (Sinesp)
def test_quatro_figuras_sinesp_preservam_valores_da_etapa_10(sinesp):
    figuras = graficos.figuras_sinesp_etapa10(sinesp)
    assert list(figuras) == ["fig_homicidio_anual_sinesp", "fig_mulher_anual_sinesp", "fig_homicidios_jan_ago_sinesp", "fig_mulher_jan_ago_sinesp"]
    linhas = figuras["fig_homicidio_anual_sinesp"].axes[0].lines
    assert list(linhas[0].get_xdata()) == [2020, 2021, 2022, 2023, 2024, 2025]
    assert list(linhas[0].get_ydata()) == [62, 62, 49, 55, 36, 29]
    barras = figuras["fig_mulher_anual_sinesp"].axes[0].containers
    assert [b.get_height() for b in barras[0]] == [3, 6, 2, 2, 3, 2]       # Feminicídio
    assert [b.get_height() for b in barras[1]] == [10, 4, 7, 7, 10, 9]     # Tentativa de feminicídio
    linhas = figuras["fig_homicidios_jan_ago_sinesp"].axes[0].lines
    assert list(linhas[0].get_xdata()) == [2020, 2021, 2022, 2023, 2024, 2025, 2026]
    assert list(linhas[0].get_ydata()) == [50, 40, 29, 40, 21, 18, 22]
    assert list(linhas[1].get_ydata()) == [74, 53, 60, 62, 57, 37, 68]
    barras = figuras["fig_mulher_jan_ago_sinesp"].axes[0].containers
    assert [b.get_height() for b in barras[0]] == [0, 0] and [b.get_height() for b in barras[1]] == [4, 10]
    for nome, figura in figuras.items():
        eixo = figura.axes[0]
        assert eixo.get_ylim()[0] == 0, nome
        texto = _texto_da_figura(figura)
        assert "MJSP / Sinesp VDE" in texto and "Joinville/SC" in texto and "Estadual" in texto and "vítimas" in texto.lower(), nome


def test_figura_anual_sinesp_recusa_periodo_parcial(sinesp):
    with pytest.raises(ValueError, match="parcial"):
        graficos.quadro_eventos(sinesp, ["Homicídio doloso"], list(range(2020, 2027)), mes_final=None)


def test_valor_ausente_nao_vira_zero_nem_soma_parcial(sinesp):
    ausente = sinesp.copy()
    ausente.loc[(ausente["evento"] == "Homicídio doloso") & (ausente["ano"] == 2021) & (ausente["mes"] == 3), "valor"] = pd.NA
    anual = calculos.tabela_anual_sinesp(ausente)
    linha = anual[(anual["evento"] == "Homicídio doloso") & (anual["ano"] == 2021)].iloc[0]
    assert linha["meses_com_valor"] == 11 and linha["meses_presentes"] == 12 and pd.isna(linha["soma"])  # nada de soma parcial
    periodo = calculos.comparacao_periodo_sinesp(ausente, 8)
    assert pd.isna(periodo[(periodo["evento"] == "Homicídio doloso") & (periodo["ano"] == 2021)]["soma"].iloc[0])
    with pytest.raises(ValueError, match="ausente"):
        graficos.quadro_eventos(ausente, ["Homicídio doloso"], [2020, 2021], mes_final=None)
    assert graficos.figura_serie_anual_sinesp(ausente, "Homicídio doloso", "Estadual", [2021]) is None
    resumo = calculos.resumo_serie_sinesp(calculos.serie_sinesp(ausente, "Homicídio doloso", "Estadual"))
    assert resumo["meses_sem_valor"] == 1 and resumo["meses_com_valor"] == 79


def test_figuras_genericas_sinesp_usam_cores_por_ano_e_eixo_em_zero(sinesp):
    figura = graficos.figura_periodo_sinesp(sinesp, "Homicídio doloso", "Estadual", list(range(2020, 2027)))
    barras = figura.axes[0].patches
    assert [b.get_height() for b in barras] == [50, 40, 29, 40, 21, 18, 22]
    assert figura.axes[0].get_ylim()[0] == 0
    mensal = graficos.figura_mensal_sinesp(sinesp, "Tentativa de homicídio", "Estadual", [2025, 2026])
    assert [len(l.get_ydata()) for l in mensal.axes[0].lines] == [12, 8]  # 2026 só tem 8 meses
    assert graficos.COR_ANO[2023] == "#2563A6" and graficos.COR_ANO[2024] == "#D97706"
    assert graficos.figura_periodo_sinesp(sinesp, "Mandado de prisão cumprido", "Polícia Federal", [2020, 2021]) is None


# ------------------------------------------------------------------------------- Etapa 14.2 (SSP/SC)
def test_seis_figuras_aprovadas_da_violencia_domestica(vd):
    figuras = graficos.figuras_vd_aprovadas(vd)
    assert list(figuras) == [
        "fig_anual_maiores_ssp142", "fig_anual_intermediarias_ssp142", "fig_anual_menores_ssp142",
        "fig_mensal_ameaca_ssp142", "fig_mensal_lesao_leve_ssp142", "fig_mensal_injuria_ssp142"]
    esperado = {
        "fig_anual_maiores_ssp142": [("Ameaça", 1957, 2085), ("Lesão corporal leve dolosa", 989, 959), ("Injúria", 541, 716)],
        "fig_anual_intermediarias_ssp142": [("Vias de fato", 229, 281), ("Difamação", 190, 211), ("Calúnia", 109, 119)],
        "fig_anual_menores_ssp142": [("Estupro", 22, 30), ("Lesão corporal grave ou gravíssima dolosa", 19, 10), ("Injúria real", 2, 6)],
    }
    for nome, itens in esperado.items():
        eixo = figuras[nome].axes[0]
        assert [t.get_text().replace("\n", " ") for t in eixo.get_xticklabels()] == [c for c, _, _ in itens]
        assert [b.get_height() for b in eixo.containers[0]] == [a for _, a, _ in itens]
        assert [b.get_height() for b in eixo.containers[1]] == [b for _, _, b in itens]
        assert len(figuras[nome].axes) == 1 and eixo.get_ylim()[0] == 0  # eixo único, iniciado em zero
        assert [t.get_text() for t in eixo.get_legend().get_texts()] == ["2023", "2024"]
    for nome, categoria in graficos.CATEGORIAS_MENSAIS_VD.items():
        eixo = figuras[nome].axes[0]
        serie = vd[vd["categoria"] == categoria]
        for linha, ano in zip(eixo.lines, (2023, 2024)):
            assert list(linha.get_xdata()) == list(range(1, 13))
            assert list(linha.get_ydata()) == serie[serie["ano"] == ano].sort_values("mes")["fatos_comunicados"].astype(int).tolist()
        assert [t.get_text() for t in eixo.get_xticklabels()] == ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
        assert categoria in figuras[nome].get_suptitle() and eixo.get_ylim()[0] == 0
    for nome, figura in figuras.items():
        texto = _texto_da_figura(figura)
        assert all(t in texto for t in ("Joinville/SC", "SSP/SC", "janeiro/2023 a dezembro/2024", "fatos comunicados"))
        assert "vítima" not in texto.lower() and "total geral" not in texto.lower()


def test_figura_anual_vd_adapta_se_aos_meses_sem_alterar_definicoes(vd):
    comparacao = calculos.comparacao_anual_vd(vd, ["Ameaça", "Injúria"], 1, 6)
    figura = graficos.figura_anual_vd(comparacao, ["Ameaça", "Injúria"], "Teste", mes_inicial=1, mes_final=6)
    eixo = figura.axes[0]
    esperado_2023 = [int(vd[(vd.categoria == c) & (vd.ano == 2023) & (vd.mes <= 6)].fatos_comunicados.sum()) for c in ("Ameaça", "Injúria")]
    assert [b.get_height() for b in eixo.containers[0]] == esperado_2023
    assert "Jan a Jun" in eixo.get_title() and "meses 1 a 6" in eixo.get_ylabel()
