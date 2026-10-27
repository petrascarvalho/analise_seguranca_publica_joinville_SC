"""Figuras Matplotlib reutilizáveis do dashboard Sinesp/MJSP (sem Streamlit e sem ``pyplot``).

Recriam, a partir dos dados curados, as quatro figuras da Etapa 10 (Sinesp) e oferecem gráficos filtráveis por indicador,
abrangência e período. Todas começam o eixo vertical em zero, usam valores inteiros, identificam fonte, município, período e
unidade, e nunca somam indicadores, abrangências ou unidades diferentes. As figuras são objetos ``matplotlib.figure.Figure``
(use ``st.pyplot(figura)``) e não gravam arquivos.
"""

from __future__ import annotations

import textwrap

import pandas as pd
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

from dashboard import calculos
from dashboard.formatacao import ABREV_MESES, fmt_int

# Cores consistentes: cada ano tem sempre a mesma cor em todas as figuras do painel.
COR_ANO = {
    2020: "#7A5195", 2021: "#188977", 2022: "#8C8C8C", 2023: "#2563A6", 2024: "#D97706", 2025: "#C0392B", 2026: "#1B1B1B",
}
COR_EVENTO = {
    "Homicídio doloso": "#2563A6", "Tentativa de homicídio": "#188977",
    "Feminicídio": "#7A5195", "Tentativa de feminicídio": "#D97706",
}
COR_CINZA_TEXTO = "#333333"
_PALETA_RESERVA = ("#0B7285", "#9C36B5", "#E67700", "#5F3DC4", "#2B8A3E")


def cor_ano(ano: int) -> str:
    """Cor fixa de cada ano; anos futuros (sem cor definida) recebem uma cor da paleta de reserva, sempre a mesma."""
    return COR_ANO.get(int(ano)) or _PALETA_RESERVA[int(ano) % len(_PALETA_RESERVA)]

FONTE_SINESP = "Fonte: MJSP / Sinesp VDE"


def _milhar(valor, _posicao=None) -> str:
    return fmt_int(valor)


def _estilo_eixo(eixo, *, grade_y=True):
    eixo.set_axisbelow(True)
    if grade_y:
        eixo.grid(axis="y", color="#DDDDDD", linewidth=0.8)
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
    eixo.yaxis.set_major_formatter(FuncFormatter(_milhar))



# --------------------------------------------------------------------------- Sinesp (Etapa 10)
def _preparar_sinesp(titulo: str, periodo: str, interpretacao: str, limite_y: float, rodape: str, ylabel: str, xlabel: str = "Ano"):
    figura = Figure(figsize=(10, 6.2), dpi=120)
    figura.subplots_adjust(left=0.09, right=0.97, bottom=0.27, top=0.80)
    eixo = figura.add_subplot(111)
    figura.suptitle(titulo, x=0.08, y=0.97, ha="left", fontsize=15, fontweight="semibold")
    figura.text(0.08, 0.91, periodo, fontsize=11, color="#444444")
    eixo.set_xlabel(xlabel, fontsize=11)
    eixo.set_ylabel(ylabel, fontsize=11)
    eixo.set_ylim(0, limite_y)
    _estilo_eixo(eixo)
    figura.text(0.08, 0.125, textwrap.fill(interpretacao, width=108), va="top", fontsize=9, color=COR_CINZA_TEXTO)
    figura.text(0.08, 0.035, rodape, fontsize=9, color="#555555")
    return figura, eixo


def _linhas_sinesp(eixo, quadro: pd.DataFrame, cores: dict[str, str]):
    for numero, nome in enumerate(quadro.columns):
        valores = [int(v) for v in quadro[nome].tolist()]
        eixo.plot(quadro.index.tolist(), valores, label=nome, color=cores[nome], marker="o" if numero == 0 else "s",
                  linestyle="-" if numero == 0 else "--", linewidth=2, markersize=6)
        for ano, valor in zip(quadro.index, valores):
            eixo.annotate(fmt_int(valor), (ano, valor), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=10)
    eixo.set_xticks(quadro.index.tolist())
    if len(quadro.columns) > 1:
        eixo.legend(loc="lower left", bbox_to_anchor=(0, 1.01), ncol=2, frameon=False, fontsize=10)


def _barras_sinesp(eixo, quadro: pd.DataFrame, cores: dict[str, str]):
    posicoes = list(range(len(quadro)))
    largura = 0.34
    for numero, nome in enumerate(quadro.columns):
        valores = [int(v) for v in quadro[nome].tolist()]
        barras = eixo.bar([p + (numero - 0.5) * largura for p in posicoes], valores, width=largura, label=nome, color=cores[nome],
                          hatch="//" if numero == 0 else None)
        eixo.bar_label(barras, labels=[fmt_int(v) for v in valores], padding=4, fontsize=10)
    eixo.set_xticks(posicoes, quadro.index.tolist())
    eixo.legend(loc="lower left", bbox_to_anchor=(0, 1.01), ncol=2, frameon=False, fontsize=10)


def quadro_eventos(sinesp: pd.DataFrame, eventos: list[str], anos: list[int], *, mes_final: int | None, abrangencia: str = "Estadual") -> pd.DataFrame:
    """Pivot ano × evento (vítimas, Estadual). Interrompe se houver valor ausente ou período não equivalente."""
    recorte = sinesp.loc[sinesp["abrangencia"].eq(abrangencia) & sinesp["evento"].isin(eventos) & sinesp["ano"].isin(anos)]
    if mes_final is None:
        tabela = calculos.tabela_anual_sinesp(recorte)
        if not tabela["cobertura"].eq("ano completo").all():
            raise ValueError("Série anual com período parcial; a figura anual usa só anos completos.")
        coluna = "soma"
    else:
        tabela = calculos.comparacao_periodo_sinesp(recorte, mes_final)
        coluna = "soma"
    if not tabela["unidade"].eq("vítimas").all():
        raise ValueError("Unidades incompatíveis: a figura exige vítimas.")
    quadro = tabela.pivot(index="ano", columns="evento", values=coluna).reindex(index=anos, columns=eventos)
    if quadro.isna().any().any():
        raise ValueError("Valor ausente: figura interrompida sem preenchimento.")
    return quadro.astype(int)


def figuras_sinesp_etapa10(sinesp: pd.DataFrame) -> dict[str, Figure]:
    """As quatro figuras da Etapa 10, recriadas dos dados curados (mesmos recortes, limites e textos)."""
    rodape = "Fonte: MJSP / Sinesp VDE | Abrangência: Estadual | Unidade: vítimas"
    homicidio = quadro_eventos(sinesp, ["Homicídio doloso"], list(range(2020, 2026)), mes_final=None)
    mulher = quadro_eventos(sinesp, ["Feminicídio", "Tentativa de feminicídio"], list(range(2020, 2026)), mes_final=None)
    homicidios_ja = quadro_eventos(sinesp, ["Homicídio doloso", "Tentativa de homicídio"], list(range(2020, 2027)), mes_final=8)
    mulher_ja = quadro_eventos(sinesp, ["Feminicídio", "Tentativa de feminicídio"], [2025, 2026], mes_final=8)
    textos = {
        "homicidio_anual": f"O total publicado passou de {homicidio.loc[2020, 'Homicídio doloso']} vítimas em 2020 para {homicidio.loc[2025, 'Homicídio doloso']} em 2025, com oscilações intermediárias. A série não demonstra causas.",
        "mulher_anual": f"Feminicídios variaram de {mulher['Feminicídio'].min()} a {mulher['Feminicídio'].max()} vítimas anuais; tentativas, de {mulher['Tentativa de feminicídio'].min()} a {mulher['Tentativa de feminicídio'].max()}. São pequenas contagens de categorias distintas, sem soma entre elas.",
        "homicidios_jan_ago": f"De janeiro a agosto, homicídios passaram de {homicidios_ja.loc[2025, 'Homicídio doloso']} em 2025 para {homicidios_ja.loc[2026, 'Homicídio doloso']} em 2026; tentativas, de {homicidios_ja.loc[2025, 'Tentativa de homicídio']} para {homicidios_ja.loc[2026, 'Tentativa de homicídio']}. Os períodos têm a mesma duração.",
        "mulher_jan_ago": f"Tentativas passaram de {mulher_ja.loc[2025, 'Tentativa de feminicídio']} para {mulher_ja.loc[2026, 'Tentativa de feminicídio']} vítimas. Feminicídio tem zero publicado nos dois recortes; isso não comprova eliminação do fenômeno.",
    }
    figuras = {}
    f, e = _preparar_sinesp("Homicídio doloso em Joinville/SC", "Anos completos: 2020–2025", textos["homicidio_anual"], 70, rodape, "Vítimas")
    _linhas_sinesp(e, homicidio, COR_EVENTO)
    figuras["fig_homicidio_anual_sinesp"] = f
    f, e = _preparar_sinesp("Feminicídio e tentativa de feminicídio em Joinville/SC", "Anos completos: 2020–2025", textos["mulher_anual"], 12, rodape, "Vítimas")
    _barras_sinesp(e, mulher, COR_EVENTO)
    figuras["fig_mulher_anual_sinesp"] = f
    f, e = _preparar_sinesp("Homicídio doloso e tentativa de homicídio em Joinville/SC", "Períodos equivalentes: janeiro–agosto de 2020 a 2026",
                            textos["homicidios_jan_ago"], 90, rodape, "Vítimas")
    _linhas_sinesp(e, homicidios_ja, COR_EVENTO)
    figuras["fig_homicidios_jan_ago_sinesp"] = f
    f, e = _preparar_sinesp("Feminicídio e tentativa de feminicídio em Joinville/SC", "Períodos equivalentes: janeiro–agosto de 2025 e 2026",
                            textos["mulher_jan_ago"], 12, rodape, "Vítimas")
    _barras_sinesp(e, mulher_ja, COR_EVENTO)
    figuras["fig_mulher_jan_ago_sinesp"] = f
    return figuras


def figura_serie_anual_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> Figure | None:
    """Série anual de um único indicador (somente anos completos selecionados)."""
    serie = sinesp.loc[sinesp["evento"].eq(evento) & sinesp["abrangencia"].eq(abrangencia)]
    tabela = calculos.tabela_anual_sinesp(serie)
    tabela = tabela.loc[tabela["ano"].isin(anos) & tabela["cobertura"].eq("ano completo") & tabela["soma"].notna()].sort_values("ano")
    if tabela.empty:
        return None
    unidade = tabela["unidade"].iloc[0]
    maximo = int(tabela["soma"].max())
    figura, eixo = _preparar_sinesp(f"{evento} em Joinville/SC", f"Anos completos selecionados ({int(tabela['ano'].min())}–{int(tabela['ano'].max())}) — abrangência {abrangencia}",
                                    "Soma dos 12 meses de cada ano. Um ano parcial (ainda incompleto) não entra em séries anuais.", max(maximo * 1.25, 1),
                                    f"{FONTE_SINESP} | Abrangência: {abrangencia} | Unidade: {unidade}", unidade.split(" (")[0].capitalize())
    _linhas_sinesp(eixo, pd.DataFrame({evento: tabela["soma"].astype(int).to_numpy()}, index=tabela["ano"].astype(int).to_numpy()), {evento: "#2563A6"})
    return figura


def figura_periodo_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int], mes_final: int = 8) -> Figure | None:
    """Barras de períodos equivalentes (janeiro até ``mes_final``) por ano para um indicador."""
    serie = sinesp.loc[sinesp["evento"].eq(evento) & sinesp["abrangencia"].eq(abrangencia)]
    tabela = calculos.comparacao_periodo_sinesp(serie, mes_final)
    tabela = tabela.loc[tabela["ano"].isin(anos) & tabela["soma"].notna()].sort_values("ano")
    if tabela.empty:
        return None
    unidade = tabela["unidade"].iloc[0]
    maximo = int(tabela["soma"].max())
    rotulo = tabela["periodo"].iloc[0]
    figura, eixo = _preparar_sinesp(f"{evento} em Joinville/SC", f"Períodos equivalentes ({rotulo}) — abrangência {abrangencia}",
                                    f"Todos os anos têm os mesmos meses ({rotulo}); a comparação é entre períodos de igual duração.", max(maximo * 1.25, 1),
                                    f"{FONTE_SINESP} | Abrangência: {abrangencia} | Unidade: {unidade}", unidade.split(" (")[0].capitalize())
    anos_plot = tabela["ano"].astype(int).tolist()
    barras = eixo.bar(range(len(anos_plot)), [int(v) for v in tabela["soma"]], color=[cor_ano(a) for a in anos_plot], width=0.55)
    eixo.bar_label(barras, labels=[fmt_int(v) for v in tabela["soma"]], padding=4, fontsize=10)
    eixo.set_xticks(range(len(anos_plot)), [str(a) for a in anos_plot])
    eixo.set_xlim(-0.7, len(anos_plot) - 0.3)
    return figura


def figura_mensal_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> Figure | None:
    """Série mensal de um indicador, uma linha por ano (cores consistentes por ano). Meses sem valor ficam em branco."""
    serie = sinesp.loc[sinesp["evento"].eq(evento) & sinesp["abrangencia"].eq(abrangencia) & sinesp["ano"].isin(anos)]
    if serie.empty:
        return None
    unidade = serie["unidade"].iloc[0]
    maximo = int(serie["valor"].max()) if serie["valor"].notna().any() else 1
    figura, eixo = _preparar_sinesp(f"{evento} em Joinville/SC — por mês", f"Meses publicados nos anos selecionados — abrangência {abrangencia}",
                                    "Cada linha é um ano; o último ano pode estar parcial. Meses sem valor publicado não são preenchidos.",
                                    max(maximo * 1.25, 1), f"{FONTE_SINESP} | Abrangência: {abrangencia} | Unidade: {unidade}",
                                    unidade.split(" (")[0].capitalize(), xlabel="Mês")
    for ano in sorted(set(serie["ano"].astype(int))):
        parte = serie.loc[serie["ano"].eq(ano)].sort_values("mes")
        eixo.plot(parte["mes"].astype(int).tolist(), [None if pd.isna(v) else int(v) for v in parte["valor"]], marker="o", markersize=4,
                  linewidth=1.8, color=cor_ano(ano), label=str(ano))
    eixo.set_xticks(range(1, 13), ABREV_MESES)
    eixo.legend(loc="lower left", bbox_to_anchor=(0, 1.01), ncol=7, frameon=False, fontsize=10)
    return figura


def figura_ranking_sinesp(ranking: pd.DataFrame, ano: int) -> Figure | None:
    """Barras horizontais das séries ordenadas pela soma do ano completo ``ano`` (uma única unidade; sem total entre séries)."""
    if ranking.empty:
        return None
    unidade = ranking["unidade"].iloc[0]
    if ranking["unidade"].nunique() != 1:
        raise ValueError("Ranking com unidades diferentes: vítimas e mandados não podem ser comparados.")
    rotulos = ["\n".join(textwrap.wrap(f"{r.evento} ({r.abrangencia})", 52)) for r in ranking.itertuples()]
    valores = [int(v) for v in ranking["soma"]]
    figura = Figure(figsize=(10, 0.55 * len(valores) + 3.2), dpi=120)
    eixo = figura.add_axes([0.42, 0.18, 0.54, 0.62])
    posicoes = list(range(len(valores)))[::-1]
    barras = eixo.barh(posicoes, valores, color="#2563A6", height=0.62)
    eixo.bar_label(barras, labels=[fmt_int(v) for v in valores], padding=4, fontsize=10)
    eixo.set_yticks(posicoes, rotulos, fontsize=9)
    eixo.set_xlim(0, max(valores) * 1.18 if max(valores) else 1)
    eixo.xaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
    eixo.xaxis.set_major_formatter(FuncFormatter(_milhar))
    eixo.grid(axis="x", color="#DDDDDD", linewidth=0.8)
    eixo.set_axisbelow(True)
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.set_xlabel(unidade.split(" (")[0].capitalize() + f" em {ano} (soma dos 12 meses)", fontsize=11)
    figura.suptitle(f"Joinville/SC — séries ordenadas pelo total de {ano} (ano completo)", x=0.01, y=0.97, ha="left", fontsize=13, fontweight="bold")
    figura.text(0.01, 0.045, f"{FONTE_SINESP} | Unidade: {unidade} | Ordenação dentro de uma única unidade; nenhum total entre indicadores.", fontsize=8.5, color=COR_CINZA_TEXTO)
    return figura
