"""Extrai somente as linhas SC/Joinville dos XLSX brutos, sem modificar valores."""

from collections import Counter
import json
from pathlib import Path
import re
from zipfile import ZipFile

from lxml import etree


ROOT = Path(__file__).resolve().parent
NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
OUT = ROOT / "data" / "joinville_rows.json"


def cell_value(cell):
    kind = cell.get("t")
    if kind == "inlineStr":
        return "".join(cell.itertext())
    node = cell.find(NS + "v")
    if node is None:
        return None
    raw = node.text
    if kind in ("str", "e", "s"):
        return raw
    if kind == "b":
        return raw == "1"
    if raw is None:
        return None
    number = float(raw)
    return int(number) if number.is_integer() else number


result = {}
for year in range(2023, 2027):
    path = ROOT / "data" / "raw" / f"bancovde-{year}.xlsx"
    rows = []
    candidates = Counter()
    with ZipFile(path) as archive:
        xml = archive.read("xl/worksheets/sheet1.xml")
    for row_match in re.finditer(rb"<row r=\"\d+\">.*?</row>", xml):
        raw_row = row_match.group()
        if b"JOINVILLE" not in raw_row:
            continue
        element = etree.fromstring(raw_row.replace(b"<row ", b'<row xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" ', 1))
        cells = {cell.get("r").rstrip("0123456789"): cell_value(cell) for cell in element.findall(NS + "c")}
        uf = cells.get("A")
        municipality = cells.get("B")
        candidates[(uf, municipality)] += 1
        if uf == "SC" and municipality == "JOINVILLE":
            rows.append([cells.get(chr(65 + col)) for col in range(14)])
    result[str(year)] = rows
    print(year, len(rows), dict(candidates), flush=True)

OUT.write_text(json.dumps(result, ensure_ascii=False), encoding="utf-8")
print("Saved intermediate", OUT, flush=True)
