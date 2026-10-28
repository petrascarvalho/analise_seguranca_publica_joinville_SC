"""Auxiliares de interface do painel (Streamlit): identidade azul e branca (CSS), cabeçalho com a bandeira, cards de mesma altura,
cache de dados, erros explícitos e avisos."""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard import dados_publicos as dp
from dashboard import graficos
from dashboard.formatacao import NOMES_MESES


# Cores da identidade visual (PROPOSTA inspirada na bandeira de Joinville; não são códigos oficiais do município).
AZUL_BANDEIRA = "#074EA2"   # azul do arquivo SVG da bandeira usado no projeto
FUNDO = "#EAF4FC"           # fundo da página
CARTAO = "#FFFFFF"          # cards
BORDA = "#BFD6EB"
TITULO = "#103C6D"
TEXTO_SECUNDARIO = "#607A94"
TEXTO_LEGENDA = "#4A6381"       # legendas e textos pequenos: contraste suficiente sobre o fundo azul-claro
DESTAQUE = "#DCECF9"

# CSS da página única: fundo azul-claro, cards brancos e a grade dos cards (CSS Grid).
# .grade-cartoes é a linha de cards; cada .cartao tem 5 linhas (título, detalhe, valor, variação, base).
# Com "subgrid", os cards da mesma linha dividem as mesmas alturas: títulos, valores e variações ficam alinhados.
CSS = f"""<style>
.stApp {{ background: {FUNDO}; }}
.block-container {{ max-width: 1200px; padding-top: 4.5rem; }}   /* deixa espaço para a barra superior do Streamlit */
h1, h2, h3, h4 {{ color: {TITULO} !important; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] * {{ color: {TEXTO_LEGENDA} !important; opacity: 1 !important; }}
[data-testid="stImage"] img {{ border: 1px solid {BORDA}; border-radius: 12px; background: {CARTAO}; }}
/* contêineres com borda e expansores viram cards brancos */
[data-testid="stVerticalBlockBorderWrapper"], [data-testid="stExpander"] {{ background: {CARTAO}; border-color: {BORDA} !important; }}
.st-key-cabecalho {{ background: {CARTAO}; border: 1px solid {BORDA}; border-bottom: 4px solid {AZUL_BANDEIRA}; border-radius: 12px; padding: 0.9rem 1.2rem; }}
.st-key-cabecalho h1 {{ padding: 0; }}
.grade-cartoes {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 0 1rem; margin: 0.25rem 0 0; }}
.cartao {{ background: {CARTAO}; border: 1px solid {BORDA}; border-radius: 12px; padding: 0.9rem 1.1rem; margin-bottom: 0.9rem;
          display: flex; flex-direction: column; gap: 0.3rem; box-shadow: 0 1px 2px rgba(16, 60, 109, 0.08); box-sizing: border-box; }}
@supports (grid-template-rows: subgrid) {{
  .cartao {{ display: grid; grid-row: span 5; grid-template-rows: subgrid; row-gap: 0.3rem; }}
}}
.cartao-titulo {{ font-weight: 700; color: {TITULO}; line-height: 1.3; overflow-wrap: anywhere; min-height: 2.6em; }}
.cartao-detalhe {{ color: {TEXTO_LEGENDA}; font-size: 0.85rem; line-height: 1.3; overflow-wrap: anywhere; min-height: 2.6em; }}
.cartao-valor {{ font-size: 2.1rem; font-weight: 700; color: {AZUL_BANDEIRA}; line-height: 1.15; overflow-wrap: anywhere; }}
.cartao-variacao {{ font-size: 0.9rem; font-weight: 600; color: {TITULO}; line-height: 1.3; overflow-wrap: anywhere; min-height: 1.3em; }}
.cartao-base {{ color: {TEXTO_LEGENDA}; font-size: 0.8rem; line-height: 1.3; overflow-wrap: anywhere; min-height: 2.6em; }}
</style>"""


def aplicar_estilo() -> None:
    """Injeta o CSS da identidade azul e branca (uma vez por execução da página)."""
    st.html(CSS)


def cabecalho(titulo: str, descricao: str) -> None:
    """Cabeçalho: bandeira de Joinville (arquivo SVG local, sem rede e sem alterar a arte) ao lado do título."""
    with st.container(key="cabecalho"):
        with st.container(horizontal=True, vertical_alignment="center", gap="medium"):
            st.image(str(Path(__file__).parent / "assets" / "bandeira_joinville.svg"),
                     width=84, alt="Bandeira de Joinville: campo azul, losango branco e brasão municipal")
            with st.container():
                st.title(titulo)
                st.caption(descricao)


def secao(titulo: str, ancora: str, descricao: str | None = None) -> None:
    """Título de uma seção da página única (com âncora para o índice do topo) e, opcionalmente, uma linha de descrição."""
    st.header(titulo, anchor=ancora)
    if descricao:
        st.caption(descricao)


def cartoes_html(cartoes: list[dict]) -> None:
    """Uma linha de cards brancos de mesma altura (CSS Grid). Cada card é um dicionário com:
    titulo, valor, e opcionalmente detalhe, variacao (texto), diferenca (número que define a seta), base e ajuda (dica ao passar o mouse).
    A seta segue o sinal da diferença e não tem cor de "bom" ou "ruim": alta não é tratada como melhor nem pior.
    """
    partes = []
    for c in cartoes:
        seta = {"up": "▲ ", "down": "▼ ", "off": ""}[direcao_da_seta(c.get("diferenca"))] if c.get("variacao") else ""
        campos = [("titulo", c["titulo"]), ("detalhe", c.get("detalhe", "")), ("valor", c["valor"]),
                  ("variacao", seta + c["variacao"] if c.get("variacao") else ""), ("base", c.get("base", ""))]
        miolo = "".join(f'<div class="cartao-{nome}">{escape(str(texto))}</div>' for nome, texto in campos)
        partes.append(f'<div class="cartao" title="{escape(c.get("ajuda", ""), quote=True)}" data-direcao="{direcao_da_seta(c.get("diferenca"))}">{miolo}</div>')
    st.html(f'<div class="grade-cartoes">{"".join(partes)}</div>')


def selecao_dependente(local, rotulo: str, opcoes: list, *, chave: str, padrao=None, **kwargs):
    """Conserva uma escolha válida; troca apenas quando o filtro anterior a exclui."""
    inicial = padrao if padrao in opcoes else opcoes[0]
    if chave in st.session_state and st.session_state[chave] not in opcoes:
        st.session_state[chave] = inicial
    return local.selectbox(rotulo, opcoes, key=chave, index=opcoes.index(inicial), **kwargs)

_TEXTO_CLASSIFICACAO = {
    "nenhuma_novidade_identificada": "nenhuma novidade identificada",
    "possivel_nova_competencia": "possível nova competência",
    "possivel_revisao_de_competencia_historica": "possível revisão de competência histórica",
    "alteracao_de_esquema_ou_fonte": "alteração de esquema, formato ou fonte",
    "falha_de_consulta": "falha de consulta",
}


def direcao_da_seta(diferenca) -> str:
    """Seta do ``st.metric`` de acordo com o sinal da diferença: "up" (aumento), "down" (queda) ou "off" (sem diferença).

    O texto do delta usa o sinal tipográfico "−" (ex.: "−7 vs 2024"); como o Streamlit decide a seta pelo primeiro caractere, ela é
    informada explicitamente para não mostrar seta para cima ao lado de um valor negativo.
    """
    if diferenca is None or pd.isna(diferenca) or int(diferenca) == 0:
        return "off"
    return "up" if int(diferenca) > 0 else "down"


def aviso_ano_parcial(ano: int, mes_final: int) -> str:
    mes = NOMES_MESES[mes_final - 1]
    return f"{ano} contém apenas janeiro a {mes}. Totais de {ano} não são comparados com anos completos; use o período janeiro–{mes}."


def periodo_sinesp_texto(manifesto: dict) -> str:
    """'janeiro/2020 a setembro/2026' a partir da cobertura do manifesto."""
    cobertura = manifesto.get("cobertura", {}).get("sinesp", {})

    def texto(competencia: str) -> str:
        ano, mes = competencia.split("-")
        return f"{NOMES_MESES[int(mes) - 1]}/{ano}"

    try:
        return f"{texto(cobertura['primeira_competencia'])} a {texto(cobertura['ultima_competencia'])}"
    except (KeyError, ValueError):
        return "período não informado no manifesto"


@st.cache_data(show_spinner=False)
def _sinesp():
    return dp.carregar_sinesp()


@st.cache_data(show_spinner=False)
def _catalogo():
    return dp.carregar_catalogo_sinesp()


@st.cache_data(show_spinner=False)
def _manifesto():
    return dp.carregar_manifesto()


@st.cache_data(show_spinner=False)
def _integridade():
    return dp.verificar_integridade()


def exigir(carregar):
    """Executa um carregador e, se os dados estiverem ausentes ou inválidos, mostra o erro e interrompe a página."""
    try:
        return carregar()
    except dp.ErroDados as erro:
        st.error(f"**Dados indisponíveis ou inválidos.** {erro}")
        st.info("Nenhum valor foi preenchido ou estimado. Restaure `dashboard/data_publica/` ou gere uma versão com `python -m src.pipeline.atualizacao_dados` "
                "(requer os XLSX oficiais do Sinesp).")
        st.stop()


def carregar_sinesp():
    return exigir(_sinesp)


def carregar_catalogo():
    return exigir(_catalogo)


def carregar_manifesto():
    return exigir(_manifesto)


def verificar_integridade():
    return exigir(_integridade)


def carregar_dados_consistentes():
    """Série mensal e catálogo, já conferidos entre si (mesmas séries, unidades e contagens)."""
    sinesp, catalogo = carregar_sinesp(), carregar_catalogo()
    try:
        dp.validar_consistencia(sinesp, catalogo)
    except dp.ErroDados as erro:
        st.error(f"**Dados inconsistentes.** {erro}")
        st.stop()
    return sinesp, catalogo


def modo_compacto() -> bool:
    """Estado do seletor "Visualização compacta (celular)" (``st.session_state['modo_compacto']``; falso por padrão)."""
    return bool(st.session_state.get("modo_compacto", False))


def mostrar_figura(figura, legenda: str | None = None, tabela=None):
    """Mostra a figura, a legenda e, opcionalmente, a tabela numérica que a sustenta (os valores desenhados vêm dela).

    No modo compacto a imagem não traz o texto interpretativo nem a fonte completa; eles aparecem aqui como texto nativo do Streamlit
    (``figura.sinesp_notas``), que se adapta à largura da tela.
    """
    if modo_compacto():
        graficos.ajustar_compacto(figura)  # sem espaço em branco abaixo de gráficos sem legenda
    else:
        graficos.ajustar_completo(figura)  # sem espaço vazio no topo quando não há legenda acima do gráfico
    st.pyplot(figura, clear_figure=False, width="stretch")
    if legenda:
        st.caption(legenda)
    notas = getattr(figura, "sinesp_notas", None)
    if modo_compacto() and notas:
        st.caption(notas["interpretacao"])
        st.caption(notas["rodape"])
    if tabela is not None:
        with st.expander("Valores usados neste gráfico (tabela)"):
            st.dataframe(tabela, hide_index=True)


def descricao_versao(manifesto: dict) -> str:
    """Texto curto: versão validada, geração, cobertura e última competência (apenas dados do manifesto)."""
    cobertura = manifesto.get("cobertura", {}).get("sinesp", {})
    ultima = cobertura.get("ultima_competencia", "—")
    texto = (f"Versão histórica validada `{manifesto.get('versao', '—')}`, gerada em {manifesto.get('datas', {}).get('gerado_em_utc', '—')} (UTC) · "
             f"cobertura {cobertura.get('primeira_competencia', '—')} a {ultima} · **última competência disponível: {ultima}**")
    if cobertura.get("ano_parcial"):
        texto += f" · {cobertura['ano_parcial']} é parcial (cada série vai até a sua última competência)"
    return texto + "."


def mostrar_versao_dos_dados() -> None:
    """Rodapé informativo com versão, fonte, atualização e atribuição. Não consulta a rede nem baixa dados."""
    try:
        manifesto = _manifesto()
    except dp.ErroDados:
        st.caption("Informações de versão dos dados indisponíveis (manifesto ausente ou inválido).")
        return
    st.caption(descricao_versao(manifesto))
    fonte = next((f for f in manifesto.get("fontes", []) if f.get("id") == "sinesp_vde"), None)
    with st.expander("Fonte, atualização dos dados e condições de uso"):
        st.markdown(manifesto.get("atribuicao", ""))
        if fonte:
            st.markdown(f"**Fonte oficial:** [{fonte['nome']}]({fonte['url']})")
            publicacao = fonte.get("publicacao") or {}
            if publicacao.get("pagina_atualizada_em"):
                st.markdown(f"**Data informada pela página da fonte ('Atualizado em'):** {publicacao['pagina_atualizada_em']} — informação da página, não prova alteração de valores.")
            consulta = fonte.get("consulta") or {}
            if consulta.get("data_consulta_utc"):
                resumo = sorted({_TEXTO_CLASSIFICACAO.get(a["classificacao"], a["classificacao"]) for a in consulta.get("achados", [])})
                st.markdown(f"**Última verificação registrada nesta versão:** {consulta['data_consulta_utc']} (UTC) — {', '.join(resumo) or 'sem achados'}.")
            else:
                st.markdown("**Última verificação da fonte:** nenhuma registrada nesta versão.")
            st.markdown(f"**Condições de reutilização verificadas:** {fonte.get('condicoes_de_reutilizacao', '—')}")
        st.markdown(
            "**Atualização dos dados:** manual e controlada (verificar → preparar → aprovar). O painel **não** baixa dados, não executa ETL e não se atualiza "
            "sozinho: você está consultando uma versão histórica validada. Novas publicações oficiais só entram após validação, registro de versão e aprovação."
        )
