"""Notebook ``notebooks/analise_seguranca_publica_joinville.ipynb``: roteiro de 16 etapas comentadas com ``#``, sem saídas gravadas e com execução de todas as células de código, em ordem."""

import json
import sys

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

from src.pipeline.utils import project_path

NOTEBOOK = project_path("notebooks", "analise_seguranca_publica_joinville.ipynb")
ETAPAS = ["Bibliotecas e pastas", "Leitura da base Sinesp aprovada", "XLSX oficial de 2026", "Tratamento", "Verificação de duplicidades",
          "Valores ausentes e zeros", "Recorte de Joinville", "Estatísticas descritivas", "Totais anuais e períodos equivalentes",
          "Outliers pelo método IQR", "Gráficos do Sinesp", "SSP/SC (fonte SEPARADA)", "SSP/SC: estatísticas por categoria",
          "SSP/SC: gráfico", "SSP/SC: rastreabilidade", "Conclusões e limitações"]


def _celulas():
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]


def test_notebook_tem_16_etapas_comentadas_no_codigo_sem_saidas_gravadas():
    celulas = _celulas()
    codigo = [c for c in celulas if c["cell_type"] == "code"]
    assert len(codigo) == 16 and all(not c["outputs"] and c["execution_count"] is None for c in codigo)  # saídas não vão para o Git
    assert "".join(celulas[0]["source"]).startswith("# Análise da segurança pública de Joinville/SC")  # título curto; o resto é código comentado
    for numero, nome in enumerate(ETAPAS, start=1):  # cada célula de código abre com o comentário "# ETAPA n — nome"
        assert "".join(codigo[numero - 1]["source"]).lstrip().startswith(f"# ETAPA {numero} — {nome}"), (numero, nome)
    assert sum(c["cell_type"] == "markdown" for c in celulas) == 1  # sem textos Markdown longos entre os comandos
    texto = "".join("".join(c["source"]) for c in codigo)
    assert "MODO DEMONSTRAÇÃO" in texto and "dashboard import calculos, graficos" in texto  # reutiliza os cálculos validados
    for proibido in ("fillna(", "drop_duplicates(", "class ", "@"):  # ausência nunca vira zero; nenhuma linha é apagada; sem classes/decorators
        assert proibido not in texto, proibido


def test_notebook_executa_todas_as_celulas_em_kernel_real(tmp_path):
    notebook = nbformat.read(NOTEBOOK, as_version=4)
    nbformat.validate(notebook)
    km = KernelManager(kernel_name="python3")
    km.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    client = NotebookClient(notebook, km=km, timeout=600, resources={"metadata": {"path": str(NOTEBOOK.parent)}})
    client.execute()
    nbformat.write(notebook, tmp_path / "notebook_executado.ipynb")
    outputs = [o for c in notebook.cells if c.cell_type == "code" for o in c.outputs]
    texto = "\n".join(o.get("text", "") for o in outputs)
    assert all(c.execution_count is not None for c in notebook.cells if c.cell_type == "code")
    assert not any(o.output_type == "error" for o in outputs)
    assert "Base aprovada: 911 observações × 6 colunas" in texto
    assert "Zeros publicados: 401" in texto and "Observações com chave repetida: 0" in texto
    imagens = [o for o in outputs if "image/png" in o.get("data", {})]
    assert len(imagens) >= 4
    from src.pipeline import ssp_sc
    if ssp_sc.acervo_disponivel():
        assert "SSP/SC: 216 células" in texto and len(imagens) >= 5
    else:
        assert "SSP/SC NÃO EXECUTADA" in texto
