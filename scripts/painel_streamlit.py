r"""Ponto de entrada do painel DADOS DA SEGURANÇA PÚBLICA DE JOINVILLE/SC (uma única página).

Execução local (a partir da raiz do projeto)::

    .\.venv\Scripts\python.exe -m streamlit run scripts/painel_streamlit.py

O Streamlit Community Cloud usa este mesmo arquivo como ponto de entrada (não mude o caminho).

Como funciona:
    • O Streamlit executa este arquivo de cima para baixo a cada interação do usuário (clique, filtro).
    • ``st.set_page_config`` define o título da aba do navegador e o layout largo.
    • ``ui.aplicar_estilo`` e ``ui.cabecalho`` mostram o fundo azul-claro e o cabeçalho com a bandeira de Joinville.
    • Cada seção da página é um arquivo de ``dashboard/pages/``; o laço abaixo executa as seções uma depois da outra, de cima para baixo:
        1. home.py                 Apresentação
        2. sinesp.py               Filtros, cards, análises e gráficos do Sinesp
        3. violencia_domestica.py  Violência doméstica SSP/SC (fonte separada, em validação)
        4. quality.py              Qualidade dos dados, fontes, metodologia e limitações

O painel usa somente os arquivos mínimos de ``dashboard/data_publica/``; não executa o ETL durante a navegação.
Os cálculos ficam em ``dashboard/calculos.py``, os gráficos em ``dashboard/graficos.py`` e os componentes em ``dashboard/ui.py``.
"""

import runpy
import sys
from pathlib import Path

# A raiz do projeto precisa estar no caminho de importação quando o Streamlit executa este arquivo
# (por exemplo, em um deploy) para que o pacote ``dashboard`` seja encontrado.
_RAIZ = Path(__file__).resolve().parents[1]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st  # noqa: E402

TITULO = "DADOS DA SEGURANÇA PÚBLICA DE JOINVILLE/SC"

# Configuração da página: precisa ser o primeiro comando do Streamlit. O título aparece na aba do navegador.
st.set_page_config(page_title=TITULO, page_icon="🛡️", layout="wide")

from dashboard import ui  # noqa: E402

ui.aplicar_estilo()
ui.cabecalho(TITULO, "Indicadores oficiais do Sinesp/MJSP e exploração separada de violência doméstica da SSP/SC · Joinville/SC")
st.markdown("**Nesta página:** [Apresentação](#apresentacao) · [Indicadores Sinesp](#indicadores) · [Violência doméstica SSP/SC](#violencia-domestica) · "
            "[Qualidade](#qualidade) · [Metodologia](#metodologia)")

# As seções, na ordem em que aparecem. Cada arquivo é executado como um programa Python independente.
SECOES = ["home.py", "sinesp.py", "violencia_domestica.py", "quality.py"]
for arquivo in SECOES:
    runpy.run_path(str(_RAIZ / "dashboard" / "pages" / arquivo))
