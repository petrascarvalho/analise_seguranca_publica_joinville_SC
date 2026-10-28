"""Auxiliares de interface do dashboard Sinesp/MJSP (Streamlit): cache de dados, erros explícitos e avisos."""

from __future__ import annotations

import pandas as pd
import streamlit as st

from dashboard import dados_publicos as dp
from dashboard import graficos
from dashboard.formatacao import NOMES_MESES

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


def link_pagina(arquivo: str, rotulo: str, icone: str) -> None:
    """Link para outra página do painel (caminho relativo ao arquivo de entrada, scripts/painel_streamlit.py). Fora da navegação principal (ex.: página aberta sozinha), mostra só o nome da página."""
    try:
        st.page_link(arquivo, label=rotulo, icon=icone)
    except st.errors.StreamlitAPIException:
        st.markdown(f"**{icone} {rotulo}**")


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
