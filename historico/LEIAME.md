# Material histórico

Conteúdo preservado para consulta e auditoria, **fora do produto entregue** (painel, ETL e notebook usam somente o Sinesp/MJSP).
Nada aqui é executado pelo painel nem pela suíte de testes ativa (`tests/`).

| Pasta | Conteúdo |
|---|---|
| `ssp_sc/` | Trabalho com a SSP/SC e a Prefeitura/SEPROT: índice (`LEIAME.md`), documentação das fontes e da extração (`documentacao/`) e o notebook de inspeção dos CSVs da SSP/SC |
| `scripts/` | Módulos de uma fase anterior (`extract.py`, `analysis.py`, `legacy/`): extração da SSP/SC, análises antigas e exportações; não são usados pelo código atual |
| `documentacao_anterior/` | Relatórios de migração, reorganização, inspeção inicial, levantamento de 2026 e pipeline antigo (16/10/2026), substituídos pela documentação atual em `documentacao/` |

O roteiro acadêmico antigo, `scripts/analise_seguranca_publica.py`, continua em `scripts/` porque é usado pelo gerador da versão inicial dos
dados (`scripts/gerar_dados_dashboard.py`) e pelos testes históricos (`tests_historicos/`). Versões anteriores de qualquer arquivo podem ser
recuperadas pelo histórico Git (por exemplo, `git show bad9723:<caminho>`).
