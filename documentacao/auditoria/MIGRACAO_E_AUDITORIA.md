# Migração e auditoria técnica

## Salvaguarda anterior à migração

Antes da primeira movimentação, foi criado `documentacao/auditoria/inventario_pre_migracao.csv`, com caminho, tamanho e SHA-256 de 82 arquivos, e `backup_pre_migracao_20261016/`, cópia integral dos mesmos arquivos e subpastas. Todos os 82 arquivos do backup foram comparados com o inventário; tamanhos e hashes coincidiram.

## Validações dos pipelines

- **Sinesp:** a saída Python foi comparada célula a célula com os XLSX gerados pelo fluxo JavaScript anterior. As 14 colunas e todas as linhas, valores e períodos coincidiram: 132 (2023), 132 (2024), 144 (2025) e 96 (2026). Os CSVs de feminicídio também coincidiram integralmente: 24, 24, 24 e 16 linhas. Registro em `documentacao/auditoria/sinesp_python_js_comparison.csv`.
- **SSP/SC:** o processamento dos 45 PDFs produziu 185, 192, 84 e 49 registros por ano de relatório. Os quatro CSVs são byte a byte idênticos aos CSVs anteriores à migração; seus hashes e números de registros foram verificados.
- **Furto/roubo:** a rotina Python exportou duas linhas para cada ano de 2023–2025, usando apenas os valores publicados pela Prefeitura.
- **2020–2022:** os arquivos foram preservados em `dados/brutos/sinesp/pendente_validacao_origem/`, mas estão excluídos do processamento até confirmação de proveniência.

## Riscos e decisões preservadas

- O XLSX de origem é nacional; o filtro municipal é exato por UF e município.
- O Sinesp não separa os resultados por Polícia Civil, Polícia Militar ou Guarda Municipal.
- Os boletins SSP repetem séries anuais e acumuladas entre edições. A aplicação não soma snapshots.
- A extração PDF registra documento e página. Variações de rótulo da violência doméstica em 2023 permanecem visíveis e não foram corrigidas.
- A aplicação inicial apresenta fontes e controles de qualidade, sem KPIs ou gráficos analíticos ainda não validados.
- O backup é local, está excluído pelo `.gitignore` e não deve ser enviado ao GitHub.

## Validação final e limites

`pytest` passou com 7 testes. `compileall` validou a sintaxe de `app.py`, `src/` e `tests/`. A aplicação iniciou localmente com status HTTP 200 no endpoint de saúde e na página raiz; o processo foi encerrado após a verificação.

O repositório de referência Mini_Projeto_SUS não foi acessível pelo mecanismo de navegação utilizado; nenhum código ou conteúdo dele foi copiado. Não houve commit, push, deploy ou publicação.
