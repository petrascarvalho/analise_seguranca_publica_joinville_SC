"""Auxiliares de interface do dashboard (Streamlit): cache de dados, erros explícitos e avisos."""

from __future__ import annotations

import streamlit as st

from dashboard import dados_publicos as dp

AVISO_FATO_COMUNICADO = (
    "**Unidade: Fato Comunicado**, conforme publicada pela SSP/SC. A definição operacional da contagem não consta dos relatórios; "
    "não deve ser interpretada automaticamente como vítimas, pessoas únicas ou boletins de ocorrência únicos."
)
AVISO_METODOLOGICO_VD = (
    "O mapeamento das grafias “0 Dolosa” e “- Dolosa” das lesões corporais é uma decisão metodológica do projeto, sem confirmação oficial da SSP/SC. "
    "Os meses foram atribuídos aos valores das páginas seguintes pela estrutura contínua das tabelas dos relatórios (o cabeçalho de meses é impresso apenas na primeira página de cada metade). "
    "Não há total geral pela soma das categorias, e as diferenças entre 2023 e 2024 são mudanças nas contagens publicadas, não necessariamente na incidência real."
)
def aviso_ano_parcial(ano: int, mes_final: int) -> str:
    from dashboard.formatacao import NOMES_MESES
    mes = NOMES_MESES[mes_final - 1]
    return f"{ano} contém apenas janeiro a {mes}. Totais de {ano} não são comparados com anos completos; use o período janeiro–{mes}."


def periodo_sinesp_texto(manifesto: dict) -> str:
    """'janeiro/2020 a agosto/2026' a partir da cobertura do manifesto."""
    from dashboard.formatacao import NOMES_MESES
    cobertura = manifesto.get("cobertura", {}).get("sinesp", {})
    def texto(competencia):
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
def _violencia_domestica():
    return dp.carregar_violencia_domestica()


@st.cache_data(show_spinner=False)
def _rastreio_vd():
    return dp.carregar_rastreio_vd()


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
        st.info("Nenhum valor foi preenchido ou estimado. Restaure `dashboard/data_publica/` ou gere-o com `python -m scripts.gerar_dados_dashboard` "
                "(requer o acervo local de dados brutos).")
        st.stop()


def carregar_sinesp():
    return exigir(_sinesp)


def carregar_catalogo():
    return exigir(_catalogo)


def carregar_violencia_domestica():
    return exigir(_violencia_domestica)


def carregar_rastreio_vd():
    return exigir(_rastreio_vd)


def carregar_manifesto():
    return exigir(_manifesto)


def verificar_integridade():
    return exigir(_integridade)


def mostrar_figura(figura, legenda: str | None = None):
    st.pyplot(figura, clear_figure=False)
    if legenda:
        st.caption(legenda)


_COBERTURA = {"sinesp": "sinesp", "ssp": "ssp_violencia_domestica"}
_FONTE_ID = {"sinesp": "sinesp_vde", "ssp": "ssp_sc_violencia_domestica"}
_TEXTO_CLASSIFICACAO = {
    "nenhuma_novidade_identificada": "nenhuma novidade identificada",
    "possivel_nova_competencia": "possível nova competência",
    "possivel_revisao_de_competencia_historica": "possível revisão de competência histórica",
    "alteracao_de_esquema_ou_fonte": "alteração de esquema, formato ou fonte",
    "falha_de_consulta": "falha de consulta",
}


def descricao_versao(manifesto: dict, chave: str) -> str:
    """Texto curto: versão validada, geração, cobertura e última competência (apenas dados do manifesto)."""
    cobertura = manifesto.get("cobertura", {}).get(_COBERTURA[chave], {})
    ultima = cobertura.get("ultima_competencia", "—")
    texto = (f"Versão histórica validada `{manifesto.get('versao', '—')}`, gerada em {manifesto.get('datas', {}).get('gerado_em_utc', '—')} (UTC) · "
             f"cobertura {cobertura.get('primeira_competencia', '—')} a {ultima} · **última competência disponível: {ultima}**")
    if cobertura.get("ano_parcial"):
        texto += f" · {cobertura['ano_parcial']} é parcial (somente até {ultima})"
    return texto + "."


def mostrar_versao_dos_dados(chave: str) -> None:
    """Rodapé informativo com versão, fonte, atualização e atribuição. Não consulta a rede nem baixa dados."""
    try:
        manifesto = _manifesto()
    except dp.ErroDados:
        st.caption("Informações de versão dos dados indisponíveis (manifesto ausente ou inválido).")
        return
    st.caption(descricao_versao(manifesto, chave))
    fonte = next((f for f in manifesto.get("fontes", []) if f.get("id") == _FONTE_ID[chave]), None)
    with st.expander("Fonte, atualização dos dados e condições de uso"):
        st.markdown(manifesto.get("atribuicao", ""))
        if fonte:
            st.markdown(f"**Fonte:** [{fonte['nome']}]({fonte['url']})")
            publicacao = fonte.get("publicacao") or {}
            if publicacao.get("pagina_atualizada_em"):
                st.markdown(f"**Data informada pela página da fonte ('Atualizado em'):** {publicacao['pagina_atualizada_em']} — informação da página, não prova alteração de valores.")
            consulta = fonte.get("consulta") or {}
            if consulta.get("data_consulta_utc"):
                resumo = sorted({_TEXTO_CLASSIFICACAO.get(a["classificacao"], a["classificacao"]) for a in consulta.get("achados", [])})
                st.markdown(f"**Última verificação registrada nesta versão:** {consulta['data_consulta_utc']} (UTC) — {', '.join(resumo) or 'sem achados'}. "
                            "Indícios de atualização ainda não foram incorporados.")
            else:
                st.markdown("**Última verificação das fontes:** nenhuma registrada nesta versão.")
            st.markdown(f"**Condições de reutilização verificadas:** {fonte.get('condicoes_de_reutilizacao', '—')}")
        st.markdown(
            "**Atualização dos dados:** manual e controlada (verificar → preparar → aprovar). O painel **não** baixa dados, não executa ETL e não se atualiza "
            "sozinho: você está consultando uma versão histórica validada. Novas publicações oficiais só entram após validação, registro de versão e aprovação."
        )
