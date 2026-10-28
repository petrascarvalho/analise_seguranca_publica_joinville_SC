# Recorte municipal Sinesp VDE

Rotina: `scripts/transform.py`. Entrada: XLSX nacional em `dados/brutos/sinesp/bancovde-ANO.xlsx`; para 2020–2022, os arquivos estão preservados no diretório histórico `dados/brutos/sinesp/pendente_validacao_origem/`. Saídas: `dados/processados/sinesp/bancovde-ANO-joinville-sc.xlsx`, os CSVs de feminicídio e o conjunto analítico CSV/Parquet em `dados/processados/analises/`.

O filtro compara `uf = SC` e `municipio = JOINVILLE`. As 14 colunas de origem, valores e ordem das linhas do recorte são preservados. Nenhuma linha municipal é agregada, corrigida ou deduplicada no XLSX derivado. A migração Python foi comparada com o legado JavaScript em 2023–2026; 2020–2022 foram comparados diretamente com as versões oficiais do MJSP. Evidências: [`../audit/sinesp_python_js_comparison.csv`](../auditoria/sinesp_python_js_comparison.csv) e [`../audit/sinesp_origem_2020_2022.csv`](../auditoria/sinesp_origem_2020_2022.csv).

| Ano | Linhas Joinville | Cobertura observada |
|---|---:|---|
| 2020 | 132 | janeiro–dezembro |
| 2021 | 132 | janeiro–dezembro |
| 2022 | 132 | janeiro–dezembro |
| 2023 | 132 | janeiro–dezembro |
| 2024 | 132 | janeiro–dezembro |
| 2025 | 144 | janeiro–dezembro |
| 2026 | 96 | janeiro–agosto, parcial |

Campos: `uf`, `municipio`, `evento`, `data_referencia`, `agente`, `arma`, `faixa_etaria`, `feminino`, `masculino`, `nao_informado`, `total_vitima`, `total`, `total_peso`, `abrangencia`.

O recorte contém vários indicadores de crimes, vítimas e atuação institucional; a tabela completa por indicador, ano e abrangência está em `documentacao/analises/tabelas/estatisticas_sinesp_indicador_ano.csv`. Linhas com `total` e `total_vitima` têm unidades distintas e são sumarizadas separadamente. Linhas por abrangência estadual, Polícia Federal e Polícia Rodoviária Federal permanecem discriminadas. `abrangencia` não identifica Polícia Civil, Polícia Militar ou Guarda Municipal de Joinville.

Não converta valores vazios em zero. Os campos `agente`, `arma` e `faixa_etaria` estão vazios em todos os 900 registros municipais nesta extração; isso limita análises por essas dimensões. O MJSP explica que valor numérico zero representa ausência de ocorrência e que os indicadores são informados pelos gestores estaduais.
