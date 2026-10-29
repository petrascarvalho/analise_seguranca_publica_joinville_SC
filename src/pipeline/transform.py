"""Leitura dos XLSX anuais do Sinesp/MJSP: percorre o XML da planilha e devolve só as linhas de SC/JOINVILLE.

Cada XLSX nacional tem cerca de 24 MB; pd.read_excel carregaria o país inteiro. Estas funções são usadas por
atualizacao_dados.ler_sinesp_xlsx, que o ETL (scripts/etl_joinville.py) e a atualização controlada chamam.
"""

from __future__ import annotations

# re: busca de padrões no texto do XML; ZipFile: abre o XLSX (um ZIP); lxml.etree: lê os elementos XML de cada linha.
import re
from pathlib import Path
from zipfile import ZipFile

from lxml import etree

# As 14 colunas oficiais do XLSX, na ordem do arquivo; qualquer mudança de nome ou de ordem interrompe a leitura.
HEADERS = [
    "uf", "municipio", "evento", "data_referencia", "agente", "arma",
    "faixa_etaria", "feminino", "masculino", "nao_informado",
    "total_vitima", "total", "total_peso", "abrangencia",
]
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _cell_value(cell, shared_strings: list[str]):
    """Valor de uma célula do XML da planilha (texto, número ou verdadeiro/falso)."""
    # O atributo t diz o tipo da célula: s = texto compartilhado, inlineStr = texto na própria célula, b = verdadeiro/falso; sem t = número.
    kind = cell.get("t")
    if kind == "inlineStr":
        return "".join(cell.itertext())
    node = cell.find(NS + "v")
    if node is None:
        return None
    raw = node.text
    if raw is None:
        return None
    if kind == "s":
        return shared_strings[int(raw)]
    if kind in ("str", "e"):
        return raw
    if kind == "b":
        return raw == "1"
    number = float(raw)
    return int(number) if number.is_integer() else number


def _parse_sheet_row(raw_row: bytes):
    """Transforma o texto XML de uma linha da planilha em um elemento que pode ser lido."""
    # Atributos de extensão como x14ac:dyDescent dependem de declarações
    # herdadas do XML da planilha; o fragmento isolado não precisa deles.
    raw_row = re.sub(rb'\s+x14ac:[\w]+="[^"]*"', b"", raw_row)
    return etree.fromstring(
        raw_row.replace(
            b"<row ",
            b'<row xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ',
            1,
        )
    )


def _shared_strings(archive: ZipFile) -> list[str]:
    """Lista dos textos compartilhados do XLSX (a planilha guarda cada texto uma vez e as células apontam para ele)."""
    if "xl/sharedStrings.xml" not in archive.namelist():
        return []
    # Lista de todos os textos da planilha; as células de texto guardam só a posição nessa lista.
    root = etree.fromstring(archive.read("xl/sharedStrings.xml"))
    return ["".join(node.itertext()) for node in root.findall(NS + "si")]


def _joinville_rows(source: Path) -> list[list[object]]:
    """Lê apenas as linhas Joinville no XML do XLSX para reduzir tempo e memória."""
    rows = []
    with ZipFile(source) as archive:
        shared_strings = _shared_strings(archive)
        # Posições da palavra JOINVILLE na lista de textos (para achar as linhas sem converter o arquivo inteiro).
        joinville_shared_ids = [
            str(index).encode("ascii")
            for index, value in enumerate(shared_strings)
            if value == "JOINVILLE"
        ]
        xml = archive.read("xl/worksheets/sheet1.xml")
    # Percorre o XML linha a linha (<row>...</row>) e só converte as linhas que mencionam JOINVILLE: muito mais rápido que ler o país inteiro.
    for match in re.finditer(rb"<row\b[^>]*\br=\"\d+\"[^>]*>.*?</row>", xml, re.DOTALL):
        raw_row = match.group()
        has_inline_city = b"JOINVILLE" in raw_row
        has_shared_city = any(
            re.search(rb'<c\b[^>]*\br="B\d+"[^>]*>.*?<v>' + index + rb"</v>.*?</c>", raw_row, re.DOTALL)
            for index in joinville_shared_ids
        )
        if not has_inline_city and not has_shared_city:
            continue
        element = _parse_sheet_row(raw_row)
        cells = {
            cell.get("r").rstrip("0123456789"): _cell_value(cell, shared_strings)
            for cell in element.findall(NS + "c")
        }
        row = [cells.get(chr(65 + column)) for column in range(len(HEADERS))]
        # Filtro final exato: UF = SC e município = JOINVILLE.
        if row[0] == "SC" and row[1] == "JOINVILLE":
            rows.append(row)
    return rows
