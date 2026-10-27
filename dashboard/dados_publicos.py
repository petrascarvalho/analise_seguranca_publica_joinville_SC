"""Carregamento e validação dos arquivos mínimos do dashboard (sem Streamlit).

Os arquivos ficam em ``dashboard/data_publica/`` e são contagens municipais
agregadas já auditadas no roteiro acadêmico. Nenhuma função aqui lê ``dados/``
(acervo bruto local): o dashboard deve funcionar em um clone limpo.

Qualquer arquivo ausente, esquema divergente ou valor inválido gera
``ErroDados`` com mensagem explícita; nada é preenchido ou corrigido.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

DIRETORIO_DADOS = Path(__file__).resolve().parent / "data_publica"

ARQ_SINESP = "sinesp_joinville_mensal.csv"
ARQ_SINESP_CATALOGO = "sinesp_catalogo_indicadores.csv"
ARQ_VD = "ssp_violencia_domestica_joinville.csv"
ARQ_VD_RASTREIO = "ssp_violencia_domestica_rastreabilidade.csv"
ARQ_MANIFESTO = "manifesto_dados_publicos.json"
ARQUIVOS_DE_DADOS = (ARQ_SINESP, ARQ_SINESP_CATALOGO, ARQ_VD, ARQ_VD_RASTREIO)

COLUNAS_SINESP = ["ano", "mes", "evento", "abrangencia", "unidade", "valor"]
COLUNAS_CATALOGO = [
    "evento", "abrangencia", "unidade", "natureza", "medida_origem", "inicio", "fim",
    "meses_observados", "meses_com_valor", "meses_valor_zero", "meses_sem_valor", "limitacoes",
]
COLUNAS_VD = ["municipio", "ano", "mes", "categoria", "fatos_comunicados"]
COLUNAS_VD_RASTREIO = [
    "municipio", "ano", "mes", "categoria", "arquivo_pdf", "pagina_pdf", "tabela_pdf", "linha_tabela",
    "coluna_csv", "rotulo_original_categoria", "cabecalho_mes_original", "valor_textual_original",
]
CATEGORIAS_VD = (
    "Ameaça", "Calúnia", "Difamação", "Estupro", "Injúria", "Injúria real",
    "Lesão corporal grave ou gravíssima dolosa", "Lesão corporal leve dolosa", "Vias de fato",
)
ANOS_SINESP = tuple(range(2020, 2036))  # a cobertura real (última competência) vem dos dados e do manifesto
UNIDADE_VD = "Fato Comunicado"


class ErroDados(Exception):
    """Dados do dashboard ausentes, incompatíveis ou inválidos."""


def sha256_normalizado(conteudo: bytes) -> str:
    """SHA-256 do conteúdo com fins de linha normalizados para LF.

    A normalização evita falso alarme quando o Git converte LF/CRLF no checkout.
    """
    return hashlib.sha256(conteudo.replace(b"\r\n", b"\n")).hexdigest()


def _ler_texto(nome: str, diretorio: Path) -> pd.DataFrame:
    caminho = Path(diretorio) / nome
    if not caminho.is_file():
        raise ErroDados(
            f"Arquivo de dados não encontrado: {nome}. Gere os arquivos com "
            "`python -m scripts.gerar_dados_dashboard` ou restaure dashboard/data_publica/."
        )
    try:
        return pd.read_csv(caminho, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8")
    except (pd.errors.ParserError, UnicodeDecodeError, pd.errors.EmptyDataError) as erro:
        raise ErroDados(f"Arquivo ilegível ou malformado: {nome} ({erro}).") from erro


def _exigir_colunas(quadro: pd.DataFrame, colunas: list[str], nome: str) -> None:
    if list(quadro.columns) != colunas:
        raise ErroDados(f"Esquema inesperado em {nome}: esperado {colunas}, encontrado {list(quadro.columns)}.")


def _inteiro(serie: pd.Series, campo: str, nome: str, *, permitir_vazio: bool) -> pd.Series:
    valores = []
    for posicao, texto in enumerate(serie.tolist()):
        if texto == "":
            if not permitir_vazio:
                raise ErroDados(f"{nome}: valor vazio em '{campo}' (linha {posicao + 2}); não é permitido.")
            valores.append(pd.NA)
            continue
        if not (texto.isascii() and texto.isdigit()):
            raise ErroDados(f"{nome}: valor inválido em '{campo}' (linha {posicao + 2}): {texto!r}; esperado inteiro não negativo.")
        valores.append(int(texto))
    return pd.Series(valores, index=serie.index, dtype="Int64")


def validar_sinesp(quadro: pd.DataFrame, nome: str = ARQ_SINESP) -> pd.DataFrame:
    """Valida e tipa a série mensal Sinesp (texto → tipos). Ausência permanece ``<NA>``."""
    _exigir_colunas(quadro, COLUNAS_SINESP, nome)
    saida = quadro.copy()
    saida["ano"] = _inteiro(saida["ano"], "ano", nome, permitir_vazio=False)
    saida["mes"] = _inteiro(saida["mes"], "mes", nome, permitir_vazio=False)
    saida["valor"] = _inteiro(saida["valor"], "valor", nome, permitir_vazio=True)
    for campo in ("evento", "abrangencia", "unidade"):
        if (saida[campo].str.strip() == "").any():
            raise ErroDados(f"{nome}: campo '{campo}' vazio.")
    if not saida["ano"].isin(ANOS_SINESP).all():
        raise ErroDados(f"{nome}: ano fora de {ANOS_SINESP[0]}–{ANOS_SINESP[-1]}.")
    if not saida["mes"].between(1, 12).all():
        raise ErroDados(f"{nome}: mês fora de 1–12.")
    if saida.duplicated(["evento", "abrangencia", "ano", "mes"]).any():
        raise ErroDados(f"{nome}: competências repetidas na mesma série (evento, abrangência, ano, mês).")
    for (evento, abrangencia), serie in saida.groupby(["evento", "abrangencia"]):
        indices = sorted((serie["ano"] * 12 + serie["mes"] - 1).astype(int).tolist())
        if indices != list(range(indices[0], indices[0] + len(indices))):
            raise ErroDados(f"{nome}: lacuna de competências na série {evento}/{abrangencia}.")
    if (saida.groupby(["evento", "abrangencia"])["unidade"].nunique() > 1).any():
        raise ErroDados(f"{nome}: uma mesma série com mais de uma unidade (vítimas e mandados não podem ser misturados).")
    return saida.reset_index(drop=True)


def validar_catalogo(quadro: pd.DataFrame, nome: str = ARQ_SINESP_CATALOGO) -> pd.DataFrame:
    _exigir_colunas(quadro, COLUNAS_CATALOGO, nome)
    if quadro.duplicated(["evento", "abrangencia"]).any():
        raise ErroDados(f"{nome}: combinação evento/abrangência repetida.")
    return quadro.reset_index(drop=True)


def validar_violencia_domestica(quadro: pd.DataFrame, nome: str = ARQ_VD) -> pd.DataFrame:
    """Valida as 216 observações: 24 competências × 9 categorias, inteiros não negativos, sem lacunas."""
    _exigir_colunas(quadro, COLUNAS_VD, nome)
    saida = quadro.copy()
    saida["ano"] = _inteiro(saida["ano"], "ano", nome, permitir_vazio=False)
    saida["mes"] = _inteiro(saida["mes"], "mes", nome, permitir_vazio=False)
    saida["fatos_comunicados"] = _inteiro(saida["fatos_comunicados"], "fatos_comunicados", nome, permitir_vazio=False)
    if not (saida["municipio"] == "JOINVILLE").all():
        raise ErroDados(f"{nome}: município diferente de JOINVILLE.")
    if not saida["ano"].isin([2023, 2024]).all():
        raise ErroDados(f"{nome}: ano fora de 2023–2024.")
    if not saida["mes"].between(1, 12).all():
        raise ErroDados(f"{nome}: mês fora de 1–12.")
    desconhecidas = sorted(set(saida["categoria"]) - set(CATEGORIAS_VD))
    if desconhecidas:
        raise ErroDados(f"{nome}: categoria desconhecida: {desconhecidas}.")
    if saida.duplicated(["municipio", "ano", "mes", "categoria"]).any():
        raise ErroDados(f"{nome}: chave (município, ano, mês, categoria) repetida.")
    esperadas = {(a, m, c) for a in (2023, 2024) for m in range(1, 13) for c in CATEGORIAS_VD}
    presentes = set(zip(saida["ano"], saida["mes"], saida["categoria"]))
    if presentes != esperadas:
        raise ErroDados(f"{nome}: grade incompleta (faltam {len(esperadas - presentes)}, sobram {len(presentes - esperadas)} competências/categorias).")
    return saida.reset_index(drop=True)


def validar_rastreio_vd(quadro: pd.DataFrame, nome: str = ARQ_VD_RASTREIO) -> pd.DataFrame:
    _exigir_colunas(quadro, COLUNAS_VD_RASTREIO, nome)
    saida = quadro.copy()
    saida["ano"] = _inteiro(saida["ano"], "ano", nome, permitir_vazio=False)
    saida["mes"] = _inteiro(saida["mes"], "mes", nome, permitir_vazio=False)
    if saida.duplicated(["municipio", "ano", "mes", "categoria"]).any():
        raise ErroDados(f"{nome}: chave repetida.")
    return saida.reset_index(drop=True)


def carregar_sinesp(diretorio: Path = DIRETORIO_DADOS) -> pd.DataFrame:
    return validar_sinesp(_ler_texto(ARQ_SINESP, diretorio))


def carregar_catalogo_sinesp(diretorio: Path = DIRETORIO_DADOS) -> pd.DataFrame:
    return validar_catalogo(_ler_texto(ARQ_SINESP_CATALOGO, diretorio))


def carregar_violencia_domestica(diretorio: Path = DIRETORIO_DADOS) -> pd.DataFrame:
    return validar_violencia_domestica(_ler_texto(ARQ_VD, diretorio))


def carregar_rastreio_vd(diretorio: Path = DIRETORIO_DADOS) -> pd.DataFrame:
    return validar_rastreio_vd(_ler_texto(ARQ_VD_RASTREIO, diretorio))


def carregar_manifesto(diretorio: Path = DIRETORIO_DADOS) -> dict:
    caminho = Path(diretorio) / ARQ_MANIFESTO
    if not caminho.is_file():
        raise ErroDados(f"Manifesto não encontrado: {ARQ_MANIFESTO}.")
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ErroDados(f"Manifesto inválido: {erro}.") from erro


def verificar_integridade(diretorio: Path = DIRETORIO_DADOS) -> pd.DataFrame:
    """Compara tamanho de linhas/colunas e SHA-256 dos arquivos com o manifesto."""
    manifesto = carregar_manifesto(diretorio)
    linhas = []
    for ficha in manifesto.get("arquivos", []):
        caminho = Path(diretorio) / ficha["arquivo"]
        existe = caminho.is_file()
        hash_atual = sha256_normalizado(caminho.read_bytes()) if existe else None
        linhas.append({
            "arquivo": ficha["arquivo"], "existe": existe, "linhas_manifesto": ficha["linhas"], "colunas_manifesto": ficha["colunas"],
            "sha256_manifesto": ficha["sha256"], "sha256_atual": hash_atual, "integro": bool(existe and hash_atual == ficha["sha256"]),
        })
    return pd.DataFrame(linhas)
