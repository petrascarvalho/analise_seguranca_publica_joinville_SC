# Segurança Pública de Joinville

Projeto acadêmico individual de Visualização de Dados e BI — SENAI/LAB365, Módulo 2, Semana 13. Estado documentado em 27/10/2026. O produto usa **exclusivamente dados do Sinesp/MJSP para Joinville/SC** (fonte única): ETL em Python, análise exploratória e estatísticas descritivas, visualizações Matplotlib e um dashboard Streamlit de três páginas (Projeto, Indicadores Sinesp e Qualidade e metodologia), com dados mínimos agregados e versionados em `dashboard/data_publica/` e um fluxo manual e controlado de atualização (verificar → preparar → aprovar). Período realmente disponível: **janeiro/2020 a setembro/2026** (2026 parcial; a série da PRF termina em agosto/2026). A aplicação está **publicada no Streamlit Community Cloud**: <https://seguranca-publica-joinville-sinesp.streamlit.app/>. O roteiro acadêmico de referência é [scripts/analise_sinesp.py](scripts/analise_sinesp.py). O trabalho anterior com a SSP/SC e com a Prefeitura/SEPROT permanece registrado como histórico e **fora do escopo** da entrega. A revisão visual e o aperfeiçoamento dos gráficos, o vídeo, o repositório da turma e o AVA permanecem pendentes.

## 1. Título e resumo

**Análise dos indicadores oficiais de segurança pública do Sinesp/MJSP em Joinville/SC, 2020–2026.** O projeto utiliza Python/Pandas, dados oficiais e visualizações Matplotlib para descrever séries mensais municipais, preservando fonte, unidade, abrangência institucional e período. O produto final inclui painel Streamlit, documentação, repositório e apresentação acadêmica.

Fonte única: Sinesp VDE / MJSP, recorte exato Joinville/SC, 12 séries (indicador × abrangência: Estadual, Polícia Federal e Polícia Rodoviária Federal), 911 observações mensais, janeiro/2020 a setembro/2026. Cada série tem cobertura própria e não há um total geral de criminalidade obtido somando indicadores, abrangências ou unidades.

## 2. Problema, objetivo e importância

**Pergunta analítica:** como evoluíram, desde janeiro/2020, os indicadores oficiais de segurança pública do Sinesp/MJSP para Joinville/SC, e o que a comparação entre períodos equivalentes permite — e não permite — afirmar sobre essa evolução?

O objetivo é produzir uma análise municipal reproduzível, com origem auditável, estatísticas adequadas às unidades e comparação de períodos equivalentes. O público inclui estudantes, cidadãos, pesquisadores e gestores. Os dados descrevem registros administrativos publicados; não medem toda a criminalidade ocorrida nem demonstram efeitos causais de políticas públicas.

## 3. Escopo e resultados esperados

**Escopo (fonte única Sinesp/MJSP, Joinville/SC):** feminicídio e tentativa de feminicídio, homicídio doloso, tentativa de homicídio, lesão corporal seguida de morte, latrocínio (roubo seguido de morte), suicídio, mortes a esclarecer, mortes no trânsito (Estadual e PRF) e mandados de prisão cumpridos (Estadual e Polícia Federal). Vítimas e mandados são conceitos distintos; atividade policial não é contagem de crimes nem de vítimas únicas.

**Fora do escopo:** furtos e roubos, atendimentos da Guarda Municipal, dados da SSP/SC e da Prefeitura/SEPROT, taxas populacionais, dados por bairro, rua, horário ou corporação, previsões e inferência causal. O trabalho já feito com a **SSP/SC e Prefeitura/SEPROT** (inspeção e auditoria de boletins, base de violência doméstica, transcrição de totais municipais) é **histórico e está fora do escopo**: não alimenta o painel nem os dados ativos e está indexado em [historico/ssp_sc/LEIAME.md](historico/ssp_sc/LEIAME.md); o código e os dados dessas fontes permanecem recuperáveis no histórico Git (último commit com a versão anterior do dashboard, que incluía uma página da SSP/SC: `bad9723`).

Requisitos acadêmicos registrados: trabalho individual do SENAI/LAB365, Módulo 2, Semana 13; ETL em Python, EDA, estatísticas, gráficos com fontes, painel interativo Streamlit, README, repositório dedicado, publicação da aplicação, vídeo de até três minutos e envio dos links ao AVA/repositório da turma conforme enunciado. O prazo informado é **30/10/2026 às 22h, horário de Brasília**, sujeito a comunicados posteriores. O planejamento no Trello foi **dispensado por orientação do professor**. Regras finais de visibilidade do repositório, divulgação e marcações do vídeo devem ser conferidas no enunciado vigente antes da entrega.

Situação: ETL, EDA, estatísticas, figuras e dashboard (três páginas) implementados e testados; atualização controlada dos dados implementada e executada com a competência de setembro/2026; dashboard **publicado** no Streamlit Community Cloud (seção 10), com a página inicial conferida em navegador. Pendentes: revisão visual e aperfeiçoamento dos gráficos (etapa posterior), validação em dispositivos móveis, vídeo, repositório da turma e AVA.

## 4. Fonte e autorização

| Fonte oficial | Aquisição e evidência | Cobertura municipal | Unidade e ressalvas |
|---|---|---|---|
| [Sinesp VDE / MJSP](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023) | Sete XLSX anuais (`bancovde-2020.xlsx` a `bancovde-2026.xlsx`); [origem e verificações](documentacao/fontes/ORIGEM_SINESP.md), [evidência de 2020–2022](documentacao/auditoria/sinesp_origem_2020_2022.csv) e SHA-256 dos XLSX de cada versão no manifesto | 2020–2025 completos; 2026 de janeiro a setembro (PRF até agosto) | Vítimas em `total_vitima`; mandados em `total`; abrangências Estadual, PF e PRF preservadas |

Os dados brutos ficam fora do Git. A disponibilidade pública de uma fonte não confirma autorização de redistribuição integral; por isso o repositório publica apenas arquivos **mínimos, agregados e derivados** (`dashboard/data_publica/`: contagens mensais municipais já auditadas e metadados de rastreabilidade). XLSX nacionais, CSVs brutos, dados pessoais e informações protegidas não são redistribuídos. Os resultados textuais próprios deste README são apresentados com atribuição ao MJSP/Sinesp.

**Condições de reutilização (consulta de 27/10/2026)**, distinguindo catálogo, licença geral do site e condições do recurso: o catálogo `dados.mj.gov.br` seria "Creative Commons Atribuição" segundo o responsável pelo projeto, mas **não pôde ser confirmado** (o domínio não resolveu; NXDOMAIN); o rodapé do portal gov.br declara "Creative Commons Atribuição-SemDerivações 3.0" (CC BY-ND 3.0, licença geral do site); a página da base VDE e o Termo de Uso do portal não trazem condições específicas. **Nenhuma proibição específica aplicável aos arquivos derivados foi encontrada, mas também não há autorização específica explícita**; trata-se de avaliação técnica, não de parecer jurídico. A atribuição da fonte é obrigatória e aparece no painel; recomenda-se confirmar o uso com o MJSP (estatistica@mj.gov.br). Detalhes em [dashboard/data_publica/LEIAME.md](dashboard/data_publica/LEIAME.md) e no manifesto.

## 5. Pipeline e metodologia

O roteiro acadêmico de referência é [scripts/analise_sinesp.py](scripts/analise_sinesp.py) (357 linhas, 21 células `# %%`), dedicado só ao Sinesp e executável no VS Code Interactive ou por `python -m scripts.analise_sinesp`. Ele lê os XLSX do acervo local, refaz o ETL passo a passo, valida o resultado e **confere que a base reconstruída é idêntica à publicada** (mesmo SHA-256 do manifesto). Não grava arquivos. Sem os XLSX, entra em **modo demonstração**: usa a base já publicada (dado derivado, não bruto) e avisa que isso não reproduz a extração. O roteiro anterior, [scripts/analise_seguranca_publica.py](scripts/analise_seguranca_publica.py), é **histórico**: contém as primeiras etapas Sinesp (1–10) e o trabalho da SSP/SC (11–14.2), preservado e fora do escopo.

| Seção do roteiro | Conteúdo |
|---|---|
| 1. Objetivo e bibliotecas | Pergunta analítica; Pandas e módulos validados do projeto |
| 2. Leitura e inspeção | Localiza os 7 XLSX, confere SHA-256 com o manifesto e extrai apenas SC/JOINVILLE (911 linhas) |
| 3. Identificação dos campos | Dicionário das 14 colunas; ausências por campo; eventos e abrangências |
| 4. ETL | Conversão de datas (serial Excel), escolha da medida (vítimas × mandados), tratamento de ausências e linhas repetidas |
| 5. Validação | Colunas, chaves, meses consecutivos, unidade única, valores; igualdade com a base aprovada |
| 6. Base analítica | 911 observações × 6 colunas e catálogo de 12 séries |
| 7. Análise exploratória | Cobertura, zeros, ausências, totais por ano completo, períodos equivalentes (janeiro–agosto e janeiro–setembro) |
| 8. Estatísticas descritivas | Soma, média, mediana, mínimo, máximo e desvio-padrão (`ddof=0`); diferença absoluta e percentual com base positiva |
| 9. Visualizações | Reutiliza as funções validadas de `dashboard/graficos.py` (sem alterá-las) |
| 10. Conclusões e limitações | Textos calculados a partir dos dados |

A **atualização dos dados do painel não depende do roteiro**: usa `scripts/atualizacao_dados.py`, um ETL independente que aplica as mesmas regras e reproduz byte a byte os dados ativos. Os dois caminhos (roteiro e atualização) são verificados contra os mesmos dois CSVs publicados.

**Regras do ETL (Sinesp).** Filtro exato `SC`/`JOINVILLE`. A chave observacional mantém UF, município, evento, competência e abrangência; na versão auditada houve zero duplicidade exata e zero repetição nas chaves com abrangência, e 20 grupos/40 linhas de mandados estaduais e PF foram preservados separadamente. As dez colunas analíticas são `uf`, `municipio`, `evento`, `data_referencia`, `feminino`, `masculino`, `nao_informado`, `total_vitima`, `total` e `abrangencia`; agente, arma, faixa etária e peso estão 100% ausentes e continuam intactos no original.

Datas: sistema Excel 1900, origem `1899-12-30`, sem `errors="coerce"`; são validados seriais inteiros, ano do arquivo, primeiro dia do mês e cobertura. As cinco contagens passaram de `float64` para `Int64` anulável após verificar valores finitos, inteiros e não negativos; as posições de ausência foram preservadas e **nenhum valor ausente foi convertido em zero**. Vítimas (`total_vitima`) e mandados (`total`) são medidas distintas e nunca são somadas. Em *Tentativa de homicídio* e *Estupro*, meses com mais de uma linha são somados porque a nota metodológica oficial trata as linhas como parcelas; não há deduplicação genérica.

Estatísticas: a soma anual só é calculada quando todos os meses presentes têm valor; a variação percentual só existe com base positiva (diferença absoluta sempre informada); desvio-padrão descritivo com `ddof=0`; médias e medianas informam seus meses de observação. Anos parciais nunca são comparados com anos completos: compara-se janeiro até a última competência equivalente, **por série** (a PRF termina em agosto, as demais em setembro).

O catálogo auxiliar tem 12 combinações evento/abrangência, com medida, unidade, natureza, cobertura e limitações. Os módulos [extract.py](scripts/extract.py), [transform.py](scripts/transform.py) e [analysis.py](scripts/analysis.py) são de fase anterior e podem gravar resultados quando chamados como programas; não devem ser executados automaticamente.

## 6. Bibliotecas e tecnologias

Ambiente local conferido: Python **3.12.14**, Pandas **3.0.6**, Matplotlib **3.11.2**, Streamlit **1.66.0**, openpyxl **3.1.5**, lxml **6.1.3**, pytest **8.4.2** e ipykernel **7.4.0**.

Os intervalos de instalação estão em [requirements.txt](requirements.txt); não constituem um arquivo de versões travadas. `ipykernel` é uma dependência adicional para uso interativo e não está declarado nesse arquivo. A validação em ambiente limpo e eventual fixação de versões continuam pendentes.

Uso de cada biblioteca (levantamento por importações no código):

| Biblioteca | Papel |
|---|---|
| `streamlit`, `pandas`, `matplotlib` | Execução do painel publicado (e do roteiro `analise_sinesp.py`) |
| `lxml` | ETL Sinesp: leitura do XML das planilhas (`scripts/transform.py`) |
| `openpyxl` | Testes (geração de XLSX sintéticos) e módulos de fase anterior |
| `pytest` | Testes |
| `ipykernel` | Execução das células no VS Code Interactive (não declarado) |
| `pdfplumber`, `pypdf` | Somente código histórico da SSP/SC e teste histórico |
| `pyarrow` | Nenhum código ativo (somente `scripts/analysis.py`, módulo histórico) |

**Proposta de simplificação (não aplicada):** separar um `requirements.txt` mínimo para o Streamlit Cloud (`streamlit`, `pandas`, `matplotlib`) e um arquivo de desenvolvimento com `lxml`, `openpyxl`, `pytest` e `ipykernel`, movendo `pdfplumber`, `pypdf` e `pyarrow` para um arquivo histórico. Nenhuma biblioteca foi removida porque a mudança ainda não foi testada em ambiente limpo e reconstruiria o aplicativo publicado.

## 7. Resultados encontrados

Os números abaixo vêm dos dados ativos (`dashboard/data_publica/`, versão `20261027T114400Z`) e são conferidos automaticamente contra as tabelas por testes (`tests/test_dashboard_dados.py`).

### Cobertura, dimensões e ausências

A versão auditada inicial preservou **900 registros Sinesp** (janeiro/2020 a agosto/2026) e 14 colunas no original; a cópia analítica tem 900 linhas e dez colunas. Em 27/10/2026, o Sinesp publicou setembro/2026: a base curada ativa passou a **911 observações** (11 novas, nenhuma revisão de valores históricos), em 12 séries, com 0 valores ausentes e 401 zeros publicados.

| Ano | Observações na base curada | Meses por série estável |
|---|---:|---|
| 2020 | 132 | janeiro–dezembro |
| 2021 | 132 | janeiro–dezembro |
| 2022 | 132 | janeiro–dezembro |
| 2023 | 132 | janeiro–dezembro |
| 2024 | 132 | janeiro–dezembro |
| 2025 | 144 | janeiro–dezembro; inclui mandados PF |
| 2026 | 107 | janeiro–setembro (PRF até agosto); inclui mandados PF |

Ausências na camada original da versão auditada (900 registros, etapas 5–9):

| Campo original | Ausências | Percentual |
|---|---:|---:|
| uf | 0 | 0,00% |
| municipio | 0 | 0,00% |
| evento | 0 | 0,00% |
| data_referencia | 0 | 0,00% |
| agente | 900 | 100,00% |
| arma | 900 | 100,00% |
| faixa_etaria | 900 | 100,00% |
| feminino | 117 | 13,00% |
| masculino | 116 | 12,89% |
| nao_informado | 119 | 13,22% |
| total_vitima | 100 | 11,11% |
| total | 800 | 88,89% |
| total_peso | 900 | 100,00% |
| abrangencia | 0 | 0,00% |

As 4.852 células ausentes originais foram preservadas; na visão analítica, as dez colunas retidas mantêm as mesmas 1.252 ausências e suas posições. As ausências de `total_vitima` e `total` refletem a divisão entre vítimas e mandados (cada linha usa uma das duas medidas). Há 20 linhas com total de vítimas informado e detalhamento de sexo incompleto, sem autorizar preenchimento residual. Na base curada ativa (uma medida por série), nenhum mês de série cadastrada está sem valor.

### Totais publicados por ano

**2020–2025 são anos completos; a coluna 2026 contém apenas janeiro–setembro (PRF: janeiro–agosto). Não comparar diretamente essa coluna parcial com totais anuais.** Unidade: vítimas, exceto mandados, que usam contagem publicada. PF = Polícia Federal; PRF = Polícia Rodoviária Federal. Não se somam linhas desta tabela.

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

Todos os valores desta tabela têm oito meses e são comparáveis entre todas as séries, inclusive a PRF. Homicídio doloso soma 18 em janeiro–agosto de 2025 e 22 em janeiro–agosto de 2026; tentativa de homicídio soma 37 e 68. Os indicadores não são somados entre si.

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

Todos os valores desta tabela têm nove meses. A série *Mortes no trânsito — PRF* ainda não tem setembro/2026 (`—` em 2026); seus anos anteriores aparecem apenas para referência. Homicídio doloso soma 21 em janeiro–setembro de 2025 e **25 em 2026**; tentativa de homicídio soma 43 e 77; feminicídio, 2 e 0; tentativa de feminicídio, 5 e 12.

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

Período observado: janeiro/2020–setembro/2026, com 81 meses por série estável; PRF tem 80 meses (até agosto/2026) e mandados PF têm 21 meses desde janeiro/2025. As medidas utilizadas possuem valores publicados em todos esses meses. A soma abaixo refere-se a todo o período observado; o desvio-padrão descreve os meses disponíveis (`ddof=0`), sem inferência causal ou amostral.

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

### Quatro gráficos da Etapa 10

As figuras são renderizadas em memória (roteiro e página *Indicadores Sinesp*). Contêm título, período, eixo de vítimas iniciado em zero, rótulos, fonte MJSP/Sinesp VDE e abrangência Estadual. Nenhum arquivo de gráfico é exportado.

| Gráfico | Anos, na ordem apresentada | Valores utilizados |
|---|---|---|
| Homicídio doloso anual | 2020, 2021, 2022, 2023, 2024, 2025 | Homicídio doloso: 62, 62, 49, 55, 36, 29 |
| Feminicídio e tentativa anuais | 2020, 2021, 2022, 2023, 2024, 2025 | Feminicídio: 3, 6, 2, 2, 3, 2; Tentativa de feminicídio: 10, 4, 7, 7, 10, 9 |
| Homicídio e tentativa, janeiro–agosto | 2020, 2021, 2022, 2023, 2024, 2025, 2026 | Homicídio doloso: 50, 40, 29, 40, 21, 18, 22; Tentativa de homicídio: 74, 53, 60, 62, 57, 37, 68 |
| Feminicídio e tentativa, janeiro–agosto | 2025, 2026 | Feminicídio: 0, 0; Tentativa de feminicídio: 4, 10 |

Além delas, a página *Indicadores Sinesp* gera figuras filtráveis: evolução anual (somente anos completos), evolução mensal com uma linha por ano, períodos equivalentes por ano e ranking de séries dentro de uma única unidade, todas com eixo iniciado em zero, fonte, unidade e cor consistente por ano.

### Atualização de 27/10/2026 (setembro/2026)

A verificação da fonte apontou indícios de nova competência e de revisão (tamanhos de arquivos diferentes). A preparação com os sete XLSX oficiais baixados nesse dia comparou a candidata com a versão ativa: **11 competências novas (setembro/2026), nenhuma alteração, remoção ou mudança de unidade em valores históricos de Joinville**; os sete arquivos têm SHA-256 diferente dos usados antes (republicação pela fonte), mas os valores de Joinville coincidem. A candidata `20261027T114400Z` foi promovida sem `--aceitar-revisoes`, em 2026-10-27T11:45:19Z (UTC), por autorização condicionada do responsável; a versão anterior (`20261027T045449Z`, até agosto/2026) está preservada localmente e pode ser restaurada com o comando de reversão.

## 8. Discussão e conclusão

Em anos completos, homicídio doloso passou de 62 vítimas em 2020 para 29 em 2025, com oscilações intermediárias: 49 em 2022 e 55 em 2023. Na comparação janeiro–agosto, passou de 18 em 2025 para 22 em 2026; na comparação janeiro–setembro, de 21 para 25 em 2026. Tentativas de homicídio passaram de 43 para 77 em janeiro–setembro. São recortes temporais distintos, com interpretações próprias; em contagens pequenas, a diferença absoluta é mais informativa que o percentual.

Feminicídio apresentou três vítimas em 2020, seis em 2021 e duas em 2025; em janeiro–setembro de 2026 o total publicado é zero (contra dois em janeiro–setembro de 2025). Tentativas de feminicídio passaram de cinco para doze na comparação janeiro–setembro. Pequenas contagens tornam percentuais instáveis; por isso, os gráficos enfatizam valores absolutos.

Latrocínio e lesão seguida de morte têm, respectivamente, quatro e oito vítimas em 81 meses. Zero publicado não demonstra eliminação do fenômeno, ausência de subnotificação ou eficácia de uma política. Não há taxas populacionais, previsão, inferência causal ou ranking territorial neste trabalho.

## 9. Aplicação profissional

A aplicação potencial é a consulta transparente de indicadores municipais agregados, com fonte, período e unidade. Vítimas e mandados precisam de definições independentes. `abrangencia` distingue as séries Estadual/PF/PRF, mas não permite atribuir todo registro à Polícia Civil, Polícia Militar ou Guarda Municipal.

Para uso operacional, seriam necessários dicionários estáveis, atualização versionada, dados territoriais validados e revisão das sobreposições. Não há série municipal estruturada e comparável de atendimentos da Guarda Municipal, bairros, endereços, horários ou corporações individuais nesta base.

## 10. Aplicação Streamlit

O painel é uma aplicação Streamlit com **três páginas** e navegação lateral (`st.navigation`/`st.Page`), layout amplo, filtros, indicadores com unidade e período explícitos, figuras Matplotlib com fonte e formatação numérica brasileira. **A aplicação está publicada no Streamlit Community Cloud: <https://seguranca-publica-joinville-sinesp.streamlit.app/>** (a página inicial foi conferida em navegador; as demais páginas, os gráficos e o uso em dispositivos móveis ainda não foram revisados visualmente). A aplicação funciona a partir de arquivos mínimos e **não executa o roteiro analítico, não lê `dados/` e não acessa a rede** durante a navegação.

### Arquitetura e páginas

| Elemento | Função |
|---|---|
| [scripts/painel_streamlit.py](scripts/painel_streamlit.py) | Ponto de entrada (`st.navigation` com três páginas: `projeto`, `sinesp`, `qualidade`) |
| [dashboard/pages/home.py](dashboard/pages/home.py) | **Projeto**: pergunta analítica, objetivo, relevância, fonte única, período real lido do manifesto, unidades e limites, principais achados descritivos e situação (sem deploy) |
| [dashboard/pages/sinesp.py](dashboard/pages/sinesp.py) | **Indicadores Sinesp**: filtros por indicador, abrangência e período; KPIs (último ano completo e período parcial equivalente da série); evolução anual e mensal; comparações entre anos completos e entre períodos equivalentes; estatísticas descritivas; ranking por unidade; as quatro figuras da Etapa 10; catálogo e interpretação (observado × hipótese) |
| [dashboard/pages/quality.py](dashboard/pages/quality.py) | **Qualidade e metodologia**: arquivos e SHA-256 contra o manifesto; versão, datas, validação e aprovação; fonte oficial e método de obtenção; cobertura por indicador, zeros e ausências; regras do ETL, das estatísticas e dos gráficos; limitações; procedimento de atualização; licenças e atribuição |
| [dashboard/dados_publicos.py](dashboard/dados_publicos.py), [calculos.py](dashboard/calculos.py), [graficos.py](dashboard/graficos.py), [formatacao.py](dashboard/formatacao.py), [ui.py](dashboard/ui.py) | Carregamento/validação (sem Streamlit; `ErroDados` explícito), cálculos descritivos, figuras Matplotlib reutilizáveis, formatação pt-BR e interface |
| [scripts/gerar_dados_dashboard.py](scripts/gerar_dados_dashboard.py) | Geração inicial reprodutível dos arquivos mínimos a partir das etapas Sinesp validadas do roteiro (sem importá-lo) |
| [scripts/fontes_oficiais.py](scripts/fontes_oficiais.py) | Operação **A — verificar**: consulta metadados do Sinesp/MJSP e classifica indícios (somente leitura) |
| [scripts/atualizacao_dados.py](scripts/atualizacao_dados.py), [scripts/versionamento_dados.py](scripts/versionamento_dados.py) | Operações **B — preparar**, **C — aprovar** e **reverter**; manifesto versionado |

Regras de apresentação: o último ano de cada série pode ser parcial e nunca é comparado com anos completos; a PRF pode terminar antes das demais e é exibida até a sua última competência, sem preenchimento; vítimas, mandados e abrangências não são misturados; não há total geral nem taxas populacionais; valores publicados não representam todos os crimes e não indicam causalidade.

### Dados mínimos (`dashboard/data_publica/`)

| Arquivo | Conteúdo | Dimensão |
|---|---|---|
| `sinesp_joinville_mensal.csv` | `ano, mes, evento, abrangencia, unidade, valor` (Sinesp, jan/2020–set/2026) | 911 × 6 |
| `sinesp_catalogo_indicadores.csv` | 12 séries: unidade, natureza, medida de origem, cobertura, meses com valor/zero/sem valor, limitações | 12 × 12 |
| `manifesto_dados_publicos.json` | Versão e versão anterior; datas (geração, última consulta); situação da validação e da aprovação; cobertura por série e última competência; unidades; fonte oficial e licenças verificadas; método de obtenção e regras de ETL; SHA-256 e tamanhos dos arquivos derivados e dos XLSX oficiais | — |

Os arquivos são **versionados no repositório** para que o painel funcione em um clone limpo. Preservam eventos e abrangências separados, unidades, o período efetivamente disponível, zeros publicados e ausências (campo vazio, nunca zero). O manifesto distingue **data de consulta, data de publicação (informada pela fonte), competência estatística e data de geração** e registra a última competência: **2026-09** (PRF **2026-08**; 2026 parcial). Nenhum valor é digitado.

### Verificar, preparar e aprovar novas publicações oficiais

Fluxo manual e reprodutível, documentado em [documentacao/ATUALIZACAO_DE_DADOS.md](documentacao/ATUALIZACAO_DE_DADOS.md):

```powershell
python -m scripts.atualizacao_dados verificar                       # A: consulta a fonte (não altera dados)
python -m scripts.atualizacao_dados preparar --entradas-sinesp <pasta com os XLSX 2020 a 2026>   # B: candidata isolada
python -m scripts.atualizacao_dados comparar <id>                   # relatório e diferenças
python -m scripts.atualizacao_dados aprovar <id> --confirmo <id>    # C: promove (preserva a versão anterior)
python -m scripts.atualizacao_dados reverter <versao> --confirmo <versao>
```

**Automático:** consulta de metadados, classificação de indícios, ETL da candidata, validações, comparação com a versão ativa, backup, troca segura e reversão. **Manual:** fornecer os XLSX, ler o relatório, digitar a aprovação (`--confirmo`; `--aceitar-revisoes` somente após analisar revisões históricas — nunca para contornar alertas não resolvidos), commit/push e deploy. **Não há atualização automática operacional** (nada roda em agendamento). O painel nunca baixa dados.

Limitações da fonte: o gov.br não tem API pública (a API REST responde 401) e bloqueia `HEAD` (403) — o tamanho dos arquivos vem de `GET` com `Range`, sem data de modificação por arquivo, e a data "Atualizado em" é da página (indício, não prova); o catálogo do MJSP não resolveu (NXDOMAIN). Bloqueios de acesso não são contornados.

### Executar o painel

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m streamlit run scripts/painel_streamlit.py
```

O painel usa Streamlit, Pandas e Matplotlib e funciona **sem `dados/`**; se os arquivos de `dashboard/data_publica/` faltarem ou forem inválidos, as páginas mostram erro explícito (sem preencher números) e não encerram a aplicação.

### Testes e verificações

Suíte **ativa**: **120 testes aprovados** (`python -m pytest tests -q`): `test_dashboard_dados.py` (30), `test_dashboard_graficos.py` (6), `test_dashboard_app.py` (16, `AppTest`), `test_atualizacao_fontes.py` (16, cliente HTTP falso), `test_atualizacao_fluxo.py` (38, XLSX sintéticos gerados a partir dos dados ativos), `test_acervo_sinesp.py` (3; reconstroem os dados a partir dos XLSX auditados e são pulados se o acervo local não existir), `test_roteiro_sinesp.py` (4; estrutura do roteiro acadêmico, execução em modo demonstração e reconstrução da base aprovada, esta pulada sem o acervo) e `test_readme_sections.py` (7). Cobrem: integridade e manifesto; totais conferidos com as tabelas deste README; nova dimensão (911 observações, 12 séries) e cobertura por série (2026-09; PRF 2026-08); valores históricos preservados; unidades; zeros e ausências; períodos equivalentes; navegação de três páginas; gráficos e filtros; página de qualidade; detecção de nova competência, de revisão histórica, de alteração de esquema e de falha de consulta (sem alterar dados); download com repetição só de quedas de conexão e sem contornar bloqueios; promoção apenas com aprovação explícita; versão anterior preservada e reversão automática em falha da troca; painel em clone limpo, sem os dados mínimos, com esquema inválido, com hash divergente e com uma competência futura sintética.

Suíte **histórica** (fora da entrega): **12 testes** em `tests_historicos/` (`python -m pytest tests_historicos -q`): `test_project_integrity.py` (9; dependem do acervo bruto e de saídas históricas locais, incluindo SSP/SC e Prefeitura) e `test_roteiro_historico_ssp.py` (3; etapas SSP/SC e Sinesp 1–10 do roteiro antigo e índice histórico). Não são necessárias para o painel.

Verificações adicionais: verificação de sintaxe (`ast`) dos módulos, `git diff --check` e execução local do servidor com `python -m streamlit run scripts/painel_streamlit.py`. **O painel completo não foi validado visualmente em dispositivos móveis nem teve todas as páginas e gráficos revisados em navegador**: a revisão visual é a próxima etapa; layout e responsividade dependem de verificação manual. Testes que dependem de acesso externo não são executados: a verificação real da fonte e o download dos XLSX foram executados manualmente (resultado na seção 7).

### Publicação no Streamlit Community Cloud

Ponto de entrada `scripts/painel_streamlit.py`; dependências em `requirements.txt` (versões testadas: Python 3.12, Streamlit 1.66.0, Pandas 3.0.6, Matplotlib 3.11.2; faixas mais antigas não testadas); caminhos relativos; sem segredos; dados mínimos no clone público. Passo a passo e conferência pós-deploy em [documentacao/DEPLOY_STREAMLIT.md](documentacao/DEPLOY_STREAMLIT.md). **Deploy realizado:** <https://seguranca-publica-joinville-sinesp.streamlit.app/>. O Cloud reconstrói o aplicativo a partir da branch `main` do GitHub a cada push.

### Pendências

- Revisão visual completa no navegador (todas as páginas, desktop e celular) e aperfeiçoamento dos gráficos (etapa posterior; nada foi alterado nesta etapa).
- Vídeo, envio ao repositório da turma e AVA.
- Confirmar o uso dos dados com o MJSP (licença do catálogo não confirmada).

## 11. Como executar

Abra **a raiz do projeto** no VS Code. Exemplo PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Opcional para Python Interactive, se ainda não estiver instalado:
python -m pip install ipykernel
python -m scripts.analise_sinesp                      # roteiro acadêmico completo (ou célula a célula no VS Code)
python -m streamlit run scripts/painel_streamlit.py   # painel (usa apenas dashboard/data_publica/)
python -m pytest tests -q                              # suíte ativa
python -m pytest tests_historicos -q                   # suíte histórica (exige o acervo local)
```

O workspace [configura a .venv e o diretório do Jupyter](.vscode/settings.json) com referências relativas a `${workspaceFolder}`. Se uma janela interativa antiga estiver em outra pasta, reinicie seu kernel e confirme `Path.cwd()`.

### Restaurar as entradas que não ficam no Git (só para refazer o ETL)

O painel e a suíte ativa funcionam sem elas (os testes que dependem do acervo são pulados). Para refazer o ETL pelo roteiro ou pela atualização controlada:

1. Obtenha os XLSX 2020–2026 no [catálogo oficial](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados), usando `bancovde-ANO.xlsx` (padrão de download: `https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/bancovde-ANO.xlsx/@@download/file`).
2. **Atualização controlada (recomendada):** salve todos os anos em uma pasta e siga `verificar → preparar → aprovar` (seção 10). Ela não depende do roteiro nem do acervo SSP/SC.
3. **Roteiro acadêmico [scripts/analise_sinesp.py](scripts/analise_sinesp.py):** salve os sete arquivos (`bancovde-2020.xlsx` a `bancovde-2026.xlsx`) em qualquer subpasta de `dados/brutos/sinesp/` (ou aponte outra pasta com a variável de ambiente `SINESP_PASTA_XLSX`). O roteiro compara o SHA-256 de cada arquivo com o do manifesto; se o arquivo for de outra edição, avisa e a comparação final com a base publicada indica se os valores diferem. Sem os arquivos, roda em modo demonstração.

### Executar o roteiro e as células

No VS Code, abra a pasta do projeto, selecione a `.venv` como interpretador e abra `scripts/analise_sinesp.py`: use *Run Cell* em cada célula `# %%` ou *Run All Cells* (Python Interactive; requer `ipykernel`). No terminal: `python -m scripts.analise_sinesp` (cerca de um minuto com os XLSX, por causa da leitura de ~170 MB). O roteiro não grava arquivos. O roteiro histórico `scripts/analise_seguranca_publica.py` não é necessário e, por incluir as etapas da SSP/SC, exige o acervo dessa fonte; não o execute para reproduzir a entrega.

## 12. Estrutura de pastas

```text
README.md                         documentação acadêmica central: 16 seções
requirements.txt                  intervalos de dependências
.gitignore                        dados, segredos, caches e backups fora do Git
.env.example                      exemplo sem credenciais
.vscode/settings.json             .venv e raiz do Python Interactive
scripts/
  analise_sinesp.py               roteiro acadêmico principal (Sinesp): células # %% para o VS Code Interactive
  analise_seguranca_publica.py     roteiro histórico: Sinesp 1–10 (primeira versão) e SSP/SC 11–14.2; fora do escopo
  painel_streamlit.py             entrada do painel (st.navigation com 3 páginas)
  gerar_dados_dashboard.py        geração inicial reprodutível de dashboard/data_publica/ (Sinesp)
  fontes_oficiais.py              verificar: consulta metadados do Sinesp/MJSP (somente leitura)
  atualizacao_dados.py            preparar / aprovar / reverter (atualização controlada)
  versionamento_dados.py          manifesto versionado e licenças da fonte
  extract.py, transform.py        módulos anteriores; podem gerar arquivos
  analysis.py, utils.py           análises históricas e resolução de caminhos
  legacy/                        código histórico, fora da execução corrente
dashboard/
  pages/                         home.py, sinesp.py e quality.py (3 páginas)
  dados_publicos.py, calculos.py,
  graficos.py, formatacao.py, ui.py  módulos do painel (sem Streamlit, exceto ui.py)
  data_publica/                  2 CSVs Sinesp + manifesto versionado + LEIAME (ver seção 10)
tests/                           suíte ativa (120 testes)
tests_historicos/                suíte histórica (acervo local e roteiro SSP/SC)
historico/ssp_sc/LEIAME.md       índice do trabalho histórico SSP/SC e Prefeitura (fora do escopo)
notebooks/                       notebook SSP de inspeção (histórico), sem saídas gravadas
documentacao/
  ESCOPO_PROJETO.md               escopo vigente: fonte única Sinesp/MJSP
  ATUALIZACAO_DE_DADOS.md         procedimento verificar → preparar → aprovar
  DEPLOY_STREAMLIT.md             preparação do Streamlit Community Cloud
  fontes/                        proveniência e métodos por fonte
  auditoria/                     relatórios e metadados/hashes
  analises/                      relato histórico; tabelas/imagens locais ignoradas
dados/                           acervo local; não versionado
atualizacao/                     entradas, candidatas, versões anteriores e verificações; local e não versionado
video/                           reservado; sem arquivo de entrega
backup_pre_migracao_20261016/     cópia local preservada e ignorada
```

Pastas vazias não são preservadas pelo Git. O README de continuidade e seus backups permanecem **fora do repositório**. O [inventário de migração](documentacao/auditoria/mapa_migracao.csv) documenta os caminhos históricos.

## 13. Limitações e melhorias futuras

- 2026 é parcial: setembro é a última competência publicada (PRF: agosto). Comparações usam períodos equivalentes por série; um ano parcial nunca é comparado com um ano completo.
- Os valores são registros administrativos agregados do Sinesp: não medem toda a criminalidade, não estimam subnotificação e não sustentam causalidade. Contagens pequenas (feminicídio, latrocínio, lesão seguida de morte) geram percentuais instáveis.
- Não há taxas populacionais (falta base demográfica oficial compatível), dados por bairro, rua, horário ou corporação, nem total geral entre indicadores, abrangências ou unidades.
- A fonte pode **revisar** valores históricos; a atualização controlada detecta revisões, e elas só entram com aprovação específica. Os XLSX oficiais foram republicados em 27/10/2026 com hashes diferentes, sem mudança nos valores de Joinville; uma nova auditoria é necessária se isso mudar.
- Condições de reutilização com ressalvas: licença do catálogo do MJSP não confirmada; CC BY-ND 3.0 no rodapé do portal. Nenhuma proibição específica foi encontrada, mas não há autorização específica explícita.
- O gov.br não oferece API pública nem data por arquivo; a verificação é indício, não prova, e o download integral (~24 MB por arquivo) pode ser interrompido e exigir repetição ou obtenção manual.
- O deploy foi feito, mas a revisão visual do painel (todas as páginas, desktop e celular) e o aperfeiçoamento dos gráficos estão pendentes.
- Melhorias possíveis: inspeção responsiva em celular, fixação de versões de dependências com validação em ambiente limpo, definição de licença do código, relatórios exportáveis e, se houver base demográfica oficial compatível, taxas por habitante.
- A SSP/SC e a Prefeitura/SEPROT ficam fora do escopo; reintegrá-las exigiria nova decisão metodológica e um fluxo auditado próprio (ver [historico/ssp_sc/LEIAME.md](historico/ssp_sc/LEIAME.md)).
- A regra `fillna(0)` no módulo histórico `scripts/analysis.py` não faz parte do fluxo atual e precisa de revisão antes de reutilização. O notebook histórico ainda contém um caminho antigo `pdfs/csv_extraidos`.
- Arquivos em `documentacao/analises/` são registros históricos; em caso de divergência, prevalecem o código atual, as evidências registradas e este estado acadêmico atualizado.

## 14. Créditos e referências

Fonte primária: MJSP/Sinesp VDE, citada na seção 4. [Documentação de fontes](documentacao/fontes/) e [auditoria de origem](documentacao/auditoria/sinesp_origem_2020_2022.csv) preservam a procedência. As fontes históricas (SSP/SC e Prefeitura/SEPROT) estão documentadas em [historico/ssp_sc/LEIAME.md](historico/ssp_sc/LEIAME.md) e em `documentacao/fontes/`.

Licença do código e permissões de redistribuição dos dados ainda devem ser definidas/documentadas; a ausência de um arquivo de licença não deve ser interpretada como autorização irrestrita.

## 15. Links de entrega

- [Repositório GitHub](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC): público; contém o roteiro, o dashboard de três páginas, os dados mínimos agregados (`dashboard/data_publica/`), o fluxo de atualização controlada, os testes e a documentação (branch `main`).
- URL Git exata: `https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC.git`.
- Pasta local: repositório Git na branch `main`, com `origin` configurado.
- Aplicação Streamlit publicada: <https://seguranca-publica-joinville-sinesp.streamlit.app/> (deploy realizado; revisão visual e aperfeiçoamento dos gráficos pendentes).
- Repositório oficial da turma: pendente.
- Vídeo e link de leitura no Drive: pendentes.
- AVA e demais itens administrativos: pendentes.
- Trello: dispensado por orientação do professor.

Antes de preparar arquivos para versionar, conferir o [gitignore](.gitignore): `dados/`, `atualizacao/`, tabelas/imagens derivadas locais, ambientes, segredos, logs, backups e o README de continuidade não devem entrar. Novos envios ao remoto dependem de autorização; usar `git push` normal, sem sobrescrever ou forçar atualização.

## 16. Conclusões sustentadas pelas análises

O fluxo Sinesp preservou 900 linhas originais na versão auditada, produziu uma cópia analítica 900 × 10, manteve ausências e abrangências, gerou tabelas descritivas por série e exibiu figuras sem exportação. A atualização controlada incorporou setembro/2026 (911 observações em 12 séries) sem alterar nenhum valor histórico de Joinville. Homicídio doloso e suas tentativas, feminicídio e suas tentativas permaneceram distintos.

A análise sustenta descrições dos valores publicados e comparações temporais equivalentes, com atenção a pequenas contagens. Não sustenta total geral de criminalidade, causalidade, estimativa de subnotificação, taxa populacional ou distribuição por bairros. O dashboard de três páginas apresenta a pergunta, a fonte única, o período real, os indicadores, as estatísticas, as figuras e a qualidade dos dados; o aplicativo está publicado, e a revisão visual dos gráficos, o vídeo, o repositório da turma e o AVA permanecem pendentes.
