# Inspeção — Etapa 1: leitura e visualização dos dados brutos

Inspeção realizada em 2026-10-16 20:22 (horário local).

Nenhum script, arquivo original, CSV ou resultado anterior foi alterado. Não foi executado o pipeline completo. O relatório registra apenas inventário e visualizações de arquivos existentes; o recorte municipal abaixo foi mantido em memória.

## Sinesp — arquivos originais

| Arquivo | Formato | Tamanho (bytes) | Ano no nome | Situação registrada |
|---|---:|---:|---:|---|
| `bancovde-2023.xlsx` | XLSX | 24,375,927 | 2023 | arquivo original |
| `bancovde-2024.xlsx` | XLSX | 24,388,231 | 2024 | arquivo original |
| `bancovde-2025.xlsx` | XLSX | 26,643,031 | 2025 | arquivo original |
| `bancovde-2026.xlsx` | XLSX | 18,023,581 | 2026 | arquivo original |
| `bancovde-2020.xlsx` | XLSX | 25,875,698 | 2020 | origem pendente de validação |
| `bancovde-2021.xlsx` | XLSX | 24,343,073 | 2021 | origem pendente de validação |
| `bancovde-2022.xlsx` | XLSX | 24,358,662 | 2022 | origem pendente de validação |

O ano acima vem do nome do arquivo; não foi usado para afirmar cobertura mensal completa. Os arquivos 2020–2022 continuam identificados como pendentes de validação de origem.

### Sinesp 2023 — amostra original lida com Pandas

Arquivo: `dados/brutos/sinesp/bancovde-2023.xlsx`; planilha `2023`; dimensão declarada pelo XLSX: 764,773 × 14.
Pandas leu somente as primeiras 20 linhas (`nrows=20`); portanto o `shape` abaixo é da amostra, não da base completa.

Amostra: `(20, 14)`. Colunas: `uf, municipio, evento, data_referencia, agente, arma, faixa_etaria, feminino, masculino, nao_informado, total_vitima, total, total_peso, abrangencia`.

Tipos observados na amostra:

```text
uf                            str
municipio                     str
evento                        str
data_referencia    datetime64[us]
agente                    float64
arma                      float64
faixa_etaria              float64
feminino                    int64
masculino                   int64
nao_informado               int64
total_vitima                int64
total                     float64
total_peso                float64
abrangencia                   str
```

Primeiras 20 linhas, sem filtro municipal:

```text
uf  municipio           evento data_referencia  agente  arma  faixa_etaria  feminino  masculino  nao_informado  total_vitima  total  total_peso abrangencia
AC ACRELÂNDIA      Feminicídio      2023-01-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA      Feminicídio      2023-02-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA      Feminicídio      2023-03-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA      Feminicídio      2023-04-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA      Feminicídio      2023-05-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA      Feminicídio      2023-06-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA      Feminicídio      2023-07-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA      Feminicídio      2023-08-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA      Feminicídio      2023-09-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA      Feminicídio      2023-10-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA      Feminicídio      2023-11-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA      Feminicídio      2023-12-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA Homicídio doloso      2023-01-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA Homicídio doloso      2023-02-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA Homicídio doloso      2023-03-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA Homicídio doloso      2023-04-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA Homicídio doloso      2023-05-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA Homicídio doloso      2023-06-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA Homicídio doloso      2023-07-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
AC ACRELÂNDIA Homicídio doloso      2023-08-01     NaN   NaN           NaN         0          0              0             0    NaN         NaN    Estadual
```

### Recorte Joinville/SC visto no mesmo XLSX

O quadro seguinte é apenas uma seleção em memória das linhas em que os campos originais indicam `uf = SC` e `municipio = JOINVILLE`. Não foi gravado nem substituído arquivo. A leitura XML existente preserva a data de referência como número serial do Excel nesta visualização.

Quantidade no recorte de 2023: 132 linhas; dimensões: `(132, 14)`.

Primeiras 10 linhas do recorte:

```text
uf municipio      evento  data_referencia agente arma faixa_etaria  feminino  masculino  nao_informado  total_vitima  total total_peso abrangencia
SC JOINVILLE Feminicídio            44927   None None         None       0.0        0.0            0.0           0.0    NaN       None    Estadual
SC JOINVILLE Feminicídio            44958   None None         None       NaN        0.0            0.0           0.0    NaN       None    Estadual
SC JOINVILLE Feminicídio            44986   None None         None       0.0        0.0            0.0           0.0    NaN       None    Estadual
SC JOINVILLE Feminicídio            45017   None None         None       0.0        0.0            0.0           0.0    NaN       None    Estadual
SC JOINVILLE Feminicídio            45047   None None         None       0.0        0.0            0.0           0.0    NaN       None    Estadual
SC JOINVILLE Feminicídio            45078   None None         None       0.0        0.0            0.0           0.0    NaN       None    Estadual
SC JOINVILLE Feminicídio            45108   None None         None       1.0        0.0            0.0           1.0    NaN       None    Estadual
SC JOINVILLE Feminicídio            45139   None None         None       0.0        0.0            0.0           0.0    NaN       None    Estadual
SC JOINVILLE Feminicídio            45170   None None         None       0.0        0.0            0.0           0.0    NaN       None    Estadual
SC JOINVILLE Feminicídio            45200   None None         None       0.0        0.0            0.0           0.0    NaN       None    Estadual
```

## SSP/SC — PDFs originais

Inventário de PDFs em `dados/brutos/ssp_sc/pdfs/`. A data é a data de atualização identificada no texto da primeira página; ela indica a edição do boletim e não significa que todas as tabelas tenham somente esse período de referência. Nos três PDFs temáticos de violência doméstica, a primeira página não apresentou a expressão de atualização pesquisada.

| Arquivo | Formato | Tamanho (bytes) | Atualização na 1ª página / referência identificada |
|---|---:|---:|---|
| `2024_05_01_janeiro_24.pdf` | PDF | 1,816,911 | 31/01/2024 |
| `2024_05_02_fevereiro_24.pdf` | PDF | 1,814,821 | 29/02/2024 |
| `2024_05_03_marco_24.pdf` | PDF | 1,809,554 | 31/03/2024 |
| `2024_05_23.01_janeiro.pdf` | PDF | 919,875 | 31/01/2023 |
| `2024_05_23.02_fevereiro.pdf` | PDF | 1,824,085 | 28/02/2023 |
| `2024_05_23.04_abril.pdf` | PDF | 1,825,992 | 30/04/2023 |
| `2024_05_23.05_maio.pdf` | PDF | 1,829,596 | 31/05/2023 |
| `2024_05_23.06_junho.pdf` | PDF | 1,834,924 | 30/06/2023 |
| `2024_05_23.07_julho.pdf` | PDF | 1,819,511 | 31/07/2023 |
| `2024_05_23.08_agosto.pdf` | PDF | 1,816,531 | 31/08/2023 |
| `2024_05_23.09_setembro.pdf` | PDF | 1,816,315 | 30/09/2023 |
| `2024_05_23.10_outubro.pdf` | PDF | 1,815,195 | 31/10/2023 |
| `2024_05_23.11_novembro.pdf` | PDF | 1,814,202 | 30/11/2023 |
| `2024_05_23.12_dezembro.pdf` | PDF | 1,818,177 | 31/12/2023 |
| `2024_06_04_abril_24.pdf` | PDF | 1,810,981 | 30/04/2024 |
| `2024_06_05_maio_24.pdf` | PDF | 1,816,784 | 31/05/2024 |
| `2024_07_06-junho-2.pdf` | PDF | 1,251,301 | 30/06/2024 |
| `2024_08_07-julho-1.pdf` | PDF | 1,695,964 | 31/07/2024 |
| `2024_09_08-agosto-1.pdf` | PDF | 631,578 | 31/08/2024 |
| `2024_10_Relatorio-SET-2024-Ratificado-1.pdf` | PDF | 641,399 | 30/09/2024 |
| `2024_11_RELATORIO-OUT.pdf` | PDF | 677,190 | 31/10/2024 |
| `2024_12_NOV-1.pdf` | PDF | 637,914 | 30/11/2024 |
| `2025_02_01-janeiro-1.pdf` | PDF | 1,803,861 | 31/01/2025 |
| `2025_02_12-dezembro-1.pdf` | PDF | 1,695,614 | 31/12/2024 |
| `2025_03_02-fevereiro-25.pdf` | PDF | 1,804,256 | 28/02/2025 |
| `2025_04_03-marco.pdf` | PDF | 1,803,248 | 31/03/2025 |
| `2025_06_04-abril-3.pdf` | PDF | 1,799,488 | 30/04/2025 |
| `2025_06_05-maio-1-1.pdf` | PDF | 1,801,377 | 31/05/2025 |
| `2025_06_VIOLENCIA-DOMESTICA-1o-SEMESTRE-2023.pdf` | PDF | 1,184,632 | não identificada na 1ª página; ver ano/tema no nome |
| `2025_06_VIOLENCIA-DOMESTICA-2024-SC.pdf` | PDF | 2,201,254 | não identificada na 1ª página; ver ano/tema no nome |
| `2025_06_VIOLENCIA-DOMESTICA-2o-SEMESTRE-2023.pdf` | PDF | 1,157,819 | não identificada na 1ª página; ver ano/tema no nome |
| `2025_08_06-junho-2025.pdf` | PDF | 1,803,764 | 30/06/2025 |
| `2025_08_07-julho-2025.pdf` | PDF | 1,803,563 | 31/07/2025 |
| `2025_10_08-agosto.pdf` | PDF | 1,806,382 | 31/08/2025 |
| `2025_10_09-setembro.pdf` | PDF | 1,806,649 | 30/09/2025 |
| `2025_11_10-outubro.pdf` | PDF | 1,805,063 | 31/10/2025 |
| `2025_12_11-novembro.pdf` | PDF | 1,805,145 | 30/11/2025 |
| `2026_01_12-dezembro.pdf` | PDF | 1,805,063 | 31/12/2025 |
| `2026_02_01-janeiro-2026.pdf` | PDF | 1,810,976 | 31/01/2026 |
| `2026_03_02-fevereiro-2026.pdf` | PDF | 1,807,843 | 28/02/2026 |
| `2026_05_03-marco-2026.pdf` | PDF | 1,806,688 | 31/03/2026 |
| `2026_05_04-abril-2026.pdf` | PDF | 1,802,731 | 30/04/2026 |
| `2026_06_05-maio.pdf` | PDF | 1,805,150 | 31/05/2026 |
| `2026_07_06-junho-de-2026.pdf` | PDF | 1,805,236 | 30/06/2026 |
| `2026_08_2026-julho.pdf` | PDF | 1,807,235 | 31/07/2026 |

Total inventariado: 45 PDFs. O arquivo `segurancaemnumeros.html` também está na pasta, mas não é PDF e não foi tratado como boletim tabular nesta inspeção.

Arquivo adicional no diretório SSP/SC: `segurancaemnumeros.html` — HTML, 198.353 bytes; página de referência arquivada localmente, sem ano de referência único.

### Visualizações dos PDFs, sem nova extração

A página 8 de `2024_05_01_janeiro_24.pdf` contém a tabela “Nº de vítimas por ano” e a tabela de vítimas no período; a linha Joinville é municipal. A página 18 de `2025_06_VIOLENCIA-DOMESTICA-2024-SC.pdf` contém linhas de Joinville por indicador. As imagens exibidas na conversa foram renderizadas somente para visualização, em pasta temporária; nenhum PDF foi alterado.

### Representação tabular SSP/SC já existente

Os CSVs abaixo já estavam no projeto antes desta inspeção. Foram lidos diretamente; não houve nova extração, limpeza ou normalização. O campo `indicador_normalizado` já consta desses arquivos como resultado de processamento anterior.

| Arquivo existente | Formato | Linhas × colunas | Tamanho (bytes) |
|---|---:|---:|---:|
| `ssp_joinville_2023.csv` | CSV | 185 × 11 | 25,435 |
| `ssp_joinville_2024.csv` | CSV | 192 × 11 | 25,522 |
| `ssp_joinville_2025.csv` | CSV | 84 × 11 | 12,556 |
| `ssp_joinville_2026.csv` | CSV | 49 × 11 | 7,474 |

Colunas já presentes: `ano_relatorio`, `data_atualizacao`, `municipio`, `indicador`, `indicador_normalizado`, `periodo_tipo`, `ano_referencia`, `periodo_referencia`, `valor`, `arquivo_pdf`, `pagina_pdf`.

Exemplo literal do CSV existente `ssp_joinville_2024.csv` (linhas iniciais):

```text
 ano_relatorio data_atualizacao municipio                  indicador      indicador_normalizado      periodo_tipo  ano_referencia periodo_referencia  valor               arquivo_pdf pagina_pdf
          2024       31/01/2024 JOINVILLE Nº de vítimas de homicídio Nº de vítimas de homicídio      ano completo            2021               2021     68 2024_05_01_janeiro_24.pdf          8
          2024       31/01/2024 JOINVILLE Nº de vítimas de homicídio Nº de vítimas de homicídio      ano completo            2022               2022     51 2024_05_01_janeiro_24.pdf          8
          2024       31/01/2024 JOINVILLE Nº de vítimas de homicídio Nº de vítimas de homicídio      ano completo            2023               2023     58 2024_05_01_janeiro_24.pdf          8
          2024       31/01/2024 JOINVILLE Nº de vítimas de homicídio Nº de vítimas de homicídio período acumulado            2021      01/01 - 31/01      6 2024_05_01_janeiro_24.pdf          8
```

Exemplo literal de registros associados ao PDF temático de violência doméstica de 2024:

```text
 ano_relatorio data_atualizacao municipio indicador indicador_normalizado periodo_tipo  ano_referencia periodo_referencia  valor                             arquivo_pdf pagina_pdf
          2024              NaN JOINVILLE    Ameaça                Ameaça       mensal            2024            2024-01    209 2025_06_VIOLENCIA-DOMESTICA-2024-SC.pdf      18;55
          2024              NaN JOINVILLE    Ameaça                Ameaça       mensal            2024            2024-02    200 2025_06_VIOLENCIA-DOMESTICA-2024-SC.pdf      18;55
          2024              NaN JOINVILLE    Ameaça                Ameaça       mensal            2024            2024-03    204 2025_06_VIOLENCIA-DOMESTICA-2024-SC.pdf      18;55
```

A coluna `pagina_pdf` aparece no CSV como foi salva anteriormente; no exemplo doméstico, ela contém `18;55`. Esta inspeção não reinterpretou esse valor. O PDF e a página 18 foram abertos visualmente para comparação.

## Prefeitura de Joinville / SEPROT

### CSVs de transcrição anterior

Os três CSVs já estavam em `dados/processados/prefeitura/`. São transcrições anteriores de números publicados pela Prefeitura; não são arquivos originais baixados em formato aberto nesta etapa.

| Arquivo | Formato | Linhas × colunas | Tamanho (bytes) |
|---|---:|---:|---:|
| `furto_roubo_joinville_2023.csv` | CSV | 2 × 8 | 469 |

Conteúdo de `furto_roubo_joinville_2023.csv`:

```text
uf municipio  ano indicador          periodo  quantidade                            fonte                                                                                                                 url_fonte
SC JOINVILLE 2023     Furto janeiro-dezembro        8865 Prefeitura de Joinville / SEPROT https://www.joinville.sc.gov.br/noticias/indices-de-criminalidade-tem-reducao-em-joinville-pelo-terceiro-ano-consecutivo/
SC JOINVILLE 2023     Roubo janeiro-dezembro         933 Prefeitura de Joinville / SEPROT https://www.joinville.sc.gov.br/noticias/indices-de-criminalidade-tem-reducao-em-joinville-pelo-terceiro-ano-consecutivo/
```

| `furto_roubo_joinville_2024.csv` | CSV | 2 × 8 | 469 |

Conteúdo de `furto_roubo_joinville_2024.csv`:

```text
uf municipio  ano indicador          periodo  quantidade                            fonte                                                                                                                 url_fonte
SC JOINVILLE 2024     Furto janeiro-dezembro        8730 Prefeitura de Joinville / SEPROT https://www.joinville.sc.gov.br/noticias/indices-de-criminalidade-tem-reducao-em-joinville-pelo-terceiro-ano-consecutivo/
SC JOINVILLE 2024     Roubo janeiro-dezembro         593 Prefeitura de Joinville / SEPROT https://www.joinville.sc.gov.br/noticias/indices-de-criminalidade-tem-reducao-em-joinville-pelo-terceiro-ano-consecutivo/
```

| `furto_roubo_joinville_2025.csv` | CSV | 2 × 8 | 469 |

Conteúdo de `furto_roubo_joinville_2025.csv`:

```text
uf municipio  ano indicador          periodo  quantidade                            fonte                                                                                                                 url_fonte
SC JOINVILLE 2025     Furto janeiro-dezembro        8372 Prefeitura de Joinville / SEPROT https://www.joinville.sc.gov.br/noticias/indices-de-criminalidade-tem-reducao-em-joinville-pelo-terceiro-ano-consecutivo/
SC JOINVILLE 2025     Roubo janeiro-dezembro         476 Prefeitura de Joinville / SEPROT https://www.joinville.sc.gov.br/noticias/indices-de-criminalidade-tem-reducao-em-joinville-pelo-terceiro-ano-consecutivo/
```

A notícia oficial da Prefeitura, publicada em 13/01/2026, informa os totais anuais: 2023 — 8.865 furtos e 933 roubos; 2024 — 8.730 furtos e 593 roubos; 2025 — 8.372 furtos e 476 roubos. Esses são os valores transcritos nos CSVs. A notícia também apresenta indicadores específicos de furto/roubo de veículos, que são diferentes destes totais gerais.

## Significado das colunas visíveis

### Sinesp

| Coluna | Significado do rótulo nesta visualização |
|---|---|
| `uf` | Sigla da unidade da federação. |
| `municipio` | Município registrado na linha. |
| `evento` | Nome do indicador/evento de segurança. |
| `data_referencia` | Data de referência mensal; o Pandas lê datas na amostra. |
| `agente`, `arma`, `faixa_etaria` | Dimensões de classificação do registro; aparecem vazias nas linhas iniciais exibidas. |
| `feminino`, `masculino`, `nao_informado` | Contagens separadas por sexo conforme os rótulos da base. |
| `total_vitima` | Campo de total de vítimas. |
| `total`, `total_peso` | Campos chamados total e total ponderado/peso no arquivo; a definição detalhada deve ser conferida no dicionário oficial antes de interpretar. |
| `abrangencia` | Campo de abrangência tal como publicado. Nas linhas municipais do recorte visualizado aparece `Estadual`; isso foi reproduzido literalmente, sem inferir que o município seja estadual. |

### SSP/SC

| Coluna | Significado |
|---|---|
| `ano_relatorio`, `data_atualizacao` | Ano do relatório e atualização indicada pelo extrator anterior; alguns temas não têm data preenchida. |
| `municipio` | Município da linha extraída da tabela. |
| `indicador` | Texto do indicador preservado na representação CSV. |
| `indicador_normalizado` | Campo de padronização que já existia no CSV; não foi recalculado nesta inspeção. |
| `periodo_tipo`, `ano_referencia`, `periodo_referencia` | Tipo e rótulo do período a que o valor se refere. |
| `valor` | Valor numérico transcrito da tabela. |
| `arquivo_pdf`, `pagina_pdf` | Referência ao PDF e página(s) registradas no CSV. |

### Prefeitura/SEPROT

| Coluna | Significado |
|---|---|
| `uf`, `municipio`, `ano` | Local e ano indicado na transcrição. |
| `indicador`, `periodo`, `quantidade` | Tipo de crime, intervalo informado e valor transcrito. |
| `fonte`, `url_fonte` | Atribuição e endereço da publicação municipal. |

## Limites desta etapa

- O Sinesp 2023 tem 764.773 linhas declaradas; a leitura Pandas geral foi limitada a 20 linhas. O recorte municipal mostrado foi lido separadamente e mantido em memória.
- As fontes apresentam tabelas e unidades diferentes. Não foram consolidadas.
- Os CSVs SSP/SC e Prefeitura são representações/processamentos anteriores, não novas extrações feitas nesta inspeção.
- O campo `abrangencia` no Sinesp deve ser interpretado com apoio do dicionário oficial; aqui foi exibido sem alteração.
- A notícia municipal contém ainda métricas específicas de veículos e atendimento policial; os CSVs transcritos aqui incluem apenas furto e roubo totais.
- Nenhuma limpeza, padronização, exclusão, deduplicação, análise estatística, exportação de dados tratados ou execução do pipeline foi feita.

## Proposta antes de alterar o script Python

Na próxima etapa autorizada, a proposta de leitura é ajustar o script principal para somente: localizar e listar arquivos; ler 20 linhas do XLSX original com Pandas e imprimir `shape`, `columns` e `dtypes`; formar em memória um recorte Joinville/SC; abrir visualmente páginas selecionadas dos PDFs e ler os CSVs SSP já existentes com suas referências de arquivo/página; ler os CSVs de transcrição SEPROT; e registrar a inspeção em texto. Nenhuma das etapas 2–12 será iniciada sem orientação específica. A leitura do Sinesp municipal deve usar apenas um leitor de seleção existente, explicado claramente, sem gravar nada.

## Referências

- Prefeitura de Joinville / SEPROT: https://www.joinville.sc.gov.br/noticias/indices-de-criminalidade-tem-reducao-em-joinville-pelo-terceiro-ano-consecutivo/
- Sinesp VDE, Ministério da Justiça e Segurança Pública: https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/diretoria-de-gestao-e-integracao-de-informacoes-1/produtos/vde
- Os PDFs SSP/SC citados estão preservados em `dados/brutos/ssp_sc/pdfs/`; CSVs existentes em `dados/processados/ssp_sc/`.
