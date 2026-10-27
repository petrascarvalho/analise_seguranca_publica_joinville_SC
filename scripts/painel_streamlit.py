"""Ponto de entrada do dashboard Segurança Pública de Joinville.

Execução local (a partir da raiz do projeto)::

    python -m streamlit run scripts/painel_streamlit.py

O painel usa somente os arquivos mínimos de ``dashboard/data_publica/``; não lê ``dados/`` nem executa
o roteiro analítico durante a navegação.
"""

import sys
from pathlib import Path

# A raiz do projeto precisa estar no caminho de importação quando o Streamlit executa este arquivo
# (por exemplo, em um deploy) para que os pacotes ``scripts`` e ``dashboard`` sejam encontrados.
_RAIZ = Path(__file__).resolve().parents[1]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st  # noqa: E402

from scripts.utils import project_path  # noqa: E402

st.set_page_config(page_title="Segurança Pública de Joinville", page_icon="🛡️", layout="wide")

pages = [
    st.Page(str(project_path("dashboard", "pages", "home.py")), title="Projeto", icon="🛡️", url_path="projeto", default=True),
    st.Page(str(project_path("dashboard", "pages", "sinesp.py")), title="Indicadores Sinesp", icon="📊", url_path="sinesp"),
    st.Page(str(project_path("dashboard", "pages", "violencia_domestica.py")), title="Violência doméstica SSP/SC", icon="🏠", url_path="violencia-domestica"),
    st.Page(str(project_path("dashboard", "pages", "quality.py")), title="Qualidade dos dados", icon="🔎", url_path="qualidade"),
]
navigation = st.navigation(pages, position="sidebar")
navigation.run()
