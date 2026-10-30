# Dados do projeto — Segurança Pública de Joinville/SC

Esta pasta guarda os **dados do Sinesp/MJSP** usados no projeto, compactados em ZIP. Os arquivos estão **sem nenhuma modificação** dentro dos ZIPs: os nomes e formatos originais foram preservados.

## Arquivos disponíveis

| Arquivo ZIP | Conteúdo | Tipo | Tamanho original | Tamanho do ZIP |
| --- | --- | --- | ---: | ---: |
| `brutos/sinesp_2020_xlsx.zip` | `bancovde-2020.xlsx` | Original (MJSP) | 23,16 MiB | 17,11 MiB |
| `brutos/sinesp_2021_xlsx.zip` | `bancovde-2021.xlsx` | Original (MJSP) | 23,22 MiB | 17,13 MiB |
| `brutos/sinesp_2022_xlsx.zip` | `bancovde-2022.xlsx` | Original (MJSP) | 23,23 MiB | 17,17 MiB |
| `brutos/sinesp_2023_xlsx.zip` | `bancovde-2023.xlsx` | Original (MJSP) | 23,25 MiB | 17,21 MiB |
| `brutos/sinesp_2024_xlsx.zip` | `bancovde-2024.xlsx` | Original (MJSP) | 23,26 MiB | 17,19 MiB |
| `brutos/sinesp_2025_xlsx.zip` | `bancovde-2025.xlsx` | Original (MJSP) | 25,41 MiB | 19,22 MiB |
| `brutos/sinesp_2026_xlsx.zip` | `bancovde-2026.xlsx` (janeiro a setembro) | Original (MJSP) | 19,71 MiB | 15,23 MiB |
| `processados/SINESP_20_26_Petras_Ruben_Carvalho.zip` | 4 arquivos gerados pelo ETL (ver abaixo) | Processado pelo projeto | 0,13 MiB | 0,01 MiB |

- **Originais:** os sete XLSX anuais da base nacional **Sinesp VDE**, na edição `20261027T114400Z` (republicada pelo MJSP em 27/10/2026). Cada arquivo traz **todos os municípios do Brasil**; o recorte de Joinville é feito pelo ETL. Só foram incluídos os arquivos cujo SHA-256 está registrado no manifesto da base aprovada.
- **Processados:** saídas do Sinesp geradas por `scripts/etl_joinville.py` a partir desses XLSX:
  - `etl_sinesp_joinville_mensal.csv`: base mensal de Joinville (911 registros, 12 séries), idêntica a `dashboard/data_publica/sinesp_joinville_mensal.csv`;
  - `etl_catalogo_series.csv`: uma linha por série, com unidade e período;
  - `etl_recorte_joinville_bruto.csv`: linhas de Joinville copiadas dos XLSX, antes da padronização;
  - `etl_relatorio.json`: contagens, conferências e SHA-256 dos XLSX usados.

Cada registro mensal é o valor de **um mês de uma série**; 911 registros não significam 911 crimes.

## Origem e licença

- **Fonte:** Ministério da Justiça e Segurança Pública — [Sinesp VDE, base de dados](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados).
- **Licença informada no portal gov.br:** [Creative Commons Atribuição-SemDerivações 3.0](https://creativecommons.org/licenses/by-nd/3.0/deed.pt_BR) (CC BY-ND 3.0). Ela permite redistribuir cópias **sem modificação**, com atribuição da fonte. Por isso os XLSX são publicados exatamente como foram baixados, apenas compactados.
- **Atribuição:** Fonte: MJSP / Sinesp VDE. Os arquivos processados são elaboração própria do projeto a partir desses dados.
- Os dados são **contagens agregadas por município**; não contêm nomes nem informações pessoais.

## Links diretos para download

Os ZIPs ficam no [GitHub pessoal do projeto](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC). Cada link abaixo baixa um arquivo; depois de baixar, confira o SHA-256 (ver “Como conferir a integridade”).

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

Para usar com o projeto, salve cada ZIP no mesmo caminho da coluna “Arquivo”, dentro da pasta `dados/`.

## Como baixar e descompactar

1. Baixe o repositório (`git clone` ou o botão **Code → Download ZIP** do GitHub). Os ZIPs de dados ocupam cerca de **120 MiB**.
2. Confira o SHA-256 dos ZIPs (ver “Como conferir a integridade”, abaixo).
3. Descompacte os ZIPs **nas pastas indicadas**, a partir da pasta principal do projeto. No **Prompt de Comando (CMD)** do Windows (`zipfile` já vem com o Python; se o comando `py` não existir, use `python`):

```bat
:: Originais: os sete XLSX vão para dados\brutos\sinesp\
py -c "import glob, zipfile; [zipfile.ZipFile(z).extractall('dados/brutos/sinesp') for z in glob.glob('dados/brutos/sinesp_*_xlsx.zip')]"

:: Processados: recria dados\processados\etl_joinville\sinesp\
py -c "import zipfile; zipfile.ZipFile('dados/processados/SINESP_20_26_Petras_Ruben_Carvalho.zip').extractall('dados/processados')"
```

Também é possível usar **Extrair tudo** no Explorador de Arquivos, escolhendo as mesmas pastas de destino (`dados\brutos\sinesp` para os sete originais e `dados\processados` para o processado).

Resultado esperado:

```text
dados/
├── brutos/
│   └── sinesp/
│       ├── bancovde-2020.xlsx
│       ├── ...
│       └── bancovde-2026.xlsx
└── processados/
    └── etl_joinville/
        └── sinesp/
            ├── etl_catalogo_series.csv
            ├── etl_recorte_joinville_bruto.csv
            ├── etl_relatorio.json
            └── etl_sinesp_joinville_mensal.csv
```

## Como conferir a integridade

O arquivo [`SHA256SUMS.txt`](SHA256SUMS.txt) tem o SHA-256 de cada ZIP, e o [`manifesto_zips.json`](manifesto_zips.json) tem, para cada ZIP, os arquivos internos com tamanho e SHA-256. Para conferir os oito ZIPs de uma vez, no CMD, a partir da pasta principal (cada linha deve mostrar `OK`):

```bat
py -c "import hashlib; [print('OK ' if hashlib.sha256(open('dados/' + nome, 'rb').read()).hexdigest() == h else 'DIFERENTE ', nome) for h, nome in (linha.split() for linha in open('dados/SHA256SUMS.txt'))]"
```

Também é possível conferir um arquivo por vez no PowerShell, com `Get-FileHash dados\brutos\sinesp_2020_xlsx.zip -Algorithm SHA256`. O valor exibido deve ser igual ao da linha correspondente em `SHA256SUMS.txt`. O ETL também confere sozinho o SHA-256 de cada XLSX e só aceita a edição aprovada.

## Como usar depois de descompactar

```bat
:: ETL: lê os XLSX, refaz o recorte de Joinville e confere com a base aprovada
.\.venv\Scripts\python.exe scripts\etl_joinville.py
```

- **ETL:** com os XLSX descompactados, as etapas do Sinesp (1 a 10) são executadas e conferidas: a base reconstruída é igual à publicada. Na etapa 11, o ETL **para com uma mensagem** porque o acervo da SSP/SC não é publicado (ver abaixo). As saídas do Sinesp que ele gravaria na etapa 13 já estão no ZIP processado.
- **Notebook:** `notebooks/analise_seguranca_publica_joinville.ipynb` encontra o `bancovde-2026.xlsx` em `dados/brutos/sinesp/` e executa a etapa 3 (inspeção do arquivo original). As demais etapas do Sinesp usam `dashboard/data_publica/` e funcionam mesmo sem os ZIPs.
- **Painel Streamlit:** não precisa desta pasta; usa somente `dashboard/data_publica/`.

## Dados que permanecem apenas no computador do autor

| Dados | Motivo |
| --- | --- |
| PDFs, CSVs extraídos e tabelas tratadas da **SSP/SC**, também compactados em três ZIPs locais (`brutos/ssp_sc/ssp_sc_pdfs_originais.zip`, `brutos/ssp_sc/ssp_sc_csv_extraidos.zip` e `processados/ssp_sc/ssp_sc_joinville_processados.zip`) | A página da fonte informa “Todos os Direitos Reservados”, sem licença de reutilização, e a unidade “Fato Comunicado” ainda não tem definição confirmada. O [README da SSP/SC](brutos/ssp_sc/README.md) descreve os arquivos, e o [catálogo de fontes](brutos/ssp_sc/fontes_oficiais.csv) traz o endereço oficial e o SHA-256 de cada PDF, para quem quiser baixá-los na [SSP/SC — Segurança em Números](https://ssp.sc.gov.br/segurancaemnumeros/). |
| Edições anteriores dos XLSX do Sinesp | Não correspondem à versão aprovada; a edição atual pode ser baixada no portal do MJSP. |
| Arquivos intermediários de etapas anteriores e números da Prefeitura | Não fazem parte da base final do projeto. |
