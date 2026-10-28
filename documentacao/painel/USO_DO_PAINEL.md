# Como usar o painel Streamlit

Aplicação publicada: <https://seguranca-publica-joinville-sinesp.streamlit.app/>. A versão publicada corresponde ao último commit enviado ao
GitHub. Para rodar no computador, veja a seção 11 do `README.md`. Fonte única: Sinesp/MJSP, Joinville/SC.

## Páginas

| Página | Para que serve |
|---|---|
| **Projeto** | Visão executiva: pergunta analítica, três indicadores de destaque, o gráfico do homicídio doloso por ano, atalhos para as análises e os limites da leitura |
| **Indicadores Sinesp** | Escolher uma série nos filtros e explorá-la em cinco abas |
| **Qualidade e metodologia** | Conferir integridade dos arquivos (SHA-256), cobertura de cada série, métodos, limitações, atualização e licenças — organizada em quatro abas |

## Filtros (página Indicadores Sinesp)

Os filtros ficam em um bloco destacado no topo:

- **Linha 1 — Categoria → Indicador → Abrangência.** A categoria (criminal, atividade policial ou complementar) limita a lista de indicadores;
  o indicador define as abrangências disponíveis (Estadual, Polícia Federal, Polícia Rodoviária Federal).
- **Linha 2 — Período (anos) → Meses.** O filtro de meses vale para o resumo e para as análises mensais. Totais anuais, média móvel,
  acumulado e perfil mensal usam sempre os 12 meses e mostram o aviso "Análise de ano completo".
- A linha **Filtros ativos** resume as escolhas em uso.
- **Visualização compacta (celular):** chave acima dos filtros. A aplicação não detecta o tamanho da tela; em telas pequenas, ative-a para
  ver figuras estreitas, com fontes maiores. Os números são os mesmos nos dois modos.

Logo abaixo, o **Resumo** mostra três cartões: último ano completo, mesmo período do ano parcial e meses com valor publicado. A seta
acompanha o sinal da diferença (para baixo quando diminui, para cima quando aumenta).

## Abas

| Aba | Conteúdo |
|---|---|
| **Evolução** | Total por ano (barras), valores mensais (barras agrupadas por ano) e variação entre anos completos |
| **Comparações** | Anos completos, comparação entre dois anos, períodos de igual duração e posição da série entre as demais da mesma unidade |
| **Padrões e tendência** | Mapa de calor ano × mês, média móvel de 12 meses, acumulado no ano e perfil mensal pela mediana |
| **Estatística e outliers** | Estatísticas por ano, boxplot, distribuição por faixas e pontos fora dos limites de Tukey (IQR) |
| **Indicadores e interpretação** | Catálogo das 12 séries e orientações de leitura |

As duas primeiras abas trazem a leitura principal; as duas seguintes são análises complementares. Cada gráfico tem, logo abaixo, o
expander **"Valores usados neste gráfico (tabela)"**. As quatro figuras fixas da Etapa 10 ficam no fim da página, em uma seção recolhida e
identificada como material histórico.

## Imagens de referência (`imagens/`)

| Arquivo | O que mostra |
|---|---|
| `01_projeto_desktop.png` | Página Projeto em tela de 1366 px |
| `02_indicadores_desktop.png` | Indicadores Sinesp: filtros, resumo, abas e o primeiro gráfico (1366 px) |
| `03_qualidade_desktop.png` | Qualidade e metodologia: integridade confirmada e abas (1366 px) |
| `04_projeto_tela_estreita.png` | Página Projeto em tela estreita (500 px): cartões empilhados |
| `05_modo_compacto_prf_mensal.png` | Modo compacto: PRF com três anos, zero publicado (traço) e mês sem valor (×) |
| `06_modo_compacto_mapa_calor.png` | Modo compacto: mapa de calor com meses nas linhas |

As imagens 01 a 04 são capturas do painel local no Chrome sem interface (headless), em 28/10/2026. As imagens 05 e 06 foram montadas por
`ferramentas/gerar_revisao_visual.py` e simulam a tela de um celular. Nenhuma delas substitui o teste em um celular real.
