"""Seção "Apresentação": o que é o painel, fonte e período, três destaques e os principais achados.

Esta seção é a primeira da página única (scripts/painel_streamlit.py). O cabeçalho com a bandeira fica no arquivo de entrada.
Os destaques abaixo NÃO mudam com os filtros: são números fixos calculados da base aprovada.
"""

import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st  # noqa: E402

from dashboard import calculos, ui  # noqa: E402
from dashboard.formatacao import fmt_dif, fmt_int  # noqa: E402

sinesp, catalogo = ui.carregar_dados_consistentes()
manifesto = ui.carregar_manifesto()
periodo = ui.periodo_sinesp_texto(manifesto)
cobertura = manifesto.get("cobertura", {}).get("sinesp", {})
parcial = cobertura.get("ano_parcial")

# ------------------------------------------------------------------------------------------ 1. apresentação resumida
ui.secao("Apresentação", "apresentacao",
         "Indicadores oficiais do Sinesp/MJSP para Joinville/SC e uma exploração separada de violência doméstica da SSP/SC. "
         "Comparações entre períodos de mesma duração; nenhuma causa é afirmada.")

# Quatro números que resumem a base (cada card é um dicionário; ui.cartoes_html desenha a linha de cards).
ui.cartoes_html([
    {"titulo": "Período", "valor": "2020–2026", "detalhe": "Sinesp/MJSP · Joinville/SC", "base": f"{periodo}. Cada série vai até a sua última competência."},
    {"titulo": "Observações mensais", "valor": fmt_int(len(sinesp)), "detalhe": "indicador × abrangência × mês", "base": "Linhas da série mensal publicada."},
    {"titulo": "Séries", "valor": str(len(catalogo)), "detalhe": "Estadual, Polícia Federal e PRF", "base": "Abrangências diferentes nunca são somadas."},
    {"titulo": "Última competência", "valor": cobertura.get("ultima_competencia", "—"), "detalhe": "Sinesp/MJSP",
     "base": f"{parcial} é parcial: só se compara com o mesmo período dos anos anteriores." if parcial else ""},
])


# ------------------------------------------------------------------------------------------ 2. destaques fixos
def _destaques() -> list[dict]:
    """Três números calculados da base: último ano completo e mesmo período do ano parcial (homicídio doloso e tentativa)."""
    lista = []
    homicidio = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    anual = calculos.tabela_anual_sinesp(homicidio)
    completos = anual.loc[anual["cobertura"].eq("ano completo") & anual["soma"].notna()].sort_values("ano")
    if len(completos) >= 2:
        ultimo, anterior = completos.iloc[-1], completos.iloc[-2]
        dif = int(ultimo["soma"]) - int(anterior["soma"])
        lista.append({"titulo": f"Homicídio doloso · {int(ultimo['ano'])} (completo)", "detalhe": "Estadual · vítimas · ano completo",
                      "valor": fmt_int(ultimo["soma"]), "variacao": f"{fmt_dif(dif)} vs {int(anterior['ano'])}", "diferenca": dif,
                      "base": f"Comparado com o ano completo de {int(anterior['ano'])}."})
    for evento in ("Homicídio doloso", "Tentativa de homicídio"):
        r = calculos.comparacao_ultimo_periodo_sinesp(calculos.serie_sinesp(sinesp, evento, "Estadual"))
        if r is not None:
            dif = int(r["diferenca_absoluta"])
            lista.append({"titulo": f"{evento} · {r['periodo']} de {r['ano_atual']}", "detalhe": "Estadual · vítimas · ano parcial",
                          "valor": fmt_int(r["valor_atual"]), "variacao": f"{fmt_dif(dif)} vs {r['periodo']} de {r['ano_anterior']}", "diferenca": dif,
                          "base": f"Comparado com {r['periodo']} de {r['ano_anterior']} (mesma duração)."})
    return lista


st.subheader("Destaques (não mudam com os filtros)")
ui.cartoes_html(_destaques())
st.caption("Diferenças entre períodos de igual duração, sem cor de \"bom\" ou \"ruim\". São contagens publicadas, não explicações.")

# ------------------------------------------------------------------------------------------ 3. achados e limites
st.subheader("Principais achados")
for achado in calculos.achados_principais(sinesp)[:3]:
    st.markdown(f"- **{achado['titulo']}:** {achado['texto']}")
atrasadas = catalogo.loc[catalogo["fim"] != catalogo["fim"].max(), ["evento", "abrangencia", "fim"]]
if len(atrasadas):
    st.info("Algumas séries terminam antes das demais: " + "; ".join(f"{r.evento} ({r.abrangencia}) até {r.fim}" for r in atrasadas.itertuples())
            + ". Isso é informado, não corrigido nem preenchido.")

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
