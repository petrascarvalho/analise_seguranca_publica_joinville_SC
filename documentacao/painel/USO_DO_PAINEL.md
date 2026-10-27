# Como usar o painel Streamlit

Aplicação publicada: <https://seguranca-publica-joinville-sinesp.streamlit.app/> (a versão publicada corresponde ao último commit enviado ao
GitHub; alterações locais só aparecem depois de commit, push e reconstrução do aplicativo). Para rodar no computador, veja o `README.md`.

## Páginas

| Página | Conteúdo |
|---|---|
| **Projeto** | Pergunta analítica, objetivo, fonte única, período real, principais achados e limitações |
| **Indicadores Sinesp** | Filtros, resumo, gráficos e tabelas da série escolhida |
| **Qualidade e metodologia** | Integridade (SHA-256), versão e aprovação dos dados, cobertura por série, regras do ETL, procedimento de atualização e licenças |

## Filtros (página Indicadores Sinesp)

- **Visualização compacta (celular):** chave no topo. A aplicação não detecta o tamanho da tela; em telas pequenas, ative-a para ver figuras
  estreitas, com fontes maiores e textos explicativos abaixo das imagens. Os números são os mesmos nos dois modos.
- **Linha 1 — Categoria → Indicador → Abrangência:** a categoria (criminal, atividade policial ou complementar) limita a lista de indicadores;
  o indicador define as abrangências disponíveis (Estadual, Polícia Federal, Polícia Rodoviária Federal).
- **Linha 2 — Período (anos) → Meses:** o filtro de meses vale para o resumo, o mapa de calor, a evolução mensal, as estatísticas, o boxplot,
  a distribuição e os outliers. Totais anuais, média móvel, acumulado e perfil mensal usam sempre os 12 meses e trazem o aviso
  "Análise de ano completo".
- A linha **Filtros ativos** resume as escolhas em uso.

## Abas

1. **Visão geral:** mapa de calor ano × mês, anos completos, comparação entre dois anos, períodos equivalentes e ranking dentro da mesma unidade.
2. **Evolução temporal:** barras anuais, barras mensais agrupadas, variação entre anos, média móvel de 12 meses e acumulado no ano.
3. **Estatística descritiva:** estatísticas por ano, boxplot, distribuição por faixas e perfil mensal pela mediana.
4. **Outliers:** limites de Tukey e o diagnóstico de quando o método é (ou não) informativo.
5. **Indicadores e interpretação:** catálogo das séries e orientações de leitura.

As quatro figuras fixas da Etapa 10 ficam no fim da página, em uma seção expansível identificada como material histórico, independente dos filtros.
Cada gráfico tem, logo abaixo, o expander **"Valores usados neste gráfico (tabela)"**.

## Imagens de referência (`imagens/`)

| Arquivo | O que mostra |
|---|---|
| `01_evolucao_anual_desktop.png` | Homicídio doloso, barras por ano completo (2020–2025) |
| `02_evolucao_mensal_desktop.png` | Barras mensais agrupadas, 2025 × 2026 |
| `03_perfil_mensal_mediana_desktop.png` | Mediana de cada mês nos anos completos, com mínimo e máximo |
| `04_outliers_iqr_desktop.png` | Série mensal com mediana, Q1–Q3 e limite de Tukey; janeiro/2020 e janeiro/2023 destacados |
| `05_prf_mensal_celular.png` | Modo compacto: PRF com três anos, zero publicado (traço) e mês sem valor (×) |
| `06_mapa_calor_celular.png` | Modo compacto: mapa de calor com meses nas linhas |

As imagens foram montadas com a função `montar_tela` de `scripts/gerar_revisao_visual.py` (que também gera, sob demanda, a grade completa de
revisão em `revisao_visual/`, pasta local fora do Git). Elas simulam a tela e não substituem o uso no navegador.
