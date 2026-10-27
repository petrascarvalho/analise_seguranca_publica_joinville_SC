import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st  # noqa: E402

from dashboard import dados_publicos as dp  # noqa: E402
from dashboard import ui  # noqa: E402

st.title("Segurança Pública de Joinville/SC")
st.caption("Painel acadêmico de indicadores oficiais agregados — SENAI/LAB365, Visualização de Dados e BI (Módulo 2, Semana 13)")

st.write(
    "Como evoluíram os indicadores oficiais disponíveis de criminalidade registrada em Joinville e quais limites das fontes "
    "afetam sua interpretação? Este painel reúne **duas análises já validadas** no roteiro acadêmico do projeto, com fonte, "
    "período, unidade e limitações explícitos."
)

manifesto = ui.carregar_manifesto()
periodo_sinesp = ui.periodo_sinesp_texto(manifesto)
parcial_sinesp = manifesto.get("cobertura", {}).get("sinesp", {}).get("ano_parcial")

c1, c2 = st.columns(2)
with c1:
    st.subheader("📊 Indicadores Sinesp / MJSP")
    st.markdown(
        f"- **Período:** {periodo_sinesp}{f' (**{parcial_sinesp} é parcial**)' if parcial_sinesp else ''}.\n"
        "- **Abrangência:** município de Joinville/SC; séries **Estadual**, **Polícia Federal** (mandados) e **PRF** (mortes no trânsito) mantidas separadas.\n"
        "- **Unidades:** vítimas (feminicídio, homicídio, tentativas, latrocínio, lesão seguida de morte, suicídio, trânsito, mortes a esclarecer) "
        "e mandados cumpridos — conceitos que **não** são somados.\n"
        "- Séries históricas, comparações anuais, períodos equivalentes (janeiro–agosto) e as quatro figuras da Etapa 10."
    )
with c2:
    st.subheader("🏠 Violência doméstica — SSP/SC")
    st.markdown(
        "- **Período:** janeiro/2023 a dezembro/2024; **nove categorias**; **216 observações** mensais.\n"
        "- **Unidade:** *Fato Comunicado* (contagem publicada nos relatórios).\n"
        "- Comparação 2023 × 2024, evolução mensal, estatísticas descritivas, tabela filtrável e as seis visualizações da Etapa 14.2."
    )

st.subheader("O que este painel não faz")
st.markdown(
    "- Não mede toda a criminalidade ocorrida, não estima subnotificação e não compara a efetividade de corporações.\n"
    "- Não calcula taxas populacionais, não apresenta dados por bairro, rua ou horário e não infere causas.\n"
    "- Não produz um “total geral de crimes” somando indicadores ou categorias diferentes.\n"
    "- Ainda **não inclui** a Prefeitura/SEPROT (furtos e roubos 2023–2025) nem a série histórica de homicídios SSP/SC, cuja auditoria ainda não resolveu as divergências entre boletins."
)

st.info(
    "**Situação:** versão local de desenvolvimento. Não há deploy público confirmado. Os dados exibidos vêm de arquivos mínimos e agregados em "
    "`dashboard/data_publica/` (veja a página *Qualidade dos dados*); os dados brutos oficiais não fazem parte do painel."
)

try:
    fichas = {f["arquivo"]: f for f in manifesto["arquivos"]}
    m1, m2, m3 = st.columns(3)
    m1.metric("Observações Sinesp (mensais)", f"{fichas[dp.ARQ_SINESP]['linhas']:,}".replace(",", "."), help="Séries mensais de 12 combinações indicador × abrangência")
    m2.metric("Observações SSP/SC", f"{fichas[dp.ARQ_VD]['linhas']:,}".replace(",", "."), help="9 categorias × 24 meses (Fato Comunicado)")
    m3.metric("Arquivos de dados", len(fichas))
except KeyError:
    st.warning("O manifesto dos dados não tem o formato esperado; consulte a página Qualidade dos dados.")

st.caption("Fontes: MJSP / Sinesp VDE e SSP/SC (Segurança em Números). Use a navegação lateral para explorar os indicadores.")
