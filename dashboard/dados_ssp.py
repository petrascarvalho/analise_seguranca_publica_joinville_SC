"""Leitura leve da violência doméstica SSP/SC (216 observações) para a seção própria do painel.

Esta leitura NÃO importa src/pipeline/ssp_sc.py (que lê PDFs): só abre um CSV pequeno já tratado e auditado.
O CSV pode estar em dois lugares, nesta ordem:
    1. dashboard/data_publica/ssp_sc_violencia_domestica.csv  → só existiria depois de uma autorização de publicação (hoje NÃO existe);
    2. dados/processados/ssp_sc/violencia_domestica_joinville_tratada.csv → arquivo local do ETL (fora do Git; não vai para o Cloud).
Se nenhum existir (por exemplo, no Streamlit Cloud), a função devolve None e a seção explica a limitação.
A fonte continua EM VALIDAÇÃO: "Fato Comunicado" não tem definição operacional confirmada.
"""

from pathlib import Path

import pandas as pd

# Pasta do projeto (uma acima de dashboard/).
RAIZ = Path(__file__).resolve().parents[1]
# Lugares onde o CSV pode estar, em ordem de preferência; o primeiro que existir é usado.
CAMINHOS = [
    RAIZ / "dashboard" / "data_publica" / "ssp_sc_violencia_domestica.csv",
    RAIZ / "dados" / "processados" / "ssp_sc" / "violencia_domestica_joinville_tratada.csv",
]
UNIDADE = "Fato Comunicado"
# Figura-resumo versionada no Git: é o que aparece quando o CSV não está disponível (Streamlit Cloud).
FIGURA_ESTATICA = RAIZ / "documentacao" / "graficos" / "analises" / "07-sspsc_violencia_domestica_2023_2024.png"


class ErroDadosSsp(Exception):
    """Dados da SSP/SC ausentes das regras esperadas (216 linhas, 9 categorias, 24 meses, sem repetição)."""


def caminho_disponivel() -> Path | None:
    """Primeiro CSV existente da lista, ou None."""
    for caminho in CAMINHOS:
        # is_file() verifica se o arquivo existe no computador.
        if caminho.is_file():
            return caminho
    return None


def carregar_violencia_domestica() -> pd.DataFrame | None:
    """Devolve ano, mes, categoria, valor (Fato Comunicado) ou None se o arquivo não existir. Levanta ErroDadosSsp se violar as regras."""
    caminho = caminho_disponivel()
    if caminho is None:
        return None
    # Lê o CSV e cria um DataFrame (tabela) com todas as colunas do arquivo.
    bruto = pd.read_csv(caminho, encoding="utf-8")
    colunas = ["ano", "mes", "indicador", "unidade", "valor"]
    # Lista das colunas esperadas que não estão no arquivo (deve ficar vazia).
    faltam = [c for c in colunas if c not in bruto.columns]
    if faltam:
        raise ErroDadosSsp(f"Colunas ausentes em {caminho.name}: {faltam}")
    # A coluna "indicador" já traz as 9 categorias com a grafia normalizada ("Violência doméstica — Ameaça"); tiramos o prefixo.
    # Seleciona só as colunas usadas (lista de nomes entre colchetes) e faz uma cópia.
    dados = bruto[["ano", "mes", "indicador", "unidade", "valor"]].copy()
    dados["categoria"] = dados["indicador"].str.replace("Violência doméstica — ", "", regex=False)
    # Regras: uma unidade só, nenhuma ausência (ausente nunca vira zero), nenhuma chave repetida e a grade completa 9 categorias × 24 meses.
    if set(dados["unidade"]) != {UNIDADE}:
        raise ErroDadosSsp(f"Unidade inesperada: {sorted(set(dados['unidade']))}")
    # isna().any() é verdadeiro se existir algum valor ausente; (< 0).any(), se existir algum negativo.
    if dados["valor"].isna().any() or (dados["valor"] < 0).any():
        raise ErroDadosSsp("Valores ausentes ou negativos")
    # duplicated marca linhas que repetem categoria + ano + mês; nenhuma pode se repetir.
    if dados.duplicated(["categoria", "ano", "mes"]).any():
        raise ErroDadosSsp("Chave categoria × ano × mês repetida")
    # Grade completa: quantidade de linhas = categorias distintas x meses distintos (9 x 24 = 216).
    if len(dados) != dados["categoria"].nunique() * dados[["ano", "mes"]].drop_duplicates().shape[0]:
        raise ErroDadosSsp("A grade categoria × mês está incompleta")
    dados["valor"] = dados["valor"].astype("int64")
    # Devolve só as colunas usadas, ordenadas por categoria, ano e mês; reset_index renumera as linhas a partir de 0.
    return dados[["ano", "mes", "categoria", "valor"]].sort_values(["categoria", "ano", "mes"]).reset_index(drop=True)
