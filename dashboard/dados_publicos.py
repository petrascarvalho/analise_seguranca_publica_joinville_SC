"""Carregamento e validação dos arquivos mínimos do dashboard — fonte única: Sinesp/MJSP (sem Streamlit).

Os arquivos ficam em dashboard/data_publica/ e são contagens municipais agregadas de Joinville/SC, já
auditadas no roteiro acadêmico e no fluxo de atualização controlada. Nenhuma função aqui lê dados/ (acervo
bruto local): o dashboard deve funcionar em um clone limpo.

Qualquer arquivo ausente, esquema divergente ou valor inválido gera ErroDados com mensagem explícita;
nada é preenchido ou corrigido. Ausência de valor é preservada (<NA>) e nunca vira zero.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pandas as pd

# Pasta com os arquivos aprovados que o painel lê (a base publicada; somente leitura).
DIRETORIO_DADOS = Path(__file__).resolve().parent / "data_publica"

# Nomes dos arquivos e colunas esperadas: se algo mudar, a leitura para com erro (nada é corrigido em silêncio).
ARQ_SINESP = "sinesp_joinville_mensal.csv"
ARQ_SINESP_CATALOGO = "sinesp_catalogo_indicadores.csv"
ARQ_MANIFESTO = "manifesto_dados_publicos.json"
ARQUIVOS_DE_DADOS = (ARQ_SINESP, ARQ_SINESP_CATALOGO)

COLUNAS_SINESP = ["ano", "mes", "evento", "abrangencia", "unidade", "valor"]
COLUNAS_CATALOGO = [
    "evento", "abrangencia", "unidade", "natureza", "medida_origem", "inicio", "fim",
    "meses_observados", "meses_com_valor", "meses_valor_zero", "meses_sem_valor", "limitacoes",
]
ANOS_SINESP = tuple(range(2020, 2036))  # a cobertura real (última competência) vem dos dados e do manifesto
UNIDADE_VITIMAS = "vítimas"
UNIDADE_MANDADOS = "mandados cumpridos (contagem publicada)"


class ErroDados(Exception):
    """Dados do dashboard ausentes, incompatíveis ou inválidos."""


def sha256_normalizado(conteudo: bytes) -> str:
    """SHA-256 do conteúdo com fins de linha normalizados para LF.

    A normalização evita falso alarme quando o Git converte LF/CRLF no checkout.
    """
    return hashlib.sha256(conteudo.replace(b"\r\n", b"\n")).hexdigest()


def _ler_texto(nome: str, diretorio: Path) -> pd.DataFrame:
    """Lê um CSV da base publicada como texto (sem converter nada); erro claro se faltar ou estiver malformado."""
    caminho = Path(diretorio) / nome
    if not caminho.is_file():
        raise ErroDados(
            f"Arquivo de dados não encontrado: {nome}. Restaure dashboard/data_publica/ ou gere os dados com "
            "`python -m src.pipeline.atualizacao_dados` (requer os XLSX oficiais do Sinesp)."
        )
    try:
        return pd.read_csv(caminho, dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8")
    except (pd.errors.ParserError, UnicodeDecodeError, pd.errors.EmptyDataError) as erro:
        raise ErroDados(f"Arquivo ilegível ou malformado: {nome} ({erro}).") from erro


def _exigir_colunas(quadro: pd.DataFrame, colunas: list[str], nome: str) -> None:
    """Confere se as colunas do arquivo são exatamente as esperadas, na mesma ordem."""
    if list(quadro.columns) != colunas:
        raise ErroDados(f"Esquema inesperado em {nome}: esperado {colunas}, encontrado {list(quadro.columns)}.")


def _inteiro(serie: pd.Series, campo: str, nome: str, *, permitir_vazio: bool) -> pd.Series:
    """Converte uma coluna de texto em inteiros; vazio vira ausente (se permitido) e qualquer outro valor inválido interrompe."""
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
    """Valida e tipa a série mensal Sinesp (texto → tipos). Ausência permanece <NA>."""
    # 1. Colunas certas e tipos: ano e mês são inteiros; "valor" vazio continua vazio (ausência não vira zero).
    _exigir_colunas(quadro, COLUNAS_SINESP, nome)
    saida = quadro.copy()
    saida["ano"] = _inteiro(saida["ano"], "ano", nome, permitir_vazio=False)
    saida["mes"] = _inteiro(saida["mes"], "mes", nome, permitir_vazio=False)
    saida["valor"] = _inteiro(saida["valor"], "valor", nome, permitir_vazio=True)
    # 2. Regras de qualidade: textos preenchidos, ano e mês válidos, sem competência repetida,
    #    sem lacuna de meses em cada série e uma única unidade por série.
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
    """Confere as colunas do catálogo e se não há série repetida (indicador + classificação)."""
    _exigir_colunas(quadro, COLUNAS_CATALOGO, nome)
    if quadro.duplicated(["evento", "abrangencia"]).any():
        raise ErroDados(f"{nome}: combinação evento/abrangência repetida.")
    return quadro.reset_index(drop=True)


def validar_consistencia(sinesp: pd.DataFrame, catalogo: pd.DataFrame) -> None:
    """Catálogo e série mensal devem descrever exatamente as mesmas séries, unidades e contagens."""
    # Mesmas séries nos dois arquivos; depois, as contagens do catálogo são recalculadas e comparadas com a série mensal.
    series_dados = set(zip(sinesp["evento"], sinesp["abrangencia"]))
    series_catalogo = set(zip(catalogo["evento"], catalogo["abrangencia"]))
    if series_dados != series_catalogo:
        raise ErroDados(f"Catálogo e série mensal descrevem séries diferentes: só nos dados {sorted(series_dados - series_catalogo)}; "
                        f"só no catálogo {sorted(series_catalogo - series_dados)}.")
    cat = catalogo.set_index(["evento", "abrangencia"])
    for (evento, abrangencia), serie in sinesp.groupby(["evento", "abrangencia"]):
        ficha = cat.loc[(evento, abrangencia)]
        esperado = (str(len(serie)), str(int(serie["valor"].notna().sum())), str(int(serie["valor"].eq(0).sum())), str(int(serie["valor"].isna().sum())),
                    serie["unidade"].iloc[0])
        informado = (ficha["meses_observados"], ficha["meses_com_valor"], ficha["meses_valor_zero"], ficha["meses_sem_valor"], ficha["unidade"])
        if esperado != informado:
            raise ErroDados(f"Catálogo inconsistente com a série {evento}/{abrangencia}: esperado {esperado}, informado {informado}.")


def carregar_sinesp(diretorio: Path = DIRETORIO_DADOS) -> pd.DataFrame:
    """Lê e valida a série mensal do Sinesp publicada no painel."""
    return validar_sinesp(_ler_texto(ARQ_SINESP, diretorio))


def carregar_catalogo_sinesp(diretorio: Path = DIRETORIO_DADOS) -> pd.DataFrame:
    """Lê e valida o catálogo de indicadores do Sinesp."""
    return validar_catalogo(_ler_texto(ARQ_SINESP_CATALOGO, diretorio))


def carregar_manifesto(diretorio: Path = DIRETORIO_DADOS) -> dict:
    """Lê o manifesto da versão publicada (hashes, cobertura e origem dos dados)."""
    caminho = Path(diretorio) / ARQ_MANIFESTO
    if not caminho.is_file():
        raise ErroDados(f"Manifesto não encontrado: {ARQ_MANIFESTO}.")
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as erro:
        raise ErroDados(f"Manifesto inválido: {erro}.") from erro


def verificar_integridade(diretorio: Path = DIRETORIO_DADOS) -> pd.DataFrame:
    """Compara linhas/colunas e SHA-256 dos arquivos de dados com o manifesto."""
    # Para cada arquivo do manifesto: ele existe? O SHA-256 de agora é igual ao registrado?
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
