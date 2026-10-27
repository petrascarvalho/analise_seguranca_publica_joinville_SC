# Relatório de reorganização e integridade

Data: 16/10/2026

## Escopo realizado

A organização local foi atualizada para `dados/brutos/`, `dados/processados/` e `documentacao/`. Foram movidos 158 arquivos, conforme o inventário SHA-256 [`inventario_sha256_pre_reorganizacao.csv`](inventario_sha256_pre_reorganizacao.csv). O inventário registra caminho de origem, destino planejado, tamanho e SHA-256 calculado antes da movimentação.

## Conferência de integridade

- Os 125 arquivos de `data/` (originais e resultados processados) mantêm o SHA-256 anterior à movimentação.
- Dos 18 gráficos/tabelas, 16 mantêm hash idêntico. Dois arquivos de metadados tiveram somente referências de caminho atualizadas: `manifesto_analise.json` e `validacao_csv_parquet.csv`. Os gráficos e os dados tabulares não foram recalculados ou alterados.
- Dez arquivos de documentação foram atualizados para apontar aos novos caminhos e explicar que o script principal executa apenas as etapas 1–4. Os outros cinco mantêm o hash original.
- Permanecem preservados `backup_pre_migracao_20261016/`, `analise_seguranca_publica.py.pre_simplificacao_20261016.bak` e a cópia exata do script anterior à reorganização em `backup_pre_migracao_20261016/analise_seguranca_publica_pre_reorganizacao_20261016.py`.

## Contagens conferidas

- Sinesp bruto na data da reorganização: 4 arquivos anuais de 2023–2026 e 3 arquivos de 2020–2022 ainda pendentes de verificação adicional de origem naquele momento.
- SSP/SC bruto: 45 PDFs, 45 CSVs extraídos e uma página HTML de referência.
- Sinesp processado: 7 XLSX municipais, incluindo 132 linhas no arquivo de 2023.
- SSP/SC processado: 4 CSVs anuais.
- Prefeitura/SEPROT: 3 CSVs, com 6 linhas no total.
- Resultados analíticos existentes: 3 pares CSV/Parquet.

### Verificação posterior de procedência do Sinesp 2020–2022

A pendência registrada acima foi resolvida em auditoria posterior à reorganização. Os três arquivos foram classificados como `VALIDADO` em [`sinesp_origem_2020_2022.csv`](sinesp_origem_2020_2022.csv): os arquivos locais de 2021 e 2022 coincidiram com as versões oficiais atuais em tamanho e SHA-256; o arquivo de 2020 tem tamanho e SHA-256 diferentes da versão oficial atual, mas a comparação de todas as células apontou igualdade de conteúdo. O nome histórico da pasta `pendente_validacao_origem/` foi mantido, sem nova movimentação de arquivos.

## Execução autorizada

Foi executado `analise_seguranca_publica.py` com o Python do ambiente `.venv`. O script leu a amostra nacional do Sinesp, selecionou 132 linhas de Joinville/SC em memória, inventariou os 45 CSVs da SSP/SC, leu o boletim selecionado e carregou os 6 registros da Prefeitura/SEPROT. Nenhuma etapa de limpeza, transformação, consolidação, estatística ou exportação foi executada.

As células `# %%` permanecem no script para execução interativa no VS Code. O teste em terminal confirmou que o roteiro termina sem erro; o Data Viewer requer executar as células dentro do Interactive Window com a extensão Jupyter/Python habilitada.

## Limite desta reorganização

Os diretórios antigos `data/` e `docs/` ficaram sem arquivos após as movimentações. Seus diretórios vazios foram removidos. A pasta `outputs/` permanece apenas para o cache local do Matplotlib, pois o código auxiliar ainda a utiliza.
