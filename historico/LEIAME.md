# Material histórico

Conteúdo preservado para consulta e auditoria, **fora do produto entregue** (ETL, notebook e painel usam somente o Sinesp/MJSP).
Nada aqui é usado pelo painel. A suíte ativa (`tests/`) só lê os arquivos de indicadores complementares, para confirmar que eles
continuam fora da base; a suíte histórica (`tests_historicos/`) usa o roteiro antigo e os inventários.

| Pasta | Conteúdo |
|---|---|
| `scripts/` | Roteiro antigo `analise_seguranca_publica.py` (Sinesp 1–10 e SSP/SC 11–14.2), gerador inicial dos dados do painel (`gerar_dados_dashboard.py`, executável com `python -m historico.scripts.gerar_dados_dashboard`), `extract.py`, `analysis.py` e `legacy/` |
| `ssp_sc/` | Trabalho com a SSP/SC e a Prefeitura/SEPROT: índice (`LEIAME.md`), documentação das fontes e da extração e o notebook de inspeção dos CSVs |
| `indicadores_complementares/` | Investigação de furto, roubo, estupro e tráfico em fontes municipais (valores divergentes, **não incorporados**) e o protótipo em CSV |
| `documentacao_anterior/` | Escopo antigo, documentos de origem substituídos por `documentacao/analises/ORIGEM_E_COBERTURA.md`, relatórios de migração e reorganização e os inventários de auditoria (`auditoria/`) |
| `saidas_antigas/` | Gráficos e tabelas do pipeline anterior (local, fora do Git; conferidos pelos testes históricos) |

Versões anteriores de qualquer arquivo podem ser recuperadas pelo histórico Git (por exemplo, `git log --follow <caminho>` ou
`git show bad9723:<caminho>`).
