# Trabalho histórico: SSP/SC (violência doméstica e homicídios) e Prefeitura/SEPROT

**Fora do escopo do produto entregue** (o painel). Desde a Etapa 24 (28/10/2026), o acervo SSP/SC de Joinville voltou ao
escopo de **dados e investigação**: a extração e a auditoria são refeitas por `src/pipeline/ssp_sc.py` (ver a seção 5.2 do `README.md`),
sem publicação no painel enquanto a validação não for concluída. A partir da Etapa 18 (27/10/2026) o projeto e o dashboard usam **exclusivamente o Sinesp/MJSP**
para Joinville/SC. Este índice registra onde está o trabalho anterior sobre a SSP/SC e a Prefeitura/SEPROT, para que ele não se perca.
Nada aqui é executado pelo painel, pela suíte de testes ativa nem pela atualização dos dados.

## O que foi feito (resumo)

* **Etapas 11 e 12 do roteiro** — inspeção de 45 PDFs/CSVs da SSP/SC (762 páginas, 25.753 linhas tabulares) e auditoria de 58 grupos de
  republicações de boletins (17 concordantes, 41 divergentes; nenhuma versão histórica de homicídio definida).
* **Etapas 13.1 a 14.2** — base analítica de violência doméstica de Joinville (janeiro/2023 a dezembro/2024; 216 × 5), rastreabilidade
  (216 × 23), estatísticas, comparação 2023 × 2024 e seis figuras Matplotlib. A unidade publicada ("Fato Comunicado") não tem definição operacional
  nos PDFs; três decisões metodológicas ficaram sem confirmação oficial.
* **Prefeitura/SEPROT** — seis totais anuais de furtos e roubos (2023–2025) transcritos de uma notícia oficial, sem definição da unidade.
* **Dashboard (Etapa 15)** — quarta página "Violência doméstica SSP/SC" e dois CSVs de dados mínimos.

## Onde está o código e a documentação

Todo o material está preservado **no histórico Git** (não é necessário nenhum arquivo extra). O último commit com o dashboard de quatro
páginas e os dados SSP/SC é `bad9723`.

| Item | Onde |
|---|---|
| Etapas 11–14.2 do roteiro | `historico/scripts/analise_seguranca_publica.py` (ainda presentes, como histórico; **não** fazem parte do painel nem dos dados ativos; o ETL da entrega é `scripts/etl_sinesp.py`; a extração SSP/SC destas etapas é reaproveitada por `src/pipeline/ssp_sc.py`) |
| Documentação da fonte e da extração | `historico/ssp_sc/documentacao/SSP_SC.md`, `historico/ssp_sc/documentacao/CSV_COMPLEMENTARES.md`, `historico/ssp_sc/documentacao/ssp_csv_extraction_etapa_1_1.md` |
| Extração histórica | `historico/scripts/legacy/extrair_ssp_joinville.py`, `historico/scripts/extract.py`, `historico/ssp_sc/ssp_csv_data_viewer.ipynb` |
| Página do dashboard | `dashboard/pages/violencia_domestica.py` (removida da navegação; recuperável no commit `bad9723`) |
| Dados mínimos SSP/SC | `dashboard/data_publica/ssp_violencia_domestica_joinville.csv` e `ssp_violencia_domestica_rastreabilidade.csv` (recuperáveis em `bad9723`) |
| Testes da versão de quatro páginas | `tests/test_dashboard_*.py`, `tests/test_atualizacao_*.py`, `tests/test_readme_sections.py` no commit `bad9723` |
| Testes dependentes do acervo bruto local | `tests_historicos/test_project_integrity.py` |

## Como recuperar um arquivo da versão anterior

```powershell
git show bad9723:dashboard/pages/violencia_domestica.py > violencia_domestica_historica.py
git show bad9723:dashboard/data_publica/ssp_violencia_domestica_joinville.csv > ssp_violencia_domestica_joinville.csv
git show bad9723:dashboard/data_publica/ssp_violencia_domestica_rastreabilidade.csv > ssp_violencia_domestica_rastreabilidade.csv
# ou restaurar toda a versão anterior em uma pasta separada, sem mexer na árvore atual:
git worktree add ../joinville_bad9723 bad9723
```

Não use `git reset --hard` nem reescreva o histórico para isso; `git show` e `git worktree add` não alteram a branch atual.

## Cópia local adicional (não versionada)

Na máquina de desenvolvimento existe uma cópia dos arquivos modificados ou removidos na Etapa 18 em
`atualizacao/arquivo_historico_ssp_sc_bad9723/` (pasta ignorada pelo Git), além da versão anterior dos dados em
`atualizacao/versoes/`. O acervo bruto (`dados/brutos/ssp_sc/`, PDFs e CSVs extraídos) e os inventários de hash permanecem intactos em `dados/` e
`historico/documentacao_anterior/auditoria/`. Esses itens locais não são necessários para recuperar o código, que está no Git.

## Se o escopo voltar a incluir a SSP/SC

Reintegrar exigiria, no mínimo: nova decisão metodológica sobre "Fato Comunicado"; resolução das divergências entre boletins republicados;
um fluxo de atualização próprio e auditado (não há ETL automático para novos relatórios); e confirmação das condições de reutilização com a SSP/SC.
