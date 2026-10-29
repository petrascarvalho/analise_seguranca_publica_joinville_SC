"""Seção "Apresentação": o que é o painel, fonte e período, três destaques e os principais achados.

Esta seção é a primeira da página única (scripts/painel_streamlit.py). O cabeçalho com a bandeira fica no arquivo de entrada.
Os destaques abaixo NÃO mudam com os filtros: são números fixos calculados da base aprovada.
"""

import sys
from pathlib import Path

# Pasta do projeto: entra no caminho de importação para o Python achar o pacote dashboard.
_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st  # noqa: E402

from dashboard import calculos, ui  # noqa: E402
from dashboard.formatacao import fmt_competencia, fmt_dif, fmt_int, fmt_mes_extenso  # noqa: E402

# Lê a base mensal e o catálogo publicados (com conferência de consistência).
sinesp, catalogo = ui.carregar_dados_consistentes()
# O manifesto é um JSON com a versão dos dados, a cobertura e os hashes; get() devolve {} se a chave não existir.
manifesto = ui.carregar_manifesto()
periodo = ui.periodo_sinesp_texto(manifesto)
cobertura = manifesto.get("cobertura", {}).get("sinesp", {})
parcial = cobertura.get("ano_parcial")

# ------------------------------------------------------------------------------------------ 1. apresentação resumida
ui.secao("Apresentação", "apresentacao",
         "Números oficiais de segurança pública do município de Joinville/SC (Sinesp/MJSP) e, em seção separada, dados de violência doméstica da SSP/SC. "
         "As comparações usam períodos de mesma duração e nenhuma causa é afirmada.")

# Quatro números que resumem a base (cada card é um dicionário; ui.cartoes_html desenha a linha de cards).
ui.cartoes_html([
    {"titulo": "Período", "valor": "2020–2026", "detalhe": "Sinesp/MJSP · Joinville/SC", "base": f"{periodo}. Cada indicador vai até o último mês disponível nesta base."},
    {"titulo": "Registros mensais", "valor": fmt_int(len(sinesp)), "detalhe": "todos os indicadores, mês a mês", "base": "Contagens publicadas pela fonte."},
    {"titulo": "Séries", "valor": str(len(catalogo)), "detalhe": "indicadores de Joinville/SC", "base": "Cada série tem a sua unidade; séries diferentes nunca são somadas."},
    {"titulo": "Último mês disponível nesta base", "valor": fmt_competencia(cobertura.get("ultima_competencia", ""), curto=True), "detalhe": "Sinesp/MJSP",
     "base": f"{fmt_mes_extenso(cobertura.get('ultima_competencia', ''))}. " + (f"O ano de {parcial} é parcial: só se compara com o mesmo período dos anos anteriores." if parcial else "")},
])


st.caption("Todos os números são de Joinville/SC. A classificação institucional da série (por exemplo, “Estadual”) vem da fonte e não indica um total de Santa Catarina; "
           "a explicação completa está em “Fontes, metodologia e limitações”.")

# ------------------------------------------------------------------------------------------ 2. destaques fixos
def _destaques() -> list[dict]:
    """Três números calculados da base: último ano completo e mesmo período do ano parcial (homicídio doloso e tentativa)."""
    lista = []
    # Série de homicídio doloso (classificação Estadual) e sua soma por ano.
    homicidio = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    anual = calculos.tabela_anual_sinesp(homicidio)
    # Só anos completos, em ordem; os dois últimos são comparados.
    completos = anual.loc[anual["cobertura"].eq("ano completo") & anual["soma"].notna()].sort_values("ano")
    if len(completos) >= 2:
        ultimo, anterior = completos.iloc[-1], completos.iloc[-2]
        dif = int(ultimo["soma"]) - int(anterior["soma"])
        lista.append({"titulo": f"Homicídio doloso · {int(ultimo['ano'])} (completo)", "detalhe": "Joinville/SC · vítimas · ano completo",
                      "valor": fmt_int(ultimo["soma"]), "variacao": f"{fmt_dif(dif)} vs {int(anterior['ano'])}", "diferenca": dif,
                      "base": f"Comparado com o ano completo de {int(anterior['ano'])}."})
    for evento in ("Homicídio doloso", "Tentativa de homicídio"):
        # Mesmo período (janeiro até o último mês publicado) no ano parcial e no ano anterior.
        r = calculos.comparacao_ultimo_periodo_sinesp(calculos.serie_sinesp(sinesp, evento, "Estadual"))
        if r is not None:
            dif = int(r["diferenca_absoluta"])
            lista.append({"titulo": f"{evento} · {r['periodo']} de {r['ano_atual']}", "detalhe": "Joinville/SC · vítimas · ano parcial",
                          "valor": fmt_int(r["valor_atual"]), "variacao": f"{fmt_dif(dif)} vs {r['periodo']} de {r['ano_anterior']}", "diferenca": dif,
                          "base": f"Comparado com {r['periodo']} de {r['ano_anterior']} (mesma duração)."})
    return lista


st.subheader("Destaques (não mudam com os filtros)")
ui.cartoes_html(_destaques())
st.caption("Diferenças entre períodos de igual duração, sem cor de \"bom\" ou \"ruim\". São contagens publicadas, não explicações.")

# ------------------------------------------------------------------------------------------ 3. achados e limites
st.subheader("Principais achados")
# Os três primeiros achados (fatiamento [:3]) viram uma lista com marcadores.
for achado in calculos.achados_principais(sinesp)[:3]:
    st.markdown(f"- **{achado['titulo']}:** {achado['texto']}")
# Séries que terminam antes do último mês da base (ex.: PRF): .loc[linhas, colunas] escolhe linhas e colunas de uma vez.
atrasadas = catalogo.loc[catalogo["fim"] != catalogo["fim"].max(), ["evento", "abrangencia", "fim"]]
if len(atrasadas):
    st.info("Algumas séries terminam antes das demais: " + "; ".join(f"{r.evento} ({r.abrangencia}) até {fmt_competencia(r.fim)}" for r in atrasadas.itertuples())
            + ". O painel mostra essas séries só até o último mês disponível, sem preencher os meses que faltam.")

# expander: bloco recolhível; o conteúdo só aparece quando o usuário clica.
with st.expander("Pergunta, unidades e limites da leitura"):
    st.markdown(
        "**Pergunta que orienta o painel:** como evoluíram, desde janeiro/2020, os indicadores oficiais de segurança pública do Sinesp/MJSP para "
        "Joinville/SC, e o que a comparação entre períodos equivalentes permite — e não permite — afirmar?\n\n"
        "- *Vítimas* e *mandados cumpridos* são unidades diferentes e **nunca são somadas**; não existe um total geral entre indicadores diferentes.\n"
        "- São registros administrativos agregados: não medem toda a criminalidade, não estimam casos não registrados e não permitem apontar causas.\n"
        "- Não há taxas por habitante nem dados por bairro, rua ou horário.\n"
        "- Zero informado é um número publicado; falta de informação não é zero. Contagens pequenas geram percentuais instáveis."
    )
    # [3:] pula os três primeiros achados (já mostrados nos cards) e escreve os demais como itens de lista.
    for achado in calculos.achados_principais(sinesp)[3:]:
        st.markdown(f"- **{achado['titulo']}:** {achado['texto']}")
