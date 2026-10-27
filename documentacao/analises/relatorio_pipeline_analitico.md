# Relatório de auditoria do pipeline analítico

Data de execução: 16/10/2026. Escopo: fontes locais preservadas em `dados/brutos/` e dados derivados exclusivamente de Joinville/SC.

## Fontes utilizadas

| Base | Responsável | Arquivo/forma coletada | Registros analisados | Período |
|---|---|---|---:|---|
| Sinesp VDE | MJSP e gestores estaduais de estatística | XLSX nacional, recortado em Python por `SC`/`JOINVILLE`; CSV e Parquet derivados | 900 | 2020–2025; jan–ago/2026 |
| Boletins SSP/SC | Secretaria de Estado da Segurança Pública de SC | 45 PDFs; tabelas Joinville extraídas para CSV e Parquet | 510 linhas de origem, incluindo snapshots | homicídio em boletins até jul/2026; violência doméstica mensal 2023–2024 |
| Furto e roubo municipal | Prefeitura de Joinville / SEPROT | Valores publicados em notícia oficial, guardados em CSV e Parquet com URL | 6 | jan–dez/2023–2025 |

Fontes consultadas, mas não incorporadas como bases analíticas: atendimentos da Guarda Municipal sem série estruturada/comparável disponível no conjunto; números de furto/roubo estaduais dos boletins SSP/SC, por não serem municipais; registros atribuídos separadamente à Polícia Civil e Militar, não identificados nas bases agregadas utilizadas.

## Procedência Sinesp de 2020–2022

A página de downloads do MJSP lista os arquivos BancoVDE de 2020, 2021 e 2022 com atualização publicada em 01/10/2026. Cada planilha tem 14 colunas e uma aba nominal do ano. O registro completo de URLs, tamanhos e SHA-256 local/oficial está em [`sinesp_origem_2020_2022.csv`](../auditoria/sinesp_origem_2020_2022.csv).

- 2020: 764.701 linhas incluindo cabeçalho nas duas versões, 14 colunas, aba `2020`; SHA-256 diferente e tamanho diferente, mas comparação de todas as células sem divergência.
- 2021: 764.733 linhas incluindo cabeçalho; SHA-256 e tamanho idênticos.
- 2022: 764.653 linhas incluindo cabeçalho; SHA-256 e tamanho idênticos.

Os três anos estão validados e entram nos resultados. Os arquivos originais locais foram preservados; o download oficial temporário não os substituiu.

## Validações por fonte e seleção de períodos

O Sinesp filtrado tem 132 linhas em cada ano de 2020–2024, 144 em 2025 e 96 em 2026. O último ano contém oito meses e está marcado parcial. O filtro `SC`/`JOINVILLE` é verificado em todas as linhas. Os campos vazios foram mantidos vazios; não são convertidos em zero.

Nos boletins SSP/SC, o arquivo municipal contém 294 linhas de homicídio reapresentadas por boletins e 216 linhas mensais de violência doméstica. As 294 linhas de homicídio são snapshots documentais, não 294 unidades independentes. Para o gráfico anual, foi retido o último valor completo encontrado para cada ano; para comparação parcial, foi usado apenas o boletim de julho de 2026 para todos os anos comparados.

| Ano de referência | Homicídios, ano completo | Data da última publicação selecionada |
|---:|---:|---|
| 2020 | 66 | 31/12/2023 |
| 2021 | 62 | 31/01/2025 |
| 2022 | 49 | 31/12/2025 |
| 2023 | 56 | 31/07/2026 |
| 2024 | 37 | 31/07/2026 |
| 2025 | 32 | 31/07/2026 |

O boletim de julho de 2026 registra 36, 20, 17 e 22 vítimas de homicídio de janeiro a julho, respectivamente, em 2023, 2024, 2025 e 2026. O período de 2026 é parcial e sujeito a revisão.

A comparação dos totais anuais de homicídio publicados por Sinesp e SSP/SC encontra igualdade em 2021 (62) e 2022 (49), e diferenças em 2020 (62 vs. 66), 2023 (55 vs. 56), 2024 (36 vs. 37) e 2025 (29 vs. 32). Nenhuma fonte foi corrigida ou substituída pela outra. Em 2026, ambos indicam 22, mas Sinesp cobre janeiro–agosto e a SSP/SC janeiro–julho; esse valor não é tratado como comparação equivalente. A reconciliação fica em [`../../documentacao/analises/tabelas/comparacao_fontes_homicidio.csv`](tabelas/comparacao_fontes_homicidio.csv).

As 9 categorias mensais de violência doméstica aparecem em cada mês de 2023 e 2024. Totais por categoria:

| Indicador normalizado | 2023 | 2024 |
|---|---:|---:|
| Ameaça | 1.957 | 2.085 |
| Calúnia | 109 | 119 |
| Difamação | 190 | 211 |
| Estupro | 22 | 30 |
| Injúria | 541 | 716 |
| Injúria real | 2 | 6 |
| Lesão corporal grave ou gravíssima - Dolosa | 19 | 10 |
| Lesão corporal leve - Dolosa | 989 | 959 |
| Vias de fato | 229 | 281 |

O campo original `indicador` é preservado. O mapeamento foi limitado às duas categorias de lesão corporal cuja grafia é publicada com `0` em 2023 e hífen em 2024; a conferência visual consta em [`evidencia_grafia_violencia_domestica_2023.png`](../auditoria/evidencia_grafia_violencia_domestica_2023.png). Após a padronização, cada chave ano/mês/indicador é única.

Na notícia municipal da Prefeitura, os totais anuais foram conferidos contra a transcrição com URL de origem: furtos 8.865, 8.730 e 8.372; roubos 933, 593 e 476 em 2023, 2024 e 2025. O arquivo não fornece valor de 2026.

## Saídas e qualidade

CSV e Parquet foram escritos e relidos. Contagem, nomes de colunas e valores foram comparados com os dados em memória antes de marcar o estado `validado`. SHA-256 das seis saídas está em [`../../documentacao/analises/tabelas/validacao_csv_parquet.csv`](tabelas/validacao_csv_parquet.csv). Os conjuntos têm 900 linhas/14 campos (Sinesp), 510/11 (SSP/SC) e 6/8 (Prefeitura).

As estatísticas descritivas incluem 79 combinações Sinesp indicador/abrangência/ano, 6 anos completos e 4 períodos parciais SSP/SC, 18 combinações de categoria de violência doméstica/ano, 6 observações municipais de furto/roubo e 7 linhas na comparação cruzada de homicídio. As fontes constam em cada tabela e nos gráficos PNG de `documentacao/analises/graficos/`.

Os valores ausentes em Sinesp permanecem como ausentes, não zero. A tabela `documentacao/analises/tabelas/auditoria_campos_vazios.csv` quantifica vazios por base/campo; `agente`, `arma` e `faixa_etaria` estão sem valor em todos os 900 registros municipais. A maioria dos eventos tem medida em `total_vitima`, enquanto mandados de prisão cumpridos usam `total`; as dimensões não foram fundidas. A SSP tem 216 células sem data de atualização nos relatórios temáticos, cujos valores são mensais.

## Testes e estado

Os testes automatizados verificam hashes dos três arquivos históricos locais contra o inventário de procedência, hashes dos 53 arquivos brutos únicos contra o mapa de migração, contagens e campos Sinesp, referências a documentos e páginas SSP/SC, preservação dos rótulos, unicidade mensal, valores de controle das fontes e releitura de CSV/Parquet. A suíte terminou com 12 testes aprovados. A aplicação Streamlit iniciou em endereço local e respondeu `200 / ok` na checagem de saúde. Nenhum arquivo foi excluído, e nenhum commit, push ou deploy foi feito.

Pendências: conferir termos/licenças para redistribuição dos dados brutos; obter série validada de atendimentos da Guarda Municipal e totais municipais de furto/roubo de 2026; integrar os gráficos ao Streamlit; e confirmar novas revisões futuras dos boletins antes de atualizar os resultados.
