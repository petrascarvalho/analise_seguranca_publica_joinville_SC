# Extrações SSP/SC — Joinville

Os 45 PDFs originais foram preservados em `dados/brutos/ssp_sc/pdfs/`. A rotina reproduzível está em `scripts/extract.py`; os CSVs ficam em `dados/processados/ssp_sc/` e registram `arquivo_pdf` e `pagina_pdf` em cada linha.

| Arquivo gerado | Registros | Conteúdo extraído |
|---|---:|---|
| `ssp_joinville_2023.csv` | 185 | 77 linhas de vítimas de homicídio em 11 boletins e 108 linhas mensais de violência doméstica |
| `ssp_joinville_2024.csv` | 192 | 84 linhas de vítimas de homicídio em 12 boletins e 108 linhas mensais de violência doméstica |
| `ssp_joinville_2025.csv` | 84 | 84 linhas de vítimas de homicídio em 12 boletins |
| `ssp_joinville_2026.csv` | 49 | 49 linhas de vítimas de homicídio em 7 boletins, até julho |

Campos: `ano_relatorio`, `data_atualizacao`, `municipio`, `indicador`, `indicador_normalizado`, `periodo_tipo`, `ano_referencia`, `periodo_referencia`, `valor`, `arquivo_pdf`, `pagina_pdf`.

As saídas da nova localização foram comparadas por SHA-256 com os CSVs existentes antes da migração. Os 45 PDFs permanecem preservados. A extração cobre tabelas municipais encontradas nos boletins; furtos e roubos publicados em nível estadual não foram atribuídos a Joinville.

**Cuidado com a granularidade:** os boletins mensais reapresentam anos completos e períodos acumulados em edições diferentes. Essas linhas são snapshots, não ocorrências únicas; não some registros de edições distintas. A análise usa o último valor anual completo disponível para cada ano de referência e uma única edição de julho de 2026 para comparar janeiro–julho de 2023 a 2026.

Nos relatórios temáticos de violência doméstica, `pagina_pdf` registra as páginas pareadas usadas para recuperar rótulos e valores mensais. O texto extraído é mantido em `indicador`; `indicador_normalizado` padroniza apenas duas variações encontradas no texto dos PDFs:

| Texto preservado em `indicador` | Rótulo em `indicador_normalizado` | Justificativa |
|---|---|---|
| `Lesão corporal grave ou gravíssima 0 Dolosa` | `Lesão corporal grave ou gravíssima - Dolosa` | O próprio PDF de 2023 publica `0` no rótulo; o relatório de 2024 apresenta a mesma categoria com hífen. |
| `Lesão corporal leve 0 Dolosa` | `Lesão corporal leve - Dolosa` | O próprio PDF de 2023 publica `0`; o relatório de 2024 usa hífen para a mesma categoria. |

As demais grafias são mantidas. A correspondência é uma padronização de grafia publicada, não uma limpeza do texto extraído: os dois campos são mantidos. A evidência visual da tabela e do rótulo original está em [`../audit/evidencia_grafia_violencia_domestica_2023.png`](../auditoria/evidencia_grafia_violencia_domestica_2023.png). Cada categoria mensal aparece uma vez depois de normalizar: os rótulos com hífen e com `0` correspondem às metades distintas de 2023 e não repetem os mesmos meses. `data_atualizacao` fica vazio nos relatórios temáticos porque eles não publicam a data no mesmo formato dos boletins mensais.
