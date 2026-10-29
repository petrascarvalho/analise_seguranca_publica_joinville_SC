"""Auxiliares de interface do painel (Streamlit): identidade azul e branca (CSS), cabeçalho com a bandeira, cards de mesma altura,
cache de dados, erros explícitos e avisos."""

from __future__ import annotations

from html import escape
from pathlib import Path

import pandas as pd
import streamlit as st

from dashboard import dados_publicos as dp
from dashboard import graficos
from dashboard.formatacao import NOMES_MESES, fmt_mes_extenso


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
[data-testid="stHeaderActionElements"] {{ display: none !important; }}   /* sem o ícone de link ao lado dos títulos (os links do índice continuam funcionando) */
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


def direcao_da_seta(diferenca) -> str:
    """Seta do st.metric de acordo com o sinal da diferença: "up" (aumento), "down" (queda) ou "off" (sem diferença).

    O texto do delta usa o sinal tipográfico "−" (ex.: "−7 vs 2024"); como o Streamlit decide a seta pelo primeiro caractere, ela é
    informada explicitamente para não mostrar seta para cima ao lado de um valor negativo.
    """
    if diferenca is None or pd.isna(diferenca) or int(diferenca) == 0:
        return "off"
    return "up" if int(diferenca) > 0 else "down"


def aviso_ano_parcial(ano: int, mes_final: int) -> str:
    """Texto de aviso para um ano que só tem os primeiros meses publicados."""
    mes = NOMES_MESES[mes_final - 1]
    return f"{ano} contém apenas janeiro a {mes}. Totais de {ano} não são comparados com anos completos; use o período janeiro–{mes}."


def periodo_sinesp_texto(manifesto: dict) -> str:
    """'janeiro/2020 a setembro/2026' a partir da cobertura do manifesto."""
    cobertura = manifesto.get("cobertura", {}).get("sinesp", {})

    def texto(competencia: str) -> str:
        """Competência '2026-09' escrita como 'setembro/2026'."""
        ano, mes = competencia.split("-")
        return f"{NOMES_MESES[int(mes) - 1]}/{ano}"

    try:
        return f"{texto(cobertura['primeira_competencia'])} a {texto(cobertura['ultima_competencia'])}"
    except (KeyError, ValueError):
        return "período não informado"


@st.cache_data(show_spinner=False)
def _sinesp():
    """Lê a série mensal do Sinesp (guardada em cache pelo Streamlit)."""
    return dp.carregar_sinesp()


@st.cache_data(show_spinner=False)
def _catalogo():
    """Lê o catálogo de indicadores (guardado em cache pelo Streamlit)."""
    return dp.carregar_catalogo_sinesp()


@st.cache_data(show_spinner=False)
def _manifesto():
    """Lê o manifesto da versão publicada (guardado em cache pelo Streamlit)."""
    return dp.carregar_manifesto()


@st.cache_data(show_spinner=False)
def _integridade():
    """Confere o SHA-256 dos arquivos de dados com o manifesto (guardado em cache pelo Streamlit)."""
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
    """Série mensal do Sinesp; se houver erro nos dados, mostra a mensagem e para o painel."""
    return exigir(_sinesp)


def carregar_catalogo():
    """Catálogo de indicadores; se houver erro nos dados, mostra a mensagem e para o painel."""
    return exigir(_catalogo)


def carregar_manifesto():
    """Manifesto da versão; se houver erro nos dados, mostra a mensagem e para o painel."""
    return exigir(_manifesto)


def verificar_integridade():
    """Resultado da conferência de integridade; se houver erro, mostra a mensagem e para o painel."""
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
    """Estado do seletor "Visualização compacta (celular)" (st.session_state['modo_compacto']; falso por padrão)."""
    return bool(st.session_state.get("modo_compacto", False))


def mostrar_figura(figura, legenda: str | None = None, tabela=None):
    """Mostra a figura, a legenda e, opcionalmente, a tabela numérica que a sustenta (os valores desenhados vêm dela).

    No modo compacto a imagem não traz o texto interpretativo nem a fonte completa; eles aparecem aqui como texto nativo do Streamlit
    (figura.sinesp_notas), que se adapta à largura da tela.
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


def data_da_atualizacao(manifesto: dict) -> str:
    """Data da última atualização dos dados (dia/mês/ano), lida do identificador da versão: '20261027T114400Z' → '27/10/2026'."""
    versao = str(manifesto.get("versao", ""))
    return f"{versao[6:8]}/{versao[4:6]}/{versao[:4]}" if len(versao) >= 8 and versao[:8].isdigit() else "não informada"


# Explicação da abrangência "Estadual", sem sugerir que o número é do estado inteiro. A versão completa aparece só na Apresentação e na
# metodologia; nos demais lugares usa-se a versão curta.
NOTA_ABRANGENCIA = ("Os indicadores do Sinesp foram selecionados para o município de **Joinville/SC**. A abrangência “Estadual” (assim como “Polícia Federal” "
                    "e “Polícia Rodoviária Federal”) identifica a classificação institucional da série na fonte; **não é um total do estado de Santa Catarina**.")
NOTA_ABRANGENCIA_CURTA = "“Estadual” é a classificação institucional da série, **não um total de Santa Catarina**."


def sem_registro(unidade_curta: str) -> str:
    """Texto para um total igual a zero (a fonte informou zero, o que não é o mesmo que ausência de informação)."""
    return "Nenhum mandado cumprido registrado" if unidade_curta.startswith("mandado") else "Nenhuma vítima registrada"


def mostrar_versao_dos_dados() -> None:
    """Rodapé simples: fonte, data da atualização e condições de uso, em linguagem comum. Não consulta a rede nem baixa dados."""
    try:
        manifesto = _manifesto()
    except dp.ErroDados:
        st.caption("Informações sobre a atualização dos dados indisponíveis no momento.")
        return
    ultima = manifesto.get("cobertura", {}).get("sinesp", {}).get("ultima_competencia", "")
    st.markdown("**Fonte dos dados:** Ministério da Justiça e Segurança Pública (MJSP) — Sinesp VDE.  \n"
                "**Análise e visualização:** Petras Ruben Carvalho — Analista de Dados | Business Intelligence.")
    st.caption(f"Dados do Sinesp/MJSP para Joinville/SC · base atualizada em {data_da_atualizacao(manifesto)} · "
               f"período: {periodo_sinesp_texto(manifesto)} (2026 é parcial; o último mês disponível nesta base é {fmt_mes_extenso(ultima)}).")
    fonte = next((f for f in manifesto.get("fontes", []) if f.get("id") == "sinesp_vde"), None)
    with st.expander("Fonte, atualização dos dados e condições de uso"):
        st.markdown("**Fonte dos dados:** Ministério da Justiça e Segurança Pública (MJSP) — Sinesp VDE (Sistema Nacional de Estatísticas de Segurança Pública). "
                    "Tabelas e gráficos são elaborações próprias, feitas a partir de números estatísticos públicos.")
        if fonte:
            st.markdown(f"**Página oficial da fonte:** [{fonte['nome']}]({fonte['url']})")
            consulta = (fonte.get("consulta") or {}).get("data_consulta_utc") or ""   # versões sem consulta registrada têm este campo vazio
            if consulta[:10].count("-") == 2:
                ano, mes, dia = consulta[:10].split("-")
                st.markdown(f"**Fonte consultada pela última vez em:** {dia}/{mes}/{ano}.")
        st.markdown(
            "**Atualização dos dados:** feita manualmente, depois de conferência. Este painel não busca informações sozinho: você vê a base "
            f"de {data_da_atualizacao(manifesto)}, que pode não incluir publicações mais recentes da fonte. Novas publicações só entram depois de conferidas."
        )
        st.markdown(
            "**Condições de uso:** o painel usa apenas contagens agregadas de Joinville/SC; os arquivos originais completos e dados pessoais não são "
            "redistribuídos. Não foi encontrada nenhuma proibição de uso, mas também não foi possível confirmar uma licença específica para esta base "
            "(o portal gov.br informa a licença CC BY-ND 3.0 para o conteúdo geral do site). Por isso a fonte é sempre citada. "
            "Esta é uma avaliação do projeto, não um parecer jurídico."
        )
