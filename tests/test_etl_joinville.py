"""ETL único scripts/etl_joinville.py: roteiro básico em 14 etapas, sem funções próprias, que reproduz a base aprovada do Sinesp e o
tratamento da SSP/SC e grava somente em uma pasta de saída própria (nunca na base publicada no painel).

A execução completa depende do acervo local (XLSX do Sinesp e PDFs da SSP/SC) e é pulada em um clone limpo.
"""

import ast
import json
import os
import re
import subprocess
import sys

import pandas as pd
import pytest

from dashboard import dados_publicos as dp
from src.pipeline import ssp_sc
from src.pipeline.utils import project_path

ETL = project_path("scripts", "etl_joinville.py")
ETAPAS = ["IMPORTAÇÃO DAS BIBLIOTECAS", "DEFINIÇÃO DAS PASTAS", "LEITURA DOS DADOS BRUTOS DO SINESP", "INSPEÇÃO DOS DATAFRAMES",
          "VERIFICAÇÃO DE DUPLICIDADES", "VERIFICAÇÃO DE VALORES AUSENTES", "TRATAMENTO DOS DADOS", "FILTRO DO MUNICÍPIO DE JOINVILLE",
          "ORGANIZAÇÃO DOS INDICADORES SINESP", "CONFERÊNCIA DOS RESULTADOS", "LEITURA DOS DADOS SSP/SC", "TRATAMENTO E CONFERÊNCIA DA SSP/SC",
          "EXPORTAÇÃO DOS DADOS TRATADOS", "VALIDAÇÕES FINAIS"]


def _executar(ambiente_extra: dict) -> subprocess.CompletedProcess:
    ambiente = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONIOENCODING": "utf-8", **ambiente_extra}
    return subprocess.run([sys.executable, str(ETL)], cwd=project_path(), capture_output=True, text=True, encoding="utf-8", timeout=900, env=ambiente)


def _hashes_publicados() -> dict:
    return {p.name: dp.sha256_normalizado(p.read_bytes()) for p in sorted(dp.DIRETORIO_DADOS.iterdir()) if p.is_file()}


def test_etl_tem_14_etapas_com_comentarios_numerados_e_e_um_roteiro_basico():
    texto = ETL.read_text(encoding="utf-8")
    titulos = re.findall(r"^# (\d{1,2})\. ([A-ZÀ-Ú /]+)$", texto, re.MULTILINE)  # comentários numerados: "# 1. IMPORTAÇÃO DAS BIBLIOTECAS"
    assert [int(n) for n, _ in titulos] == list(range(1, 15)), titulos
    assert [t for _, t in titulos] == ETAPAS
    arvore = ast.parse(texto)
    # Programação básica e sequencial: nenhuma função, classe ou decorator próprios.
    assert not [n for n in ast.walk(arvore) if isinstance(n, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef))]
    codigo = [l for l in texto.splitlines() if l.strip() and not l.lstrip().startswith("#")]
    assert len(codigo) < 220  # roteiro curto: menos de 220 linhas de código (os comentários explicativos não contam)
    assert texto.count("#") > 60  # comentado em português com #
    assert "Pandas" in texto and "display" in texto and "print(" in texto  # funciona no Interactive e como programa


def test_etl_grava_so_na_pasta_de_saida_e_nunca_apaga_nem_inventa_dados():
    texto = ETL.read_text(encoding="utf-8")
    codigo = ast.unparse(ast.parse(texto))
    for proibido in (".to_excel(", ".to_parquet(", "fillna(", "inplace=True", "graficos", "calculos", "pdfplumber"):
        assert proibido not in codigo, proibido  # sem trocar ausência por zero e sem a análise (que fica no notebook)
    assert not re.search(r"dados_\w+ = dados_\w+\.drop_duplicates", codigo)  # nenhuma linha é apagada (drop_duplicates só conta meses distintos)
    assert "pasta_saida.resolve() != dp.DIRETORIO_DADOS.resolve()" in codigo  # trava contra gravar sobre a base publicada
    gravacoes = re.findall(r"(?:to_csv|write_bytes|write_text)\((pasta_\w+)", codigo.replace("\n", " "))
    assert gravacoes and all(g in ("pasta_sinesp", "pasta_ssp") for g in gravacoes)  # só as duas subpastas da saída
    assert "merge(" not in codigo and "pd.concat([" not in codigo  # Sinesp e SSP/SC nunca são juntados
    assert "Fato Comunicado" in texto and "não é tratada como vítimas" in texto  # a unidade da SSP/SC não é reinterpretada


def test_etl_sem_os_xlsx_oficiais_para_com_mensagem_clara_e_nao_grava(tmp_path):
    antes = _hashes_publicados()
    saida = tmp_path / "saida"
    resultado = _executar({"SINESP_PASTA_XLSX": str(tmp_path / "vazio"), "ETL_PASTA_SAIDA": str(saida)})
    assert resultado.returncode != 0
    assert "FileNotFoundError" in resultado.stderr and "XLSX de 2020 não encontrado" in resultado.stderr
    assert not saida.exists()  # nada é gravado sem a leitura dos originais
    assert _hashes_publicados() == antes


def test_etl_reproduz_a_base_aprovada_do_sinesp_e_a_ssp_sc_e_grava_so_na_saida(tmp_path):
    if not ssp_sc.acervo_disponivel() or not list(project_path("dados", "brutos", "sinesp").rglob("bancovde-2020.xlsx")):
        pytest.skip("Acervo oficial (XLSX do Sinesp e PDFs da SSP/SC) ausente neste ambiente (esperado em clone limpo ou deploy).")
    antes = _hashes_publicados()
    saida = tmp_path / "saida"
    resultado = _executar({"ETL_PASTA_SAIDA": str(saida)})
    assert resultado.returncode == 0, resultado.stderr[-1500:]
    texto = resultado.stdout
    for esperado in ("Linhas totalmente idênticas: 0", "Todas as linhas são de JOINVILLE: True", "Valores ausentes: 0 | zeros publicados: 401",
                     "Base reconstruída igual à publicada: True", "SHA-256 reconstruído igual ao do manifesto: True", "Catálogo igual ao publicado: True",
                     "Violência doméstica: 216 observações | 9 categorias | 24 meses | zeros publicados: 27 | ausentes: 0",
                     "Verificações contra os PDFs: 159 aprovadas de 159", "ETL concluído sem divergências."):
        assert esperado in texto, esperado
    assert sorted(p.relative_to(saida).as_posix() for p in saida.rglob("*") if p.is_file()) == [
        "sinesp/etl_catalogo_series.csv", "sinesp/etl_recorte_joinville_bruto.csv", "sinesp/etl_relatorio.json", "sinesp/etl_sinesp_joinville_mensal.csv",
        "ssp_sc/homicidios_boletins_joinville_versoes.csv", "ssp_sc/homicidios_republicacoes_grupos.csv", "ssp_sc/inventario_acervo_ssp_sc.csv",
        "ssp_sc/rastreabilidade_celulas_ssp_sc.csv", "ssp_sc/relatorio_auditoria_ssp_sc.json", "ssp_sc/verificacoes_extracao_ssp_sc.csv",
        "ssp_sc/violencia_domestica_joinville_tratada.csv"]
    # Sinesp: a base reconstruída é a publicada (byte a byte, ignorando só o tipo de quebra de linha) e o relatório confere o manifesto.
    mensal = (saida / "sinesp" / "etl_sinesp_joinville_mensal.csv").read_bytes().replace(b"\r\n", b"\n")
    assert mensal == (dp.DIRETORIO_DADOS / dp.ARQ_SINESP).read_bytes().replace(b"\r\n", b"\n")
    relatorio = json.loads((saida / "sinesp" / "etl_relatorio.json").read_text(encoding="utf-8"))
    assert relatorio["observacoes"] == 911 and relatorio["series"] == 12 and relatorio["zeros_publicados"] == 401 and relatorio["valores_ausentes"] == 0
    assert relatorio["igual_a_base_publicada"] is True and relatorio["versao_publicada"] == "20261027T114400Z" and len(relatorio["xlsx"]) == 7
    # SSP/SC: 216 observações, 9 categorias × 24 meses, 27 zeros, unidade preservada; as 41 republicações divergentes seguem sem versão escolhida.
    vd = pd.read_csv(saida / "ssp_sc" / "violencia_domestica_joinville_tratada.csv")
    assert len(vd) == 216 and vd["indicador"].nunique() == 9 and int(vd["valor"].eq(0).sum()) == 27 and set(vd["unidade"]) == {"Fato Comunicado"}
    auditoria = json.loads((saida / "ssp_sc" / "relatorio_auditoria_ssp_sc.json").read_text(encoding="utf-8"))
    assert auditoria["verificacoes_aprovadas"] == "159 de 159" and auditoria["originais_inalterados"] is True
    assert auditoria["homicidios"]["grupos_republicados"] == 58 and auditoria["homicidios"]["grupos_divergentes"] == 41
    assert _hashes_publicados() == antes  # a base publicada no painel não foi tocada


def test_nenhum_python_ativo_usa_marcador_de_celula_nem_markdown_nos_comentarios():
    marcador = "# " + "%%"  # montado em duas partes para este arquivo não contar a si mesmo
    arquivos = [ETL, *project_path("scripts").glob("*.py"), *project_path("dashboard").rglob("*.py"), *project_path("src").rglob("*.py")]
    for arquivo in arquivos:
        texto = arquivo.read_text(encoding="utf-8")
        assert marcador not in texto, arquivo.name  # comentários comuns com #, sem marcadores de célula
        comentarios = [linha for linha in texto.splitlines() if linha.lstrip().startswith("#")]
        assert not [c for c in comentarios if "**" in c or "`" in c or c.lstrip().startswith("# #")], arquivo.name  # sem Markdown nos comentários
