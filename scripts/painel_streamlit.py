r"""Ponto de entrada do dashboard Segurança Pública de Joinville (fonte única: Sinesp/MJSP).

Execução local (a partir da raiz do projeto)::

    .\.venv\Scripts\python.exe -m streamlit run scripts/painel_streamlit.py

O Streamlit Community Cloud usa este mesmo arquivo como ponto de entrada (não mude o caminho).

Como funciona:
    • O Streamlit executa este arquivo de cima para baixo a cada interação do usuário (clique, filtro, troca de página).
    • ``st.set_page_config`` define título da aba, ícone e layout largo.
    • ``st.Page`` declara cada página (um arquivo em ``dashboard/pages/``) e ``st.navigation`` monta o menu lateral com elas;
      ``navigation.run()`` executa a página escolhida.

O painel usa somente os arquivos mínimos de ``dashboard/data_publica/``; não lê ``dados/`` nem executa o ETL durante a navegação.
Os cálculos ficam em ``dashboard/calculos.py``, os gráficos em ``dashboard/graficos.py`` e os componentes reutilizáveis em ``dashboard/ui.py``.
"""

import sys
from pathlib import Path

# A raiz do projeto precisa estar no caminho de importação quando o Streamlit executa este arquivo
# (por exemplo, em um deploy) para que o pacote ``dashboard`` seja encontrado.
_RAIZ = Path(__file__).resolve().parents[1]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st  # noqa: E402


# Configuração da página: precisa ser o primeiro comando do Streamlit.
st.set_page_config(page_title="Segurança Pública de Joinville", page_icon="🛡️", layout="wide")

# As três páginas do painel. url_path define o endereço (ex.: /sinesp) e default=True indica a página inicial.
pages = [
    st.Page(str(_RAIZ / "dashboard" / "pages" / "home.py"), title="Projeto", icon="🛡️", url_path="projeto", default=True),
    st.Page(str(_RAIZ / "dashboard" / "pages" / "sinesp.py"), title="Indicadores Sinesp", icon="📊", url_path="sinesp"),
    st.Page(str(_RAIZ / "dashboard" / "pages" / "quality.py"), title="Qualidade e metodologia", icon="🔎", url_path="qualidade"),
]
# Menu lateral com as páginas; run() executa a página que o usuário escolheu.
navigation = st.navigation(pages, position="sidebar")
navigation.run()
