# ETAPA 1.1 — Extração bruta das tabelas dos PDFs SSP/SC

## Resultado da conversão

- PDFs encontrados recursivamente em `dados/brutos/ssp_sc/pdfs/`: **45**.
- PDFs processados com CSV gerado: **45**.
- CSVs gerados: **45**; cada arquivo usa o mesmo nome-base do PDF.
- Linhas de dados CSV (sem contar a linha do cabeçalho): **25.753**.
- Exceções de abertura ou extração de página: **0**.
- Páginas sem nenhuma tabela detectada pelo `pdfplumber`: **0**.
- Os 45 arquivos foram reabertos com `pandas.read_csv`; todos têm BOM UTF-8, separador `;`, largura de linha consistente e dimensões lidas sem divergência.

## Método e preservação

Foi usado `pdfplumber` para ler as tabelas de todas as páginas. O extrator existente `src/extract.py` não foi chamado: ele seleciona somente tabelas de homicídio e violência doméstica para Joinville e aplica limpeza de espaços e normalização de dois rótulos. Isso não atende à extração integral e literal solicitada. Nenhum critério do módulo existente foi alterado.

Cada CSV contém `arquivo_pdf`, `pagina_pdf`, `tabela_pdf`, `linha_tabela` e campos `celula_01` a `celula_N`. Os cabeçalhos e rótulos originais aparecem como linhas de células, em vez de virarem nomes de coluna, porque um documento pode conter muitas tabelas com cabeçalhos e larguras diferentes. Essa forma mantém todas as linhas na ordem detectada e permite rastrear cada linha até página, tabela e posição.

Codificação: `utf-8-sig`, para leitura correta de acentos em programas que reconhecem BOM. Separador: `;`, para reduzir conflitos com conteúdo textual que usa vírgulas. Linhas de larguras diferentes são completadas à direita com campos vazios para formar um CSV retangular; isso não altera células existentes nem preenche valores. Células que o leitor retorna como `None` são escritas vazias, pois CSV não distingue vazio de nulo.

## Dimensões dos arquivos

Linhas abaixo contam registros de dados, sem a linha de cabeçalho; colunas incluem quatro campos de rastreabilidade e as colunas genéricas de conteúdo. O `shape` no Pandas corresponde a `linhas × colunas`.

| PDF de origem | CSV gerado | Tabelas | Linhas × colunas |
|---|---|---:|---:|
| `2024_05_01_janeiro_24.pdf` | [`2024_05_01_janeiro_24.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_01_janeiro_24.csv) | 19 | 373 × 15 |
| `2024_05_02_fevereiro_24.pdf` | [`2024_05_02_fevereiro_24.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_02_fevereiro_24.csv) | 19 | 371 × 15 |
| `2024_05_03_marco_24.pdf` | [`2024_05_03_marco_24.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_03_marco_24.csv) | 19 | 373 × 15 |
| `2024_05_23.01_janeiro.pdf` | [`2024_05_23.01_janeiro.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_23.01_janeiro.csv) | 15 | 368 × 15 |
| `2024_05_23.02_fevereiro.pdf` | [`2024_05_23.02_fevereiro.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_23.02_fevereiro.csv) | 22 | 376 × 15 |
| `2024_05_23.04_abril.pdf` | [`2024_05_23.04_abril.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_23.04_abril.csv) | 20 | 374 × 15 |
| `2024_05_23.05_maio.pdf` | [`2024_05_23.05_maio.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_23.05_maio.csv) | 20 | 372 × 15 |
| `2024_05_23.06_junho.pdf` | [`2024_05_23.06_junho.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_23.06_junho.csv) | 20 | 374 × 15 |
| `2024_05_23.07_julho.pdf` | [`2024_05_23.07_julho.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_23.07_julho.csv) | 19 | 376 × 15 |
| `2024_05_23.08_agosto.pdf` | [`2024_05_23.08_agosto.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_23.08_agosto.csv) | 19 | 376 × 15 |
| `2024_05_23.09_setembro.pdf` | [`2024_05_23.09_setembro.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_23.09_setembro.csv) | 18 | 375 × 17 |
| `2024_05_23.10_outubro.pdf` | [`2024_05_23.10_outubro.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_23.10_outubro.csv) | 18 | 375 × 18 |
| `2024_05_23.11_novembro.pdf` | [`2024_05_23.11_novembro.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_23.11_novembro.csv) | 18 | 374 × 18 |
| `2024_05_23.12_dezembro.pdf` | [`2024_05_23.12_dezembro.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_05_23.12_dezembro.csv) | 20 | 375 × 15 |
| `2024_06_04_abril_24.pdf` | [`2024_06_04_abril_24.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_06_04_abril_24.csv) | 19 | 374 × 15 |
| `2024_06_05_maio_24.pdf` | [`2024_06_05_maio_24.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_06_05_maio_24.csv) | 18 | 374 × 15 |
| `2024_07_06-junho-2.pdf` | [`2024_07_06-junho-2.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_07_06-junho-2.csv) | 12 | 366 × 20 |
| `2024_08_07-julho-1.pdf` | [`2024_08_07-julho-1.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_08_07-julho-1.csv) | 17 | 371 × 22 |
| `2024_09_08-agosto-1.pdf` | [`2024_09_08-agosto-1.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_09_08-agosto-1.csv) | 13 | 368 × 22 |
| `2024_10_Relatorio-SET-2024-Ratificado-1.pdf` | [`2024_10_Relatorio-SET-2024-Ratificado-1.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_10_Relatorio-SET-2024-Ratificado-1.csv) | 13 | 367 × 21 |
| `2024_11_RELATORIO-OUT.pdf` | [`2024_11_RELATORIO-OUT.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_11_RELATORIO-OUT.csv) | 12 | 366 × 21 |
| `2024_12_NOV-1.pdf` | [`2024_12_NOV-1.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2024_12_NOV-1.csv) | 13 | 369 × 21 |
| `2025_02_01-janeiro-1.pdf` | [`2025_02_01-janeiro-1.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_02_01-janeiro-1.csv) | 17 | 370 × 31 |
| `2025_02_12-dezembro-1.pdf` | [`2025_02_12-dezembro-1.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_02_12-dezembro-1.csv) | 18 | 373 × 21 |
| `2025_03_02-fevereiro-25.pdf` | [`2025_03_02-fevereiro-25.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_03_02-fevereiro-25.csv) | 21 | 376 × 15 |
| `2025_04_03-marco.pdf` | [`2025_04_03-marco.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_04_03-marco.csv) | 22 | 380 × 15 |
| `2025_06_04-abril-3.pdf` | [`2025_06_04-abril-3.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_06_04-abril-3.csv) | 22 | 381 × 15 |
| `2025_06_05-maio-1-1.pdf` | [`2025_06_05-maio-1-1.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_06_05-maio-1-1.csv) | 19 | 374 × 15 |
| `2025_06_VIOLENCIA-DOMESTICA-1o-SEMESTRE-2023.pdf` | [`2025_06_VIOLENCIA-DOMESTICA-1o-SEMESTRE-2023.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_06_VIOLENCIA-DOMESTICA-1o-SEMESTRE-2023.csv) | 66 | 3226 × 9 |
| `2025_06_VIOLENCIA-DOMESTICA-2024-SC.pdf` | [`2025_06_VIOLENCIA-DOMESTICA-2024-SC.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_06_VIOLENCIA-DOMESTICA-2024-SC.csv) | 74 | 3652 × 13 |
| `2025_06_VIOLENCIA-DOMESTICA-2o-SEMESTRE-2023.pdf` | [`2025_06_VIOLENCIA-DOMESTICA-2o-SEMESTRE-2023.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_06_VIOLENCIA-DOMESTICA-2o-SEMESTRE-2023.csv) | 64 | 3144 × 8 |
| `2025_08_06-junho-2025.pdf` | [`2025_08_06-junho-2025.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_08_06-junho-2025.csv) | 21 | 379 × 15 |
| `2025_08_07-julho-2025.pdf` | [`2025_08_07-julho-2025.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_08_07-julho-2025.csv) | 20 | 380 × 15 |
| `2025_10_08-agosto.pdf` | [`2025_10_08-agosto.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_10_08-agosto.csv) | 21 | 381 × 15 |
| `2025_10_09-setembro.pdf` | [`2025_10_09-setembro.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_10_09-setembro.csv) | 18 | 376 × 16 |
| `2025_11_10-outubro.pdf` | [`2025_11_10-outubro.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_11_10-outubro.csv) | 18 | 376 × 17 |
| `2025_12_11-novembro.pdf` | [`2025_12_11-novembro.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2025_12_11-novembro.csv) | 19 | 372 × 15 |
| `2026_01_12-dezembro.pdf` | [`2026_01_12-dezembro.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2026_01_12-dezembro.csv) | 20 | 374 × 15 |
| `2026_02_01-janeiro-2026.pdf` | [`2026_02_01-janeiro-2026.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2026_02_01-janeiro-2026.csv) | 23 | 382 × 15 |
| `2026_03_02-fevereiro-2026.pdf` | [`2026_03_02-fevereiro-2026.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2026_03_02-fevereiro-2026.csv) | 20 | 378 × 15 |
| `2026_05_03-marco-2026.pdf` | [`2026_05_03-marco-2026.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2026_05_03-marco-2026.csv) | 20 | 379 × 15 |
| `2026_05_04-abril-2026.pdf` | [`2026_05_04-abril-2026.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2026_05_04-abril-2026.csv) | 20 | 379 × 15 |
| `2026_06_05-maio.pdf` | [`2026_06_05-maio.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2026_06_05-maio.csv) | 20 | 380 × 15 |
| `2026_07_06-junho-de-2026.pdf` | [`2026_07_06-junho-de-2026.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2026_07_06-junho-de-2026.csv) | 18 | 379 × 15 |
| `2026_08_2026-julho.pdf` | [`2026_08_2026-julho.csv`](../../dados/brutos/ssp_sc/csv_extraidos/2026_08_2026-julho.csv) | 17 | 375 × 15 |

## Conferência com os PDFs

Foram renderizadas páginas originais e comparadas com as linhas correspondentes dos CSVs:

- `2024_05_01_janeiro_24.pdf`, página 8: a linha Joinville mostra 68, 51 e 58 vítimas nos anos 2021–2023 e 6, 2, 19 e 2 no período 01/01–31/01. A linha correspondente está em `2024_05_01_janeiro_24.csv`, tabela 1, linha 36.
- `2025_06_VIOLENCIA-DOMESTICA-2024-SC.pdf`, página 18: a linha Joinville/Ameaça mostra 209, 200 e 204; a linha correspondente está no CSV, tabela 1, linha 32.
- `2026_08_2026-julho.pdf`, página 8: a linha Joinville contém 56, 37 e 32 nos anos 2023–2025 e 36, 20, 17 e 22 no período 01/01–31/07/2026; a linha correspondente está no CSV, tabela 1, linha 36.

Essas conferências visuais cobrem dois modelos de boletim mensal e o PDF temático doméstico. A leitura foi executada em todos os PDFs e cada página retornou ao menos uma tabela; a conferência visual de cada célula em todas as páginas não foi feita. Tabelas complexas podem apresentar células mescladas ou quebras de linha próprias do layout do PDF; esta extração registra a estrutura retornada pelo leitor, não reconstrói o desenho visual.

## Páginas com falha

Não houve falha técnica de leitura nem página sem tabela detectada nos 45 documentos. Isso não garante que cada célula esteja perfeitamente segmentada pelo parser; os exemplos de confronto acima foram verificados no PDF renderizado. Os dados não foram corrigidos ou inventados.

## Visualização das primeiras 20 linhas

O notebook [`ssp_csv_data_viewer.ipynb`](../ssp_csv_data_viewer.ipynb) contém uma célula por CSV. Cada célula lê o arquivo com `sep=";"`, `encoding="utf-8-sig"`, `keep_default_na=False`, guarda somente `head(20)` em uma variável `amostra_01`–`amostra_45` e exibe a tabela. No VS Code, abra o notebook, selecione o kernel Python e execute as células desejadas; as variáveis de amostra podem ser abertas no Visualizador de Dados. Os CSVs completos permanecem em `dados/brutos/ssp_sc/csv_extraidos/`.

## Limites e operações não realizadas

- A extração inclui tabelas estaduais e municipais de cada PDF; não há filtro para Joinville.
- Os arquivos foram mantidos separados por documento; nenhum CSV foi consolidado.
- Não foram aplicados `dropna`, `fillna`, deduplicação, padronização, limpeza ou cálculo estatístico.
- Os PDFs não foram modificados e os CSVs processados anteriormente em `dados/processados/ssp_sc/` não foram sobrescritos.
- Nenhuma etapa posterior do ETL foi executada.
