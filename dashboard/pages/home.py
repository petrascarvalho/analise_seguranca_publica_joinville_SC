"""Página "Projeto": apresentação executiva do painel (pergunta, números de destaque, um gráfico e acesso às análises)."""

import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st  # noqa: E402

from dashboard import calculos, graficos, ui  # noqa: E402
from dashboard.formatacao import fmt_dif, fmt_int  # noqa: E402

st.title("Segurança Pública de Joinville/SC — Indicadores Sinesp/MJSP")
st.caption("Projeto acadêmico individual de Visualização de Dados e BI — SENAI/LAB365, Módulo 2, Semana 13")

sinesp, catalogo = ui.carregar_dados_consistentes()
manifesto = ui.carregar_manifesto()
periodo = ui.periodo_sinesp_texto(manifesto)
cobertura = manifesto.get("cobertura", {}).get("sinesp", {})
parcial = cobertura.get("ano_parcial")

# --------------------------------------------------------------------------------- pergunta e objetivo
st.subheader("Pergunta analítica")
st.markdown(
    "**Como evoluíram, desde janeiro/2020, os indicadores oficiais de segurança pública do Sinesp/MJSP para Joinville/SC, "
    "e o que a comparação entre períodos equivalentes permite — e não permite — afirmar?**"
)
st.write(
    "O painel organiza as séries mensais municipais publicadas pelo Ministério da Justiça e Segurança Pública, com filtros por indicador, "
    "abrangência e período, estatísticas descritivas e comparações entre anos completos e entre períodos equivalentes. "
    "Cada número traz fonte, unidade e limitações."
)

# ------------------------------------------------------------------------------------ destaques
st.subheader("Indicadores de destaque")
st.caption("Homicídio doloso e tentativa de homicídio (Estadual, vítimas). Veja os demais indicadores na página *Indicadores Sinesp*.")


def _destaques() -> list[dict]:
    """Três números descritivos calculados da base: último ano completo e período parcial equivalente do homicídio doloso e da tentativa."""
    cartoes = []
    homicidio = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    anual = calculos.tabela_anual_sinesp(homicidio)
    completos = anual.loc[anual["cobertura"].eq("ano completo") & anual["soma"].notna()].sort_values("ano")
    if len(completos) >= 2:
        ultimo, anterior = completos.iloc[-1], completos.iloc[-2]
        dif = int(ultimo["soma"]) - int(anterior["soma"])
        cartoes.append({"rotulo": f"Homicídio doloso · {int(ultimo['ano'])} (completo)", "valor": fmt_int(ultimo["soma"]),
                        "delta": f"{fmt_dif(dif)} vs {int(anterior['ano'])}", "seta": ui.direcao_da_seta(dif),
                        "ajuda": f"Homicídio doloso, Estadual (vítimas). Soma dos 12 meses de {int(ultimo['ano'])}, comparada com o ano completo {int(anterior['ano'])}."})
    for evento in ("Homicídio doloso", "Tentativa de homicídio"):
        r = calculos.comparacao_ultimo_periodo_sinesp(calculos.serie_sinesp(sinesp, evento, "Estadual"))
        if r is not None:
            dif = int(r["diferenca_absoluta"])
            curto = "–".join(mes[:3] for mes in r["periodo"].split("–"))  # "janeiro–setembro" → "jan–set": o rótulo curto não é cortado no cartão
            cartoes.append({"rotulo": f"{evento} · {curto}/{r['ano_atual']}", "valor": fmt_int(r["valor_atual"]),
                            "delta": f"{fmt_dif(dif)} vs {r['periodo']} de {r['ano_anterior']}", "seta": ui.direcao_da_seta(dif),
                            "ajuda": f"{evento}, Estadual (vítimas). Soma de {r['periodo']} de {r['ano_atual']}, comparada com o mesmo período de {r['ano_anterior']}."})
    return cartoes


colunas = st.columns(3)
for coluna, cartao in zip(colunas, _destaques()):
    coluna.metric(cartao["rotulo"], cartao["valor"], delta=cartao["delta"], delta_color="off", delta_arrow=cartao["seta"], help=cartao["ajuda"], border=True)
st.caption("Diferenças entre períodos de igual duração. São observações sobre contagens publicadas, não explicações: nenhuma causa é afirmada.")

# ------------------------------------------------------------------------------------ gráfico principal
st.subheader("Evolução do homicídio doloso")
anos = sorted(int(a) for a in sinesp["ano"].unique())
figura = graficos.figura_serie_anual_sinesp(sinesp, "Homicídio doloso", "Estadual", anos)
if figura is not None:
    anual = calculos.tabela_anual_sinesp(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual"))
    completos = anual.loc[anual["cobertura"].eq("ano completo") & anual["soma"].notna()]
    tabela = completos[["ano", "soma"]].assign(soma=lambda t: t["soma"].map(fmt_int)).rename(columns={"ano": "Ano", "soma": "Vítimas"})
    ui.mostrar_figura(figura, "Total de vítimas por ano completo (2026 é parcial e não entra). Eixo vertical iniciado em zero.", tabela)

# ------------------------------------------------------------------------------------ acesso às análises
st.subheader("Explore")
a1, a2 = st.columns(2)
with a1:
    ui.link_pagina("../dashboard/pages/sinesp.py", "Indicadores Sinesp", "📊")
    st.caption("12 séries, filtros por categoria, indicador, abrangência, anos e meses, comparações e estatísticas.")
with a2:
    ui.link_pagina("../dashboard/pages/quality.py", "Qualidade e metodologia", "🔎")
    st.caption("Integridade dos arquivos (SHA-256), cobertura, regras do ETL, limitações e licenças.")

# ------------------------------------------------------------------------------------ sobre os dados
st.subheader("Sobre os dados")
m1, m2, m3 = st.columns(3)
m1.metric("Observações mensais", fmt_int(len(sinesp)), help="Linhas da série mensal (indicador × abrangência × competência)", border=True)
m2.metric("Séries", len(catalogo), border=True)
m3.metric("Última competência", cobertura.get("ultima_competencia", "—"), border=True)
st.markdown(
    f"- **Fonte oficial:** MJSP / Sinesp VDE, recorte exato **Joinville/SC** — única fonte deste painel.\n"
    f"- **Período disponível:** **{periodo}**{f' ({parcial} é parcial)' if parcial else ''}.\n"
    "- **Unidades:** *vítimas* e *mandados cumpridos* são conceitos distintos e **nunca são somados**."
)
tabela_ultimas = catalogo[["evento", "abrangencia", "fim"]].copy()
atrasadas = tabela_ultimas.loc[tabela_ultimas["fim"] != tabela_ultimas["fim"].max()]
if len(atrasadas):
    st.info("Algumas séries terminam antes das demais: " + "; ".join(f"{r.evento} ({r.abrangencia}) até {r.fim}" for r in atrasadas.itertuples())
            + ". Isso é informado, não corrigido nem preenchido.")

with st.expander("Principais achados descritivos"):
    for achado in calculos.achados_principais(sinesp):
        st.markdown(f"**{achado['titulo']}.** {achado['texto']}")
    st.caption("São observações sobre contagens publicadas, não explicações. Nenhuma causa é afirmada.")

st.subheader("Limites da leitura")
st.markdown(
    "- Registros administrativos agregados: não medem toda a criminalidade, não estimam subnotificação e não permitem inferir causalidade.\n"
    "- Sem taxas populacionais, sem dados por bairro, rua, horário ou corporação, e **sem total geral** entre indicadores ou abrangências.\n"
    "- O ano parcial nunca é comparado com anos completos; zeros publicados são observações e ausência de cobertura não é zero.\n"
    "- Contagens pequenas geram variações percentuais instáveis: observe sempre o valor absoluto."
)
st.caption("Fonte: MJSP / Sinesp VDE. Os dados exibidos são uma versão validada (página *Qualidade e metodologia*); a atualização é manual e controlada e o painel nunca baixa dados.")
