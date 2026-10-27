import streamlit as st


st.title("Segurança Pública de Joinville")
st.write(
    "Projeto acadêmico para organizar e analisar indicadores públicos agregados "
    "de segurança pública de Joinville, com fontes, períodos e limitações explícitos."
)
st.subheader("Objetivo")
st.write(
    "Documentar a evolução dos indicadores municipais disponíveis e permitir a "
    "consulta auditável das fontes. A aplicação não mede toda a criminalidade "
    "ocorrida e não compara a efetividade das corporações."
)
st.subheader("Fontes coletadas")
st.markdown(
    "- **Sinesp VDE / MJSP:** indicadores municipais filtrados de XLSX oficiais, 2023–2026 (2026 parcial).\n"
    "- **SSP/SC:** 45 boletins e relatórios PDF; CSVs municipais extraídos com referência ao arquivo e página.\n"
    "- **Prefeitura de Joinville / SEPROT:** totais anuais de furto e roubo publicados para 2023–2025."
)
st.info(
    "Os resultados analíticos e gráficos estão pendentes de validação. Esta versão inicial "
    "exibe fontes e qualidade dos arquivos, sem apresentar KPIs ou gráficos não revisados."
)
st.caption("Use a navegação lateral para consultar a auditoria de qualidade dos dados.")
