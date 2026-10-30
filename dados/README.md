# Dados do projeto — Segurança Pública de Joinville/SC

Esta pasta reúne os dados do projeto em arquivos ZIP, separados por fonte:

- **Sinesp/MJSP:** a fonte principal do painel;
- **SSP/SC:** fonte complementar, em validação;
- **arquivos históricos e complementares**, identificados como tais.

Dentro dos ZIPs, os arquivos estão **sem nenhuma modificação**, com os nomes e formatos originais. O inventário completo de todos os arquivos da pasta, publicados ou não, está em [`inventario_dados.csv`](inventario_dados.csv).

## Arquivos publicados

| Arquivo ZIP | Fonte | Conteúdo | Situação | ZIP |
| --- | --- | --- | --- | ---: |
| `brutos/sinesp_2020_xlsx.zip` … `brutos/sinesp_2026_xlsx.zip` | MJSP / Sinesp VDE | Um XLSX original por ano (`bancovde-ANO.xlsx`), edição `20261027T114400Z`; 2026 de janeiro a setembro | Atual (original) | 15,2 a 19,2 MiB cada |
| `processados/SINESP_20_26_Petras_Ruben_Carvalho.zip` | MJSP / Sinesp VDE | 4 saídas do ETL: base mensal (911 registros, 12 séries), catálogo, recorte bruto e relatório | Atual (processado) | 0,01 MiB |
| `processados/consolidacao_union_joinville.zip` | MJSP / Sinesp VDE | Estudo UNION/JOIN de `src/pipeline/consolidacao.py`: Sinesp no esquema comum (911 registros) e matriz de compatibilidade | Atual (processado) | 0,01 MiB |
| `brutos/ssp_sc/ssp_sc_csv_extraidos.zip` | SSP/SC (extraído pelo projeto) | 45 CSVs extraídos dos PDFs; são **derivados**, não publicações oficiais | Atual | 0,28 MiB |
| `processados/ssp_sc/ssp_sc_joinville_processados.zip` | SSP/SC | 7 saídas do ETL: violência doméstica (216), homicídios por edição (294), republicações, inventário, rastreabilidade, verificações e relatório | Atual (processado) | 0,02 MiB |
| `processados/historico/sinesp_edicao_anterior_ate_ago2026.zip` | MJSP / Sinesp VDE, edição anterior | Recortes de Joinville gerados em 16/10/2026, com dados até agosto/2026 (900 registros) | **Histórico** | 0,07 MiB |
| `processados/historico/ssp_sc_versoes_anteriores.zip` | SSP/SC | Tabelas de Joinville de etapas anteriores (16/10 e 28/10/2026), substituídas pelas saídas atuais | **Histórico** | 0,02 MiB |
| `processados/complementares/fontes_complementares_joinville.zip` | Prefeitura/SEPROT; SSP/SC via ALESC | Furtos e roubos divulgados (2023–2025) e matriz de evidências | **Complementar, não validado** | 0,005 MiB |

- Os arquivos **históricos** e **complementares** servem para documentar o caminho da análise e as divergências entre fontes. **Não são resultados atuais** e não entram no painel.
- Cada registro mensal do Sinesp é o valor de **um mês de uma série**: 911 registros não significam 911 crimes.
- O [`manifesto_zips.json`](manifesto_zips.json) lista, para cada ZIP, a fonte, o período, a situação e o SHA-256 de cada arquivo interno.

## Arquivo não publicado

| Arquivo | Motivo |
| --- | --- |
| `brutos/ssp_sc/ssp_sc_pdfs_originais.zip` (45 PDFs originais da SSP/SC) | O site da fonte informa “Copyright © 2023 Todos os Direitos Reservados SC - Governo de Santa Catarina” ([Segurança em Números](https://ssp.sc.gov.br/segurancaemnumeros/), conferido em 29/10/2026), e os PDFs não trazem licença de reutilização. Por isso, os documentos **não são republicados na íntegra**. Os 45 PDFs podem ser baixados nos endereços oficiais, com conferência automática do SHA-256 (ver abaixo). |

Também ficam só no computador as edições anteriores dos XLSX do Sinesp, uma cópia da página da SSP/SC e cópias locais duplicadas. Todos esses arquivos estão listados no inventário.

## Origem e reutilização

- **Sinesp/MJSP:** [base de dados do Sinesp VDE](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados).
  - A licença informada no portal gov.br é a [CC BY-ND 3.0](https://creativecommons.org/licenses/by-nd/3.0/deed.pt_BR), que permite redistribuir cópias **sem modificação**, com atribuição. Por isso os XLSX são publicados exatamente como foram baixados.
  - Os arquivos processados são elaboração do projeto a partir desses dados.
- **SSP/SC:** [Segurança em Números](https://ssp.sc.gov.br/segurancaemnumeros/).
  - **Não há licença de reutilização informada.** O projeto publica somente os **dados estatísticos** extraídos e tratados, com atribuição da fonte. Os PDFs, que são os documentos com reserva de direitos, não são republicados.
  - A unidade “Fato Comunicado” não tem definição oficial nos PDFs, e os boletins republicam valores diferentes para o mesmo período.
- **Prefeitura/SEPROT e relatório da SSP/SC via ALESC:** números divulgados publicamente, com divergências entre fontes. Ver o [anexo de fontes complementares](../documentacao/anexos/notas_fontes_complementares.md).
- **Dados pessoais:** todos os dados são **contagens agregadas por município**. Nos arquivos publicados não foram encontrados nomes, CPFs, e-mails ou telefones.

Avaliação técnica de reutilização, não parecer jurídico. **Atribuição:** Fontes: MJSP / Sinesp VDE; SSP/SC — Segurança em Números. Tabelas processadas: elaboração do projeto.

## Links diretos para download

Os ZIPs ficam no [GitHub pessoal do projeto](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC). Depois de baixar, confira o SHA-256 (ver “Como conferir a integridade”). Para usar com o projeto, salve cada ZIP no mesmo caminho da coluna “Arquivo”, dentro da pasta `dados/`.

| Arquivo | Download |
| --- | --- |
| `brutos/sinesp_2020_xlsx.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/brutos/sinesp_2020_xlsx.zip) |
| `brutos/sinesp_2021_xlsx.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/brutos/sinesp_2021_xlsx.zip) |
| `brutos/sinesp_2022_xlsx.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/brutos/sinesp_2022_xlsx.zip) |
| `brutos/sinesp_2023_xlsx.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/brutos/sinesp_2023_xlsx.zip) |
| `brutos/sinesp_2024_xlsx.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/brutos/sinesp_2024_xlsx.zip) |
| `brutos/sinesp_2025_xlsx.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/brutos/sinesp_2025_xlsx.zip) |
| `brutos/sinesp_2026_xlsx.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/brutos/sinesp_2026_xlsx.zip) |
| `processados/SINESP_20_26_Petras_Ruben_Carvalho.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/processados/SINESP_20_26_Petras_Ruben_Carvalho.zip) |
| `processados/consolidacao_union_joinville.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/processados/consolidacao_union_joinville.zip) |
| `brutos/ssp_sc/ssp_sc_csv_extraidos.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/brutos/ssp_sc/ssp_sc_csv_extraidos.zip) |
| `processados/ssp_sc/ssp_sc_joinville_processados.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/processados/ssp_sc/ssp_sc_joinville_processados.zip) |
| `processados/historico/sinesp_edicao_anterior_ate_ago2026.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/processados/historico/sinesp_edicao_anterior_ate_ago2026.zip) |
| `processados/historico/ssp_sc_versoes_anteriores.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/processados/historico/ssp_sc_versoes_anteriores.zip) |
| `processados/complementares/fontes_complementares_joinville.zip` | [baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/processados/complementares/fontes_complementares_joinville.zip) |

## Como conferir a integridade

O [`SHA256SUMS.txt`](SHA256SUMS.txt) tem o SHA-256 de cada ZIP publicado. No CMD, a partir da pasta principal do projeto, o comando abaixo confere todos de uma vez; cada linha deve mostrar `OK`:

```bat
py -c "import hashlib; [print('OK ' if hashlib.sha256(open('dados/' + nome, 'rb').read()).hexdigest() == h else 'DIFERENTE ', nome) for h, nome in (linha.split() for linha in open('dados/SHA256SUMS.txt'))]"
```

Se o comando `py` não existir, use `python`. Também é possível conferir um arquivo por vez no PowerShell, com `Get-FileHash dados\brutos\sinesp_2020_xlsx.zip -Algorithm SHA256`. O ETL também confere sozinho o SHA-256 de cada XLSX e só aceita a edição aprovada.

## Como descompactar

No **Prompt de Comando (CMD)**, a partir da pasta principal do projeto (`zipfile` já vem com o Python). Os destinos são as pastas que o ETL e o notebook procuram:

```bat
:: Sinesp: os sete XLSX vão para dados\brutos\sinesp\
py -c "import glob, zipfile; [zipfile.ZipFile(z).extractall('dados/brutos/sinesp') for z in glob.glob('dados/brutos/sinesp_*_xlsx.zip')]"

:: Sinesp processado: recria dados\processados\etl_joinville\sinesp\
py -c "import zipfile; zipfile.ZipFile('dados/processados/SINESP_20_26_Petras_Ruben_Carvalho.zip').extractall('dados/processados')"

:: SSP/SC: CSVs extraídos vão para dados\brutos\ssp_sc\csv_extraidos\
py -c "import zipfile; zipfile.ZipFile('dados/brutos/ssp_sc/ssp_sc_csv_extraidos.zip').extractall('dados/brutos/ssp_sc/csv_extraidos')"

:: SSP/SC: baixa os 45 PDFs dos endereços oficiais do catálogo e grava só os que têm o SHA-256 esperado
py -c "import csv, hashlib, os, urllib.request; os.makedirs('dados/brutos/ssp_sc/pdfs', exist_ok=True); [(open('dados/brutos/ssp_sc/' + r['arquivo'], 'wb').write(d), print('OK', r['arquivo'])) if hashlib.sha256(d).hexdigest() == r['sha256'] else print('DIFERENTE (não gravado)', r['arquivo']) for r in csv.DictReader(open('dados/brutos/ssp_sc/fontes_oficiais.csv', encoding='utf-8')) if r['arquivo'].startswith('pdfs/') for d in [urllib.request.urlopen(urllib.request.Request(r['url_oficial'], headers={'User-Agent': 'Mozilla/5.0'})).read()]]"

:: SSP/SC processado: recria dados\processados\etl_joinville\ssp_sc\
py -c "import zipfile; zipfile.ZipFile('dados/processados/ssp_sc/ssp_sc_joinville_processados.zip').extractall('dados/processados')"
```

Os ZIPs históricos, complementares e de consolidação podem ser abertos em qualquer pasta, por exemplo com **Extrair tudo** no Explorador de Arquivos. Eles não são usados pelo ETL.

## Como usar depois de descompactar

- **ETL** (`.\.venv\Scripts\python.exe scripts\etl_joinville.py`):
  - **só com os XLSX do Sinesp:** executa e confere as etapas 1 a 10 e para na etapa 11 com a mensagem “Acervo da SSP/SC incompleto”;
  - **com os 45 CSVs extraídos e os 45 PDFs baixados da fonte:** executa as 14 etapas e grava as saídas em `dados/processados/etl_joinville/`. Elas são iguais às dos ZIPs processados.
- **Notebook:** com o `bancovde-2026.xlsx` descompactado, a etapa 3 inspeciona o arquivo original. As etapas da SSP/SC usam os arquivos locais quando existem.
- **Painel Streamlit:** não precisa desta pasta; usa somente `dashboard/data_publica/`.
