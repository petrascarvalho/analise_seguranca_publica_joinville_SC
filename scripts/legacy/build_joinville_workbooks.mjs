import fs from "node:fs/promises";
import { Workbook, SpreadsheetFile } from "@oai/artifact-tool";

const headers = ["uf", "municipio", "evento", "data_referencia", "agente", "arma", "faixa_etaria", "feminino", "masculino", "nao_informado", "total_vitima", "total", "total_peso", "abrangencia"];
const data = JSON.parse(await fs.readFile("data/joinville_rows.json", "utf8"));
await fs.mkdir("data/joinville", { recursive: true });

for (const year of [2023, 2024, 2025, 2026]) {
  const rows = data[String(year)];
  if (!Array.isArray(rows) || !rows.length) throw new Error(`Sem linhas para ${year}`);
  if (rows.some((r) => r.length !== headers.length || r[0] !== "SC" || r[1] !== "JOINVILLE")) {
    throw new Error(`Filtro inconsistente em ${year}`);
  }
  const workbook = Workbook.create();
  const sheet = workbook.worksheets.add(String(year));
  sheet.getRangeByIndexes(0, 0, rows.length + 1, headers.length).values = [headers, ...rows];
  sheet.getRange(`D2:D${rows.length + 1}`).setNumberFormat("yyyy-mm-dd");
  sheet.freezePanes.freezeRows(1);
  workbook.recalculate();
  const file = await SpreadsheetFile.exportXlsx(workbook);
  const path = `data/joinville/bancovde-${year}-joinville-sc.xlsx`;
  await file.save(path);
  const preview = await workbook.inspect({ kind: "region", sheetId: String(year), range: "A1:N3", maxChars: 1500 });
  console.log(JSON.stringify({ year, rows: rows.length, path, preview: preview.ndjson }));
}
