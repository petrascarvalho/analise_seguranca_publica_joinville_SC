# CSVs complementares — Joinville/SC

## Furto e roubo

`dados/processados/prefeitura/furto_roubo_joinville_2023.csv` a `..._2025.csv` contêm os totais anuais publicados pela [Prefeitura de Joinville/SEPROT](https://www.joinville.sc.gov.br/noticias/indices-de-criminalidade-tem-reducao-em-joinville-pelo-terceiro-ano-consecutivo/). A rotina está em `scripts/transform.py`; os valores foram transcritos da notícia e não são obtidos por scraping ou por uma base tabular baixada.

Campos: `uf`, `municipio`, `ano`, `indicador`, `periodo`, `quantidade`, `fonte`, `url_fonte`. Há 2 linhas por ano: Furto e Roubo. A série cobre 2023–2025. Não há valor municipal de 2026 validado.

## Feminicídio e tentativa

`dados/processados/sinesp/feminicidio_sinesp_joinville_2023.csv` a `..._2026.csv` são exportações de linhas dos XLSX municipais Sinesp filtradas para `Feminicídio` e `Tentativa de feminicídio`, mantendo as 14 colunas originais. A comparação Python/JavaScript confirmou 24, 24, 24 e 16 registros e igualdade de todas as células nos anos 2023–2026.

Os totais de furto/roubo não devem ser misturados com indicadores do Sinesp ou com atendimentos da Guarda Municipal: fonte, definição e unidade são diferentes.
