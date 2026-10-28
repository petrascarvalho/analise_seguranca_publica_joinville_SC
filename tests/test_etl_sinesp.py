"""ETL principal ``scripts/etl_sinesp.py``: 18 etapas didáticas, modo demonstração sem os XLSX, reprodução da base aprovada com os
XLSX e exportação controlada (somente em dados/processados, nunca na base publicada).

A execução completa depende do acervo local e é pulada em um clone limpo.
"""

import ast
import json
import os
import re
import subprocess
import sys

import pytest

from dashboard import dados_publicos as dp
from src.pipeline.utils import project_path

ETL = project_path("scripts", "etl_sinesp.py")
ETAPAS = ["Importação das bibliotecas", "Configuração dos diretórios e caminhos", "Localização dos arquivos originais", "Leitura dos XLSX",
          "Inspeção dos dados brutos", "Identificação e descrição das colunas", "Verificação de duplicidades", "Tratamento e padronização dos dados",
          "Identificação de valores ausentes e zeros", "Seleção de Joinville/SC", "Ajustes dos tipos de dados", "Consolidação das observações mensais",
          "Validação e rastreabilidade", "Estatísticas descritivas", "Análise exploratória", "Construção dos gráficos", "Exportação controlada",
          "Conclusões e limitações"]


def _executar(ambiente_extra: dict) -> subprocess.CompletedProcess:
    ambiente = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", "MPLBACKEND": "Agg", **ambiente_extra}
    return subprocess.run([sys.executable, "-m", "scripts.etl_sinesp"], cwd=project_path(), capture_output=True, text=True,
                          encoding="utf-8", timeout=600, env=ambiente)


def _hashes_publicados() -> dict:
    return {p.name: dp.sha256_normalizado(p.read_bytes()) for p in sorted(dp.DIRETORIO_DADOS.iterdir()) if p.is_file()}


def test_etl_tem_as_18_etapas_didaticas_em_celulas_interativas():
    texto = ETL.read_text(encoding="utf-8")
    titulos = re.findall(r"^# # ETAPA (\d{2}) — (.+)$", texto, re.MULTILINE)
    assert [int(n) for n, _ in titulos] == list(range(1, 19)), titulos
    assert [t for _, t in titulos] == ETAPAS
    assert texto.count("# %%") >= 18
    for parte in ("**Objetivo:**", "**Resultado esperado:**"):
        assert texto.count(parte) >= 15, parte  # cada etapa explica objetivo e resultado esperado
    assert "MODO DEMONSTRAÇÃO" in texto and "NÃO reproduz a extração" in texto
    arvore = ast.parse(texto)
    funcoes = [n for n in arvore.body if isinstance(n, ast.FunctionDef)]
    assert funcoes and all(ast.get_docstring(f) for f in funcoes)  # toda função tem docstring (objetivo, parâmetros, retorno)


def test_etl_e_sinesp_only_e_so_exporta_para_dados_processados():
    texto = ETL.read_text(encoding="utf-8")
    arvore = ast.parse(texto)
    arvore.body = arvore.body[1:]  # sem a docstring, que cita o roteiro histórico
    codigo = ast.unparse(arvore)
    for proibido in (".to_excel(", ".to_parquet(", "ssp", "SSP", "Prefeitura", "pdfplumber", "violencia", "drop_duplicates(", "fillna("):
        assert proibido not in codigo, proibido  # sem outras fontes, sem apagar duplicados e sem trocar ausência por zero
    escritas = re.findall(r"(PASTA_\w+) / '[^']+'\)\.(?:write_bytes|write_text)|(\w+)\.to_csv\((PASTA_\w+)", codigo)
    assert escritas and all("PASTA_PROCESSADOS" in "".join(e) for e in escritas)  # todas as gravações vão para dados/processados
    assert "dp.DIRETORIO_DADOS.resolve()" in codigo  # trava contra gravar sobre a base publicada
    assert "from dashboard import calculos, graficos" in codigo
    assert "analise_seguranca_publica" in texto.split('"""')[1]  # o roteiro histórico não é o principal


def test_etl_executa_em_modo_demonstracao_sem_os_xlsx(tmp_path):
    antes = _hashes_publicados()
    resultado = _executar({"SINESP_PASTA_XLSX": str(tmp_path / "vazio"), "SINESP_PASTA_PROCESSADOS": str(tmp_path / "saida")})
    assert resultado.returncode == 0, resultado.stderr[-1500:]
    saida = resultado.stdout
    assert "MODO DEMONSTRAÇÃO" in saida and "NÃO reproduz a extração" in saida and "nada é exportado" in saida
    assert not (tmp_path / "saida").exists()  # sem extração, nada é gravado
    assert "Séries: 12 | observações: 911" in saida and "catálogo confere com o publicado: True" in saida
    assert "ESTA EXECUÇÃO FOI EM MODO DEMONSTRAÇÃO" in saida
    assert "homicídio doloso 21 (2025) e 25 (2026)" in saida and "62 vítimas em 2020 e 29 em 2025" in saida
    assert "Mapa de calor = tabela ano × mês: True" in saida and "Média móvel desenhada = tabela: True" in saida
    assert "Critério IQR (Tukey): informativo em 5 das 12 séries" in saida and "anos completos (2020–2025, n = 6); 2026 é parcial" in saida
    assert _hashes_publicados() == antes


def test_etl_com_serie_sem_variacao_nao_aponta_pontos_atipicos(tmp_path):
    resultado = _executar({"SINESP_PASTA_XLSX": str(tmp_path), "SINESP_EVENTO_ESTUDO": "Roubo seguido de morte (latrocínio)"})
    assert resultado.returncode == 0, resultado.stderr[-1500:]
    assert "IQR igual a zero" in resultado.stdout and "Nenhum ponto é apresentado como atípico" in resultado.stdout
    pf = _executar({"SINESP_PASTA_XLSX": str(tmp_path), "SINESP_EVENTO_ESTUDO": "Mandado de prisão cumprido", "SINESP_ABRANGENCIA_ESTUDO": "Polícia Federal"})
    assert pf.returncode == 0, pf.stderr[-1500:]
    assert "Sazonalidade não apresentada: menos de 2 anos completos" in pf.stdout


def test_etl_reconstroi_a_base_aprovada_e_exporta_so_em_dados_processados(tmp_path):
    antes = _hashes_publicados()
    destino = tmp_path / "processados"
    resultado = _executar({"SINESP_PASTA_PROCESSADOS": str(destino)})
    assert resultado.returncode == 0, resultado.stderr[-1500:]
    saida = resultado.stdout
    if "MODO DEMONSTRAÇÃO" in saida:
        pytest.skip("XLSX oficiais da versão aprovada ausentes neste ambiente (esperado em clone limpo ou deploy).")
    assert "Total de linhas originais de Joinville/SC lidas: 911" in saida
    assert "Linhas totalmente idênticas: 0" in saida and "Zeros publicados após o tratamento: 401" in saida and "Valores ausentes após o tratamento: 0" in saida
    assert "Todas as linhas são de SC: True | todas são de JOINVILLE: True" in saida
    assert "Base reconstruída igual à publicada (valores, tipos e ordem): True" in saida
    assert "SHA-256 do CSV reconstruído = SHA-256 do manifesto: True" in saida
    assert sorted(p.name for p in destino.iterdir()) == ["etl_catalogo_series.csv", "etl_recorte_joinville_bruto.csv", "etl_relatorio.json", "etl_sinesp_joinville_mensal.csv"]
    assert (destino / "etl_sinesp_joinville_mensal.csv").read_bytes().replace(b"\r\n", b"\n") == (dp.DIRETORIO_DADOS / dp.ARQ_SINESP).read_bytes().replace(b"\r\n", b"\n")
    relatorio = json.loads((destino / "etl_relatorio.json").read_text(encoding="utf-8"))
    assert relatorio["observacoes"] == 911 and relatorio["series"] == 12 and relatorio["zeros_publicados"] == 401 and relatorio["igual_a_base_publicada"] is True
    assert relatorio["versao_publicada"] == "20261027T114400Z" and len(relatorio["xlsx"]) == 7
    assert _hashes_publicados() == antes  # a base publicada não foi tocada
