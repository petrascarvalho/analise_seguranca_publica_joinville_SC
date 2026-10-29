# PAINEL DADOS DA SEGURANÇA PÚBLICA DE JOINVILLE/SC (uma única página)
#
# Como executar (na pasta do projeto):
#   .\.venv\Scripts\python.exe -m streamlit run scripts/painel_streamlit.py
# O Streamlit Community Cloud usa este mesmo arquivo como ponto de entrada (não mude o caminho).
#
# Como funciona:
#   - O Streamlit executa este arquivo de cima para baixo a cada interação do usuário (clique, filtro).
#   - st.set_page_config define o título da aba do navegador e o layout largo.
#   - ui.aplicar_estilo e ui.cabecalho mostram o fundo azul-claro e o cabeçalho com a bandeira de Joinville.
#   - Cada seção da página é um arquivo de dashboard/pages/; o laço no final executa as seções de cima para baixo:
#       1. home.py                 Apresentação
#       2. sinesp.py               Filtros, cards, análises e gráficos do Sinesp
#       3. violencia_domestica.py  Violência doméstica SSP/SC (fonte separada, em validação)
#       4. quality.py              Qualidade dos dados, fontes, metodologia e limitações
#   - O painel usa só os arquivos mínimos de dashboard/data_publica/; não executa o ETL durante a navegação.
#   - Os cálculos ficam em dashboard/calculos.py, os gráficos em dashboard/graficos.py e os componentes em dashboard/ui.py.


# runpy executa outro arquivo Python (cada seção da página); sys e Path tratam do caminho de importação.
import runpy
import sys
from pathlib import Path

# A raiz do projeto precisa estar no caminho de importação quando o Streamlit executa este arquivo
# (por exemplo, em um deploy) para que o pacote dashboard seja encontrado.
_RAIZ = Path(__file__).resolve().parents[1]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st  # noqa: E402

TITULO = "DADOS DA SEGURANÇA PÚBLICA DE JOINVILLE/SC"

# Configuração da página: precisa ser o primeiro comando do Streamlit. O título aparece na aba do navegador.
st.set_page_config(page_title=TITULO, page_icon="🛡️", layout="wide")



# cache_resource: o dicionário é criado uma vez e dura enquanto o servidor estiver aberto.
@st.cache_resource
def horarios_dos_arquivos() -> dict:
    """Um dicionário que dura enquanto o servidor estiver aberto: guarda o horário de modificação de cada arquivo de dashboard/."""
    return {}


# Servidor aberto durante uma alteração do código: o Python guarda na memória os módulos já importados. Sem este cuidado, a página
# nova pode misturar este arquivo (novo) com um módulo antigo, e aparece um erro como "módulo 'dashboard.ui' não possui atributo ...".
# Se algum arquivo de dashboard/ mudou desde a execução anterior, tiramos todos os módulos "dashboard" da memória; eles são importados de novo abaixo.
horarios = horarios_dos_arquivos()
atuais = {str(arquivo): arquivo.stat().st_mtime for arquivo in (_RAIZ / "dashboard").rglob("*.py")}
if horarios and atuais != horarios:
    for nome in [nome for nome in sys.modules if nome == "dashboard" or nome.startswith("dashboard.")]:
        del sys.modules[nome]
horarios.clear()
horarios.update(atuais)

# Componentes visuais do painel (estilo, cabeçalho, cards).
from dashboard import ui  # noqa: E402

ui.aplicar_estilo()
ui.cabecalho(TITULO, "Indicadores oficiais do Sinesp/MJSP e exploração separada de violência doméstica da SSP/SC · Joinville/SC")
st.markdown("**Nesta página:** [Apresentação](#apresentacao) · [Indicadores Sinesp](#indicadores) · [Violência doméstica SSP/SC](#violencia-domestica) · "
            "[Qualidade](#qualidade) · [Metodologia](#metodologia)")

# As seções, na ordem em que aparecem. Cada arquivo é executado como um programa Python independente.
SECOES = ["home.py", "sinesp.py", "violencia_domestica.py", "quality.py"]
# Executa as quatro seções em ordem; cada uma desenha a sua parte da página.
for arquivo in SECOES:
    runpy.run_path(str(_RAIZ / "dashboard" / "pages" / arquivo))
