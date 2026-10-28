"""Notebook ``notebooks/analise_seguranca_publica_joinville.ipynb``: estrutura didática, sem saídas gravadas e execução de todas as células de código, em ordem."""

import json
import sys

import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager

from src.pipeline.utils import project_path

NOTEBOOK = project_path("notebooks", "analise_seguranca_publica_joinville.ipynb")
SECOES = ["1. Fonte oficial", "2. Bibliotecas", "3. Diretórios", "4. Leitura dos arquivos", "5. Inspeção bruta", "6. Tratamento",
          "7. Verificação de duplicidades", "8. Valores ausentes e zeros", "9. Recorte Joinville", "10. Estatísticas", "11. Gráficos e interpretações",
          "12. Conclusões", "13. Limitações", "14. Exploração separada", "15. Síntese"]


def _celulas():
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]


def test_notebook_tem_introducao_e_as_secoes_da_analise_sem_saidas_gravadas():
    celulas = _celulas()
    titulos = [linha for c in celulas if c["cell_type"] == "markdown" for linha in "".join(c["source"]).splitlines() if linha.startswith("#")]
    assert titulos[0].startswith("# Análise da segurança pública de Joinville/SC")  # introdução
    for secao in SECOES:
        assert any(t.startswith(f"## {secao}") for t in titulos), secao
    codigo = [c for c in celulas if c["cell_type"] == "code"]
    assert len(codigo) >= 15 and all(not c["outputs"] and c["execution_count"] is None for c in codigo)  # saídas não vão para o Git
    texto = "".join("".join(c["source"]) for c in celulas)
    assert "MODO DEMONSTRAÇÃO" in texto and "dashboard import calculos, graficos" in texto  # reutiliza os cálculos validados
    for proibido in ("fillna(", "drop_duplicates("):  # ausência nunca vira zero; nenhuma linha é apagada
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
