# Origem dos arquivos Sinesp VDE

Os arquivos de 2020–2026 foram confrontados com os XLSX anuais publicados pelo Ministério da Justiça e Segurança Pública (MJSP). A página oficial lista as versões de 2015 a 2026; os arquivos de 2020–2022 aparecem com última modificação em 01/10/2026. Os recortes municipais são derivados e nunca substituem os originais.

- Página oficial: https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023
- Catálogo de downloads: https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados
- Padrão oficial de download direto: `https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/bancovde-ANO.xlsx/@@download/file`
- Arquivos 2023–2026: `dados/brutos/sinesp/`.
- Arquivos 2020–2022 preservados em `dados/brutos/sinesp/pendente_validacao_origem/`; o caminho antigo da migração foi mantido, mas a procedência agora está **validada**.
- Evidências por arquivo, incluindo tamanho e SHA-256: [`../audit/sinesp_origem_2020_2022.csv`](../auditoria/sinesp_origem_2020_2022.csv).
- Cópia de segurança do estado pré-migração: `backup_pre_migracao_20261016/`.

Em 2021 e 2022, tamanho e SHA-256 local coincidem com os arquivos oficiais atuais. Para 2020, tamanho e SHA-256 são distintos, mas a comparação de todas as 764.701 linhas/células, incluindo cabeçalho, foi idêntica; os dois arquivos têm 14 colunas e a aba `2020`. Assim, os três anos foram validados e incluídos nos indicadores. A cópia oficial foi mantida apenas em pasta temporária e não foi copiada sobre o original local.

Os tamanhos e hashes dos 82 arquivos que existiam antes da migração seguem no inventário [`../audit/inventario_pre_migracao.csv`](../auditoria/inventario_pre_migracao.csv). O MJSP informa que os dados são enviados pelos gestores estaduais via Sinesp VDE e que valor zero significa ausência de ocorrência no período. Esta base é agregada e não separa individualmente Polícia Civil, Polícia Militar ou Guarda Municipal.
