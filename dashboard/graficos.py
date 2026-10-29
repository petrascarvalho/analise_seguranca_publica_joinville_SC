"""Figuras Matplotlib reutilizáveis do dashboard Sinesp/MJSP (sem Streamlit e sem pyplot).

Recriam, a partir dos dados curados, as quatro figuras da Etapa 10 (Sinesp) e oferecem gráficos filtráveis por indicador,
abrangência e período. Todas começam o eixo vertical em zero, usam valores inteiros, identificam fonte, município, período e
unidade, e nunca somam indicadores, abrangências ou unidades diferentes. As figuras são objetos matplotlib.figure.Figure
(use st.pyplot(figura)) e não gravam arquivos.
"""

from __future__ import annotations

# textwrap quebra textos longos em linhas; contextvars/contextmanager guardam se o modo compacto está ligado.
import textwrap
from contextlib import contextmanager
from contextvars import ContextVar

# numpy: contas com listas de números; pandas: tabelas.
import numpy as np
import pandas as pd
from matplotlib import colormaps
# Matplotlib: Figure cria a figura sem abrir janela (adequado ao Streamlit); colormaps dá a escala de azuis do mapa de calor;
# MaxNLocator escolhe marcas inteiras no eixo e FuncFormatter formata os números do eixo.
from matplotlib.figure import Figure
from matplotlib.ticker import FuncFormatter, MaxNLocator

from dashboard import calculos
from dashboard.formatacao import ABREV_MESES, fmt_dec, fmt_int

# Identidade azul e branca (proposta inspirada na bandeira de Joinville; não são códigos oficiais do município).
# Cada ano tem sempre o mesmo tom de azul em todas as figuras do painel: do mais claro (2020) ao mais escuro (2026).
# Dicionário ano -> cor: o mesmo ano sempre aparece com o mesmo azul.
COR_ANO = {
    2020: "#A9CBEA", 2021: "#7FB0DE", 2022: "#4F8FCB", 2023: "#2A73B8", 2024: "#074EA2", 2025: "#0A3470", 2026: "#04193A",
}
COR_EVENTO = {
    "Homicídio doloso": "#074EA2", "Tentativa de homicídio": "#4F8FCB",
    "Feminicídio": "#0A3470", "Tentativa de feminicídio": "#8FBBE3",
}
COR_AZUL = "#074EA2"           # azul principal (barras e destaques)
COR_AZUL_CLARO = "#8FBBE3"     # barras de apoio
COR_BARRA_ANUAL = "#A8CDEB"    # barras preenchidas do gráfico combinado (evolução anual)
COR_CINZA_TEXTO = "#20354F"
_PALETA_RESERVA = ("#3E7FBF", "#1C5FA8", "#6AA3D6", "#0D4283", "#90B9E2")  # anos sem cor definida: ainda tons de azul


def cor_ano(ano: int) -> str:
    """Cor fixa de cada ano; anos futuros (sem cor definida) recebem uma cor da paleta de reserva, sempre a mesma."""
    return COR_ANO.get(int(ano)) or _PALETA_RESERVA[int(ano) % len(_PALETA_RESERVA)]

FONTE_SINESP = "Fonte: MJSP / Sinesp VDE"

# ---------------------------------------------------------------------------------------------------- modo compacto
# No modo compacto as figuras são criadas já estreitas (4,4 × 6,4 pol.; ~358 px na tela de um celular), com fontes de 10–13 pt, títulos
# quebrados em linhas, legenda abaixo do gráfico, menos marcas nos eixos e SEM os textos longos dentro da imagem (a interpretação e a
# fonte completa ficam em figura.sinesp_notas e são exibidas pela interface como texto nativo). Os valores desenhados são os mesmos.
# Variável que guarda se o modo compacto está ligado nesta execução da página (cada usuário tem a sua).
_COMPACTO: ContextVar[bool] = ContextVar("sinesp_modo_compacto", default=False)


def definir_modo_compacto(ativo: bool) -> None:
    """Liga/desliga o modo compacto para as figuras criadas a seguir, no contexto (thread) atual."""
    _COMPACTO.set(bool(ativo))


def esta_compacto() -> bool:
    """Diz se as figuras desta execução estão no modo compacto (celular)."""
    return _COMPACTO.get()


@contextmanager
def modo_compacto(ativo: bool = True):
    """with modo_compacto(): figura = ... — cria figuras compactas só dentro do bloco."""
    token = _COMPACTO.set(bool(ativo))
    try:
        yield
    finally:
        _COMPACTO.reset(token)


def _milhar(valor, _posicao=None) -> str:
    """Formata o número do eixo com ponto de milhar (função usada pelo Matplotlib)."""
    return fmt_int(valor)


# Estilo comum: grade horizontal clara, sem bordas de cima e da direita, marcas inteiras com ponto de milhar.
def _estilo_eixo(eixo, *, grade_y=True):
    """Aplica o estilo comum aos eixos: grade horizontal suave, sem bordas superior e direita, valores inteiros."""
    eixo.set_axisbelow(True)
    if grade_y:
        eixo.grid(axis="y", color="#D9E5F2", linewidth=0.8)
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
    eixo.yaxis.set_major_formatter(FuncFormatter(_milhar))



# --------------------------------------------------------------------------- Sinesp (Etapa 10)
def _preparar_compacto(titulo: str, periodo: str, interpretacao: str, limite_y: float, rodape: str, ylabel: str, xlabel: str):
    """Figura estreita para celular: título e subtítulo quebrados, só a fonte curta na imagem; o resto vai para figura.sinesp_notas."""
    # Figura estreita (4,4 x 6,4 polegadas) para caber na tela de um celular.
    figura = Figure(figsize=(4.4, 6.4), dpi=120)
    linhas_titulo, linhas_subtitulo = textwrap.wrap(titulo, 30), textwrap.wrap(periodo, 42)
    y = 0.985
    figura.text(0.04, y, "\n".join(linhas_titulo), ha="left", va="top", fontsize=13, fontweight="semibold")
    y -= 0.037 * len(linhas_titulo) + 0.008
    figura.text(0.04, y, "\n".join(linhas_subtitulo), ha="left", va="top", fontsize=10, color="#444444", linespacing=1.25)
    y -= 0.028 * len(linhas_subtitulo) + 0.03
    figura.subplots_adjust(left=0.18, right=0.95, bottom=0.31, top=max(y, 0.5))  # sem rodapé na imagem
    eixo = figura.add_subplot(111)
    eixo.set_xlabel(xlabel, fontsize=11)
    eixo.set_ylabel(ylabel, fontsize=11)
    eixo.set_ylim(0, limite_y)
    _estilo_eixo(eixo)
    eixo.tick_params(labelsize=10)
    figura.sinesp_compacta = True
    figura.sinesp_notas = {"interpretacao": interpretacao, "rodape": rodape}  # a fonte completa vai UMA vez, como texto nativo abaixo da figura
    return figura, eixo


def _preparar_sinesp(titulo: str, periodo: str, interpretacao: str, limite_y: float, rodape: str, ylabel: str, xlabel: str = "Ano"):
    """Cria a figura-padrão (título, período, texto de interpretação e rodapé) e devolve a figura e o eixo."""
    if esta_compacto():
        return _preparar_compacto(titulo, periodo, interpretacao, limite_y, rodape, ylabel, xlabel)
    # Figura de 10 x 6,2 polegadas; subplots_adjust define as margens e add_subplot cria a área do gráfico (eixo).
    figura = Figure(figsize=(10, 6.2), dpi=120)
    figura.subplots_adjust(left=0.09, right=0.97, bottom=0.27, top=0.80)
    eixo = figura.add_subplot(111)
    # Título e subtítulo no topo; x e y são posições relativas (0 a 1) dentro da figura.
    figura.suptitle(titulo, x=0.08, y=0.97, ha="left", fontsize=15, fontweight="semibold")
    figura.text(0.08, 0.91, periodo, fontsize=11, color="#444444")
    eixo.set_xlabel(xlabel, fontsize=11)
    eixo.set_ylabel(ylabel, fontsize=11)
    eixo.set_ylim(0, limite_y)
    _estilo_eixo(eixo)
    # Texto de interpretação e fonte (rodapé) escritos abaixo do gráfico.
    linhas_texto = textwrap.wrap(interpretacao, width=108)
    figura.text(0.08, 0.125 + 0.02 * max(len(linhas_texto) - 2, 0), "\n".join(linhas_texto), va="top", fontsize=9, color=COR_CINZA_TEXTO)
    figura.text(0.08, 0.035, rodape, fontsize=9, color="#555555")
    figura.sinesp_notas = {"interpretacao": interpretacao, "rodape": rodape}
    return figura, eixo


def ajustar_compacto(figura):
    """Tira o espaço em branco abaixo das figuras COMPACTAS: mede o que está mais embaixo (rótulos do eixo ou legenda) e corta o resto,
    deslocando tudo de forma uniforme (títulos, gráfico e legenda mantêm tamanho e posição relativa). Idempotente; não mexe em figuras do
    modo completo nem em dados."""
    if getattr(figura, "sinesp_ajustada", False) or not getattr(figura, "sinesp_compacta", False) or len(figura.axes) != 1:
        return figura
    from matplotlib.backends.backend_agg import FigureCanvasAgg

    figura.sinesp_ajustada = True
    FigureCanvasAgg(figura)
    figura.canvas.draw()
    eixo, dpi = figura.axes[0], figura.dpi
    # Mede, em pixels, onde termina o conteúdo mais baixo da figura para cortar só o espaço vazio.
    inferior = float(eixo.get_tightbbox(figura.canvas.get_renderer()).y0)  # pixels, a partir da base (inclui marcas, rótulos e legenda)
    legenda = eixo.get_legend()
    if legenda is not None:
        inferior = min(inferior, float(legenda.get_window_extent(figura.canvas.get_renderer()).y0))
    corte = inferior - 0.12 * dpi  # mantém uma pequena margem
    altura = figura.get_figheight() * dpi
    if corte <= 0:
        return figura
    nova = altura - corte
    posicao = eixo.get_position()
    eixo.set_position([posicao.x0, (posicao.y0 * altura - corte) / nova, posicao.width, posicao.height * altura / nova])
    for texto in figura.texts:
        x, y = texto.get_position()
        texto.set_position((x, (y * altura - corte) / nova))
    if legenda is not None:
        legenda.set_bbox_to_anchor((0.565, (0.205 * altura - corte) / nova), transform=figura.transFigure)
    figura.set_size_inches(figura.get_figwidth(), nova / dpi)
    return figura


def ajustar_completo(figura):
    """Tira o espaço vazio do topo das figuras do modo COMPLETO que não têm legenda nem aviso acima do eixo.

    A figura reserva espaço para uma legenda acima do gráfico; quando ela não existe, o eixo sobe até perto do subtítulo.
    Só a posição do eixo muda (valores, textos e cores ficam iguais). Idempotente; ignora figuras compactas e com mais de um eixo.
    """
    if getattr(figura, "sinesp_ajustada", False) or getattr(figura, "sinesp_compacta", False) or len(figura.axes) != 1:
        return figura
    figura.sinesp_ajustada = True
    eixo = figura.axes[0]
    legenda = eixo.get_legend()
    acima = legenda is not None and legenda.get_bbox_to_anchor().transformed(eixo.transAxes.inverted()).y0 >= 0.99
    aviso_acima = any(t.get_transform() == eixo.transAxes and t.get_position()[1] > 1 for t in eixo.texts)
    posicao = eixo.get_position()
    if not acima and not aviso_acima and posicao.y1 < 0.85:
        eixo.set_position([posicao.x0, posicao.y0, posicao.width, 0.85 - posicao.y0])
    return figura


def _legenda(eixo, ncol: int, handles=None, **desktop):
    """Legenda acima do gráfico (desktop) ou abaixo dele, em até 2 colunas (compacto). handles fixa a ordem das entradas."""
    extra = {"handles": handles} if handles is not None else {}
    if esta_compacto():
        return eixo.legend(loc="upper center", bbox_to_anchor=(0.565, 0.205), bbox_transform=eixo.figure.transFigure, ncol=min(ncol, 2), frameon=False, fontsize=10, **extra)
    return eixo.legend(loc="lower left", bbox_to_anchor=(0, 1.01), ncol=ncol, frameon=False, fontsize=10, **extra, **desktop)


def _eixo_meses(eixo) -> None:
    """Marcas dos meses: os 12 meses no desktop; Jan, Mar, Jun, Set e Dez no compacto (menos rótulos, mesma escala)."""
    if esta_compacto():
        eixo.set_xticks([1, 3, 6, 9, 12], [ABREV_MESES[m - 1] for m in (1, 3, 6, 9, 12)])
    else:
        eixo.set_xticks(range(1, 13), ABREV_MESES)


def _linhas_sinesp(eixo, quadro: pd.DataFrame, cores: dict[str, str]):
    """Desenha uma linha com marcadores para cada coluna da tabela e escreve o valor de cada ponto."""
    for numero, nome in enumerate(quadro.columns):
        valores = [int(v) for v in quadro[nome].tolist()]
        # plot desenha uma linha com marcadores (bolinha na primeira série, quadrado na segunda).
        eixo.plot(quadro.index.tolist(), valores, label=nome, color=cores[nome], marker="o" if numero == 0 else "s",
                  linestyle="-" if numero == 0 else "--", linewidth=2, markersize=6)
        for ano, valor in zip(quadro.index, valores):
            # annotate escreve o valor um pouco acima (8 pontos) de cada marcador.
            eixo.annotate(fmt_int(valor), (ano, valor), textcoords="offset points", xytext=(0, 8), ha="center", fontsize=10)
    eixo.set_xticks(quadro.index.tolist())
    if len(quadro.columns) > 1:
        _legenda(eixo, 2)


def _barras_sinesp(eixo, quadro: pd.DataFrame, cores: dict[str, str]):
    """Desenha barras lado a lado para cada coluna da tabela e escreve o valor sobre cada barra."""
    posicoes = list(range(len(quadro)))
    largura = 0.34
    for numero, nome in enumerate(quadro.columns):
        valores = [int(v) for v in quadro[nome].tolist()]
        # bar desenha as barras; cada série é deslocada meia largura para os lados, para ficarem lado a lado.
        barras = eixo.bar([p + (numero - 0.5) * largura for p in posicoes], valores, width=largura, label=nome, color=cores[nome],
                          hatch="//" if numero == 0 else None)
        # bar_label escreve o valor sobre cada barra (só quando maior que zero).
        eixo.bar_label(barras, labels=[fmt_int(v) if v > 0 else "" for v in valores], padding=4, fontsize=10)
    eixo.set_xticks(posicoes, quadro.index.tolist())
    _legenda(eixo, 2)


def quadro_eventos(sinesp: pd.DataFrame, eventos: list[str], anos: list[int], *, mes_final: int | None, abrangencia: str = "Estadual") -> pd.DataFrame:
    """Pivot ano × evento (vítimas, Estadual). Interrompe se houver valor ausente ou período não equivalente."""
    # Filtra a classificação, os indicadores (isin = está na lista) e os anos pedidos.
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
    # pivot: anos nas linhas e indicadores nas colunas; reindex garante a ordem pedida.
    quadro = tabela.pivot(index="ano", columns="evento", values=coluna).reindex(index=anos, columns=eventos)
    # Se faltar algum valor, a figura não é feita (nada é preenchido com zero).
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
    # Textos das figuras fixas: .loc[2020, "Homicídio doloso"] lê o valor da linha 2020 na coluna do indicador.
    textos = {
        "homicidio_anual": f"O total publicado passou de {homicidio.loc[2020, 'Homicídio doloso']} vítimas em 2020 para {homicidio.loc[2025, 'Homicídio doloso']} "
                           "em 2025, com oscilações intermediárias. A série não demonstra causas.",
        "mulher_anual": f"Feminicídios variaram de {mulher['Feminicídio'].min()} a {mulher['Feminicídio'].max()} vítimas anuais; tentativas, de {mulher['Tentativa de feminicídio'].min()} "
                        f"a {mulher['Tentativa de feminicídio'].max()}. São pequenas contagens de categorias distintas, sem soma entre elas.",
        "homicidios_jan_ago": f"De janeiro a agosto, homicídios passaram de {homicidios_ja.loc[2025, 'Homicídio doloso']} em 2025 para {homicidios_ja.loc[2026, 'Homicídio doloso']} "
                              f"em 2026; tentativas, de {homicidios_ja.loc[2025, 'Tentativa de homicídio']} para {homicidios_ja.loc[2026, 'Tentativa de homicídio']}. "
                              "Os períodos têm a mesma duração.",
        "mulher_jan_ago": f"Tentativas passaram de {mulher_ja.loc[2025, 'Tentativa de feminicídio']} para {mulher_ja.loc[2026, 'Tentativa de feminicídio']} vítimas. "
                          "Feminicídio tem zero publicado nos dois recortes; isso não comprova eliminação do fenômeno.",
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


def _fonte_no_subtitulo() -> str:
    """Fonte no subtítulo da figura. No modo compacto ela aparece uma única vez, em texto nativo abaixo da imagem (ver ui.mostrar_figura)."""
    return "" if esta_compacto() else " · MJSP/Sinesp VDE"


def _subtitulo(unidade: str, texto: str) -> str:
    """Subtítulo padrão das figuras: município, fonte (fora do modo compacto) e o que é mostrado, na unidade da série.
    A classificação institucional (Estadual, Polícia Federal, PRF) fica só na nota de rodapé da figura, não no subtítulo."""
    return f"Joinville/SC{_fonte_no_subtitulo()} · {unidade.split(' (')[0]} {texto}"


def _barras_e_linha_anual(eixo, valores: list[int], gid_linha: str, gid_barras: str):
    """Gráfico combinado de evolução anual: barras azul-claras com o valor de cada ano e, por cima, uma linha azul-escura com marcadores circulares.

    As barras e a linha usam a MESMA escala vertical (iniciada em zero). O valor é escrito uma só vez, acima de cada ponto da linha (nada é escrito nas
    barras). Usada só em séries de poucos pontos (anos), para não sobrecarregar o gráfico.
    """
    x = list(range(len(valores)))
    # Gráfico combinado: primeiro as barras azul-claras; set_gid dá um nome a cada elemento (permite conferir os valores desenhados).
    barras = eixo.bar(x, valores, width=0.62, color=COR_BARRA_ANUAL, zorder=2)
    for barra in barras:
        barra.set_gid(gid_barras)
    # Depois a linha azul-escura com marcadores circulares, na mesma escala; zorder=3 a coloca na frente das barras.
    linha, = eixo.plot(x, valores, color=COR_AZUL, linewidth=2.4, marker="o", markersize=8, markerfacecolor=COR_AZUL, markeredgecolor="white", zorder=3)
    linha.set_gid(gid_linha)
    for posicao, valor in zip(x, valores):
        # annotate escreve o número acima de cada ponto da linha (xytext desloca o texto 11 pontos para cima).
        eixo.annotate(fmt_int(valor), (posicao, valor), textcoords="offset points", xytext=(0, 11), ha="center", fontsize=10.5, fontweight="semibold", color="#103C6D", zorder=4)
    return linha


def figura_serie_anual_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> Figure | None:
    """Série anual de um único indicador (somente anos completos selecionados), em gráfico combinado: barras azul-claras e linha azul-escura com marcadores e rótulos."""
    # Seleciona as linhas do indicador escolhido (.loc com duas condições ligadas por &).
    serie = sinesp.loc[sinesp["evento"].eq(evento) & sinesp["abrangencia"].eq(abrangencia)]
    tabela = calculos.tabela_anual_sinesp(serie)
    # Totais anuais só dos anos escolhidos que estão completos e têm soma conhecida, em ordem de ano.
    tabela = tabela.loc[tabela["ano"].isin(anos) & tabela["cobertura"].eq("ano completo") & tabela["soma"].notna()].sort_values("ano")
    if tabela.empty:
        return None
    # Unidade da série (vítimas ou mandados), lida na primeira linha: aparece no rodapé e no eixo vertical.
    unidade = tabela["unidade"].iloc[0]
    maximo = int(tabela["soma"].max())
    figura, eixo = _preparar_sinesp(f"{evento} em Joinville/SC", _subtitulo(unidade, f"por ano completo ({int(tabela['ano'].min()) if tabela['ano'].min() == tabela['ano'].max() else str(int(tabela['ano'].min())) + '–' + str(int(tabela['ano'].max()))})"),
                                    "Barras e linha mostram a mesma soma dos 12 meses de cada ano, na mesma escala (iniciada em zero); o valor está escrito acima "
                                    "de cada ponto. "
                                    "Um ano parcial (ainda incompleto) não entra em séries anuais.", max(maximo * 1.25, 1),
                                    f"{FONTE_SINESP} | Abrangência: {abrangencia} | Unidade: {unidade}", unidade.split(" (")[0].capitalize())
    # Listas Python com os anos e os totais: são as coordenadas x e y do gráfico.
    anos_plot = tabela["ano"].astype(int).tolist()
    # Desenha barras + linha e escreve os anos no eixo horizontal (set_xticks).
    _barras_e_linha_anual(eixo, [int(v) for v in tabela["soma"]], "linha_anual", "barra_anual")
    eixo.set_xticks(range(len(anos_plot)), [str(a) for a in anos_plot])
    eixo.set_xlim(-0.5, len(anos_plot) - 0.5)
    _aviso_sem_variacao(eixo, tabela["soma"])
    return figura


def figura_periodo_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int], mes_final: int = 8) -> Figure | None:
    """Gráfico combinado (barras claras + linha com marcadores) dos períodos equivalentes (janeiro até mes_final) por ano para um indicador."""
    # Mesma seleção do indicador; depois soma o período equivalente (janeiro até o mês final) de cada ano.
    serie = sinesp.loc[sinesp["evento"].eq(evento) & sinesp["abrangencia"].eq(abrangencia)]
    tabela = calculos.comparacao_periodo_sinesp(serie, mes_final)
    # Só os anos escolhidos no filtro (isin) e com total conhecido (notna), em ordem.
    tabela = tabela.loc[tabela["ano"].isin(anos) & tabela["soma"].notna()].sort_values("ano")
    if tabela.empty:
        return None
    unidade = tabela["unidade"].iloc[0]
    maximo = int(tabela["soma"].max())
    # Nome do período (ex.: janeiro–setembro), igual em todas as linhas.
    rotulo = tabela["periodo"].iloc[0]
    figura, eixo = _preparar_sinesp(f"{evento} em Joinville/SC", _subtitulo(unidade, f"em {rotulo}, em cada ano"),
                                    f"Todos os anos têm os mesmos meses ({rotulo}); a comparação é entre períodos de igual duração. Barras e linha mostram o mesmo valor, na mesma escala (iniciada em zero).", max(maximo * 1.25, 1),
                                    f"{FONTE_SINESP} | Abrangência: {abrangencia} | Unidade: {unidade}", unidade.split(" (")[0].capitalize())
    anos_plot = tabela["ano"].astype(int).tolist()
    # O mesmo gráfico combinado, agora com a soma do período equivalente.
    _barras_e_linha_anual(eixo, [int(v) for v in tabela["soma"]], "linha_periodo", "barra_periodo")
    eixo.set_xticks(range(len(anos_plot)), [str(a) for a in anos_plot])
    eixo.set_xlim(-0.5, len(anos_plot) - 0.5)
    _aviso_sem_variacao(eixo, tabela["soma"])
    return figura


def figura_mensal_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> Figure | None:
    """Série mensal de um indicador, uma linha por ano (cores consistentes por ano). Meses sem valor ficam em branco."""
    # Linhas da série escolhida nos anos do filtro.
    serie = sinesp.loc[sinesp["evento"].eq(evento) & sinesp["abrangencia"].eq(abrangencia) & sinesp["ano"].isin(anos)]
    if serie.empty:
        return None
    unidade = serie["unidade"].iloc[0]
    maximo = int(serie["valor"].max()) if serie["valor"].notna().any() else 1
    figura, eixo = _preparar_sinesp(_titulo(evento), _subtitulo(unidade, "por mês, uma barra por ano"),
                                    "Barras agrupadas por mês, uma cor por ano; o último ano pode estar parcial. Zero publicado é uma observação (barra sem altura; "
                                    "no celular, um traço na base) e mês sem valor publicado fica sem barra (no celular, ×). Ano parcial: 2026 vai até o último "
                                    "mês disponível; nenhum mês é preenchido.",
                                    max(maximo * 1.25, 1), f"{FONTE_SINESP} | Abrangência: {abrangencia} | Unidade: {unidade}",
                                    unidade.split(" (")[0].capitalize(), xlabel="Mês")
    # set() tira os anos repetidos e sorted() os coloca em ordem: um grupo de barras por ano.
    anos_barras = sorted(set(serie["ano"].astype(int)))
    # Cada mês tem 0,8 de largura dividida entre os anos (uma barra por ano).
    largura = 0.8 / len(anos_barras)
    compacto = esta_compacto()
    zeros, ausentes, entradas = [], [], []  # entradas: itens da legenda, anos em ordem cronológica e depois as marcações
    for i, ano in enumerate(anos_barras):  # barras agrupadas: um grupo por mês, uma barra por ano (zero publicado: sem altura; sem valor: sem barra)
        # Meses do ano com valor publicado (mês sem valor fica sem barra).
        parte = serie.loc[serie["ano"].eq(ano) & serie["valor"].notna()].sort_values("mes")
        # Desloca as barras de cada ano para que o grupo fique centralizado no mês.
        deslocamento = (i - (len(anos_barras) - 1) / 2) * largura
        posicoes = [int(m) + deslocamento for m in parte["mes"]]
        rotulo = str(ano)
        if compacto and len(parte) < 12:  # ano parcial identificado na legenda (ex.: 2026 até setembro; PRF até agosto)
            rotulo = f"{ano} (parcial)"
        # eixo.bar desenha as barras de um ano, deslocadas para ficarem lado a lado com as dos outros anos.
        barras = eixo.bar(posicoes, [int(v) for v in parte["valor"]], width=largura * 0.92, color=cor_ano(ano), label=rotulo)
        entradas.append(barras)
        for barra in barras:
            barra.set_gid(f"mensal_{ano}")
        # Valores sobre as barras, só quando maiores que zero. Poucos anos: texto horizontal; muitos anos: texto em pé e menor, para caber.
        # No celular (modo compacto) só há rótulos quando um único ano está em tela (12 barras); com mais anos eles ficam nas tabelas.
        if not compacto or len(anos_barras) == 1:
            muitos_anos = len(anos_barras) > 3
            eixo.bar_label(barras, labels=[fmt_int(v) if int(v) > 0 else "" for v in parte["valor"]], padding=1.5,
                           fontsize=6.5 if muitos_anos else (7 if compacto else 8), rotation=90 if muitos_anos else 0)
        zeros += [(ano, int(m) + deslocamento) for m, v in zip(parte["mes"], parte["valor"]) if int(v) == 0]
        # Guarda as posições dos zeros e dos meses sem valor, para marcá-los no modo compacto.
        ausentes += [(ano, m + deslocamento) for m in range(1, 13) if m not in set(parte["mes"].astype(int))]
    if compacto:  # marcações discretas, sem barras artificiais: "—" = zero publicado (observação); "×" cinza = mês sem valor publicado
        for chave, pontos, marca, cor, legenda in (("zero", zeros, "_", None, "Zero publicado"), ("sem_valor", ausentes, "x", "#9A9A9A", "Sem valor (×)")):
            for k, (ano, x) in enumerate(pontos):
                # Marca no eixo os meses com zero publicado (traço) e os meses sem valor (×), para não confundir zero com ausência.
                linha, = eixo.plot([x], [0], linestyle="none", marker=marca, markersize=7 if marca == "_" else 4, markeredgewidth=2 if marca == "_" else 1,
                                   color=cor or cor_ano(ano), label=legenda if k == 0 else None)
                linha.set_gid(f"{chave}_{ano}")
                if k == 0:
                    entradas.append(linha)
    eixo.set_xlim(0.4, 12.6)
    _eixo_meses(eixo)
    _legenda(eixo, 7, handles=entradas)
    _aviso_sem_variacao(eixo, serie["valor"])
    return figura


def figura_ranking_sinesp(ranking: pd.DataFrame, ano: int, destaque: tuple[str, str] | None = None) -> Figure | None:
    """Barras horizontais das séries ordenadas pela soma do ano completo ano (uma única unidade; sem total entre séries).

    destaque = (indicador, abrangência) da série selecionada, que recebe cor de destaque.
    """
    if ranking.empty:
        return None
    # Todas as barras do ranking têm a mesma unidade (o cálculo não mistura vítimas com mandados).
    unidade = ranking["unidade"].iloc[0]
    # Segurança: o ranking nunca mistura vítimas com mandados.
    if ranking["unidade"].nunique() != 1:
        raise ValueError("Ranking com unidades diferentes: vítimas e mandados não podem ser comparados.")
    compacto = esta_compacto()
    abreviacao = {"Polícia Federal": "PF", "Polícia Rodoviária Federal": "PRF"}
    if compacto:
        rotulos = ["\n".join(textwrap.wrap(f"{NOME_CURTO.get(r.evento, r.evento)} ({abreviacao.get(r.abrangencia, r.abrangencia)})", 24)) for r in ranking.itertuples()]
    else:
        rotulos = ["\n".join(textwrap.wrap(f"{r.evento} ({r.abrangencia})", 52)) for r in ranking.itertuples()]
    valores = [int(v) for v in ranking["soma"]]
    if compacto:
        altura = 0.62 * len(valores) + 2.5
        # Figure cria a área da figura: figsize é largura × altura em polegadas; a altura cresce com o número de barras.
        figura = Figure(figsize=(4.4, altura), dpi=120)
        eixo = figura.add_axes([0.46, 0.95 / altura, 0.50, (altura - 0.95 - 1.0) / altura])
    else:
        figura = Figure(figsize=(10, 0.55 * len(valores) + 3.2), dpi=120)
        eixo = figura.add_axes([0.42, 0.18, 0.54, 0.62])
    posicoes = list(range(len(valores)))[::-1]
    cores = ["#0A3470" if destaque and (r.evento, r.abrangencia) == tuple(destaque) else COR_AZUL_CLARO for r in ranking.itertuples()]
    # barh desenha barras horizontais; a barra do indicador escolhido fica mais escura.
    barras = eixo.barh(posicoes, valores, color=cores, height=0.62)
    for barra in barras:
        barra.set_gid("ranking")
    # bar_label escreve o valor ao lado de cada barra (padding é a distância entre a barra e o texto).
    eixo.bar_label(barras, labels=[fmt_int(v) for v in valores], padding=4, fontsize=10)
    eixo.set_yticks(posicoes, rotulos, fontsize=10 if compacto else 9)
    eixo.set_xlim(0, max(valores) * 1.18 if max(valores) else 1)
    eixo.xaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
    eixo.xaxis.set_major_formatter(FuncFormatter(_milhar))
    eixo.grid(axis="x", color="#D9E5F2", linewidth=0.8)
    eixo.set_axisbelow(True)
    eixo.spines[["top", "right"]].set_visible(False)
    nota = f"{FONTE_SINESP} | Unidade: {unidade} | Ordenação dentro de uma única unidade; nenhum total entre indicadores." + (" Barra mais escura: indicador escolhido." if destaque else "")
    if compacto:
        eixo.set_xlabel(unidade.split(" (")[0].capitalize() + f" em {ano}", fontsize=11)
        eixo.tick_params(axis="x", labelsize=10)
        figura.text(0.04, 1 - 0.1 / altura, "\n".join(textwrap.wrap(f"Séries ordenadas pelo total de {ano} (ano completo)", 30)), ha="left", va="top", fontsize=13, fontweight="semibold")
    else:
        eixo.set_xlabel(unidade.split(" (")[0].capitalize() + f" em {ano} (soma dos 12 meses)", fontsize=11)
        figura.suptitle(f"Joinville/SC — séries ordenadas pelo total de {ano} (ano completo)", x=0.01, y=0.97, ha="left", fontsize=13, fontweight="bold")
        figura.text(0.01, 0.045, nota, fontsize=8.5, color=COR_CINZA_TEXTO)
    figura.sinesp_notas = {"interpretacao": "Soma dos 12 meses do ano completo. A barra mais escura é o indicador escolhido." if destaque else "Soma dos 12 meses do ano completo.", "rodape": nota}
    return figura


# ===================================================================================================================
# Etapa 20 — figuras de visão geral, evolução temporal, estatística descritiva e outliers.
# Cada figura desenha EXATAMENTE a tabela devolvida pela função homônima de calculos.py (os elementos recebem um nome, gid,
# que permite conferir o desenhado com a tabela). Elas usam a série selecionada (um indicador × uma abrangência × uma unidade).
# ===================================================================================================================
NOME_CURTO = {
    "Morte no trânsito ou em decorrência dele (exceto homicídio doloso)": "Mortalidade no trânsito",
    "Mortes a esclarecer (sem indício de crime)": "Mortes a esclarecer",
    "Roubo seguido de morte (latrocínio)": "Latrocínio",
    "Mandado de prisão cumprido": "Mandados de prisão cumpridos",
    "Lesão corporal seguida de morte": "Lesão corporal seguida de morte",
}


def _titulo(evento: str) -> str:
    """Título da figura: nome curto do indicador seguido de Joinville/SC."""
    return f"{NOME_CURTO.get(evento, evento)} em Joinville/SC"


def _dec1(valor) -> str:
    """Decimal pt-BR com uma casa e sinal de menos tipográfico (−2,5)."""
    return fmt_dec(valor, 1).replace("-", "−")


def _anos_em_texto(anos: list[int]) -> str:
    """[2020, 2023, 2024, 2025] → '2020, 2023–2025' (anos consecutivos viram intervalo)."""
    grupos, atual = [], [anos[0]]
    for ano in anos[1:]:
        if ano == atual[-1] + 1:
            atual.append(ano)
        else:
            grupos.append(atual)
            atual = [ano]
    grupos.append(atual)
    return ", ".join(str(g[0]) if len(g) == 1 else (f"{g[0]}, {g[1]}" if len(g) == 2 else f"{g[0]}–{g[-1]}") for g in grupos)


def _banner(eixo, texto: str, *, y: float = 0.93, va: str = "top") -> None:
    """Faixa de aviso metodológico. Desktop: dentro do gráfico. Compacto: texto quebrado em linhas curtas, ACIMA do eixo (o eixo encolhe
    para dar espaço), para não cobrir os pontos de uma figura estreita."""
    estilo = {"boxstyle": "round,pad=0.4", "facecolor": "#FFF4DC", "edgecolor": "#D97706"}
    if esta_compacto():
        linhas = textwrap.wrap(texto, 30)
        reserva = 0.03 * len(linhas) + 0.035  # fração da altura da figura
        posicao = eixo.get_position()
        eixo.set_position([posicao.x0, posicao.y0, posicao.width, posicao.height - reserva])
        eixo.text(0.5, 1.025, "\n".join(linhas), transform=eixo.transAxes, ha="center", va="bottom", fontsize=10.5, fontweight="semibold", color="#7A4B00", bbox=estilo, zorder=5)
        return
    eixo.text(0.5, y, texto, transform=eixo.transAxes, ha="center", va=va, fontsize=12, fontweight="semibold", color="#7A4B00", bbox=estilo, zorder=5)


def _aviso_sem_variacao(eixo, valores, *, acima_do_eixo: bool = False) -> None:
    """Se todos os valores desenhados são iguais, diz isso na figura (série sem variabilidade); não altera nenhum dado."""
    unicos = {float(v) for v in valores if pd.notna(v)}
    if len(unicos) == 1:
        valor = unicos.pop()
        texto = "Série sem variação: todos os meses têm zero publicado" if valor == 0 else f"Série sem variação: todos os valores são {fmt_int(valor)}"
        y, va = (1.035, "bottom") if acima_do_eixo else (0.93, "top")
        _banner(eixo, texto, y=y, va=va)


def _serie_figura(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> pd.DataFrame:
    """Linhas da série escolhida nos anos pedidos."""
    serie = calculos.serie_sinesp(sinesp, evento, abrangencia)
    # isin(anos) mantém só as linhas dos anos escolhidos.
    return serie.loc[serie["ano"].isin(anos)]


def _rodape(abrangencia: str, unidade: str) -> str:
    """Texto de rodapé da figura: fonte, classificação institucional e unidade."""
    return f"{FONTE_SINESP} | Abrangência: {abrangencia} | Unidade: {unidade}"


def _x_mensal(quadro: pd.DataFrame) -> list[float]:
    """Posição de cada mês no eixo contínuo: ano + (mês − 1)/12."""
    return [int(a) + (int(m) - 1) / 12 for a, m in zip(quadro["ano"], quadro["mes"])]


def _eixo_anos(eixo, quadro: pd.DataFrame) -> None:
    """Marca no eixo horizontal só os anos que existem na tabela."""
    anos = sorted({int(a) for a in quadro["ano"]})
    eixo.set_xticks(anos, [str(a) for a in anos])
    eixo.set_xlim(min(anos) - 0.2, max(anos) + 1.0)


def _valores_float(coluna) -> list[float]:
    """Converte uma coluna em lista de números decimais (ausente vira NaN, sem virar zero)."""
    # to_numpy converte para números do NumPy; na_value=nan deixa a ausência como espaço vazio no gráfico.
    return pd.Series(coluna).astype("Float64").to_numpy(dtype="float64", na_value=float("nan")).tolist()


def figura_mapa_calor_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> Figure | None:
    """Mapa de calor ano × mês dos valores publicados. Células cinza = mês sem valor publicado (nunca zero)."""
    serie = _serie_figura(sinesp, evento, abrangencia, anos)
    if serie.empty:
        return None
    tabela = calculos.quadro_ano_mes(serie)
    unidade = serie["unidade"].iloc[0]
    compacto = esta_compacto()
    grade = tabela.T if compacto else tabela  # compacto: meses nas linhas e anos nas colunas (nomes dos meses inteiros e legíveis)
    # Converte a tabela ano x mês em matriz de números; masked_invalid "esconde" os meses sem valor (ficam cinza, não viram zero).
    matriz = np.ma.masked_invalid(grade.astype("float64").to_numpy())
    maximo = max(float(matriz.max()), 1.0) if matriz.count() else 1.0
    figura, eixo = _preparar_sinesp(_titulo(evento), _subtitulo(unidade, f"por mês, de {int(tabela.index.min())} a {int(tabela.index.max())} (mapa de calor)"),
                                    "Cada célula é um mês; quanto mais escura, maior o valor. Cinza: mês sem valor publicado (não preenchido). O número na célula "
                                    "é o valor da tabela.",
                                    1, _rodape(abrangencia, unidade), "Mês" if compacto else "Ano", xlabel="Ano" if compacto else "Mês")
    # Escala de azuis: quanto maior o valor, mais escura a célula.
    paleta = colormaps["Blues"].with_extremes(bad="#E6E6E6")  # mês sem valor: cinza
    # imshow desenha a matriz como uma grade de células coloridas (o mapa de calor).
    imagem = eixo.imshow(matriz, cmap=paleta, vmin=0, vmax=maximo, aspect="auto")
    imagem.set_gid("mapa_calor")
    # Dois laços (linhas e colunas) escrevem o número dentro de cada célula; texto branco nas células escuras.
    for i in range(matriz.shape[0]):
        for j in range(matriz.shape[1]):
            valor = matriz[i, j]
            if valor is not np.ma.masked:
                eixo.text(j, i, fmt_int(valor), ha="center", va="center", fontsize=9 if compacto else 10, color="white" if valor > 0.55 * maximo else "#222222")
    nomes_anos = [str(int(a)) for a in tabela.index]
    if compacto:
        eixo.set_xticks(range(len(nomes_anos)), nomes_anos, fontsize=9)
        eixo.set_yticks(range(12), ABREV_MESES)
    else:
        eixo.set_xticks(range(12), ABREV_MESES)
        eixo.set_yticks(range(len(nomes_anos)), nomes_anos)
    eixo.set_xlim(-0.5, matriz.shape[1] - 0.5)
    eixo.set_ylim(matriz.shape[0] - 0.5, -0.5)  # primeira linha (ano mais antigo ou janeiro) no topo, como numa tabela
    eixo.grid(False)
    eixo.spines[["left", "bottom"]].set_visible(False)
    eixo.tick_params(length=0)
    _aviso_sem_variacao(eixo, tabela.to_numpy().ravel(), acima_do_eixo=True)  # não cobre os números das células
    return figura


def figura_media_movel_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> Figure | None:
    """Valores mensais e média móvel de 12 meses (só onde os 12 meses têm valor). None se não houver nenhuma janela completa."""
    serie = _serie_figura(sinesp, evento, abrangencia, anos)
    if serie.empty:
        return None
    tabela = calculos.media_movel(serie)
    # Se nenhum mês tem média móvel (menos de 12 meses seguidos com valor), não há gráfico.
    if tabela["media_movel"].notna().sum() == 0:
        return None
    unidade = serie["unidade"].iloc[0]
    maximo = float(np.nanmax(_valores_float(tabela["valor"])))
    figura, eixo = _preparar_sinesp(_titulo(evento), _subtitulo(unidade, "por mês e média móvel de 12 meses"),
                                    "A média móvel é a média dos 12 meses até o mês indicado e só existe quando os 12 meses têm valor. Suaviza oscilações; não "
                                    "indica causa.",
                                    max(maximo * 1.25, 1), _rodape(abrangencia, unidade), unidade.split(" (")[0].capitalize(), xlabel="Ano (cada marca = janeiro)")
    x = _x_mensal(tabela)
    # Duas linhas: a fina mostra cada mês; a grossa, a média móvel de 12 meses calculada em calculos.media_movel.
    mensal, = eixo.plot(x, _valores_float(tabela["valor"]), color="#8FA9C4", linewidth=1.2, marker="o", markersize=3.5, label="Valor mensal")
    movel, = eixo.plot(x, _valores_float(tabela["media_movel"]), color=COR_AZUL, linewidth=2.8, label="Média móvel de 12 meses")
    mensal.set_gid("serie_mensal")
    movel.set_gid("media_movel")
    _eixo_anos(eixo, tabela)
    _legenda(eixo, 2)
    _aviso_sem_variacao(eixo, tabela["valor"])
    return figura


def _separar_rotulos(posicoes: list[float], separacao: float) -> list[float]:
    """Afasta verticalmente rótulos que se sobreporiam, preservando a ordem. Muda só a posição do TEXTO, nunca os dados."""
    ordem = sorted(range(len(posicoes)), key=lambda i: posicoes[i])
    ajustadas = list(posicoes)
    for anterior, atual in zip(ordem, ordem[1:]):
        if ajustadas[atual] - ajustadas[anterior] < separacao:
            ajustadas[atual] = ajustadas[anterior] + separacao
    return ajustadas


def figura_acumulado_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> Figure | None:
    """Soma acumulada de janeiro até cada mês, uma linha por ano (cor fixa por ano). Anos parciais terminam no último mês publicado.

    Os valores finais ficam em rótulos à direita, ligados à ponta de cada linha, sem sobreposição (rótulos de anos que terminam no mesmo
    valor são separados na vertical; a posição dos pontos não muda). O ano parcial é identificado na legenda e no rótulo.
    """
    serie = _serie_figura(sinesp, evento, abrangencia, anos)
    if serie.empty:
        return None
    tabela = calculos.acumulado_no_ano(serie)
    unidade = serie["unidade"].iloc[0]
    maximo = float(np.nanmax(_valores_float(tabela["acumulado"])))
    limite_y = max(maximo * 1.25, 1)
    figura, eixo = _preparar_sinesp(_titulo(evento), _subtitulo(unidade, "acumuladas de janeiro até cada mês, em cada ano"),
                                    "Cada linha acumula os meses de um ano; o valor do último mês disponível de cada ano está nos rótulos (ou na legenda) e na "
                                    "tabela de apoio. "
                                    "Ano parcial termina antes de dezembro: compare os anos no mesmo mês, nunca o total de um ano parcial com o de um ano completo.",
                                    limite_y, _rodape(abrangencia, unidade), unidade.split(" (")[0].capitalize(), xlabel="Mês")
    finais = []
    # Uma linha por ano: groupby("ano") separa os meses de cada ano.
    for ano, parte in tabela.groupby("ano", sort=True):
        valores = _valores_float(parte["acumulado"])
        observados = [(int(m), v) for m, v in zip(parte["mes"], valores) if v == v]
        mes_final, valor_final = observados[-1]
        parcial = mes_final < 12
        legenda = f"{int(ano)} (parcial, até {ABREV_MESES[mes_final - 1].lower()})" if parcial else str(int(ano))
        rotulo_legenda = f"{legenda}: {fmt_int(valor_final)}" if esta_compacto() else legenda  # compacto: o valor final fica na legenda
        # eixo.plot desenha a linha do acumulado do ano (x = mês, y = soma acumulada) com marcadores redondos.
        linha, = eixo.plot(parte["mes"].astype(int).tolist(), valores, color=cor_ano(int(ano)), linewidth=2, marker="o", markersize=4, label=rotulo_legenda,
                           linestyle="-" if int(ano) % 2 == 0 else "--")  # tons de azul + traço alternado ajudam a separar anos vizinhos
        linha.set_gid(f"acumulado_{int(ano)}")
        finais.append((int(ano), mes_final, valor_final, parcial, cor_ano(int(ano))))
    # Anos completos que terminam no mesmo valor dividem um único rótulo (evita pilhas de textos); anos parciais têm rótulo próprio.
    rotulos = []
    completos = {}
    for ano, mes_final, valor_final, parcial, cor in finais:
        if parcial:
            rotulos.append((f"{ano} (jan–{ABREV_MESES[mes_final - 1].lower()}): {fmt_int(valor_final)}", mes_final, valor_final, cor, True))
        else:
            completos.setdefault(valor_final, []).append((ano, cor))
    for valor_final, anos_iguais in completos.items():
        rotulos.append((f"{_anos_em_texto([a for a, _ in anos_iguais])}: {fmt_int(valor_final)}", 12, valor_final, anos_iguais[0][1], False))
    if esta_compacto():
        rotulos = []  # compacto: sem rótulos soltos no gráfico; valores finais na legenda e na tabela de apoio
    posicoes = _separar_rotulos([r[2] for r in rotulos], 0.075 * limite_y)
    for (texto, mes_final, valor_final, cor, parcial), y in zip(rotulos, posicoes):
        # Escreve o total final de cada ano à direita do gráfico, na altura do último ponto da linha.
        rotulo = eixo.annotate(texto, xy=(mes_final, valor_final), xytext=(12.45, y), textcoords="data", va="center", ha="left", fontsize=10, color="#222222",
                               arrowprops={"arrowstyle": "-", "color": cor, "linewidth": 0.9, "shrinkA": 0, "shrinkB": 4, "linestyle": ":" if parcial else "-"})
        rotulo.set_gid("rotulo_final")
    _eixo_meses(eixo)
    eixo.set_xlim(0.6, 12.4 if esta_compacto() else 16.6)
    eixo.spines["bottom"].set_bounds(0.6, 12.4)
    _legenda(eixo, 7, columnspacing=1.2, handlelength=1.6)
    _aviso_sem_variacao(eixo, tabela["acumulado"])
    return figura


def figura_boxplot_anual_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> Figure | None:
    """Boxplot dos valores MENSAIS de cada ano (resumo de cinco números e critério de Tukey, calculados em quartis_por_ano).

    Anos com IQR = 0 têm caixa degenerada: não mostram pontos atípicos e são rotulados. n = meses com valor do ano.
    """
    serie = _serie_figura(sinesp, evento, abrangencia, anos)
    if serie.empty:
        return None
    tabela = calculos.quartis_por_ano(serie)
    if tabela.empty:
        return None
    unidade = serie["unidade"].iloc[0]
    maximo = float(max(tabela["maximo"].max(), 1))
    figura, eixo = _preparar_sinesp(_titulo(evento), _subtitulo(unidade, "por mês, resumidas em um gráfico de caixa para cada ano"),
                                    "Caixa: de Q1 a Q3 (1º e 3º quartis); traço: mediana; hastes: menor e maior valor dentro dos limites de referência (Q1 − "
                                    "1,5 × IQR e Q3 + 1,5 × IQR); "
                                    "pontos: meses fora desses limites (incomuns, não anomalias comprovadas). Em anos com IQR = 0 não há pontos destacados. "
                                    "n = meses com valor; o ano parcial tem menos meses.",
                                    max(maximo * 1.25, 1), _rodape(abrangencia, unidade), unidade.split(" (")[0].capitalize())
    estatisticas = [{"label": f"{int(r.ano)}\nn={int(r.n)}", "med": r.mediana, "q1": r.q1, "q3": r.q3, "whislo": r.bigode_inferior, "whishi": r.bigode_superior,
                     "fliers": [] if r.iqr_zero else list(r.valores_fora)} for r in tabela.itertuples()]
    # bxp desenha um gráfico de caixa por ano a partir dos quartis já calculados (a caixa vai de Q1 a Q3; o traço é a mediana).
    elementos = eixo.bxp(estatisticas, widths=0.55, showfliers=True, patch_artist=False)
    for i, r in enumerate(tabela.itertuples()):
        cor = cor_ano(int(r.ano))
        for chave in ("boxes", "medians"):
            elementos[chave][i].set_color(cor)
        elementos["boxes"][i].set_linewidth(2)
        elementos["medians"][i].set_linewidth(2.6)
        for linha in elementos["whiskers"][2 * i:2 * i + 2] + elementos["caps"][2 * i:2 * i + 2]:
            linha.set_color(cor)
        elementos["fliers"][i].set(marker="o", markerfacecolor="none", markeredgecolor=cor, markersize=7)
        elementos["boxes"][i].set_gid("caixa")
        elementos["medians"][i].set_gid("mediana")
        elementos["caps"][2 * i].set_gid("bigode_inferior")
        elementos["caps"][2 * i + 1].set_gid("bigode_superior")
        elementos["fliers"][i].set_gid("atipicos")
        if r.iqr_zero:
            # Avisa no gráfico os anos em que a caixa vira um traço (IQR = 0).
            eixo.annotate("IQR = 0", (i + 1, r.q3), textcoords="offset points", xytext=(0, 6 if esta_compacto() else 10), ha="center", va="bottom",
                          rotation=90 if esta_compacto() else 0, fontsize=10, color="#555555")  # compacto: vertical, para os rótulos não se tocarem
    eixo.set_xlabel("Ano", fontsize=11)
    if bool(tabela["iqr_zero"].all()):
        _banner(eixo, "Valores muito concentrados: IQR = 0 em todos os anos (a caixa vira um traço)")
    return figura


def figura_distribuicao_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> Figure | None:
    """Frequência dos valores mensais em faixas de contagem (barras categóricas; regra em calculos.distribuicao_frequencias).

    O zero publicado é uma faixa própria (hachurada) e o valor extremo fica na última faixa. A soma das barras é o número de meses com valor.
    """
    serie = _serie_figura(sinesp, evento, abrangencia, anos)
    if serie.empty:
        return None
    tabela = calculos.distribuicao_frequencias(serie)
    if tabela.empty:
        return None
    unidade = serie["unidade"].iloc[0]
    # Quantos meses têm zero publicado (eq(0) marca e sum() conta).
    zeros = int(serie["valor"].eq(0).sum())
    total = int(serie["valor"].count())
    largura = int(tabela.attrs.get("largura", 1))
    regra = ("Cada valor inteiro forma uma faixa" if largura == 1 else f"Valores positivos agrupados em intervalos de {largura}; a última faixa pode ser menor")
    figura, eixo = _preparar_sinesp(_titulo(evento), _subtitulo(unidade, "por mês: quantos meses tiveram valores em cada faixa"),
                                    f"{regra}; barras categóricas com a contagem de meses (n = {total}). Barra hachurada: zero informado ({zeros} {'mês' if zeros == 1 else 'meses'}, "
                                    f"{zeros / total * 100:.0f}%), "
                                    "faixa própria. O maior valor observado está na última faixa; faixas vazias são mantidas.",
                                    max(float(tabela["n_meses"].max()) * 1.25, 1), _rodape(abrangencia, unidade), "Número de meses",
                                    xlabel=f"Faixa do valor mensal ({unidade.split(' (')[0]})")
    # Distribuição: uma barra por faixa de valores; a altura é o número de meses na faixa.
    barras = eixo.bar(range(len(tabela)), [int(n) for n in tabela["n_meses"]], color=COR_AZUL, width=0.8)
    for barra, inicio in zip(barras, tabela["inicio"]):
        barra.set_gid("frequencia")
        if int(inicio) == 0:
            barra.set_hatch("//")
            barra.set_edgecolor("white")
    # Escreve acima de cada barra quantos meses caíram naquela faixa.
    eixo.bar_label(barras, labels=[fmt_int(n) for n in tabela["n_meses"]], padding=3, fontsize=10)
    eixo.set_xticks(range(len(tabela)), tabela["rotulo"].tolist(), rotation=0 if len(tabela) <= (5 if esta_compacto() else 9) else 45, fontsize=10)
    return figura


def figura_sazonalidade_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> Figure | None:
    """Perfil por mês-calendário em BARRAS: mediana de cada mês nos anos completos (traço fino = mínimo a máximo). None com menos de 2 anos.

    Usa somente anos completos (12 meses com valor); anos parciais, como 2026, ficam de fora, e nenhum mês é inventado. Os anos usados
    aparecem no subtítulo.
    """
    serie = _serie_figura(sinesp, evento, abrangencia, anos)
    if serie.empty:
        return None
    perfil = calculos.perfil_sazonal(serie)
    usados = perfil.attrs.get("anos_usados", [])
    if len(usados) < 2:
        return None
    unidade = serie["unidade"].iloc[0]
    aviso = ("Menos de 3 anos completos: quadro apenas ilustrativo." if len(usados) < calculos.ANOS_MINIMOS_SAZONALIDADE
             else "Com poucos anos completos, o quadro descreve esses anos e não prova um padrão sazonal.")
    anos_texto = _anos_em_texto(usados)
    figura, eixo = _preparar_sinesp(_titulo(evento), _subtitulo(unidade, f"· mediana de cada mês nos anos completos {anos_texto} (n = {len(usados)})"),
                                    f"Barras: mediana do mês nos anos completos usados ({anos_texto}); traço fino: mínimo a máximo desses anos. Anos parciais "
                                    f"(como 2026) ficam de fora. {aviso}",
                                    max(float(perfil["maximo"].max()) * 1.25, 1), _rodape(abrangencia, unidade), unidade.split(" (")[0].capitalize(), xlabel="Mês")
    # Listas com os meses (1 a 12) e a mediana de cada mês, usadas para desenhar as barras.
    meses = perfil["mes"].astype(int).tolist()
    medianas = perfil["mediana"].astype("float64").tolist()
    # Barras com a mediana de cada mês do ano e, por cima, traços verticais (vlines) do menor ao maior valor.
    barras = eixo.bar(meses, medianas, width=0.7, color=COR_AZUL, label="Mediana do mês" if esta_compacto() else f"Mediana do mês ({anos_texto})")
    for barra in barras:
        barra.set_gid("mediana_mensal")
    # vlines desenha uma linha vertical do mínimo ao máximo de cada mês (quanto o mês variou entre os anos).
    faixa = eixo.vlines(meses, perfil["minimo"].astype("float64").tolist(), perfil["maximo"].astype("float64").tolist(), color="#20354F", linewidth=1.2, label="Mínimo a máximo")
    faixa.set_gid("faixa_min_max")
    if not esta_compacto():
        # Escreve a mediana dentro de cada barra (inteiro sem casas decimais; senão, com uma casa).
        eixo.bar_label(barras, labels=[fmt_int(m) if float(m).is_integer() else fmt_dec(m, 1) for m in medianas], label_type="center", color="white", fontweight="bold", fontsize=9,
                      bbox={"boxstyle": "square,pad=0.15", "facecolor": COR_AZUL, "edgecolor": "none"})  # dentro da barra: o traço mínimo–máximo não cobre o número
    _eixo_meses(eixo)
    _legenda(eixo, 2)
    _aviso_sem_variacao(eixo, perfil["maximo"].tolist() + perfil["minimo"].tolist())
    return figura


def figura_outliers_iqr_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str, anos: list[int]) -> Figure | None:
    """Série mensal com mediana, Q1–Q3 e limites de referência (Tukey), calculados SEMPRE sobre os meses da série e do período selecionados.

    Os pontos só são destacados quando o método é informativo; senão a figura diz por quê. O limite inferior só é desenhado se for maior
    que zero (uma contagem não pode ficar abaixo de zero); a legenda informa seu valor mesmo assim.
    """
    serie = _serie_figura(sinesp, evento, abrangencia, anos)
    if serie.empty:
        return None
    # Ordem cronológica; o diagnóstico IQR dá os limites e diz se o critério se aplica a esta série.
    serie = serie.sort_values(["ano", "mes"])
    d = calculos.diagnostico_outliers_iqr(serie)
    unidade = serie["unidade"].iloc[0]
    maximo = float(serie["valor"].max()) if serie["valor"].notna().any() else 1.0
    topo = max(maximo, d["limite_superior"] if d["interpretavel"] else 0)
    # Primeiro e último mês da série (iloc[0] e iloc[-1]), usados para descrever o período.
    primeiro, ultimo = serie.iloc[0], serie.iloc[-1]
    referencia = (f"{d['n']} meses, {ABREV_MESES[int(primeiro['mes']) - 1].lower()}/{int(primeiro['ano'])} a "
                  f"{ABREV_MESES[int(ultimo['mes']) - 1].lower()}/{int(ultimo['ano'])}")
    figura, eixo = _preparar_sinesp(_titulo(evento), _subtitulo(unidade, "por mês, com os limites de referência (IQR)"),
                                    f"Conjunto de referência: {referencia}. " + (
                                        "Meses fora dos limites são incomuns em relação aos demais; não são prova de erro, de anomalia ou de mudança real."
                                        if d["interpretavel"] else
                                        f"Os limites de referência não ajudam a interpretar esta série ({d['rotulo']}): nenhum mês é apontado como incomum."), max(topo * 1.2, 1), _rodape(abrangencia, unidade), unidade.split(" (")[0].capitalize(), xlabel="Ano (cada marca = janeiro)")
    x = _x_mensal(serie)
    # Série mensal em cinza; axhline traça linhas horizontais na mediana e nos limites de referência.
    pontos, = eixo.plot(x, _valores_float(serie["valor"]), color="#7A7A7A", linewidth=1, marker="o", markersize=4, label="Valor mensal")
    pontos.set_gid("pontos")
    if d["interpretavel"]:
        faixa = eixo.axhspan(d["q1"], d["q3"], color=COR_AZUL, alpha=0.12, label="Q1 a Q3" if esta_compacto() else f"Q1 a Q3 ({_dec1(d['q1'])} a {_dec1(d['q3'])}; IQR = {_dec1(d['iqr'])})")
        faixa.set_gid("faixa_q1_q3")
        mediana = eixo.axhline(d["mediana"], color=COR_AZUL, linestyle=":", linewidth=1.6, label="Mediana" if esta_compacto() else f"Mediana ({_dec1(d['mediana'])})")
        mediana.set_gid("mediana")
        superior = eixo.axhline(d["limite_superior"], color="#C0392B", linestyle="--", linewidth=1.6, label="Limite superior" if esta_compacto() else f"Limite superior ({_dec1(d['limite_superior'])})")
        superior.set_gid("limite_superior")
        if d["limite_inferior"] > 0:
            inferior = eixo.axhline(d["limite_inferior"], color="#C0392B", linestyle="--", linewidth=1.6, label="Limite inferior" if esta_compacto() else f"Limite inferior ({_dec1(d['limite_inferior'])})")
            inferior.set_gid("limite_inferior")
        else:
            # Linha sem pontos, só para a legenda explicar que o limite inferior não se aplica.
            eixo.plot([], [], linestyle="none", label="Limite inferior (n/a)" if esta_compacto() else f"Limite inferior ({_dec1(d['limite_inferior'])}): não se aplica")
        fora = d["fora"]
        if len(fora):
            # Círculos vazios destacam os meses fora dos limites de referência.
            atipicos, = eixo.plot(_x_mensal(fora), _valores_float(fora["valor"]), linestyle="none", marker="o", markersize=10, markerfacecolor="none",
                                  markeredgecolor="#C0392B", markeredgewidth=2, label=f"Fora dos limites ({len(fora)})")
            atipicos.set_gid("pontos_atipicos")
            nivel, x_anterior = 0, None
            for r in fora.itertuples():  # rótulos de pontos próximos sobem em degraus para não se sobreporem
                x_ponto = int(r.ano) + (int(r.mes) - 1) / 12
                nivel = nivel + 1 if x_anterior is not None and x_ponto - x_anterior < 0.8 else 0
                x_anterior = x_ponto
                a_direita = esta_compacto() and x_ponto > min(x) + 0.65 * (max(x) - min(x))  # compacto: rótulo de ponto perto da borda direita vai para a esquerda
                # Rótulo de cada mês destacado (ex.: jan/2023: 19).
                rotulo = eixo.annotate(f"{ABREV_MESES[int(r.mes) - 1]}/{int(r.ano)}: {fmt_int(r.valor)}", (x_ponto, float(r.valor)),
                                       textcoords="offset points", xytext=(-8 if a_direita else 8, 8 + 16 * nivel), ha="right" if a_direita else "left", fontsize=10, color="#C0392B")
                rotulo.set_gid("rotulo_atipico")
    else:
        _banner(eixo, f"Limites de referência (IQR) pouco úteis nesta série: {d['rotulo']}")
    _eixo_anos(eixo, serie)
    _legenda(eixo, 3)
    return figura


# ------------------------------------------------------------------------------------------ SSP/SC (violência doméstica)
COR_SSP_2023, COR_SSP_2024 = "#8FBBE3", "#074EA2"   # dois tons de azul para os dois anos


def figura_violencia_domestica_ssp(vd: pd.DataFrame, categoria: str | None = None) -> Figure | None:
    """Fatos comunicados de violência doméstica (SSP/SC, Joinville), 2023 × 2024.

    Sem categoria: barras horizontais, uma por categoria e ano (cada categoria só se compara com ela mesma; nada é somado).
    Com categoria: barras mensais dessa categoria, janeiro a dezembro, um tom de azul por ano.
    A unidade "Fato Comunicado" está em validação: o gráfico diz isso e não sugere comparação com o Sinesp.
    """
    if vd is None or vd.empty:
        return None
    compacto = esta_compacto()
    # Figura da SSP/SC: tamanho menor no modo compacto (celular).
    figura = Figure(figsize=(4.4, 6.8) if compacto else (10, 6.2), dpi=120)
    eixo = figura.add_subplot(111)
    cores = {2023: COR_SSP_2023, 2024: COR_SSP_2024}
    nome = f"— {categoria}" if categoria else "por categoria"
    largura_titulo = 30 if compacto else 90
    titulo = "\n".join(textwrap.wrap(f"Violência doméstica em Joinville/SC — fatos comunicados {nome}", largura_titulo))
    aviso = "\n".join(textwrap.wrap("Unidade: Fato Comunicado — definição em validação (não equivale a vítimas, pessoas ou ocorrências únicas).", 44 if compacto else 120))
    rodape = "Fonte: SSP/SC — Segurança em Números, relatórios de violência doméstica (2023–2024). Análise exploratória; não integra os indicadores Sinesp."
    rodape = "\n".join(textwrap.wrap(rodape, 48 if compacto else 130))
    # Alturas dos textos em fração da figura (tamanho da fonte × 1,5 de entrelinha ÷ 72 pontos por polegada ÷ altura em polegadas).
    altura = figura.get_figheight()
    fonte_titulo, fonte_aviso = (12, 9) if compacto else (14, 10)
    altura_titulo = (titulo.count("\n") + 1) * fonte_titulo * 1.5 / 72 / altura
    altura_aviso = (aviso.count("\n") + 1) * fonte_aviso * 1.5 / 72 / altura
    figura.text(0.03, 0.985, titulo, ha="left", va="top", fontsize=fonte_titulo, fontweight="semibold", color="#103C6D")
    figura.text(0.03, 0.985 - altura_titulo - 0.01, aviso, ha="left", va="top", fontsize=fonte_aviso, color="#7A4B00")
    figura.text(0.03, 0.015, rodape, ha="left", va="bottom", fontsize=8 if compacto else 9, color="#607A94")
    topo = 0.985 - altura_titulo - altura_aviso - 0.07   # o gráfico começa logo abaixo dos textos
    if categoria is None:
        # SSP/SC, todas as categorias: soma dos 12 meses por categoria e ano (unstack põe os anos em colunas), ordenada pelo total de 2024.
        totais = vd.groupby(["categoria", "ano"])["valor"].sum().unstack("ano").sort_values(2024)
        posicoes = list(range(len(totais)))
        for deslocamento, ano in ((-0.2, 2023), (0.2, 2024)):
            # Barras horizontais: uma para 2023 (azul-claro) e outra para 2024 (azul-escuro) em cada categoria.
            barras = eixo.barh([p + deslocamento for p in posicoes], [int(v) for v in totais[ano]], height=0.38, color=cores[ano], label=str(ano))
            eixo.bar_label(barras, labels=[fmt_int(v) if v > 0 else "" for v in totais[ano]], padding=3, fontsize=8 if compacto else 9, color="#103C6D")
        eixo.set_yticks(posicoes, ["\n".join(textwrap.wrap(c, 22 if compacto else 40)) for c in totais.index], fontsize=8 if compacto else 10)
        eixo.set_xlabel("Fatos comunicados no ano" if compacto else "Fatos comunicados no ano (soma dos 12 meses publicados)", fontsize=9 if compacto else 10)
        eixo.set_xlim(0, float(totais.to_numpy().max()) * 1.18)
        eixo.xaxis.set_major_formatter(FuncFormatter(_milhar))
        eixo.grid(axis="x", color="#D9E5F2", linewidth=0.8)
        # subplots_adjust define as margens (frações da figura) para os nomes das categorias caberem à esquerda.
        figura.subplots_adjust(left=0.36 if compacto else 0.30, right=0.95, bottom=0.2 if compacto else 0.17, top=topo)
    else:
        # Categoria escolhida no filtro: só as linhas dela; depois, uma linha por ano (2023 e 2024), mês a mês.
        parte = vd.loc[vd["categoria"].eq(categoria)]
        # SSP/SC, uma categoria: tabela mês x ano para desenhar as duas linhas (2023 e 2024).
        mensal = parte.pivot(index="mes", columns="ano", values="valor").reindex(range(1, 13))
        for ano in (2023, 2024):
            valores = [int(v) for v in mensal[ano]]
            # Uma linha por ano: x = mês, y = fatos comunicados naquele mês.
            linha, = eixo.plot(list(mensal.index), valores, color=cores[ano], linewidth=2.2, marker="o", markersize=6 if compacto else 7, label=str(ano))
            linha.set_gid(f"linha_ssp_{ano}")
            if not compacto:
                outro = 2024 if ano == 2023 else 2023
                for mes, valor in zip(mensal.index, valores):
                    # em cada mês, o MAIOR valor leva o rótulo acima do ponto e o menor, abaixo: assim os dois nunca se sobrepõem onde as linhas se cruzam
                    # O rótulo do maior valor do mês vai acima do ponto e o do menor vai abaixo, para os números não se sobreporem.
                    acima = valor > int(mensal.loc[mes, outro]) or (valor == int(mensal.loc[mes, outro]) and ano == 2024)
                    eixo.annotate(fmt_int(valor), (mes, valor), textcoords="offset points", xytext=(0, 8 if acima else -9), ha="center", va="bottom" if acima else "top",
                                  fontsize=8, color="#103C6D")
        eixo.set_xticks(range(1, 13), ABREV_MESES, fontsize=8 if compacto else 10)
        eixo.set_ylabel("Fatos comunicados no mês", fontsize=9 if compacto else 10)
        eixo.set_xlim(0.5, 12.5)
        eixo.set_ylim(0, max(float(mensal.to_numpy().max()) * 1.3, 1))
        eixo.yaxis.set_major_locator(MaxNLocator(nbins=6, integer=True))
        eixo.grid(axis="y", color="#D9E5F2", linewidth=0.8)
        figura.subplots_adjust(left=0.14 if compacto else 0.08, right=0.97, bottom=0.2 if compacto else 0.17, top=topo)
    eixo.set_axisbelow(True)
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.legend(loc="lower right" if categoria is None else "upper right", ncol=1 if categoria is None else 2, frameon=False, fontsize=9 if compacto else 10, title="Ano", title_fontsize=9 if compacto else 10)
    figura.sinesp_ajustada = True   # o layout já é fixo: ui.mostrar_figura não precisa reajustá-lo
    figura.sinesp_compacta = compacto
    figura.sinesp_notas = {"interpretacao": "Cada categoria é comparada apenas consigo mesma; categorias não são somadas e o total não é vítimas.", "rodape": rodape.replace("\n", " ")}
    return figura
