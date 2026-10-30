# Dados da SSP/SC — Segurança em Números (Joinville/SC)

Esta pasta descreve os documentos da **Secretaria de Estado da Segurança Pública de Santa Catarina (SSP/SC)** usados no projeto e os arquivos que o projeto produziu a partir deles. É uma fonte **separada** do Sinesp/MJSP: os números das duas fontes não são somados nem misturados.

> **Situação de publicação:**
>
> - **No GitHub:** os **dados estatísticos**, ou seja, os CSVs extraídos (`ssp_sc_csv_extraidos.zip`) e as tabelas processadas de Joinville (`ssp_sc_joinville_processados.zip`), além deste `README.md` e do catálogo [`fontes_oficiais.csv`](fontes_oficiais.csv).
> - **Não republicados:** os **PDFs originais** (`ssp_sc_pdfs_originais.zip`), porque o site da fonte declara reserva de direitos. Eles podem ser baixados nos endereços oficiais do catálogo (seção 4).

## 1. Fonte

- **Órgão:** Secretaria de Estado da Segurança Pública de Santa Catarina (SSP/SC).
- **Página oficial:** [Segurança em Números](https://ssp.sc.gov.br/segurancaemnumeros/).
- **Documentos usados:** **45 PDFs**:
  - **42 boletins mensais** “Segurança em Números” (indicadores estaduais e municipais), com edições de janeiro/2023 a julho/2026: 11 edições de 2023 (não há edição de março de 2023 no acervo), 12 de 2024, 12 de 2025 e 7 de 2026;
  - **3 relatórios de violência doméstica** de todos os municípios de SC: 1º semestre de 2023, 2º semestre de 2023 e ano de 2024.
- **Endereços conferidos:** em 29/10/2026, cada um dos 45 PDFs foi baixado novamente do site da SSP/SC e comparado com o arquivo local: **os 45 são idênticos** (mesmo SHA-256). O endereço de cada um está em `fontes_oficiais.csv`.

## 2. Arquivos

### 2.1 PDFs originais — `ssp_sc_pdfs_originais.zip` (somente no computador do autor)

Os 45 PDFs exatamente como foram baixados, sem modificação. Eles são os **documentos oficiais**: qualquer número usado no projeto pode ser conferido neles.

- **Nome local:** `AAAA_MM_nome-original.pdf`. O prefixo `AAAA_MM` repete a pasta de envio do arquivo no site. Por exemplo, `2025_06_VIOLENCIA-DOMESTICA-2024-SC.pdf` corresponde a `https://ssp.sc.gov.br/wp-content/uploads/2025/06/VIOLENCIA-DOMESTICA-2024-SC.pdf`.

### 2.2 CSVs extraídos — `ssp_sc_csv_extraidos.zip` ([baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/brutos/ssp_sc/ssp_sc_csv_extraidos.zip))

São 45 CSVs (UTF-8), um para cada PDF, com o mesmo nome e extensão `.csv`.

**Atenção:** esses CSVs **não são publicações oficiais da SSP/SC**. São **arquivos derivados**, preparados no projeto para localizar a **página, a tabela e a linha** de cada célula das tabelas dos PDFs. O programa usa o CSV para encontrar o valor e depois **confere o valor no próprio PDF**.

### 2.3 Dados processados de Joinville — `dados/processados/ssp_sc/ssp_sc_joinville_processados.zip` ([baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/processados/ssp_sc/ssp_sc_joinville_processados.zip))

São as sete saídas da SSP/SC geradas pela versão atual do ETL (`scripts/etl_joinville.py`), dentro de `etl_joinville/ssp_sc/`.

| Arquivo | Conteúdo | Linhas |
| --- | --- | ---: |
| `violencia_domestica_joinville_tratada.csv` | Violência doméstica em Joinville: 9 categorias × 24 meses (2023–2024), unidade **“Fato Comunicado”** | 216 |
| `homicidios_boletins_joinville_versoes.csv` | Vítimas de homicídio em Joinville publicadas em cada edição dos boletins (anos de referência 2020 a 2026) | 294 |
| `homicidios_republicacoes_grupos.csv` | Comparação das republicações do mesmo período: 58 grupos, 41 com valores diferentes | 58 |
| `inventario_acervo_ssp_sc.csv` | Um registro por PDF: tipo, tamanho, SHA-256 do PDF e do CSV | 45 |
| `rastreabilidade_celulas_ssp_sc.csv` | Origem de cada valor usado: PDF, página, tabela e linha | 510 |
| `verificacoes_extracao_ssp_sc.csv` | Conferências feitas diretamente nos PDFs (todas aprovadas) | 159 |
| `relatorio_auditoria_ssp_sc.json` | Resumo das contagens e conferências | — |

Violência doméstica e homicídios ficam em **arquivos separados**, porque têm unidades diferentes (“Fato Comunicado” e “vítimas”). Nenhum arquivo soma categorias nem junta números da SSP/SC com os do Sinesp.

**Cuidados de leitura:**

- O significado operacional de “Fato Comunicado” **não foi esclarecido** nos PDFs: não deve ser lido como número de vítimas, de pessoas ou de ocorrências únicas.
- Os boletins republicam valores de períodos anteriores com números às vezes diferentes. Nenhuma versão foi escolhida como definitiva.

**Versões anteriores:** as tabelas da SSP/SC de etapas anteriores (16/10 e 28/10/2026) estão em `dados/processados/historico/ssp_sc_versoes_anteriores.zip` ([baixar](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC/raw/main/dados/processados/historico/ssp_sc_versoes_anteriores.zip)). São **históricas**: foram substituídas pelas saídas atuais e não devem ser usadas como resultado.

## 3. Relação com o ETL

| Etapa do ETL | O que usa |
| --- | --- |
| 11 — Leitura da SSP/SC | Exige os 45 PDFs em `dados/brutos/ssp_sc/pdfs/` e os 45 CSVs em `dados/brutos/ssp_sc/csv_extraidos/` |
| 12 — Tratamento e conferência | Lê as células indicadas pelos CSVs e confere cada valor no PDF |
| 13 — Exportação | Grava os sete arquivos da seção 2.3 em `dados/processados/etl_joinville/ssp_sc/` |

Sem os PDFs e os CSVs, o ETL executa e confere toda a parte do Sinesp (etapas 1 a 10) e **para na etapa 11** com uma mensagem explicativa. Com os CSVs publicados e os PDFs baixados da fonte (seção 4), as 14 etapas são executadas. O painel Streamlit não usa estes arquivos: no Streamlit Cloud, a seção da SSP/SC mostra a figura-resumo já publicada.

## 4. Como reproduzir

No Prompt de Comando (CMD), a partir da pasta principal do projeto. Se o comando `py` não existir, use `python`.

```bat
:: CSVs extraídos (publicados): vão para dados\brutos\ssp_sc\csv_extraidos\
py -c "import zipfile; zipfile.ZipFile('dados/brutos/ssp_sc/ssp_sc_csv_extraidos.zip').extractall('dados/brutos/ssp_sc/csv_extraidos')"

:: PDFs (não republicados): baixa os 45 dos endereços oficiais e grava só os que têm o SHA-256 do catálogo
py -c "import csv, hashlib, os, urllib.request; os.makedirs('dados/brutos/ssp_sc/pdfs', exist_ok=True); [(open('dados/brutos/ssp_sc/' + r['arquivo'], 'wb').write(d), print('OK', r['arquivo'])) if hashlib.sha256(d).hexdigest() == r['sha256'] else print('DIFERENTE (não gravado)', r['arquivo']) for r in csv.DictReader(open('dados/brutos/ssp_sc/fontes_oficiais.csv', encoding='utf-8')) if r['arquivo'].startswith('pdfs/') for d in [urllib.request.urlopen(urllib.request.Request(r['url_oficial'], headers={'User-Agent': 'Mozilla/5.0'})).read()]]"

:: Dados processados (publicados): recria dados\processados\etl_joinville\ssp_sc\
py -c "import zipfile; zipfile.ZipFile('dados/processados/ssp_sc/ssp_sc_joinville_processados.zip').extractall('dados/processados')"
```

- Cada linha do download deve mostrar `OK`. Se a SSP/SC alterar ou retirar algum PDF do site, a linha mostra `DIFERENTE` ou um erro, e o arquivo não é gravado. Nesse caso, a etapa 11 do ETL não é executada.
- **No computador do autor**, os PDFs também podem ser restaurados do ZIP local: `py -c "import zipfile; zipfile.ZipFile('dados/brutos/ssp_sc/ssp_sc_pdfs_originais.zip').extractall('dados/brutos/ssp_sc/pdfs')"`.

## 5. Catálogo `fontes_oficiais.csv`

O catálogo tem uma linha por arquivo, num total de 90 linhas: 45 PDFs e 45 CSVs.

| Coluna | Conteúdo |
| --- | --- |
| `arquivo` | Caminho dentro desta pasta (`pdfs/...` ou `csv_extraidos/...`), igual ao nome dentro do ZIP |
| `fonte` | SSP/SC, ou “Elaboração do projeto a partir de …” no caso dos CSVs |
| `tipo_documento` | Boletim mensal, relatório de violência doméstica ou CSV extraído (derivado) |
| `periodo_referencia` | Período escrito no cabeçalho do boletim, ou meses cobertos pelo relatório |
| `url_oficial` | Endereço oficial do PDF, conferido pelo SHA-256; “não se aplica” para os CSVs |
| `data_publicacao` | “não informado”: os documentos e a página não trazem data oficial de publicação |
| `sha256` | Impressão digital do arquivo, para conferir a integridade |
| `observacoes` | Data de envio ao site informada pelo servidor (não oficial), linhas do CSV e PDF de origem |

## 6. Integridade dos ZIPs

Criados com Python (`zipfile`, ZIP_DEFLATED, nível 9) e conferidos assim:

- teste de CRC;
- quantidade, nomes e tamanhos dos arquivos internos;
- SHA-256 de cada arquivo;
- descompactação completa comparada byte a byte com os originais.

| ZIP | Arquivos | Original | ZIP | SHA-256 do ZIP |
| --- | ---: | ---: | ---: | --- |
| `ssp_sc_pdfs_originais.zip` | 45 | 70,83 MiB | 46,40 MiB | `5631757879994f77eb8da0b602c16e8ac44556fa84c180b446a837c8b36e323c` |
| `ssp_sc_csv_extraidos.zip` | 45 | 1,72 MiB | 0,28 MiB | `cf9825cdca918b66ea4a2547ba0634423cd00b8a1304088a4f52c96563ddce12` |
| `ssp_sc_joinville_processados.zip` | 7 | 0,24 MiB | 0,02 MiB | `c0146c0876c15c1ea57214071d20cbf53f9b61bbd5bf20dd75824358aaafd80e` |

Os PDFs originais e os CSVs continuam também descompactados nas pastas `pdfs/` e `csv_extraidos/`; nada foi apagado ou alterado.

## 7. Condições de reutilização

- **Evidência sobre os direitos:** a página oficial informa “Copyright © 2023 Todos os Direitos Reservados SC - Governo de Santa Catarina” (conferido em 29/10/2026). Nem a página nem os PDFs indicam licença de reutilização.
- **PDFs originais:** por causa dessa reserva de direitos, **não são republicados na íntegra**. Eles continuam disponíveis gratuitamente no endereço oficial, e o catálogo permite obter exatamente os mesmos arquivos e conferir o SHA-256.
- **Dados estatísticos** (CSVs extraídos e tabelas processadas): são publicados pelo projeto, com atribuição da fonte. São contagens agregadas por município, e não o documento em si. Como **não há licença declarada**, a publicação não implica autorização da SSP/SC. Se a SSP/SC se opuser, esses arquivos podem ser retirados.
- **Autorização:** a republicação dos PDFs dependeria de autorização da SSP/SC, que pode ser pedida pelos canais oficiais do órgão, por exemplo pela Lei de Acesso à Informação.
- **Dados pessoais:** nos CSVs extraídos e nos arquivos processados, não foram encontrados nomes, CPFs, e-mails ou telefones.

Avaliação técnica de reutilização, não parecer jurídico.

Fonte: SSP/SC — Segurança em Números. Tabelas e conferências são elaboração própria do projeto.
