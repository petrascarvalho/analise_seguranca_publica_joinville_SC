"""Roteiro acadêmico ``scripts/analise_sinesp.py``: estrutura, execução sem os XLSX (demonstração) e reprodução com os XLSX.

A execução completa depende do acervo local e é pulada em um clone limpo.
"""

import ast
import os
import re
import subprocess
import sys

import pytest

from scripts.utils import project_path

ROTEIRO = project_path("scripts", "analise_sinesp.py")


def _executar(ambiente_extra: dict) -> subprocess.CompletedProcess:
    ambiente = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg", **ambiente_extra}
    return subprocess.run([sys.executable, "-m", "scripts.analise_sinesp"], cwd=project_path(), capture_output=True, text=True,
                          encoding="utf-8", timeout=600, env=ambiente)


def test_estrutura_do_roteiro_tem_as_dez_secoes_em_celulas_interativas():
    texto = ROTEIRO.read_text(encoding="utf-8")
    assert texto.count("# %%") >= 10
    titulos = re.findall(r"^# # (\d+)\. (.+)$", texto, re.MULTILINE)
    assert [int(n) for n, _ in titulos] == list(range(1, 11)), titulos
    esperados = ["Objetivo", "Leitura", "Identificação", "ETL", "Validação", "Construção", "exploratória", "Estatísticas", "Visualizações", "Conclusões"]
    for trecho, (_, titulo) in zip(esperados, titulos):
        assert trecho in titulo, (trecho, titulo)
    assert "MODO DEMONSTRAÇÃO" in texto and "NÃO reproduz a extração" in texto
    for subsecao in ("7.1", "8.1", "8.2", "9.1 Visão geral", "9.2 Evolução temporal", "9.3 Estatística descritiva", "9.4 Outliers", "9.5 Conferência"):
        assert f"# ## {subsecao}" in texto, subsecao  # quatro grupos de análise + conferência figura × tabela


def test_roteiro_e_sinesp_only_e_nao_exporta_arquivos():
    texto = ROTEIRO.read_text(encoding="utf-8")
    arvore = ast.parse(texto)
    arvore.body = arvore.body[1:]  # sem a docstring, que cita o roteiro histórico
    codigo = ast.unparse(arvore)  # só código: comentários e células markdown ficam de fora
    for proibido in (".savefig(", ".to_excel(", ".to_parquet(", "write_text(", "write_bytes(", "'wb'", "'w'", "ssp", "SSP", "Prefeitura", "pdfplumber", "violencia"):
        assert proibido not in codigo, proibido
    assert "to_csv(index=False, lineterminator=" in codigo and ".encode('utf-8')" in codigo  # CSV só em memória, para conferir o hash
    assert "from dashboard import calculos, graficos" in codigo and "graficos.figuras_sinesp_etapa10" in codigo  # reutiliza as figuras validadas
    assert "analise_seguranca_publica" in texto.split('"""')[1]  # docstring remete ao roteiro histórico, que não é o principal


def test_roteiro_executa_em_modo_demonstracao_sem_os_xlsx(tmp_path):
    resultado = _executar({"SINESP_PASTA_XLSX": str(tmp_path)})
    assert resultado.returncode == 0, resultado.stderr[-1500:]
    saida = resultado.stdout
    assert "MODO DEMONSTRAÇÃO" in saida and "NÃO reproduz a extração" in saida
    assert "Séries: 12 | observações: 911" in saida and "catálogo confere com o publicado: True" in saida
    assert "ESTA EXECUÇÃO FOI EM MODO DEMONSTRAÇÃO" in saida
    assert "homicídio doloso 21 (2025) e 25 (2026)" in saida and "62 vítimas em 2020 e 29 em 2025" in saida
    assert "Mapa de calor = tabela ano × mês: True" in saida and "Média móvel desenhada = tabela: True" in saida
    assert "Critério IQR (Tukey): informativo em 5 das 12 séries" in saida and "anos completos (2020–2025, n = 6); 2026 é parcial" in saida
    assert "Método IQR" not in saida or "não informativo" in saida  # nunca afirma anomalia sem método informativo


def test_roteiro_com_serie_sem_variacao_nao_aponta_pontos_atipicos(tmp_path):
    resultado = _executar({"SINESP_PASTA_XLSX": str(tmp_path), "SINESP_EVENTO_ESTUDO": "Roubo seguido de morte (latrocínio)"})
    assert resultado.returncode == 0, resultado.stderr[-1500:]
    assert "IQR igual a zero" in resultado.stdout and "Nenhum ponto é apresentado como atípico" in resultado.stdout
    pf = _executar({"SINESP_PASTA_XLSX": str(tmp_path), "SINESP_EVENTO_ESTUDO": "Mandado de prisão cumprido", "SINESP_ABRANGENCIA_ESTUDO": "Polícia Federal"})
    assert pf.returncode == 0, pf.stderr[-1500:]
    assert "Sazonalidade não apresentada: menos de 2 anos completos" in pf.stdout


def test_roteiro_reconstroi_a_base_aprovada_a_partir_dos_xlsx_oficiais():
    resultado = _executar({})
    assert resultado.returncode == 0, resultado.stderr[-1500:]
    saida = resultado.stdout
    if "MODO DEMONSTRAÇÃO" in saida:
        pytest.skip("XLSX oficiais da versão aprovada ausentes neste ambiente (esperado em clone limpo ou deploy).")
    assert "Total de linhas originais de Joinville/SC lidas: 911" in saida
    assert "Base reconstruída igual à publicada (valores, tipos e ordem): True" in saida
    assert "SHA-256 do CSV reconstruído = SHA-256 do manifesto: True" in saida
    assert "ESTA EXECUÇÃO FOI EM MODO DEMONSTRAÇÃO" not in saida
