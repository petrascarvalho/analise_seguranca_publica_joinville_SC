import streamlit as st

from scripts.analysis import quality_inventory


st.title("Qualidade e cobertura dos dados")
st.write(
    "A tabela resume os arquivos derivados disponíveis, sua granularidade básica e "
    "lacunas conhecidas. As contagens de linhas não representam necessariamente eventos únicos."
)
results = quality_inventory()
if results:
    st.dataframe(results, use_container_width=True, hide_index=True)
else:
    st.warning("Ainda não há arquivos processados nas pastas esperadas.")

st.subheader("Ressalvas conhecidas")
st.markdown(
    "- XLSX Sinesp de 2020–2022 foram comparados com as publicações oficiais e estão incluídos.\n"
    "- Boletins SSP/SC repetem valores históricos entre edições; não some snapshots de boletins.\n"
    "- A série municipal de furto e roubo termina em 2025; não há total municipal de 2026 validado.\n"
    "- Duas grafias de lesão corporal aparecem diferentes entre os relatórios SSP de 2023 e 2024; os textos originais são preservados junto dos rótulos padronizados.\n"
    "- Atendimentos da Guarda Municipal não foram incorporados a uma série estruturada nesta versão."
)
