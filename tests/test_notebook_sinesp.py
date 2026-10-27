"""Notebook ``notebooks/analise_sinesp.ipynb``: estrutura didática, sem saídas gravadas e execução de todas as células de código, em ordem."""

import json
import os
import subprocess
import sys
import textwrap

from scripts.utils import project_path

NOTEBOOK = project_path("notebooks", "analise_sinesp.ipynb")
SECOES = ["1. Fonte oficial", "2. Bibliotecas", "3. Diretórios", "4. Leitura dos arquivos", "5. Inspeção bruta", "6. Tratamento",
          "7. Verificação de duplicidades", "8. Valores ausentes e zeros", "9. Recorte Joinville", "10. Estatísticas", "11. Gráficos e interpretações",
          "12. Conclusões", "13. Limitações"]


def _celulas():
    return json.loads(NOTEBOOK.read_text(encoding="utf-8"))["cells"]


def test_notebook_tem_introducao_e_as_secoes_da_analise_sem_saidas_gravadas():
    celulas = _celulas()
    titulos = [linha for c in celulas if c["cell_type"] == "markdown" for linha in "".join(c["source"]).splitlines() if linha.startswith("#")]
    assert titulos[0].startswith("# Análise dos indicadores do Sinesp/MJSP em Joinville/SC")  # introdução
    for secao in SECOES:
        assert any(t.startswith(f"## {secao}") for t in titulos), secao
    codigo = [c for c in celulas if c["cell_type"] == "code"]
    assert len(codigo) >= 15 and all(not c["outputs"] and c["execution_count"] is None for c in codigo)  # saídas não vão para o Git
    texto = "".join("".join(c["source"]) for c in celulas)
    assert "MODO DEMONSTRAÇÃO" in texto and "dashboard import calculos, graficos" in texto  # reutiliza os cálculos validados
    for proibido in ("fillna(", "drop_duplicates("):  # ausência nunca vira zero; nenhuma linha é apagada
        assert proibido not in texto, proibido


def test_notebook_executa_todas_as_celulas_em_ordem_sem_erro(tmp_path):
    codigo = "\n\n".join("".join(c["source"]) for c in _celulas() if c["cell_type"] == "code")
    script = tmp_path / "notebook_como_script.py"
    script.write_text("display = print\n" + codigo + "\nprint('NOTEBOOK_OK')\n", encoding="utf-8")
    ambiente = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg"}
    resultado = subprocess.run([sys.executable, str(script)], cwd=project_path("notebooks"), capture_output=True, text=True, encoding="utf-8",
                               timeout=600, env=ambiente)
    assert resultado.returncode == 0, resultado.stderr[-2000:]
    assert "NOTEBOOK_OK" in resultado.stdout and "Base aprovada: 911 observações × 6 colunas" in resultado.stdout
    assert "Zeros publicados: 401" in resultado.stdout and "Observações com chave repetida: 0" in resultado.stdout
