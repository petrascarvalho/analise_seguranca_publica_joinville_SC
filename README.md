# Segurança Pública de Joinville

**Curso:** SENAI/SC — LAB365 | Módulo 2 — Semana 13 (Visualização de Dados e Business Intelligence)
**Aluno:** Petras Ruben Carvalho
**Projeto:** Análise dos indicadores oficiais do Sinesp/MJSP em Joinville/SC, janeiro/2020 a setembro/2026

Projeto acadêmico individual. O produto usa **exclusivamente dados do Sinesp/MJSP para Joinville/SC** (fonte única) e é formado por três peças que se complementam:

| Peça | Arquivo | Para que serve |
|---|---|---|
| ETL acadêmico | [scripts/etl_sinesp.py](scripts/etl_sinesp.py) | Lê os XLSX oficiais, transforma, valida, confere com a base publicada e exporta resultados para `dados/processados/sinesp/` (18 etapas comentadas) |
| Notebook de análise | [notebooks/analise_sinesp.ipynb](notebooks/analise_sinesp.ipynb) | Apresenta a análise passo a passo, com tabelas, estatísticas e gráficos |
| Painel Streamlit | [scripts/painel_streamlit.py](scripts/painel_streamlit.py) | Dashboard de três páginas (Projeto, Indicadores Sinesp e Qualidade e metodologia), alimentado pela base publicada em `dashboard/data_publica/` |

Período realmente disponível: **janeiro/2020 a setembro/2026** (2026 parcial; a série da PRF termina em agosto/2026). Aplicação publicada no Streamlit Community Cloud: <https://seguranca-publica-joinville-sinesp.streamlit.app/>. A versão publicada corresponde ao último commit enviado ao GitHub; alterações feitas depois disso só aparecem no aplicativo após push e reconstrução. O trabalho anterior com a SSP/SC e com a Prefeitura/SEPROT é histórico e está **fora do escopo** da entrega.

## 1. Título e resumo

**Análise dos indicadores oficiais de segurança pública do Sinesp/MJSP em Joinville/SC, 2020–2026.** O projeto usa Python, Pandas e Matplotlib para descrever séries mensais municipais publicadas pelo Ministério da Justiça e Segurança Pública, preservando fonte, unidade, abrangência institucional e período de cada série.

Fonte única: Sinesp VDE / MJSP, recorte exato Joinville/SC, 12 séries (indicador × abrangência: Estadual, Polícia Federal e Polícia Rodoviária Federal), 911 observações mensais, janeiro/2020 a setembro/2026. Cada série tem cobertura própria e não existe um total geral de criminalidade obtido somando indicadores, abrangências ou unidades.

## 2. Problema, objetivo e importância

**Pergunta analítica:** como evoluíram, desde janeiro/2020, os indicadores oficiais de segurança pública do Sinesp/MJSP para Joinville/SC, e o que a comparação entre períodos equivalentes permite — e não permite — afirmar sobre essa evolução?

O objetivo é produzir uma análise municipal reproduzível, com origem auditável, estatísticas adequadas às unidades e comparação de períodos equivalentes. O público inclui estudantes, cidadãos, pesquisadores e gestores. Os dados descrevem registros administrativos publicados: não medem toda a criminalidade ocorrida nem demonstram efeitos de políticas públicas.

## 3. Escopo e resultados esperados

**Escopo (fonte única Sinesp/MJSP, Joinville/SC):** feminicídio e tentativa de feminicídio, homicídio doloso, tentativa de homicídio, lesão corporal seguida de morte, latrocínio (roubo seguido de morte), suicídio, mortes a esclarecer, mortes no trânsito (Estadual e PRF) e mandados de prisão cumpridos (Estadual e Polícia Federal). Vítimas e mandados são conceitos distintos; atividade policial não é contagem de crimes nem de vítimas únicas.

**Fora do escopo:** furtos e roubos em geral, estupro, tráfico de drogas, atendimentos da Guarda Municipal, taxas populacionais, dados por bairro, rua, horário ou corporação, previsões e inferência causal. O trabalho anterior com a **SSP/SC e Prefeitura/SEPROT** (inspeção de boletins, base de violência doméstica, transcrição de totais municipais) é **histórico e está fora do escopo**: não alimenta o painel nem a base publicada e está indexado em [historico/ssp_sc/LEIAME.md](historico/ssp_sc/LEIAME.md). O código e os dados dessas fontes continuam recuperáveis pelo Git (último commit com a página da SSP/SC no dashboard: `bad9723`).

Requisitos acadêmicos: trabalho individual do SENAI/LAB365, Módulo 2, Semana 13; ETL em Python, análise exploratória, estatísticas, gráficos com fonte, painel interativo Streamlit, README, repositório dedicado, publicação da aplicação, vídeo de até três minutos e envio dos links ao AVA e ao repositório da turma. Prazo informado: **30/10/2026 às 22h, horário de Brasília**, sujeito a comunicados posteriores. O planejamento no Trello foi **dispensado por orientação do professor**.

Situação: ETL, notebook, estatísticas, gráficos e dashboard implementados e testados; atualização controlada executada com a competência de setembro/2026; dashboard publicado (seção 10). Pendentes: revisão visual final no navegador, validação em dispositivos móveis, vídeo, repositório da turma e AVA.

## 4. Fonte e autorização

| Fonte oficial | Aquisição e evidência | Cobertura municipal | Unidade e ressalvas |
|---|---|---|---|
| [Sinesp VDE / MJSP](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023) | Sete XLSX anuais (`bancovde-2020.xlsx` a `bancovde-2026.xlsx`); [origem e verificações](documentacao/analises/fontes/ORIGEM_SINESP.md), [evidência de 2020–2022](documentacao/auditoria/sinesp_origem_2020_2022.csv) e SHA-256 dos XLSX no manifesto | 2020–2025 completos; 2026 de janeiro a setembro (PRF até agosto) | Vítimas em `total_vitima`; mandados em `total`; abrangências Estadual, PF e PRF preservadas |

Os XLSX ficam em `dados/brutos/sinesp/`, fora do Git. A disponibilidade pública de uma fonte não confirma autorização de redistribuição integral; por isso o repositório publica apenas arquivos **mínimos, agregados e derivados** (`dashboard/data_publica/`: contagens mensais municipais e metadados de rastreabilidade). XLSX nacionais, dados pessoais e informações protegidas não são redistribuídos.

**Condições de reutilização (consulta de 27/10/2026):** o catálogo `dados.mj.gov.br` seria "Creative Commons Atribuição", segundo o responsável pelo projeto, mas isso **não pôde ser confirmado** (o domínio não resolveu; NXDOMAIN); o rodapé do portal gov.br declara "Creative Commons Atribuição-SemDerivações 3.0" (CC BY-ND 3.0, licença geral do site); a página da base VDE e o Termo de Uso do portal não trazem condições específicas. **Nenhuma proibição específica aplicável aos arquivos derivados foi encontrada, mas também não há autorização específica explícita.** É uma avaliação técnica, não parecer jurídico. A atribuição da fonte aparece no painel; recomenda-se confirmar o uso com o MJSP (estatistica@mj.gov.br). Detalhes em [dashboard/data_publica/LEIAME.md](dashboard/data_publica/LEIAME.md).

## 5. Pipeline e metodologia

O fluxo segue quatro camadas, cada uma em um lugar próprio:

| Camada | Onde fica | Versionada no Git? |
|---|---|---|
| Arquivo bruto | `dados/brutos/sinesp/` — XLSX oficiais, sem alteração | Não |
| Base transformada | `dados/processados/sinesp/etl_recorte_joinville_bruto.csv` — 911 linhas de Joinville, 14 colunas originais | Não (gerada pelo ETL) |
| Base analítica validada | `dados/processados/sinesp/etl_sinesp_joinville_mensal.csv` — 911 × 6, igual à publicada | Não (gerada pelo ETL) |
| Base publicada | `dashboard/data_publica/` — 2 CSVs + manifesto com SHA-256 | Sim (usada pelo Streamlit) |

### ETL acadêmico: `scripts/etl_sinesp.py`

Script em células `# %%` (VS Code: *Run Cell* / *Run All Cells*) ou executado de uma vez no terminal. Cada etapa começa com **Objetivo**, explica o que é feito, informa o **Resultado esperado** e termina com uma conferência (`assert`) que interrompe o processo se algo não bater.

| Etapas | O que fazem |
|---|---|
| 01–03 | Importam as bibliotecas, configuram os caminhos e localizam os sete XLSX, conferindo o SHA-256 de cada um com o manifesto |
| 04–06 | Leem os XLSX guardando só as linhas de SC/JOINVILLE (911 linhas) e descrevem as 14 colunas, eventos e abrangências |
| 07 | Verifica duplicidades **sem apagar linhas**: soma só as parcelas que a nota oficial manda somar (*Tentativa de homicídio* e *Estupro*) |
| 08–12 | Convertem datas (serial do Excel), escolhem a medida (vítimas × mandados), mantêm ausências como `<NA>` (nunca zero), ajustam tipos e consolidam as observações mensais |
| 13 | Valida a base e confere que ela é **idêntica à publicada** (mesmo SHA-256 do manifesto) |
| 14–16 | Estatísticas descritivas, análise exploratória e gráficos (funções de `dashboard/graficos.py`) |
| 17 | Exportação controlada: grava somente em `dados/processados/sinesp/`; **nunca altera `dashboard/data_publica/`** |
| 18 | Conclusões e limitações calculadas a partir dos dados |

Sem os XLSX, o ETL entra em **modo demonstração**: usa a base publicada (dado derivado, não bruto), avisa que isso não reproduz a extração e não exporta nada. A série estudada pode ser trocada pelas variáveis `SINESP_EVENTO_ESTUDO` e `SINESP_ABRANGENCIA_ESTUDO`.

O roteiro anterior, [historico/scripts/analise_seguranca_publica.py](historico/scripts/analise_seguranca_publica.py), é **histórico**: reúne as primeiras etapas Sinesp (1–10) e o trabalho da SSP/SC (11–14.2). Continua em `scripts/` porque o gerador da versão inicial dos dados e os testes históricos dependem dele; não é necessário para reproduzir a entrega.

### Notebook: `notebooks/analise_sinesp.ipynb`

Apresenta a mesma análise em formato de relatório, em 13 seções: fonte oficial, bibliotecas, diretórios, leitura dos arquivos, inspeção bruta, tratamento, duplicidades, ausências e zeros, recorte de Joinville e cobertura, estatísticas, gráficos e interpretações, conclusões e limitações. Usa as mesmas funções validadas do ETL e do painel; sem os XLSX, roda em modo demonstração. É versionado sem saídas gravadas.

### Regras do ETL

Filtro exato `SC`/`JOINVILLE`. Datas pelo sistema Excel 1900 (origem `1899-12-30`), sem `errors="coerce"`: o serial precisa ser inteiro, cair no dia 1 do mês e no ano do arquivo. As contagens passam para `Int64` anulável depois de verificar valores finitos, inteiros e não negativos; **nenhum valor ausente é convertido em zero**, e zeros publicados são mantidos. Vítimas (`total_vitima`) e mandados (`total`) são medidas distintas e nunca são somadas. Não há deduplicação genérica: em qualquer indicador fora da regra oficial, uma repetição interrompe o processo.

Estatísticas: a soma anual só é calculada quando todos os meses têm valor; a variação percentual só existe com base positiva (a diferença absoluta é sempre informada); desvio-padrão descritivo com `ddof=0`. Anos parciais nunca são comparados com anos completos: compara-se janeiro até a última competência equivalente, **por série** (a PRF termina em agosto, as demais em setembro). Detalhes em [documentacao/analises/METODOLOGIA.md](documentacao/analises/METODOLOGIA.md).

A **atualização dos dados do painel não depende do ETL acadêmico**: usa `src/pipeline/atualizacao_dados.py`, que aplica as mesmas regras e reproduz byte a byte os dados ativos. Os dois caminhos são conferidos contra os mesmos CSVs publicados.

## 6. Bibliotecas e tecnologias

Ambiente local conferido: Python **3.12.14**, Pandas **3.0.6**, Matplotlib **3.11.2**, Streamlit **1.66.0**, openpyxl **3.1.5**, lxml **6.1.3**, pytest **8.4.2** e ipykernel **7.4.0**. As faixas de instalação estão em [requirements.txt](requirements.txt) (não é um arquivo de versões travadas).

| Biblioteca | Papel |
|---|---|
| `pandas` | Leitura, transformação, validação e tabelas |
| `matplotlib` | Todos os gráficos (ETL, notebook e painel) |
| `streamlit` | Painel interativo |
| `lxml` | Leitura do XML interno das planilhas do Sinesp (`src/pipeline/transform.py`) |
| `openpyxl` | Testes (XLSX sintéticos) e módulos históricos |
| `pytest` | Testes automatizados |
| `ipykernel` | Execução do notebook e das células `# %%` no VS Code (instalar à parte) |
| `pdfplumber`, `pypdf`, `pyarrow` | Somente código histórico da SSP/SC |

Separar um `requirements.txt` mínimo para o Streamlit Cloud de um arquivo de desenvolvimento é uma melhoria possível, ainda não aplicada para não reconstruir o aplicativo sem teste em ambiente limpo.

## 7. Resultados encontrados

Os números abaixo vêm da base publicada (`dashboard/data_publica/`, versão `20261027T114400Z`) e são conferidos automaticamente contra as tabelas por testes (`tests/test_dashboard_dados.py`).

### Cobertura, dimensões e ausências

A versão auditada inicial preservou **900 registros Sinesp** (janeiro/2020 a agosto/2026) e 14 colunas no original. Em 27/10/2026, o Sinesp publicou setembro/2026: a base ativa passou a **911 observações** (11 novas, nenhuma revisão de valores históricos), em 12 séries, com 0 valores ausentes e 401 zeros publicados.

| Ano | Observações na base | Meses por série estável |
|---|---:|---|
| 2020 | 132 | janeiro–dezembro |
| 2021 | 132 | janeiro–dezembro |
| 2022 | 132 | janeiro–dezembro |
| 2023 | 132 | janeiro–dezembro |
| 2024 | 132 | janeiro–dezembro |
| 2025 | 144 | janeiro–dezembro; inclui mandados PF |
| 2026 | 107 | janeiro–setembro (PRF até agosto); inclui mandados PF |

Na camada original, agente, arma, faixa etária e peso estão 100% vazios; `total_vitima` e `total` se alternam (cada linha usa uma das duas medidas). As ausências foram preservadas nas mesmas posições. Na base ativa, com uma medida por série, nenhum mês de série cadastrada está sem valor.

### Totais publicados por ano

**2020–2025 são anos completos; a coluna 2026 contém apenas janeiro–setembro (PRF: janeiro–agosto) e não deve ser comparada diretamente com totais anuais.** Unidade: vítimas, exceto mandados (contagem publicada). PF = Polícia Federal; PRF = Polícia Rodoviária Federal. As linhas não se somam.

| Indicador / abrangência | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (parcial) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Feminicídio — Estadual | 3 | 6 | 2 | 2 | 3 | 2 | 0 |
| Homicídio doloso — Estadual | 62 | 62 | 49 | 55 | 36 | 29 | 25 |
| Lesão corporal seguida de morte — Estadual | 0 | 2 | 3 | 1 | 1 | 0 | 1 |
| Mandados — Estadual | 612 | 790 | 884 | 980 | 1035 | 1248 | 936 |
| Mortalidade no trânsito¹ — Estadual | 22 | 21 | 33 | 26 | 34 | 20 | 14 |
| Mortes a esclarecer — Estadual | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Mortes no trânsito — PRF | 10 | 11 | 13 | 7 | 8 | 13 | 6 |
| Latrocínio — Estadual | 0 | 1 | 3 | 0 | 0 | 0 | 0 |
| Suicídio — Estadual | 43 | 52 | 67 | 44 | 48 | 39 | 31 |
| Tentativa de feminicídio — Estadual | 10 | 4 | 7 | 7 | 10 | 9 | 12 |
| Tentativa de homicídio — Estadual | 98 | 96 | 103 | 101 | 82 | 53 | 77 |
| Mandados — PF | — | — | — | — | — | 8 | 8 |

¹ Morte no trânsito ou em decorrência dele, exceto homicídio doloso. `—` representa falta de cobertura da série, não zero. O valor de 2026 de *Mortes no trânsito — PRF* cobre janeiro–agosto.

### Comparações equivalentes: janeiro–agosto

Todos os valores têm oito meses e são comparáveis entre todas as séries, inclusive a PRF. Homicídio doloso soma 18 em janeiro–agosto de 2025 e 22 em janeiro–agosto de 2026; tentativa de homicídio soma 37 e 68.

| Indicador / abrangência | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Feminicídio — Estadual | 2 | 3 | 1 | 1 | 3 | 0 | 0 |
| Homicídio doloso — Estadual | 50 | 40 | 29 | 40 | 21 | 18 | 22 |
| Lesão corporal seguida de morte — Estadual | 0 | 2 | 0 | 1 | 0 | 0 | 1 |
| Mandados — Estadual | 396 | 517 | 605 | 567 | 729 | 836 | 821 |
| Mortalidade no trânsito¹ — Estadual | 15 | 15 | 25 | 20 | 28 | 12 | 12 |
| Mortes a esclarecer — Estadual | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Mortes no trânsito — PRF | 5 | 9 | 9 | 4 | 5 | 10 | 6 |
| Latrocínio — Estadual | 0 | 1 | 1 | 0 | 0 | 0 | 0 |
| Suicídio — Estadual | 21 | 30 | 41 | 33 | 36 | 22 | 27 |
| Tentativa de feminicídio — Estadual | 8 | 2 | 3 | 7 | 4 | 4 | 10 |
| Tentativa de homicídio — Estadual | 74 | 53 | 60 | 62 | 57 | 37 | 68 |
| Mandados — PF | — | — | — | — | — | 6 | 6 |

### Comparações equivalentes: janeiro–setembro

Todos os valores têm nove meses. A série *Mortes no trânsito — PRF* ainda não tem setembro/2026 (`—` em 2026); seus anos anteriores aparecem só como referência. Homicídio doloso soma 21 em janeiro–setembro de 2025 e **25 em 2026**; tentativa de homicídio soma 43 e 77; feminicídio, 2 e 0; tentativa de feminicídio, 5 e 12.

| Indicador / abrangência | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Feminicídio — Estadual | 2 | 3 | 1 | 1 | 3 | 2 | 0 |
| Homicídio doloso — Estadual | 53 | 46 | 34 | 47 | 25 | 21 | 25 |
| Lesão corporal seguida de morte — Estadual | 0 | 2 | 1 | 1 | 0 | 0 | 1 |
| Mandados — Estadual | 468 | 589 | 681 | 654 | 812 | 954 | 936 |
| Mortalidade no trânsito¹ — Estadual | 18 | 17 | 28 | 22 | 30 | 14 | 14 |
| Mortes a esclarecer — Estadual | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Mortes no trânsito — PRF | 5 | 10 | 10 | 5 | 7 | 11 | — |
| Latrocínio — Estadual | 0 | 1 | 3 | 0 | 0 | 0 | 0 |
| Suicídio — Estadual | 25 | 34 | 45 | 35 | 41 | 25 | 31 |
| Tentativa de feminicídio — Estadual | 9 | 2 | 4 | 7 | 5 | 5 | 12 |
| Tentativa de homicídio — Estadual | 77 | 60 | 69 | 73 | 65 | 43 | 77 |
| Mandados — PF | — | — | — | — | — | 6 | 8 |

### Estatísticas mensais descritivas

Período observado: janeiro/2020–setembro/2026, com 81 meses por série estável; a PRF tem 80 meses (até agosto/2026) e os mandados da PF, 21 meses desde janeiro/2025. A soma refere-se a todo o período observado; o desvio-padrão descreve os meses disponíveis (`ddof=0`), sem inferência.

| Indicador / abrangência | Meses | Soma | Média mensal | Mediana | Mín. | Máx. | DP (ddof=0) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Feminicídio — Estadual | 81 | 18 | 0,22 | 0 | 0 | 3 | 0,54 |
| Homicídio doloso — Estadual | 81 | 318 | 3,93 | 3 | 0 | 19 | 2,78 |
| Lesão corporal seguida de morte — Estadual | 81 | 8 | 0,10 | 0 | 0 | 2 | 0,34 |
| Mandados — Estadual | 81 | 6485 | 80,06 | 80 | 0 | 160 | 26,24 |
| Mortalidade no trânsito¹ — Estadual | 81 | 170 | 2,10 | 2 | 0 | 7 | 1,45 |
| Mortes a esclarecer — Estadual | 81 | 0 | 0,00 | 0 | 0 | 0 | 0,00 |
| Mortes no trânsito — PRF | 80 | 68 | 0,85 | 1 | 0 | 3 | 0,85 |
| Latrocínio — Estadual | 81 | 4 | 0,05 | 0 | 0 | 2 | 0,27 |
| Suicídio — Estadual | 81 | 324 | 4,00 | 4 | 0 | 12 | 2,01 |
| Tentativa de feminicídio — Estadual | 81 | 59 | 0,73 | 0 | 0 | 5 | 0,97 |
| Tentativa de homicídio — Estadual | 81 | 610 | 7,53 | 8 | 0 | 16 | 3,00 |
| Mandados — PF | 21 | 16 | 0,76 | 0 | 0 | 4 | 1,11 |

### Quartis, outliers, distribuição e perfil mensal

- **Quartis e IQR:** quartis por interpolação linear; IQR = Q3 − Q1; limites de Tukey Q1 − 1,5·IQR e Q3 + 1,5·IQR. Pontos fora dos limites são **atípicos estatísticos, não anomalias comprovadas**.
- **O método nem sempre é informativo.** Com IQR = 0, maioria de zeros (≥ 50% dos meses), contagens muito baixas (Q3 ≤ 1), distribuição degenerada ou menos de 12 meses, nenhum ponto é apontado como atípico e a figura informa o motivo. Nos dados atuais, o método é informativo em 5 das 12 séries. Em homicídio doloso (Estadual), Q1 = 2, Q3 = 5 e o limite superior é 9,5: ficam acima dele janeiro/2020 (10) e janeiro/2023 (19).
- **Distribuição por faixas:** o zero publicado é faixa própria; os demais valores entram em faixas de largura igual (regra de Sturges).
- **Perfil mensal:** mediana de cada mês usando **somente anos completos** (2020–2025). Com tão poucos anos, o perfil descreve esses anos e não demonstra sazonalidade.
- **Média móvel de 12 meses** e **acumulado no ano** (anos parciais terminam no último mês publicado).

Furto, roubo em geral, estupro e tráfico de drogas **não existem** nos arquivos do Sinesp para Joinville. A investigação de fontes municipais e as divergências encontradas estão em [documentacao/analises/fontes/INDICADORES_COMPLEMENTARES_JOINVILLE.md](documentacao/analises/fontes/INDICADORES_COMPLEMENTARES_JOINVILLE.md); nenhum desses números entra na base.

### Atualização de 27/10/2026 (setembro/2026)

A preparação com os sete XLSX oficiais baixados nesse dia encontrou **11 competências novas (setembro/2026) e nenhuma alteração, remoção ou mudança de unidade em valores históricos de Joinville**; os sete arquivos têm SHA-256 diferente dos anteriores (republicação pela fonte), mas os valores de Joinville coincidem. A candidata `20261027T114400Z` foi promovida sem `--aceitar-revisoes`, em 2026-10-27T11:45:19Z (UTC); a versão anterior (`20261027T045449Z`) está preservada localmente e pode ser restaurada.

## 8. Discussão e conclusão

Em anos completos, homicídio doloso passou de 62 vítimas em 2020 para 29 em 2025, com oscilações intermediárias (49 em 2022 e 55 em 2023). Em períodos equivalentes, passou de 18 para 22 vítimas em janeiro–agosto e de 21 para 25 em janeiro–setembro (2025 → 2026). As tentativas de homicídio passaram de 43 para 77 em janeiro–setembro. Em contagens pequenas, a diferença absoluta é mais informativa que o percentual.

Feminicídio teve três vítimas em 2020, seis em 2021 e duas em 2025; em janeiro–setembro de 2026 o total publicado é zero (contra dois no mesmo período de 2025). Tentativas de feminicídio passaram de cinco para doze na comparação janeiro–setembro.

Latrocínio e lesão corporal seguida de morte somam, respectivamente, quatro e oito vítimas em 81 meses. Zero publicado não demonstra eliminação do fenômeno, ausência de subnotificação ou eficácia de uma política.

## 9. Aplicação profissional

A aplicação potencial é a consulta transparente de indicadores municipais agregados, com fonte, período e unidade explícitos, e um fluxo de atualização que detecta revisões da fonte antes de aceitá-las. `abrangencia` distingue as séries Estadual/PF/PRF, mas não permite atribuir cada registro à Polícia Civil, Polícia Militar ou Guarda Municipal.

Para uso operacional seriam necessários dicionários estáveis, dados territoriais validados e base demográfica para taxas. Não há, nesta base, série municipal comparável de atendimentos da Guarda Municipal, bairros, endereços, horários ou corporações individuais.

## 10. Aplicação Streamlit

O painel tem **três páginas** com navegação lateral (`st.navigation` / `st.Page`), layout amplo, filtros, indicadores com unidade e período explícitos e figuras Matplotlib com fonte e formatação numérica brasileira. **Aplicação publicada no Streamlit Community Cloud: <https://seguranca-publica-joinville-sinesp.streamlit.app/>.** Durante a navegação, o painel **não executa o ETL, não lê `dados/` e não acessa a rede**: usa somente `dashboard/data_publica/`. Guia de uso: [documentacao/painel/USO_DO_PAINEL.md](documentacao/painel/USO_DO_PAINEL.md).

| Página | Conteúdo |
|---|---|
| **Projeto** ([home.py](dashboard/pages/home.py)) | Pergunta analítica, objetivo, fonte única, período real lido do manifesto, principais achados e limitações |
| **Indicadores Sinesp** ([sinesp.py](dashboard/pages/sinesp.py)) | Filtros em duas linhas — **Categoria → Indicador → Abrangência** e **Período (anos) → Meses** —, resumo com setas que acompanham o sinal da diferença, e cinco abas: Visão geral, Evolução temporal, Estatística descritiva, Outliers e Indicadores e interpretação; cada gráfico tem a tabela com os valores usados |
| **Qualidade e metodologia** ([quality.py](dashboard/pages/quality.py)) | SHA-256 dos arquivos contra o manifesto, versão e aprovação dos dados, cobertura por série, regras do ETL e das estatísticas, procedimento de atualização e licenças |

Há uma chave **Visualização compacta (celular)**: a aplicação não detecta o tamanho da tela; a pessoa escolhe o modo, que gera figuras estreitas com fontes maiores e os mesmos números.

| Módulo | Função |
|---|---|
| [dashboard/dados_publicos.py](dashboard/dados_publicos.py) | Carrega e valida a base publicada (esquema, SHA-256, manifesto); erro explícito `ErroDados` |
| [dashboard/calculos.py](dashboard/calculos.py) | Totais, períodos equivalentes, estatísticas, quartis, outliers, perfil mensal, média móvel, acumulado |
| [dashboard/graficos.py](dashboard/graficos.py) | Figuras Matplotlib reutilizadas pelo painel, pelo ETL e pelo notebook |
| [dashboard/formatacao.py](dashboard/formatacao.py), [dashboard/ui.py](dashboard/ui.py) | Formatação pt-BR e componentes de interface |

### Dados mínimos (`dashboard/data_publica/`)

| Arquivo | Conteúdo | Dimensão |
|---|---|---|
| `sinesp_joinville_mensal.csv` | `ano, mes, evento, abrangencia, unidade, valor` (jan/2020–set/2026) | 911 × 6 |
| `sinesp_catalogo_indicadores.csv` | 12 séries: unidade, natureza, medida de origem, cobertura, meses com valor/zero/sem valor, limitações | 12 × 12 |
| `manifesto_dados_publicos.json` | Versão, datas, validação e aprovação, cobertura por série, fonte e licenças, regras de ETL, SHA-256 dos arquivos derivados e dos XLSX de origem | — |

Os arquivos são versionados para que o painel funcione em um clone limpo. A base publicada **só muda pelo fluxo controlado** abaixo; o ETL acadêmico nunca a sobrescreve.

### Verificar, preparar e aprovar novas publicações oficiais

Fluxo manual documentado em [documentacao/analises/ATUALIZACAO_DE_DADOS.md](documentacao/analises/ATUALIZACAO_DE_DADOS.md). Com a `.venv` ativada (`.\.venv\Scripts\Activate.ps1`):

```powershell
python -m src.pipeline.atualizacao_dados verificar                       # A: consulta a fonte (não altera dados)
python -m src.pipeline.atualizacao_dados preparar --entradas-sinesp <pasta com os XLSX 2020 a 2026>   # B: candidata isolada
python -m src.pipeline.atualizacao_dados comparar <id>                   # relatório e diferenças
python -m src.pipeline.atualizacao_dados aprovar <id> --confirmo <id>    # C: promove (preserva a versão anterior)
python -m src.pipeline.atualizacao_dados reverter <versao> --confirmo <versao>
```

**Automático:** consulta de metadados, ETL da candidata, validações, comparação com a versão ativa, backup, troca segura e reversão. **Manual:** fornecer os XLSX, ler o relatório, aprovar (`--confirmo`; `--aceitar-revisoes` só depois de analisar revisões históricas), commit, push e deploy. **Não há atualização automática operacional** (nada roda em agendamento) e o painel nunca baixa dados. O gov.br não tem API pública e bloqueia `HEAD`; a verificação é indício, não prova.

### Testes e verificações

Suíte **ativa**: **234 testes aprovados** (`.\.venv\Scripts\python.exe -m pytest tests -q`), cobrindo integridade e manifesto, totais conferidos com as tabelas deste README, cobertura por série, zeros e ausências, períodos equivalentes, navegação de três páginas, filtros e sua ordem, setas do resumo, gráficos e modo compacto, quartis e outliers, atualização controlada (com cliente HTTP falso e XLSX sintéticos), ETL acadêmico (estrutura, modo demonstração, reconstrução da base e exportação só para `dados/processados/sinesp/`) e notebook (estrutura, ausência de saídas e execução). Os testes que dependem dos XLSX são pulados quando o acervo local não existe.

Suíte **histórica** (fora da entrega): **12 testes** em `tests_historicos/` (`.\.venv\Scripts\python.exe -m pytest tests_historicos -q`), que dependem do acervo bruto local e do roteiro antigo.

O painel foi conferido por testes `AppTest` e por imagens que simulam telas de desktop e celular ([documentacao/painel/imagens/](documentacao/painel/imagens/)); isso **não substitui a revisão visual em navegador e em dispositivos móveis reais**, ainda pendente.

### Publicação no Streamlit Community Cloud

Ponto de entrada `scripts/painel_streamlit.py`; dependências em `requirements.txt`; caminhos relativos; sem segredos. Passo a passo em [documentacao/painel/DEPLOY_STREAMLIT.md](documentacao/painel/DEPLOY_STREAMLIT.md). **Deploy realizado:** <https://seguranca-publica-joinville-sinesp.streamlit.app/>. O Cloud reconstrói o aplicativo a partir da branch `main` do GitHub a cada push.

## 11. Como executar

Abra **a raiz do projeto** no VS Code e use o PowerShell. Os comandos abaixo chamam diretamente o Python da `.venv`, sem precisar ativá-la.

```powershell
# 1. Criar o ambiente e instalar as dependências
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install ipykernel    # para o notebook e as células # %%

# 2. ETL acadêmico (lê dados/brutos/sinesp e grava só em dados/processados/sinesp)
.\.venv\Scripts\python.exe -m scripts.etl_sinesp

# 3. Painel Streamlit (usa apenas dashboard/data_publica/)
.\.venv\Scripts\python.exe -m streamlit run scripts/painel_streamlit.py

# 4. Testes
.\.venv\Scripts\python.exe -m pytest tests -q              # suíte ativa
.\.venv\Scripts\python.exe -m pytest tests_historicos -q   # suíte histórica (exige o acervo local)
```

**Notebook:** abra [notebooks/analise_sinesp.ipynb](notebooks/analise_sinesp.ipynb) no VS Code, selecione o kernel da `.venv` e use *Run All*. O notebook procura a raiz do projeto sozinho; sem os XLSX, roda em modo demonstração.

**ETL célula a célula:** abra [scripts/etl_sinesp.py](scripts/etl_sinesp.py) e use *Run Cell* em cada célula `# %%` (ou *Run All Cells*). No terminal, a execução completa leva cerca de um minuto por causa da leitura de ~170 MB de planilhas. Para ler os XLSX de outra pasta, defina `SINESP_PASTA_XLSX`; para exportar em outro lugar, `SINESP_PASTA_PROCESSADOS`.

### Obter os arquivos que não ficam no Git

O painel e a suíte ativa funcionam sem eles. Para refazer o ETL:

1. Baixe os XLSX 2020–2026 no [catálogo oficial](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados) (`bancovde-ANO.xlsx`; padrão de download: `.../dnsp-base-de-dados/bancovde-ANO.xlsx/@@download/file`).
2. Salve os sete arquivos em qualquer subpasta de `dados/brutos/sinesp/`. O ETL compara o SHA-256 de cada arquivo com o do manifesto; se for outra edição, avisa, e a conferência da etapa 13 mostra se os valores mudaram.
3. Para atualizar a base do painel, use o fluxo `verificar → preparar → aprovar` (seção 10), não o ETL acadêmico.

## 12. Estrutura de pastas

```text
README.md                          documentação central (16 seções)
requirements.txt                   dependências
.gitignore                         dados, segredos, caches, logs e backups fora do Git
.env.example                       exemplo sem credenciais
.vscode/settings.json              .venv e raiz do Python Interactive
dados/                             acervo local, fora do Git
  brutos/sinesp/                   XLSX oficiais (oficial_20261027/ = edição da base aprovada;
                                   raiz + pendente_validacao_origem/ = edição auditada em agosto/2026)
  processados/sinesp/              saídas do ETL acadêmico (etl_*.csv, etl_relatorio.json)
scripts/
  etl_sinesp.py                    ETL acadêmico principal: 18 etapas em células # %%
  painel_streamlit.py              entrada do painel (st.navigation com 3 páginas)
src/pipeline/                      módulos auxiliares: leitura dos XLSX (transform.py), caminhos (utils.py),
                                   atualização controlada, verificação da fonte e manifesto versionado
ferramentas/gerar_revisao_visual.py  imagens de revisão (simulação de telas)
notebooks/
  analise_sinesp.ipynb             notebook de análise, sem saídas gravadas
dashboard/
  pages/                           home.py, sinesp.py e quality.py (3 páginas)
  dados_publicos.py, calculos.py,
  graficos.py, formatacao.py, ui.py   módulos do painel
  data_publica/                    base publicada: 2 CSVs + manifesto + LEIAME
documentacao/
  analises/                        ESCOPO_PROJETO.md, METODOLOGIA.md, ATUALIZACAO_DE_DADOS.md
    fontes/                        origem do Sinesp, recorte de Joinville e indicadores complementares
  painel/                          USO_DO_PAINEL.md, DEPLOY_STREAMLIT.md e imagens/
  auditoria/                       inventários e evidência de origem 2020–2022
tests/                             suíte ativa
tests_historicos/                  suíte histórica (acervo local e roteiro antigo)
historico/                         material preservado fora do produto (ver historico/LEIAME.md)
  ssp_sc/                          trabalho com SSP/SC e Prefeitura/SEPROT
  scripts/                         roteiro antigo, gerador inicial dos dados e módulos de fase anterior
  documentacao_anterior/           relatórios de migração, reorganização e pipeline antigo
```

Ficam fora do Git, além de `dados/`: `atualizacao/` (entradas, candidatas e versões anteriores da atualização controlada), `revisao_visual/` (capturas de revisão), backups, logs, ambientes e o README de continuidade. Pastas vazias não são preservadas pelo Git. Versões anteriores de qualquer arquivo movido podem ser recuperadas com `git log --follow <caminho>`.

## 13. Limitações e melhorias futuras

- 2026 é parcial: setembro é a última competência publicada (PRF: agosto). Comparações usam períodos equivalentes por série.
- Os valores são registros administrativos agregados: não medem toda a criminalidade, não estimam subnotificação e não sustentam causalidade. Contagens pequenas geram percentuais instáveis.
- Não há taxas populacionais, dados por bairro, rua, horário ou corporação, nem total geral entre indicadores, abrangências ou unidades.
- A fonte pode **revisar** valores históricos; a atualização controlada detecta revisões, e elas só entram com aprovação específica.
- Condições de reutilização com ressalvas: licença do catálogo do MJSP não confirmada; CC BY-ND 3.0 no rodapé do portal.
- O gov.br não oferece API pública nem data por arquivo; o download integral (~24 MB por arquivo) pode exigir repetição ou obtenção manual.
- O painel ainda precisa de revisão visual final em navegador e em dispositivos móveis reais.
- Melhorias possíveis: fixar versões de dependências com validação em ambiente limpo, definir a licença do código, relatórios exportáveis e, com base demográfica oficial compatível, taxas por habitante.
- Reintegrar a SSP/SC ou a Prefeitura/SEPROT exigiria nova decisão metodológica e um fluxo auditado próprio (ver [historico/ssp_sc/LEIAME.md](historico/ssp_sc/LEIAME.md)).

## 14. Créditos e referências

Fonte primária: MJSP/Sinesp VDE, citada na seção 4. A procedência está em [documentacao/analises/fontes/](documentacao/analises/fontes/) e na [auditoria de origem](documentacao/auditoria/sinesp_origem_2020_2022.csv). As fontes históricas (SSP/SC e Prefeitura/SEPROT) estão documentadas em [historico/ssp_sc/LEIAME.md](historico/ssp_sc/LEIAME.md).

A licença do código ainda deve ser definida; a ausência de um arquivo de licença não deve ser interpretada como autorização irrestrita.

## 15. Links de entrega

- [Repositório GitHub](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC) (branch `main`); URL Git: `https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC.git`.
- Aplicação Streamlit publicada: <https://seguranca-publica-joinville-sinesp.streamlit.app/> (deploy realizado; revisão visual final em navegador e celular pendente).
- Repositório oficial da turma: pendente.
- Vídeo e link de leitura no Drive: pendentes.
- AVA e demais itens administrativos: pendentes.
- Trello: dispensado por orientação do professor.

## 16. Conclusões sustentadas pelas análises

O ETL reconstrói, a partir dos XLSX oficiais, exatamente a base publicada: 911 observações em 12 séries, com o mesmo SHA-256 registrado no manifesto, sem apagar linhas, sem converter ausências em zero e sem misturar vítimas, mandados ou abrangências. A atualização controlada incorporou setembro/2026 sem alterar nenhum valor histórico de Joinville.

A análise sustenta descrições dos valores publicados e comparações temporais equivalentes, com atenção a pequenas contagens. Não sustenta total geral de criminalidade, causalidade, estimativa de subnotificação, taxa populacional ou distribuição por bairros. O dashboard de três páginas apresenta a pergunta, a fonte única, o período real, os indicadores, as estatísticas, os gráficos e a qualidade dos dados; a revisão visual final, o vídeo, o repositório da turma e o AVA permanecem pendentes.
