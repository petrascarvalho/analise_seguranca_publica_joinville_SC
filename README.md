# Segurança Pública de Joinville — Visualização de Dados e Business Intelligence

**Curso:** SENAI/SC - LAB365 | Módulo 2
**Aluno:** Petras Ruben Carvalho
**Projeto:** Indicadores oficiais de segurança pública de Joinville/SC

Análise de indicadores oficiais de segurança pública de **Joinville/SC** com Python: um ETL único, um notebook didático e um painel Streamlit de página única. A fonte do painel é o **Sinesp/MJSP**; a violência doméstica da **SSP/SC** aparece em seção separada e continua **em validação**.

**Aplicação publicada:** [https://seguranca-publica-joinville-sinesp.streamlit.app/](https://seguranca-publica-joinville-sinesp.streamlit.app/)

![Painel de página única: cabeçalho com a bandeira de Joinville, índice e apresentação](documentacao/graficos/painel/01_visao_geral_pagina_unica.png)

*Captura do painel executado localmente em 29/10/2026 (1440 px).*

---

## 1. Título e resumo

**Indicadores oficiais de segurança pública de Joinville/SC: análise do Sinesp/MJSP (2020–2026) e auditoria do acervo SSP/SC.**

Os sete arquivos anuais do Sinesp viram **911 observações** mensais de **12 séries** (indicador × classificação institucional), de janeiro/2020 a setembro/2026, publicadas num painel Streamlit. Cada série mantém sua unidade (vítimas ou mandados cumpridos) e sua cobertura. Em paralelo, os 45 documentos da SSP/SC foram inventariados e auditados: a violência doméstica de Joinville (216 observações, 2023–2024) está extraída e conferida, mas não foi identificada uma definição operacional da unidade publicada, "Fato Comunicado", nos documentos analisados; os homicídios dos boletins mensais têm versões divergentes entre edições. Nenhum total geral é calculado: indicadores, unidades e fontes diferentes nunca são somados.

## 2. Problema, objetivo e importância

**Pergunta analítica:** como evoluíram, desde janeiro/2020, os indicadores oficiais de segurança pública de Joinville/SC, e o que a comparação entre períodos equivalentes permite — e não permite — afirmar?

**Objetivo:** produzir uma análise municipal reproduzível, com origem auditável, estatísticas adequadas a contagens mensais, comparações justas entre períodos de mesma duração e um registro honesto do que ainda não pode ser publicado.

**Importância:** estudantes, cidadãos, pesquisadores e gestores podem consultar os números com fonte, unidade e limites explícitos. São registros administrativos: não medem toda a criminalidade e não demonstram efeitos de políticas públicas.

## 3. Escopo e resultados esperados

| Situação | Conteúdo |
| --- | --- |
| **No painel (validado)** | Sinesp/MJSP: homicídio doloso e tentativa, feminicídio e tentativa, lesão corporal seguida de morte, latrocínio, suicídio, mortes a esclarecer, mortes no trânsito (Estadual e PRF), mandados de prisão cumpridos (Estadual e Polícia Federal) |
| **No painel, em seção separada (em validação)** | SSP/SC: violência doméstica mensal (9 categorias, 2023–2024), com todos os detalhes só na execução local (seção 10) |
| **Preservado para auditoria** | SSP/SC: vítimas de homicídio nos boletins mensais (2020–2026); Prefeitura/SEPROT (furtos e roubos 2023–2025, valores divergentes); a antiga página SSP/SC do painel (último commit com ela: `bad9723`) |
| **Fora do escopo** | Furtos, roubos em geral, estupro e tráfico no Sinesp (não existem nos arquivos de Joinville), atendimentos da Guarda Municipal, taxas populacionais, dados por bairro ou horário, previsões e inferência causal |

Para os indicadores do painel, o Sinesp/MJSP é a **fonte única**: SSP/SC e Prefeitura/SEPROT ficam fora do escopo dos indicadores Sinesp e nunca são somadas a eles.

**Requisitos da atividade:** repositório individual com histórico e README completo; ETL em Python reproduzível e documentado; EDA, estatísticas e visualizações fundamentadas; aplicação Streamlit publicada no Streamlit Community Cloud; fontes, licenças e proteção de dados; publicação no repositório da turma; vídeo de até três minutos; envio dos links no AVA até **30/10/2026, 22h (Brasília)**. O planejamento no Trello foi **dispensado por orientação do professor**.

## 4. Fontes e autorização

### 4.1 Sinesp/MJSP (validado)

| Item | Descrição |
| --- | --- |
| Fonte | [Sinesp VDE / MJSP](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023) — base nacional enviada pelos gestores estaduais |
| Arquivos | `bancovde-2020.xlsx` a `bancovde-2026.xlsx` (um por ano, 14 colunas, ~24 MB cada) |
| Recorte | `uf = SC` e `municipio = JOINVILLE` (filtro exato) |
| Medidas | vítimas em `total_vitima`; mandados cumpridos em `total` |
| Versão dos dados | `20261027T114400Z` (SHA-256 de cada XLSX e dos arquivos publicados no manifesto) |

A edição oficial usada está em `dados/brutos/sinesp/oficial_20261027/` (republicada em 27/10/2026); a edição auditada em agosto/2026 também foi guardada. A procedência de 2020–2022 foi conferida ([evidência](documentacao/auditoria/sinesp_origem_2020_2022.csv)). O MJSP informa que o valor zero significa ausência de ocorrência.

**Condições de reutilização (consulta de 27/10/2026):** o catálogo `dados.mj.gov.br` seria "Creative Commons Atribuição", mas esse registro **não pôde ser confirmado** (o domínio não resolveu); o rodapé do portal gov.br declara CC BY-ND 3.0, licença geral do site. Não há proibição nem autorização específica explícita (avaliação técnica, não parecer jurídico). Por prudência, o repositório publica só arquivos **mínimos, agregados e derivados** (`dashboard/data_publica/`), sempre com atribuição; os XLSX ficam fora do Git.

### 4.2 SSP/SC (em validação)

Secretaria de Estado da Segurança Pública de SC — [Segurança em Números](https://ssp.sc.gov.br/segurancaemnumeros/): **45 PDFs oficiais** (42 boletins mensais de 2023–2026 e 3 relatórios de violência doméstica: [1º semestre de 2023](https://ssp.sc.gov.br/wp-content/uploads/2025/06/VIOLENCIA-DOMESTICA-1o-SEMESTRE-2023.pdf), [2º semestre de 2023](https://ssp.sc.gov.br/wp-content/uploads/2025/06/VIOLENCIA-DOMESTICA-2o-SEMESTRE-2023.pdf) e [2024](https://ssp.sc.gov.br/wp-content/uploads/2025/06/VIOLENCIA-DOMESTICA-2024-SC.pdf)), cada um com um CSV extraído que localiza página, tabela e linha. Os SHA-256 estão em [`documentacao/auditoria/ssp_sc_acervo_sha256.csv`](documentacao/auditoria/ssp_sc_acervo_sha256.csv).

A procedência é oficial e verificável e os PDFs não têm dados pessoais (só contagens por município, categoria e mês). Mas os relatórios não trazem nota metodológica, definição de "Fato Comunicado" nem licença, e a página da fonte só informa "Todos os Direitos Reservados". **Por isso o CSV tratado da SSP/SC não é publicado** sem autorização específica, e os PDFs ficam fora do Git.

### 4.3 Base publicada no painel (Sinesp)

| Arquivo em `dashboard/data_publica/` | Conteúdo | Dimensão |
| --- | --- | --- |
| `sinesp_joinville_mensal.csv` | `ano, mes, evento, abrangencia, unidade, valor` | 911 × 6 |
| `sinesp_catalogo_indicadores.csv` | 12 séries, unidades, natureza, medida original, cobertura, zeros e ausentes | 12 × 12 |
| `manifesto_dados_publicos.json` | origens, SHA-256, tamanhos, regras, datas, aprovação e cobertura por série | metadados |

Versão `20261027T114400Z`, aprovada em **2026-10-27T11:45:19Z** (UTC), sem aceitar revisões históricas. Cobertura **2020-01 a 2026-09**; a PRF termina em **2026-08** e os mandados da Polícia Federal começam em 2025-01. Somente contagens municipais agregadas: nenhum dado pessoal nem XLSX nacional.

### 4.4 Fontes complementares (investigação preservada)

Consulta de 27/10/2026 a fontes da Prefeitura, do Governo de SC e da ALESC; nada disso foi incorporado ao painel.

<details>
<summary>Fontes, divergências e matriz de indicadores</summary>

Consulta feita em 27/10/2026. **Nada deste documento foi incorporado ao dashboard nem à base Sinesp**. Dados estaduais não foram usados como se fossem de Joinville.

#### 1. O que o Sinesp realmente traz para Joinville

Nos sete XLSX oficiais (2020–2026) o recorte `SC`/`JOINVILLE` tem apenas **11 eventos**: Feminicídio, Homicídio doloso, Lesão corporal seguida de morte, Mandado de prisão cumprido, Morte no trânsito ou em decorrência dele (exceto homicídio doloso), Mortes a esclarecer (sem indício de crime), Mortes no trânsito (PRF), Roubo seguido de morte (latrocínio), Suicídio, Tentativa de feminicídio e Tentativa de homicídio. **Furto, roubo, furto/roubo de veículos, estupro e tráfico de drogas não existem nos arquivos VDE de Joinville.** O código recusa evento novo; incluí-los exige decisão metodológica.

#### 2. Fontes consultadas

| Fonte                                                                                                                                         | URL                                                                                                                           | Publicador / data                                                                                 | Conteúdo para Joinville                                                                                                                                                                                                     | Série histórica        | Limitações                                                                                                                                                                                       |
| --------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Notícia "Índices de criminalidade têm redução…"                                                                                         | https://www.joinville.sc.gov.br/noticias/indices-de-criminalidade-tem-reducao-em-joinville-pelo-terceiro-ano-consecutivo/     | Prefeitura / SEPROT, 13/01/2026                                                                   | Totais anuais 2023–2025: furtos, roubos, furtos e roubos de veículos; residências 2024–2025; latrocínio só em texto                                                                                                    | Só 3 anos; anual        | Não nomeia a fonte dos números nem define "furto/roubo"; sem mensal; sem estupro/tráfico                                                                                                        |
| Notícia "Prefeitura reconhece empenho…"                                                                                                     | https://www.joinville.sc.gov.br/noticias/prefeitura-de-joinville-reconhece-empenho-dos-profissionais-das-forcas-de-seguranca/ | Prefeitura / SEPROT, 12/01/2024                                                                   | 2023: roubos 361, furtos 1351, latrocínio 0, taxa de mortes violentas 9,57/100 mil; **estupros −22% e tráfico −30% sobre 2022 (só variação %)**                                                                 | Só 2023 (vs. 2022 em %) | Valores de 2022 não informados; contagens de estupro e tráfico **não localizadas**                                                                                                        |
| Joinville Cidade em Dados                                                                                                                     | https://www.joinville.sc.gov.br/publicacoes/joinville-cidade-em-dados/                                                        | Prefeitura; edições 2010–2025 (HTML/PDF)                                                       | A página de 2025 lista 5 capítulos em PDF; **não verifiquei o conteúdo dos PDFs**                                                                                                                                  | Possível                | PENDENTE: abrir os PDFs (Desenvolvimento Social e Gestão Institucional) para ver se há segurança pública                                                                                       |
| Portal de Dados Abertos de SC                                                                                                                 | https://dados.sc.gov.br/                                                                                                      | Governo de SC                                                                                     | Único conjunto de segurança: "Segurança em Números" (link para o site da SSP/SC; sem arquivo de dados)                                                                                                                   | —                       | Sem recorte municipal em arquivo                                                                                                                                                                   |
| **Relatório de Estatística nº 061/2024/GEAC/DINE/SSP/SC**, de 15/03/2024 (solicitação da ALESC, dep. Emerson Stein, de 11/03/2024) | https://portalelegis.alesc.sc.gov.br/documentos/z1LZ8                                                                         | SSP/SC — Gerência de Estatística e Análise Criminal; fonte declarada: GEAC/DINE/SSP/SC e SISP | "Mortes violentas, roubo e furto em 2023 em SC". Joinville 2023: **58 vítimas** de morte violenta (9,41/100 mil; população 616.323); **669 ocorrências de roubo** (Tabela 03, página 16/29; 108,55/100 mil) | Só 2023 (sem série)    | Lido diretamente do PDF em 27/10/2026. Sem definição de roubo/furto, de abrangência nem de revisões; os 58 não são o homicídio doloso do Sinesp (55); a Tabela 04 repete a 03 (seção 3.1) |

#### 3. Divergência de 2023 (Prefeitura)

| Indicador 2023 | Notícia de 12/01/2024   | Notícia de 13/01/2026 |
| -------------- | ------------------------ | ---------------------- |
| Furtos         | 1.351 (−52% sobre 2022) | 8.865                  |
| Roubos         | 361 (−42% sobre 2022)   | 933                    |

Os totais diferem 6,6× (furtos) e 2,6× (roubos). **Não está resolvida.** Observação, sem concluir: a mesma notícia de 2026 informa 1.249 furtos de veículos em 2023, valor próximo ao total de 1.351 de 2024, o que sugere que o total de 2024 pode ser outro recorte, mas **nenhuma das duas publicações define o recorte**. Decisão aplicada: os dois pares ficam como **divergentes**, sem escolher um, sem série definitiva. Também **não** há como comprovar que 2024–2025 sigam a mesma definição de 2023; ficam "disponíveis, não validados". Para resolver é preciso consultar a SEPROT/SSP-SC (a notícia de 2024 atribui os números aos "registros oficiais das Forças de Segurança").

##### 3.1 Terceira evidência oficial: SSP/SC (Relatório nº 061/2024/GEAC/DINE/SSP/SC)

Leitura direta do PDF (https://portalelegis.alesc.sc.gov.br/documentos/z1LZ8), em 27/10/2026. O relatório de 15/03/2024 traz "dados estatísticos referentes a mortes violentas, roubo e furto no ano de 2023 no Estado de Santa Catarina" (fonte: GEAC/DINE/SSP/SC e SISP).

| Roubos em Joinville, 2023         | Valor                                                         | Fonte                           |
| --------------------------------- | ------------------------------------------------------------- | ------------------------------- |
| SSP/SC, Tabela 03 (página 16/29) | **669** ocorrências (616.323 hab.; 108,55 por 100 mil) | Relatório 061/2024, 15/03/2024 |
| Prefeitura / SEPROT               | 361                                                           | Notícia de 12/01/2024          |
| Prefeitura / SEPROT               | 933                                                           | Notícia de 13/01/2026          |

**Três valores diferentes para o mesmo indicador e ano.** Nenhum deles vem com definição de "roubo", abrangência institucional, critério de contagem (ocorrências, registros, vítimas), data de extração ou indicação de revisão. A Prefeitura não nomeia a fonte; a SSP/SC cita o SISP.

**Possível inconsistência editorial (não é erro comprovado).** A Tabela 04, "Número de ocorrências de furto em SC" (página 23/29), traz para Joinville exatamente **669**, a mesma população e a mesma taxa (108,55) da Tabela 03, e os valores de outros municípios que conferi (Florianópolis 829, São José 457, Itajaí 417, Balneário Camboriú 335, Blumenau 232…) também são idênticos aos da Tabela 03, apenas em outra ordem (a Tabela 04 está ordenada por população). Isso sugere que a Tabela 04 reproduz os dados da 03, mas **só a SSP/SC pode confirmar** se é falha de edição ou se os valores coincidem por alguma regra. **Decisão: não usar 669 como total de furtos** (nem como roubo definitivo). O 669 está no protótipo apenas como "Roubos (ocorrências)", situação **divergente**.

Esclarecimentos necessários (SEPROT/SSP-SC): definição de cada indicador; abrangência territorial e institucional (Polícia Militar, Civil, Guarda; boletins registrados no município ou ocorridos nele); critério de contagem (ocorrência, vítima, registro, natureza principal ou todas); período de referência e data da extração; revisões históricas; inclusão ou exclusão de subclasses (veículos, residências, comércio, pessoas; tentativas; furto qualificado).

Também não é o mesmo conceito que o Sinesp: as 58 vítimas de "mortes violentas" do relatório não equivalem ao homicídio doloso do Sinesp (55 vítimas em 2023); não foi feita reconciliação.

#### 4. Matriz de indicadores

Situações: **V** disponível e validado · **NV** disponível, mas não validado · **D** divergente · **P** parcial · **NL** não localizado. `—` = não publicado (nunca zero). Todas as fontes são anuais; **não há dados mensais**.

| Indicador                                                                                | Fonte                                   | Município | 2020                            | 2021 | 2022 | 2023                                  | 2024                 | 2025                 | 2026 | Unidade             | Situação                                                 |
| ---------------------------------------------------------------------------------------- | --------------------------------------- | ---------- | ------------------------------- | ---- | ---- | ------------------------------------- | -------------------- | -------------------- | ---- | ------------------- | ---------------------------------------------------------- |
| Homicídio doloso, feminicídio, tentativas, latrocínio, suicídio, trânsito, mandados | Sinesp VDE                              | Joinville  | série mensal 2020-01 a 2026-09 |      |      |                                       |                      |                      |      | vítimas / mandados | **V** (base atual)                                   |
| Furtos                                                                                   | Prefeitura                              | Joinville  | —                              | —   | —   | 8.865 ou 1.351                        | 8.730                | 8.372                | —   | registros           | **D** (2023); 2024–25 **NV**                  |
| Roubos                                                                                   | Prefeitura; SSP/SC                      | Joinville  | —                              | —   | —   | 933 ou 361 (Prefeitura); 669 (SSP/SC) | 593                  | 476                  | —   | registros           | **D** (2023); 2024–25 **NV**                  |
| Furtos de veículos                                                                      | Prefeitura (2026)                       | Joinville  | —                              | —   | —   | 1.249                                 | 758                  | 668                  | —   | registros           | NV                                                         |
| Roubos de veículos                                                                      | Prefeitura (2026)                       | Joinville  | —                              | —   | —   | 191                                   | 75                   | 65                   | —   | registros           | NV                                                         |
| Furtos de residência                                                                    | Prefeitura (2026)                       | Joinville  | —                              | —   | —   | —                                    | 2.378                | 2.347                | —   | registros           | P / NV                                                     |
| Roubos de residência                                                                    | Prefeitura (2026)                       | Joinville  | —                              | —   | —   | —                                    | 82                   | 61                   | —   | registros           | P / NV                                                     |
| Latrocínio                                                                              | Prefeitura (2024, texto 2026) × Sinesp | Joinville  | —                              | —   | —   | 0                                     | sem registro (texto) | sem registro (texto) | —   | registros           | confirmado pelo Sinesp (V no Sinesp)                       |
| Estupro                                                                                  | Prefeitura (2024)                       | Joinville  | —                              | —   | —   | só −22% vs 2022                     | —                   | —                   | —   | —                  | **NL** (sem valor absoluto)                          |
| Tráfico de drogas                                                                       | Prefeitura (2024)                       | Joinville  | —                              | —   | —   | só −30% vs 2022                     | —                   | —                   | —   | —                  | **NL** (sem valor absoluto)                          |
| Mortes violentas (relatório SSP/ALESC)                                                  | SSP/SC (PDF lido)                       | Joinville  | —                              | —   | —   | 58 vítimas                           | —                   | —                   | —   | vítimas            | NV (conceito diferente do homicídio doloso do Sinesp: 55) |
| Mortes violentas (taxa)                                                                  | Prefeitura (2024)                       | Joinville  | —                              | —   | —   | 9,57                                  | —                   | —                   | —   | por 100 mil hab.    | NV                                                         |
| Outros 2025 (prisões PM 2.633, armas apreendidas 66, drogas 1,7 t, etc.)                | Prefeitura (2026)                       | Joinville  | —                              | —   | —   | —                                    | —                   | valores únicos      | —   | atividade policial  | NV; não são contagens de crimes                          |

Não foram convertidas variações percentuais em contagens estimadas (estupro, tráfico).

#### 5. Próximo passo

Nenhum dado complementar entra no painel antes de validado. Foi preparada, e não enviada, uma minuta de solicitação à SEPROT e à GEAC/DINE/SSP/SC pedindo a série oficial de furtos e roubos de Joinville de 2020 a 2026, a definição de cada indicador, a abrangência, o critério de contagem e a data de extração.

</details>

## 5. ETL e metodologia

### 5.1 Decisões metodológicas

- **Recorte municipal:** só linhas com `uf = SC` e `municipio = JOINVILLE`. Nenhum dado estadual ou nacional é usado como se fosse de Joinville.
- **Classificação institucional (`abrangencia`):** Estadual, Polícia Federal e Polícia Rodoviária Federal dizem quem informa a série. "Estadual" **não** é o total de Santa Catarina. Classificações diferentes nunca são somadas.
- **Séries com períodos diferentes:** a maioria vai de janeiro/2020 a setembro/2026; a PRF termina em agosto/2026 e os mandados da Polícia Federal começam em 2025. Cada série só aparece até o seu último mês, sem preenchimento.
- **Ano de 2026 parcial e períodos equivalentes:** totais anuais só usam anos com os 12 meses; 2026 só é comparado com o mesmo período dos anos anteriores (por exemplo, janeiro–setembro). A diferença absoluta é sempre informada; o percentual só existe quando a base é maior que zero.
- **Zero informado × dado ausente:** zero é um número publicado pela fonte (401 casos); ausência é falta de informação e nunca é preenchida nem trocada por zero (hoje, nenhuma ausência).
- **Vítimas × mandados cumpridos:** unidades diferentes, nunca somadas. Não existe total geral entre indicadores.
- **Sinesp × SSP/SC:** fontes, unidades e critérios diferentes. A SSP/SC fica em seção separada, nunca é somada nem comparada com o Sinesp, e "Fato Comunicado" não é lido como vítimas, pessoas ou ocorrências únicas.
- **Estatística:** média, mediana e desvio-padrão (`ddof=0`) descrevem os meses observados; quartis por interpolação linear; limites de Tukey (Q1 − 1,5·IQR e Q3 + 1,5·IQR) só quando a série permite (pelo menos 12 meses, IQR > 0, menos de 50% de zeros e Q3 > 1). São critérios estatísticos, não parâmetros oficiais, e não indicam causa. A distribuição usa o zero como faixa própria (regra de Sturges) e o perfil por mês do ano usa só anos completos, sem afirmar sazonalidade.
- **Integridade e rastreabilidade:** o SHA-256 de cada XLSX e dos arquivos publicados fica no manifesto; cada valor da SSP/SC é localizado por PDF, página, tabela e linha; o ETL para se qualquer conferência divergir.
- **Publicação do CSV da SSP/SC:** condições de reutilização não esclarecidas (seção 4.2); o CSV não é publicado.

### 5.2 ETL único — [`scripts/etl_joinville.py`](scripts/etl_joinville.py)

Um só programa, sequencial, sem funções nem classes próprias, com etapas numeradas em comentários `#` (por exemplo, `# 3. LEITURA DOS DADOS BRUTOS DO SINESP`) e um comentário junto de cada operação importante. Roda no terminal e no VS Code (por partes, com Shift+Enter).

| Etapas | O que fazem |
| --- | --- |
| 1–2 | Bibliotecas e pastas de entrada e saída |
| 3–4 | Leitura só das linhas SC/JOINVILLE (911) dos sete XLSX cujo SHA-256 é o do manifesto; inspeção com `head()` e `info()` |
| 5–6 | Duplicidades (`duplicated()`; nenhuma linha é apagada) e valores ausentes (`isna()`) |
| 7–8 | Tratamento: data serial do Excel, medida (vítimas × mandados), tipo `Int64`; conferência de que só há Joinville/SC |
| 9–10 | Uma linha por série e mês (`groupby` + `sum(min_count=1)`; só *Tentativa de homicídio* e *Estupro* podem ter parcelas somadas) e conferência com a base publicada e o SHA-256 do manifesto |
| 11–12 | SSP/SC: 45 PDFs, extração do bloco de Joinville e 159 verificações contra os PDFs |
| 13–14 | Exportação **somente** para `dados/processados/etl_joinville/` (`sinesp/` e `ssp_sc/`, separados) e releitura dos arquivos gravados |

Sem os XLSX oficiais (ou com outra edição) ou sem os PDFs da SSP/SC, o ETL **para com uma mensagem clara** e não grava nada. A base do painel (`dashboard/data_publica/`) nunca é alterada por ele. Variáveis opcionais: `SINESP_PASTA_XLSX` e `ETL_PASTA_SAIDA`. As saídas foram comparadas byte a byte com a versão aprovada.

### 5.3 Extração da SSP/SC — [`src/pipeline/ssp_sc.py`](src/pipeline/ssp_sc.py)

Os CSVs posicionais localizam o bloco de JOINVILLE e cada linha é conferida diretamente na tabela do PDF (159 verificações, todas aprovadas); nada é redigitado. Violência doméstica: 216 linhas (9 categorias × 24 meses), com página e SHA-256 do documento; as duas grafias das lesões corporais viram a mesma categoria. Homicídios dos boletins: 294 valores publicados, ligados por JOIN muitos-para-um a 58 grupos de republicação; nenhuma versão é escolhida. O arquivo de rastreabilidade localiza as 510 células (216 + 294).

### 5.4 UNION e JOIN — [`src/pipeline/consolidacao.py`](src/pipeline/consolidacao.py)

Cada fonte é convertida para um esquema comum (`fonte`, `municipio`, `serie_id`, `indicador`, `abrangencia`, `ano`, `mes`, `periodicidade`, `unidade`, `valor`, `arquivo_origem`, `situacao_validacao`...) e só então pode ser empilhada com `pd.concat` (UNION); a função recusa a união se mudar a quantidade de linhas, repetir uma observação ou misturar unidades. A união candidata Sinesp + violência doméstica tem 1.127 linhas (911 + 216), sem chave repetida, mas **não foi gravada** como consolidação, porque a SSP/SC continua em validação. O único JOIN aprovado é o da série com o catálogo (indicador + classificação, muitos-para-um).

### 5.5 Notebook — [`notebooks/analise_seguranca_publica_joinville.ipynb`](notebooks/analise_seguranca_publica_joinville.ipynb)

Roteiro de 16 etapas de código comentadas com `#` e uma célula de identificação: conferência da base aprovada, leitura bruta ilustrada com 2026, tratamento, duplicidades, ausências e zeros, estatísticas, totais anuais e períodos equivalentes, outliers (IQR), gráficos do Sinesp e a exploração separada da SSP/SC. Executa integralmente em kernel real; o arquivo versionado fica sem saídas.

## 6. Bibliotecas e tecnologias

| Ferramenta | Uso |
| --- | --- |
| Python 3.12, VS Code | Desenvolvimento e execução |
| pandas | Leitura, tratamento, validação, UNION e estatísticas |
| Matplotlib | Todos os gráficos |
| Streamlit 1.66.0 | Painel (versão fixa; o mínimo seria a 1.55) |
| lxml / openpyxl | Leitura do XML das planilhas do Sinesp / planilhas de teste |
| pdfplumber, pypdf | Leitura dos PDFs da SSP/SC |
| pytest | Testes automatizados |
| ipykernel, nbformat, nbclient | Execução do notebook |

As versões estão em [requirements.txt](requirements.txt), comentado por finalidade.

## 7. Resultados encontrados

### 7.1 Sinesp/MJSP (validado)

A versão auditada inicial tinha **900 registros Sinesp** (até agosto/2026). Em 27/10/2026 o Sinesp publicou setembro/2026 e a base passou a **911 observações**, com 12 séries, 0 valores ausentes e 401 zeros publicados — 11 observações novas e nenhum valor histórico alterado.

| Indicador (Estadual, vítimas) | Anos completos | Mesmo período |
| --- | --- | --- |
| Homicídio doloso | 62 em 2020 → 29 em 2025 | 21 em jan–set/2025 → **25 em 2026**; 18 em jan–ago/2025 → 22 em janeiro–agosto de 2026 |
| Tentativa de homicídio | 98 em 2020 → 53 em 2025 | 43 → 77 (jan–set) |
| Feminicídio | 3 em 2020 → 2 em 2025 | 2 → 0 (jan–set) |
| Tentativa de feminicídio | 10 em 2020 → 9 em 2025 | 5 → 12 (jan–set) |

Em homicídio doloso, janeiro/2020 (10) e janeiro/2023 (19) ficam acima do limite superior de Tukey (9,5); o método IQR só é informativo em 5 das 12 séries. Latrocínio e lesão corporal seguida de morte somam 4 e 8 vítimas em 81 meses.

![Gráfico combinado: homicídio doloso em Joinville/SC por ano completo, 2020–2025](documentacao/graficos/painel/04_grafico_homicidio_doloso_anual.png)

![Gráfico combinado: feminicídio em Joinville/SC por ano completo, 2020–2025](documentacao/graficos/painel/05_grafico_feminicidio_anual.png)

*Gráficos do painel (aba "Evolução"): barras azul-claras e linha azul-escura com o mesmo total anual, escala iniciada em zero e o valor escrito acima de cada ponto.*

<details>
<summary><b>Tabelas completas do Sinesp (por ano, períodos equivalentes e estatísticas mensais)</b></summary>

#### Totais publicados por ano

**2020–2025 são anos completos; a coluna 2026 contém apenas janeiro–setembro (PRF: janeiro–agosto) e não deve ser comparada diretamente com totais anuais.** Unidade: vítimas, exceto mandados (contagem publicada). PF = Polícia Federal; PRF = Polícia Rodoviária Federal. As linhas não se somam.

| Indicador / abrangência | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 (parcial) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
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

#### Comparações equivalentes: janeiro–agosto

Todos os valores têm oito meses e são comparáveis entre todas as séries, inclusive a PRF. Homicídio doloso soma 18 em janeiro–agosto de 2025 e 22 em janeiro–agosto de 2026; tentativa de homicídio soma 37 e 68.

| Indicador / abrangência | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
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

#### Comparações equivalentes: janeiro–setembro

Todos os valores têm nove meses. A série *Mortes no trânsito — PRF* ainda não tem setembro/2026 (`—` em 2026); seus anos anteriores aparecem só como referência. Homicídio doloso soma 21 em janeiro–setembro de 2025 e **25 em 2026**; tentativa de homicídio soma 43 e 77; feminicídio, 2 e 0; tentativa de feminicídio, 5 e 12.

| Indicador / abrangência | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
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

#### Estatísticas mensais descritivas

Período observado: janeiro/2020–setembro/2026, com 81 meses por série estável; a PRF tem 80 meses (até agosto/2026) e os mandados da PF, 21 meses desde janeiro/2025. A soma refere-se a todo o período observado; o desvio-padrão descreve os meses disponíveis (`ddof=0`), sem inferência.

| Indicador / abrangência | Meses | Soma | Média mensal | Mediana | Mín. | Máx. | DP (ddof=0) |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
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

</details>

### 7.2 SSP/SC — violência doméstica (exploratório, em validação)

Fatos comunicados por categoria em Joinville, segundo os três relatórios da SSP/SC: 216 células (9 categorias × 24 meses, janeiro/2023 a dezembro/2024), sem republicações, 27 zeros publicados e nenhum valor ausente.

| Categoria | 2023 | 2024 | Diferença | Média mensal (24 meses) |
| --- | ---: | ---: | ---: | ---: |
| Ameaça | 1.957 | 2.085 | +128 | 168,4 |
| Lesão corporal leve dolosa | 989 | 959 | −30 | 81,2 |
| Injúria | 541 | 716 | +175 | 52,4 |
| Vias de fato | 229 | 281 | +52 | 21,3 |
| Difamação | 190 | 211 | +21 | 16,7 |
| Calúnia | 109 | 119 | +10 | 9,5 |
| Estupro | 22 | 30 | +8 | 2,2 |
| Lesão corporal grave ou gravíssima dolosa | 19 | 10 | −9 | 1,2 |
| Injúria real | 2 | 6 | +4 | 0,3 |

**Leitura permitida:** comparar cada categoria consigo mesma entre 2023 e 2024, na unidade publicada. **Não permitida:** somar categorias (um mesmo fato pode envolver mais de uma), tratar "Fato Comunicado" como vítima, pessoa ou ocorrência única, comparar com o Sinesp ou apresentar os números como definitivos.

### 7.3 SSP/SC — vítimas de homicídio nos boletins (republicações)

Os 42 boletins mensais republicam os totais de anos anteriores. Dos 58 grupos de valores republicados, 17 são iguais em todas as edições e **41 têm versões diferentes** (37 inconsistências ainda não explicadas e 4 possíveis problemas de cabeçalho); nenhuma versão é escolhida.

| Ano | Edições | Versões publicadas (SSP/SC) | Sinesp, homicídio doloso |
| --- | ---: | --- | ---: |
| 2020 | 11 | 65 ou 66 | 62 |
| 2021 | 24 | 62 ou 68 | 62 |
| 2022 | 35 | 49 ou 51 | 49 |
| 2023 | 31 | 56 ou 58 | 55 |
| 2024 | 18 | 36 ou 37 | 36 |
| 2025 | 7 | 32 | 29 |

Os conceitos não são iguais ("vítimas de homicídio" na SSP/SC; "homicídio doloso" no Sinesp): a comparação só mostra a diferença, nunca serve para somar ou escolher um valor.

## 8. Discussão e conclusão

No Sinesp, homicídio doloso caiu de 62 vítimas em 2020 para 29 em 2025, com oscilações (49 em 2022, 55 em 2023). Em 2026, o mesmo período mostra alta em relação a 2025 (21 para 25 em janeiro–setembro), e as tentativas de homicídio subiram de 43 para 77. Em contagens pequenas, a diferença absoluta informa mais que o percentual, e zero publicado não prova eliminação do fenômeno nem eficácia de política.

Na SSP/SC, a violência doméstica teve, em 2024, mais registros que em 2023 em sete das nove categorias, com a ameaça como a mais frequente — uma descrição na unidade publicada, enquanto o significado de "Fato Comunicado" não for confirmado. Os homicídios dos boletins mostram que o mesmo número pode mudar entre edições: sem a versão definitiva, servem para auditoria, não para série histórica.

## 9. Aplicação profissional

O projeto mostra como publicar indicadores municipais com transparência: fonte, período e unidade explícitos, comparações entre períodos equivalentes, conferência de integridade por hash e uma atualização controlada que detecta revisões da fonte antes de aceitá-las. A auditoria da SSP/SC mostra o outro lado do trabalho com dados públicos: documentar divergências e lacunas antes de qualquer gráfico.

## 10. Aplicação Streamlit

O painel é **uma única página** com a bandeira de Joinville no cabeçalho, fundo azul-claro e cards brancos de mesma altura. Ele lê somente `dashboard/data_publica/` (Sinesp), não executa o ETL e não acessa a internet. Um índice no topo leva a cada seção:

| Seção | Conteúdo |
| --- | --- |
| **Apresentação** | Período, registros, séries e último mês disponível; três destaques fixos e os principais achados |
| **Indicadores Sinesp** | Filtros **Indicador**, **Período (anos)**, **Meses** e **Restaurar filtros**; cards do indicador; cinco abas (Evolução, Comparações, Meses e tendência, Estatísticas e meses incomuns, Indicadores e como interpretar) |
| **VIOLÊNCIA DOMÉSTICA — SSP/SC** | Fonte separada, em validação, com filtro próprio **Categoria (SSP/SC)** |
| **Qualidade dos dados** | Arquivos conferidos, data da base, último mês disponível, dados não informados e "Sobre os dados apresentados" |
| **Fontes, metodologia e limitações** | Origem dos dados, como os números são tratados e limitações; fonte e autoria no rodapé |

![Destaques fixos e principais achados](documentacao/graficos/painel/02_destaques_e_achados.png)

![Filtros e resumo do indicador escolhido](documentacao/graficos/painel/03_filtros_e_resumo_sinesp.png)

**Filtros.** O seletor **Indicador** mostra só o nome principal (11 opções). A classificação institucional só vira uma segunda escolha no "Mandado de prisão cumprido", que existe como série Estadual e da Polícia Federal; nos demais, aparece numa nota discreta. O período em anos depende do indicador, **Meses** vale para as análises mensais (totais anuais, média móvel e acumulado usam sempre os 12 meses) e **Restaurar filtros** volta ao início. Só a aba aberta é calculada. Cada gráfico tem, logo abaixo, a tabela com os números desenhados. A chave **Visualização compacta (celular)** gera figuras estreitas com os mesmos números.

**Linguagem.** O texto é escrito para qualquer cidadão, sem nomes de arquivos, comandos ou termos de programação. O painel diz que os números são de Joinville/SC e que "Estadual" não é o total do estado; cita a fonte ("Ministério da Justiça e Segurança Pública (MJSP) — Sinesp VDE") e a autoria ("Petras Ruben Carvalho — Analista de Dados | Business Intelligence"); escreve os meses por extenso; e explica que zero informado não é ausência. As cores são uma proposta inspirada na bandeira (azul `#074EA2`, fundo `#EAF4FC`), não códigos oficiais do município.

**Violência doméstica SSP/SC.** Usa as 216 observações auditadas, em "Fato Comunicado" (unidade em validação). Como o CSV não é publicado, **a seção completa (filtro de categoria, cards, gráfico e tabela) só funciona na execução local**, quando o arquivo `dados/processados/ssp_sc/violencia_domestica_joinville_tratada.csv` existe. Na aplicação publicada no Streamlit Cloud, a seção mostra apenas o aviso da limitação e uma figura-resumo com os totais anuais por categoria.

![Seção de violência doméstica SSP/SC na execução local (no Streamlit Cloud aparece só a figura-resumo)](documentacao/graficos/painel/06_violencia_domestica_ssp_sc.png)

![Qualidade dos dados e metodologia](documentacao/graficos/painel/07_qualidade_e_metodologia.png)

**Publicação:** Aplicação Streamlit publicada: [https://seguranca-publica-joinville-sinesp.streamlit.app/](https://seguranca-publica-joinville-sinesp.streamlit.app/). **Deploy realizado** no Streamlit Community Cloud (repositório `petrascarvalho/analise_seguranca_publica_joinville_SC`, branch `main`, arquivo `scripts/painel_streamlit.py`, Python 3.12, tema em `.streamlit/config.toml`); o aplicativo reflete o último commit enviado ao GitHub. As capturas acima são da execução local; a revisão visual no aplicativo publicado e em dispositivos móveis reais ainda está pendente.

**Atualização dos dados (Sinesp):** manual e controlada. **Não há atualização automática operacional**: nada roda em agendamento e o painel nunca baixa dados.

```bat
python -m src.pipeline.atualizacao_dados verificar
python -m src.pipeline.atualizacao_dados preparar --entradas-sinesp <pasta com os XLSX 2020 a 2026>
python -m src.pipeline.atualizacao_dados comparar <id>
python -m src.pipeline.atualizacao_dados aprovar <id> --confirmo <id>
python -m src.pipeline.atualizacao_dados reverter <versao> --confirmo <versao>
```

**Verificar** só consulta a fonte e classifica indícios, sem alterar nada. **Preparar** monta uma versão candidata isolada e a compara com a ativa; esquema alterado, indicador novo, valor inválido ou lacuna bloqueiam, e valores históricos revisados pela fonte exigem `--aceitar-revisoes`. **Aprovar** só promove com a confirmação igual ao id, guarda a versão anterior e desfaz a troca se algo falhar. A última atualização (27/10/2026) trouxe setembro/2026, sem revisão histórica.

**Testes:** **293 testes aprovados**, nenhum ignorado, em 29/10/2026, na suíte `tests/`: integridade e manifesto, tabelas deste README, filtros e página única, gráficos, modo compacto, estatísticas, atualização controlada, ETL único (com os XLSX e os PDFs), notebook em kernel real, SSP/SC e o padrão de comentários do código. As garantias de testes históricos foram migradas para `tests/test_integridade_acervo.py`; três deles conferem um backup externo (variável `JOINVILLE_ARQUIVO_ETAPA26`) e aparecem como não executados quando ele não existe. Os 147 arquivos de dados protegidos mantiveram os mesmos hashes.

## 11. Como executar

No **Prompt de Comando (CMD)** do Windows, na pasta do projeto:

```bat
:: 1. Ambiente e dependências
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

:: 2. ETL único (lê dados/brutos/sinesp e dados/brutos/ssp_sc; grava só em dados/processados/etl_joinville)
.\.venv\Scripts\python.exe scripts\etl_joinville.py

:: 3. Painel (abre em http://localhost:8501)
.\.venv\Scripts\python.exe -m streamlit run scripts/painel_streamlit.py

:: 4. Testes
.\.venv\Scripts\python.exe -m pytest tests -q
```

**Notebook:** abra `notebooks/analise_seguranca_publica_joinville.ipynb` no VS Code, escolha o kernel da `.venv` e use *Run All*.

**Arquivos fora do Git:** baixe os sete `bancovde-ANO.xlsx` do [catálogo do MJSP](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados) para `dados/brutos/sinesp/` e os PDFs da SSP/SC da página [Segurança em Números](https://ssp.sc.gov.br/segurancaemnumeros/) para `dados/brutos/ssp_sc/pdfs/`. Sem eles, o painel funciona normalmente (a seção SSP/SC mostra só a figura-resumo) e o ETL avisa que precisa dos originais. Opcional: `.\.venv\Scripts\python.exe -m src.pipeline.consolidacao` grava a Sinesp no esquema comum e a matriz de compatibilidade.

## 12. Estrutura de pastas

```text
Seguranca Publica Joinville/
├── README.md, requirements.txt
├── scripts/
│   ├── etl_joinville.py        programa principal 1: ETL único (14 etapas)
│   └── painel_streamlit.py     programa principal 2: painel de página única
├── notebooks/analise_seguranca_publica_joinville.ipynb
├── dashboard/                  seções do painel (pages/), cálculos, gráficos, componentes e data_publica/ (base aprovada)
├── src/pipeline/               leitura dos XLSX (transform.py), SSP/SC (ssp_sc.py), UNION (consolidacao.py),
│                               atualização controlada (atualizacao_dados.py, fontes_oficiais.py, versionamento_dados.py)
├── documentacao/
│   ├── auditoria/              procedência do Sinesp e inventários SHA-256
│   └── graficos/
│       ├── painel/             sete capturas do painel atual (29/10/2026)
│       └── analises/           figura-resumo da SSP/SC usada pelo painel publicado
├── tests/                      suíte automatizada (293 testes)
├── .streamlit/, .vscode/       tema do painel e configuração do VS Code
├── dados/                      (local, fora do Git) brutos/ e processados/
└── atualizacao/                (local, fora do Git; criada quando a atualização controlada é usada)
```

**Histórico e recuperação.** O ETL único substituiu o roteiro `scripts/etl_sinesp.py` (682 linhas, com análise e gráficos que já estão no notebook): `git show 22688ae^:scripts/etl_sinesp.py`. Materiais antigos (`historico/`, `tests_historicos/`, a antiga página SSP/SC em `bad9723`) são recuperáveis com `git show 5702724:<caminho>`. Cópias externas com SHA-256 conferido ficam em `C:\Users\Ususario\Desktop\readme.ia\` (`arquivo_etapa26\`, `arquivo_etapa29\`, `arquivo_fase2_etl\` e `arquivo_limpeza_final\`, que guarda também as seis capturas da interface antiga). Nada disso é necessário para executar o projeto.

## 13. Limitações e melhorias futuras

- 2026 é parcial (até setembro; PRF até agosto) e só é comparado com o mesmo período dos anos anteriores.
- Registros administrativos agregados: não medem toda a criminalidade, não estimam subnotificação e não sustentam causalidade.
- Sem taxas populacionais, dados por bairro ou horário, nem total entre indicadores ou fontes.
- O Sinesp pode revisar valores históricos; a atualização controlada detecta e só aceita com aprovação.
- SSP/SC: definição operacional de "Fato Comunicado" não identificada nos documentos analisados; violência doméstica só para 2023–2024; homicídios com 41 grupos de versões divergentes; condições de reutilização não confirmadas (CSV não publicado).
- Próximos passos: confirmar com a SSP/SC a definição de "Fato Comunicado", a versão definitiva dos homicídios e a autorização de reutilização; confirmar o uso dos dados com o MJSP e definir a licença do código.

## 14. Créditos e referências

- **Bandeira municipal:** arquivo local [bandeira de Joinville](dashboard/assets/bandeira_joinville.svg), sem alteração do desenho. Fonte: [Wikimedia Commons — Bandeira de Joinville.svg](https://commons.wikimedia.org/wiki/File:Bandeira_de_Joinville.svg) (Great Brightstar e Prefeitura de Joinville, versão de 06/10/2020; domínio público, PD Brazil Government). Uso como identificação territorial em trabalho acadêmico.
- **Identidade da interface:** azul `#074EA2` (o azul do arquivo SVG da bandeira), fundo `#EAF4FC`, cards `#FFFFFF`, bordas `#BFD6EB` e títulos `#103C6D` — escolhas de interface, não códigos oficiais do município.
- Ministério da Justiça e Segurança Pública — Sinesp VDE, base de dados e notas metodológicas dos gestores estaduais.
- Secretaria de Estado da Segurança Pública de Santa Catarina — Segurança em Números (boletins mensais e relatórios de violência doméstica).
- Prefeitura de Joinville / SEPROT — notícias com totais de furtos e roubos (acervo histórico).

## 15. Links de entrega

- Repositório GitHub: [https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC) (branch `main`).
- Aplicação Streamlit publicada: [https://seguranca-publica-joinville-sinesp.streamlit.app/](https://seguranca-publica-joinville-sinesp.streamlit.app/).
- Trello: dispensado por orientação do professor.
- Repositório oficial da turma: pendente.
- Vídeo (até três minutos): pendente.
- AVA: pendente.

## 16. Conclusões sustentadas pelas análises

O ETL reconstrói, a partir dos XLSX oficiais, exatamente a base publicada do Sinesp (911 observações, mesmo SHA-256 do manifesto), sem apagar linhas, sem converter ausências em zero e sem misturar unidades. A extração da SSP/SC também é reproduzível a partir dos PDFs (216 células de violência doméstica, 294 valores de homicídio, 159 verificações aprovadas) e mostra os limites dessa fonte: unidade sem definição identificada e versões divergentes de homicídio. A análise sustenta descrições dos valores publicados e comparações entre períodos equivalentes; não sustenta total geral de criminalidade, causalidade, subnotificação, taxas populacionais nem a soma de fontes diferentes.
