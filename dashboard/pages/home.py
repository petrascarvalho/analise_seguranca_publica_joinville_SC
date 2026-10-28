"""Página "Projeto": apresentação executiva — o que é o painel, fonte e período, três destaques, um gráfico, achados e atalhos."""

import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st  # noqa: E402

from dashboard import calculos, graficos, ui  # noqa: E402
from dashboard.formatacao import fmt_dif, fmt_int  # noqa: E402

sinesp, catalogo = ui.carregar_dados_consistentes()
manifesto = ui.carregar_manifesto()
periodo = ui.periodo_sinesp_texto(manifesto)
cobertura = manifesto.get("cobertura", {}).get("sinesp", {})
parcial = cobertura.get("ano_parcial")

# --------------------------------------------------------------------------------------------- 1. título e descrição
st.title("Segurança Pública de Joinville/SC")
st.markdown(
    "Indicadores oficiais do **Sinesp/MJSP** para Joinville: evolução mensal e anual, comparações entre períodos de mesma duração e "
    "estatísticas descritivas, sempre com fonte, unidade e limites explícitos."
)

# --------------------------------------------------------------------------------------------- 2. fonte e período
with st.container(border=True):
    f1, f2, f3, f4 = st.columns(4)
    f1.metric("Período", "2020–2026", help=f"{periodo}. Cada série vai até a sua última competência.")
    f2.metric("Observações mensais", fmt_int(len(sinesp)), help="Linhas da série mensal (indicador × abrangência × competência)")
    f3.metric("Séries", len(catalogo), help="Combinações indicador × abrangência (Estadual, Polícia Federal, PRF)")
    f4.metric("Última competência", cobertura.get("ultima_competencia", "—"))
    st.caption(f"Fonte: MJSP / Sinesp VDE, recorte exato Joinville/SC — única fonte deste painel. Período disponível: **{periodo}**"
               f"{f' ({parcial} é parcial: só é comparado com o mesmo período dos anos anteriores)' if parcial else ''}.")

# --------------------------------------------------------------------------------------------- 3. destaques
st.subheader("Indicadores de destaque")


def _destaques() -> list[dict]:
    """Três números calculados da base: último ano completo e mesmo período do ano parcial (homicídio doloso e tentativa)."""
    cartoes = []
    homicidio = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    anual = calculos.tabela_anual_sinesp(homicidio)
    completos = anual.loc[anual["cobertura"].eq("ano completo") & anual["soma"].notna()].sort_values("ano")
    if len(completos) >= 2:
        ultimo, anterior = completos.iloc[-1], completos.iloc[-2]
        dif = int(ultimo["soma"]) - int(anterior["soma"])
        cartoes.append({"indicador": "Homicídio doloso", "detalhe": f"Estadual · vítimas · ano completo de {int(ultimo['ano'])}",
                        "rotulo": f"Homicídio doloso · {int(ultimo['ano'])} (completo)", "valor": fmt_int(ultimo["soma"]),
                        "delta": f"{fmt_dif(dif)} vs {int(anterior['ano'])}", "diferenca": dif,
                        "base": f"Comparado com o ano completo de {int(anterior['ano'])}."})
    for evento in ("Homicídio doloso", "Tentativa de homicídio"):
        r = calculos.comparacao_ultimo_periodo_sinesp(calculos.serie_sinesp(sinesp, evento, "Estadual"))
        if r is not None:
            dif = int(r["diferenca_absoluta"])
            curto = "–".join(mes[:3] for mes in r["periodo"].split("–"))  # "janeiro–setembro" → "jan–set"
            cartoes.append({"indicador": evento, "detalhe": f"Estadual · vítimas · {r['periodo']} de {r['ano_atual']} (ano parcial)",
                            "rotulo": f"{evento} · {curto}/{r['ano_atual']}", "valor": fmt_int(r["valor_atual"]),
                            "delta": f"{fmt_dif(dif)} vs {r['periodo']} de {r['ano_anterior']}", "diferenca": dif,
                            "base": f"Comparado com {r['periodo']} de {r['ano_anterior']} (mesma duração)."})
    return cartoes


for coluna, cartao in zip(st.columns(3), _destaques()):
    ui.cartao_indicador(coluna, **cartao)
st.caption("Diferenças entre períodos de igual duração, sem cor de \"bom\" ou \"ruim\". São contagens publicadas, não explicações: nenhuma causa é afirmada.")

# --------------------------------------------------------------------------------------------- 4. gráfico principal
st.subheader("Evolução do homicídio doloso")
anos = sorted(int(a) for a in sinesp["ano"].unique())
figura = graficos.figura_serie_anual_sinesp(sinesp, "Homicídio doloso", "Estadual", anos)
if figura is not None:
    anual = calculos.tabela_anual_sinesp(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual"))
    completos = anual.loc[anual["cobertura"].eq("ano completo") & anual["soma"].notna()]
    tabela = completos[["ano", "soma"]].assign(soma=lambda t: t["soma"].map(fmt_int)).rename(columns={"ano": "Ano", "soma": "Vítimas"})
    ui.mostrar_figura(figura, "Vítimas por ano completo (2026 é parcial e não entra). Eixo vertical iniciado em zero.", tabela)

# --------------------------------------------------------------------------------------------- 5. achados
st.subheader("Principais achados")
for achado in calculos.achados_principais(sinesp)[:3]:
    st.markdown(f"- **{achado['titulo']}:** {achado['texto']}")
tabela_ultimas = catalogo[["evento", "abrangencia", "fim"]].copy()
atrasadas = tabela_ultimas.loc[tabela_ultimas["fim"] != tabela_ultimas["fim"].max()]
if len(atrasadas):
    st.info("Algumas séries terminam antes das demais: " + "; ".join(f"{r.evento} ({r.abrangencia}) até {r.fim}" for r in atrasadas.itertuples())
            + ". Isso é informado, não corrigido nem preenchido.")

# --------------------------------------------------------------------------------------------- 6. acesso às análises
st.subheader("Explore as análises")
a1, a2 = st.columns(2)
with a1.container(border=True):
    ui.link_pagina("../dashboard/pages/sinesp.py", "Indicadores Sinesp", "📊")
    st.caption("12 séries, filtros, comparações, padrões e estatísticas.")
with a2.container(border=True):
    ui.link_pagina("../dashboard/pages/quality.py", "Qualidade e metodologia", "🔎")
    st.caption("Integridade dos arquivos, cobertura, métodos e limitações.")

with st.expander("Pergunta, unidades e limites da leitura"):
    st.markdown(
        "**Pergunta analítica:** como evoluíram, desde janeiro/2020, os indicadores oficiais de segurança pública do Sinesp/MJSP para "
        "Joinville/SC, e o que a comparação entre períodos equivalentes permite — e não permite — afirmar?\n\n"
        "- *Vítimas* e *mandados cumpridos* são unidades distintas e **nunca são somadas**; não há total geral entre indicadores ou abrangências.\n"
        "- Registros administrativos agregados: não medem toda a criminalidade, não estimam subnotificação e não permitem inferir causalidade.\n"
        "- Sem taxas populacionais e sem dados por bairro, rua ou horário.\n"
        "- Zero publicado é observação; ausência de cobertura não é zero. Contagens pequenas geram percentuais instáveis."
    )
    for achado in calculos.achados_principais(sinesp)[3:]:
        st.markdown(f"- **{achado['titulo']}:** {achado['texto']}")
st.caption("Fonte: MJSP / Sinesp VDE. Versão validada dos dados (página *Qualidade e metodologia*); a atualização é manual e controlada e o painel nunca baixa dados.")
