import streamlit as st

from scripts.utils import project_path


st.set_page_config(page_title="Segurança Pública de Joinville", page_icon="🛡️", layout="wide")

pages = [
    st.Page(str(project_path("dashboard", "pages", "home.py")), title="Projeto", icon="🛡️", default=True),
    st.Page(str(project_path("dashboard", "pages", "quality.py")), title="Qualidade dos dados", icon="🔎"),
]
navigation = st.navigation(pages, position="sidebar")
navigation.run()
