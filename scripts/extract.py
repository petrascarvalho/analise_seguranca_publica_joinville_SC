from __future__ import annotations

import csv
import re
from collections import defaultdict
from pathlib import Path

import pdfplumber
from pypdf import PdfReader

from scripts.utils import project_path
from scripts.transform import normalize_ssp_indicator


RAW_DIR = project_path("dados", "brutos", "ssp_sc", "pdfs")
OUT_DIR = project_path("dados", "processados", "ssp_sc")
FIELDS = [
    "ano_relatorio", "data_atualizacao", "municipio", "indicador",
    "indicador_normalizado", "periodo_tipo", "ano_referencia", "periodo_referencia", "valor",
    "arquivo_pdf", "pagina_pdf",
]
SHORT_MONTHS = {
    "jan": "01", "fev": "02", "mar": "03", "abr": "04", "mai": "05",
    "jun": "06", "jul": "07", "ago": "08", "set": "09", "out": "10",
    "nov": "11", "dez": "12",
}


def clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def integer(value):
    text = clean(value)
    return int(text) if re.fullmatch(r"\d+", text) else None


def pdf_update_date(path: Path) -> str:
    reader = PdfReader(str(path))
    text = "\n".join((page.extract_text() or "") for page in reader.pages[:2])
    match = re.search(r"ATUALIZAÇÃO DOS DADOS:\s*(\d{2}/\d{2}/\d{4})", text, re.I)
    return match.group(1) if match else ""


def municipal_homicide_rows(path: Path) -> list[dict]:
    date = pdf_update_date(path)
    if not date:
        return []
    report_year = int(date[-4:])
    output = []
    with pdfplumber.open(path) as pdf:
        for page_number, page in enumerate(pdf.pages, 1):
            text = page.extract_text() or ""
            if "Nº DE VÍTIMAS POR ANO" not in text.upper() or "JOINVILLE" not in text.upper():
                continue
            period_match = re.search(
                r"N[º°]\s*DE V[IÍ]TIMAS NO PER[IÍ]ODO\s*\(([^)]+)\)", text, re.I
            )
            period_label = clean(period_match.group(1)) if period_match else ""
            tables = page.extract_tables()
            if not tables:
                continue
            table = tables[0]
            header_years = []
            for row in table:
                joined = " ".join(clean(cell) for cell in row)
                if "MUNICÍPIO" in joined.upper() or "MUNICIPIO" in joined.upper():
                    header_years = [int(value) for value in re.findall(r"\b20\d{2}\b", joined)]
                    if len(header_years) >= 6:
                        break
            joinville = next(
                (row for row in table if any(clean(cell).upper() == "JOINVILLE" for cell in row)),
                None,
            )
            if joinville is None or len(header_years) < 6:
                continue
            values = [integer(cell) for cell in joinville]
            values = [value for value in values if value is not None]
            if len(values) != len(header_years):
                continue
            split = min(3, len(values) - 1)
            for year, value in zip(header_years[:split], values[:split]):
                output.append({
                    "ano_relatorio": report_year,
                    "data_atualizacao": date,
                    "municipio": "JOINVILLE",
                    "indicador": "Nº de vítimas de homicídio",
                    "indicador_normalizado": "Nº de vítimas de homicídio",
                    "periodo_tipo": "ano completo",
                    "ano_referencia": year,
                    "periodo_referencia": str(year),
                    "valor": value,
                    "arquivo_pdf": path.name,
                    "pagina_pdf": page_number,
                })
            for year, value in zip(header_years[split:], values[split:]):
                output.append({
                    "ano_relatorio": report_year,
                    "data_atualizacao": date,
                    "municipio": "JOINVILLE",
                    "indicador": "Nº de vítimas de homicídio",
                    "indicador_normalizado": "Nº de vítimas de homicídio",
                    "periodo_tipo": "período acumulado",
                    "ano_referencia": year,
                    "periodo_referencia": period_label,
                    "valor": value,
                    "arquivo_pdf": path.name,
                    "pagina_pdf": page_number,
                })
    return output


def domestic_file_periods(path: Path):
    name = path.name.upper()
    if "1O-SEMESTRE-2023" in name:
        return 2023, ["jan"], ["fev", "mar", "abr", "mai", "jun"]
    if "2O-SEMESTRE-2023" in name:
        return 2023, ["jul", "ago"], ["set", "out", "nov", "dez"]
    if "VIOLENCIA-DOMESTICA-2024" in name:
        return 2024, ["jan", "fev", "mar"], ["abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]
    return None


def domestic_rows(path: Path) -> list[dict]:
    config = domestic_file_periods(path)
    if config is None:
        return []
    year, first_months, second_months = config
    output = []
    with pdfplumber.open(path) as pdf:
        half = len(pdf.pages) // 2
        if half * 2 != len(pdf.pages):
            raise ValueError(f"Número ímpar de páginas no PDF temático: {path.name}")
        for page_index in range(half):
            first_tables = pdf.pages[page_index].extract_tables()
            second_tables = pdf.pages[page_index + half].extract_tables()
            if not first_tables or not second_tables:
                continue
            first_table, second_table = first_tables[0], second_tables[0]
            if len(first_table) != len(second_table):
                raise ValueError(f"Tabelas desalinhadas em {path.name}, páginas {page_index+1} e {page_index+half+1}")
            current_municipality = ""
            for row_index, row in enumerate(first_table):
                if len(row) < 2:
                    continue
                municipality = clean(row[0]).upper()
                if municipality == "JOINVILLE":
                    current_municipality = municipality
                elif municipality and municipality not in {"MUNICÍPIO", "MUNICIPIO"}:
                    if municipality == municipality.upper() and re.search(r"[A-ZÁÉÍÓÚÂÊÔÃÕÇ]", municipality):
                        current_municipality = municipality
                indicator = clean(row[1])
                first_values = [integer(cell) for cell in row[2:]]
                first_values = [value for value in first_values if value is not None]
                if current_municipality != "JOINVILLE" or not indicator or not first_values:
                    continue
                second_values = [integer(cell) for cell in second_table[row_index]]
                second_values = [value for value in second_values if value is not None]
                values = first_values + second_values
                months = first_months + second_months
                if len(values) != len(months):
                    raise ValueError(f"Meses não conferem em {path.name}, linha {row_index+1}")
                for month, value in zip(months, values):
                    output.append({
                        "ano_relatorio": year,
                        "data_atualizacao": "",
                        "municipio": "JOINVILLE",
                        "indicador": indicator,
                        "indicador_normalizado": normalize_ssp_indicator(indicator),
                        "periodo_tipo": "mensal",
                        "ano_referencia": year,
                        "periodo_referencia": f"{year}-{SHORT_MONTHS[month]}",
                        "valor": value,
                        "arquivo_pdf": path.name,
                        "pagina_pdf": f"{page_index+1};{page_index+half+1}",
                    })
    return output


def extract_all() -> dict[int, list[dict]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    by_report_year: dict[int, list[dict]] = defaultdict(list)
    pdfs = sorted(RAW_DIR.glob("*.pdf"))
    if len(pdfs) != 45:
        raise ValueError(f"Esperados 45 PDFs SSP/SC, encontrados {len(pdfs)} em {RAW_DIR}")
    for path in pdfs:
        rows = domestic_rows(path) if "VIOLENCIA-DOMESTICA" in path.name.upper() else municipal_homicide_rows(path)
        for row in rows:
            by_report_year[int(row["ano_relatorio"])].append(row)
    return by_report_year


def write_extractions(results: dict[int, list[dict]]) -> list[tuple[Path, int]]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    outputs = []
    for year, rows in sorted(results.items()):
        target = OUT_DIR / f"ssp_joinville_{year}.csv"
        with target.open("w", encoding="utf-8-sig", newline="") as stream:
            writer = csv.DictWriter(stream, fieldnames=FIELDS, extrasaction="ignore")
            writer.writeheader()
            writer.writerows(rows)
        outputs.append((target, len(rows)))
    return outputs


def main() -> None:
    results = extract_all()
    write_extractions(results)
    source_count = sum(1 for p in RAW_DIR.glob("*.pdf"))
    for year, rows in sorted(results.items()):
        print(f"ssp_joinville_{year}.csv: {len(rows)} registros")
    extracted_pdf_count = len({row["arquivo_pdf"] for rows in results.values() for row in rows})
    print(f"PDFs de origem: {source_count}; PDFs com extração municipal: {extracted_pdf_count}")


if __name__ == "__main__":
    main()
