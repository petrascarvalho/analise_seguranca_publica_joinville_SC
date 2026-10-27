# Segurança Pública de Joinville

Projeto acadêmico individual de Visualização de Dados e BI — SENAI/LAB365, Módulo 2, Semana 13. Estado documentado em 27/10/2026. As etapas Sinesp 1–10 e as etapas SSP/SC 11, 12, 13.1, 13.2, 13.3, 14.1 e 14.2 (violência doméstica de Joinville) foram implementadas e executadas em memória; os resultados abaixo foram observados nessas execuções, sem reexecutar o ETL durante a atualização documental. A integração dos resultados e figuras ao Streamlit, o tratamento da Prefeitura e o deploy permanecem pendentes.

## 1. Título e resumo

**Análise dos indicadores públicos de segurança de Joinville/SC, 2020–2026.** O projeto utiliza Python/Pandas, dados oficiais e visualizações Matplotlib para descrever séries municipais, preservando fonte, unidade, abrangência institucional e período. O produto final previsto inclui painel Streamlit, documentação, repositório e apresentação acadêmica.

Sinesp: janeiro/2020 a agosto/2026; SSP/SC: homicídios anuais de 2020–2025 e acumulados até julho/2026, além de violência doméstica em 2023–2024; Prefeitura/SEPROT: furtos e roubos anuais de 2023–2025. Cada indicador possui cobertura própria. Não há um total geral de criminalidade obtido somando essas fontes.

## 2. Problema, objetivo e importância

**Pergunta analítica:** como evoluíram os indicadores oficiais disponíveis de criminalidade registrada em Joinville entre 2020 e 2026, e quais limites das fontes afetam sua interpretação?

O objetivo é produzir uma análise municipal reproduzível, com origens auditáveis, estatísticas adequadas às unidades e comparação de períodos equivalentes. O público inclui estudantes, cidadãos, pesquisadores e gestores. Os dados descrevem registros informados/publicados; não medem toda a criminalidade ocorrida nem demonstram efeitos causais de políticas públicas.

## 3. Escopo e resultados esperados

O escopo inclui feminicídio, tentativa de feminicídio, violência doméstica e suas categorias disponíveis, homicídio doloso, tentativa de homicídio, latrocínio, lesão corporal seguida de morte, furtos e roubos. Suicídio, mortes a esclarecer, trânsito e mandados são indicadores complementares; atividade policial não é contagem de crimes ou de vítimas únicas.

Requisitos acadêmicos registrados: trabalho individual do SENAI/LAB365, Módulo 2, Semana 13; ETL em Python, EDA, estatísticas, gráficos com fontes, painel interativo Streamlit, README, repositório dedicado, publicação da aplicação, vídeo de até três minutos e envio dos links ao AVA/repositório da turma conforme enunciado. O prazo informado é **30/10/2026 às 22h, horário de Brasília**, sujeito a comunicados posteriores. Regras finais de visibilidade do repositório, divulgação e marcações do vídeo devem ser conferidas no enunciado vigente antes da entrega.

As etapas Sinesp 1–10 e as etapas SSP/SC 11–14.2 (incluindo as seis visualizações da violência doméstica, produzidas em memória) estão implementadas e foram executadas. A próxima prioridade é a **integração dos resultados Sinesp e SSP/SC ao Streamlit**. Tratamento da Prefeitura, exportações, deploy e entrega final permanecem pendentes.

## 4. Fonte e autorização

| Fonte oficial | Aquisição e evidência | Cobertura municipal local | Unidade e ressalvas |
|---|---|---|---|
| [Sinesp VDE / MJSP](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023) | Sete XLSX anuais; [origem e verificações](documentacao/fontes/ORIGEM_SINESP.md) e [evidência de 2020–2022](documentacao/auditoria/sinesp_origem_2020_2022.csv) | 2020–2025 completos; janeiro–agosto/2026 | Vítimas em `total_vitima`; mandados em `total`; abrangências preservadas |
| [Segurança em Números — SSP/SC](https://ssp.sc.gov.br/segurancaemnumeros/) | 45 PDFs e 45 CSVs intermediários locais; [método registrado](documentacao/fontes/SSP_SC.md) | Homicídios anuais 2020–2025 e acumulados até julho/2026; violência doméstica 2023–2024 | Vítimas de homicídio; fatos comunicados/registros domésticos; boletins republicam e revisam valores |
| [Prefeitura de Joinville / SEPROT](https://www.joinville.sc.gov.br/noticias/indices-de-criminalidade-tem-reducao-em-joinville-pelo-terceiro-ano-consecutivo/) | Seis valores transcritos de notícia de 13/01/2026; [documentação](documentacao/fontes/CSV_COMPLEMENTARES.md) | Furtos e roubos anuais 2023–2025 | Totais publicados de delitos registrados; boletim, fato ou registro único ainda não esclarecido por dicionário |

A conferência anterior da notícia confirmou os seis números de furto/roubo. Isso não resolve a definição estatística da unidade. Não há série municipal de 2026 para esses indicadores nos arquivos locais.

Os dados brutos e processados ficam fora do primeiro commit. A disponibilidade pública de uma fonte não confirma autorização de redistribuição integral; termos/licenças ainda precisam de conferência. Os resultados textuais próprios deste README são apresentados com atribuição. Não são publicados microdados pessoais, credenciais ou referências artificiais a bairros.

## 5. Pipeline e metodologia

O roteiro principal é [scripts/analise_seguranca_publica.py](scripts/analise_seguranca_publica.py), organizado em células `# %%`. As execuções recentes reconstruíram os recortes pelos XLSX originais no mesmo processo e não usaram CSV histórico como substituto. O roteiro atual mantém resultados em memória e não chama as rotinas antigas de exportação.

| Etapa | Situação | Operação e controle |
|---|---|---|
| 1. Importação | Implementada; executada anteriormente | Pandas, leitores e caminhos do pacote `scripts` |
| 2. Diretórios | Implementada; executada anteriormente | Raiz do projeto e arquivos locais por fonte |
| 3. Leitura | Implementada; executada anteriormente | Amostra Sinesp 2023, CSVs intermediários SSP e transcrições Prefeitura |
| 4. Inspeção | Implementada; executada anteriormente | Colunas, tipos, amostras e contexto das páginas PDF; sem alteração dos originais |
| 5. Concatenação Sinesp | Implementada e executada | Sete recortes exatos `SC`/`JOINVILLE`; compatibilidade das 14 colunas; 900 linhas em memória |
| 6. Diagnóstico | Implementada e executada | Duplicidades, ausências e tipos; sem preenchimento ou exclusão |
| 7. Investigação | Implementada e executada | 20 linhas com sexo incompleto, 20 pares de mandados e propostas de campos/tipos |
| 8. Base analítica | Implementada e executada | Cópia 900 × 10; datas e cinco medidas `Int64`; original 900 × 14 intacto |
| 9. EDA | Implementada e executada | Tabelas mensais/anuais, janeiro–agosto e estatísticas por indicador/abrangência |
| 10. Visualizações | Implementada e executada | Quatro figuras Matplotlib em memória; valores conferidos contra as tabelas |
| 11. Inspeção SSP/SC | Implementada e executada | 45 PDFs e 45 CSVs brutos, 25.753 linhas tabulares, 11 esquemas de cabeçalho; sem alteração dos originais |
| 12. Auditoria SSP/SC | Implementada e executada | 58 grupos de republicações (17 concordantes, 41 divergentes); inconsistências do boletim de janeiro/2025; nenhuma versão histórica definitiva selecionada |
| 13.1. Blocos de violência doméstica | Implementada e executada | Leitura literal e exibição dos blocos de Joinville (páginas esquerda e direita) dos três relatórios; 68 verificações, zero divergências |
| 13.2. Base analítica | Implementada e executada | `df_violencia_domestica_joinville_ssp132` (216 × 5) e rastreabilidade (216 × 23), somente em memória |
| 13.3. Validação integral | Implementada e executada | 67 verificações aprovadas; 216 observações conferidas individualmente contra CSV e PDF |
| 14.1. EDA da violência doméstica | Implementada e executada | Inspeção, estatísticas por categoria, comparação 2023 × 2024 e análise mensal; 28 verificações aprovadas; sem gráficos |
| 14.2. Visualizações da violência doméstica | Implementada e executada | Seis figuras Matplotlib em memória (três anuais e três mensais); 79 verificações aprovadas e 90 valores plotados conferidos; nenhuma imagem exportada |
| Exportação de resultados | Pendente; não autorizada | Nenhuma base ou figura nova foi exportada |

A chave observacional mantém UF, município, evento, competência e abrangência; agente, arma e faixa etária permanecem disponíveis na camada original. Na última reconstrução houve zero duplicidade exata e zero repetição nas chaves que incluem abrangência. O controle sem abrangência identificou 20 grupos/40 linhas de mandados estaduais e PF, preservados separadamente.

As dez colunas analíticas são `uf`, `municipio`, `evento`, `data_referencia`, `feminino`, `masculino`, `nao_informado`, `total_vitima`, `total` e `abrangencia`. Agente, arma, faixa etária e peso não foram incluídos nessa cópia porque estão 100% ausentes; continuam intactos no original.

Datas: sistema Excel 1900 confirmado nos sete arquivos, origem `1899-12-30`, sem `errors="coerce"`. Foram validados seriais inteiros, ano do arquivo, primeiro dia do mês, cobertura e correspondência com o leitor Excel. O Pandas instalado produziu `datetime64[s]`. As cinco contagens passaram de `float64` para `Int64` anulável, após verificar valores finitos, inteiros e não negativos. As posições de ausência foram preservadas.

O catálogo auxiliar tem 12 combinações evento/abrangência, com medida, unidade, natureza e limitações. As estatísticas não misturam vítimas com mandados; somas temporais usam apenas a medida apropriada. Desvio-padrão descritivo usa `ddof=0`; médias/medianas informam seus meses de observação. Nenhum valor ausente foi convertido em zero.

**SSP/SC — violência doméstica (Etapas 11–14.2).** As etapas leem os 45 PDFs e CSVs brutos sem alterá-los (os hashes SHA-256 são conferidos contra o inventário histórico). A base analítica reúne os três relatórios de violência doméstica (1º e 2º semestres de 2023 e ano de 2024) em nove categorias e 24 competências mensais (216 observações), com `municipio`, `ano`, `mes`, `categoria` e `fatos_comunicados`. Três decisões metodológicas aprovadas pelo projeto, **sem confirmação oficial da SSP/SC**: (i) as grafias "0 Dolosa" e "- Dolosa" das duas lesões corporais foram mapeadas por dicionário explícito para "Lesão corporal leve dolosa" e "Lesão corporal grave ou gravíssima dolosa", e os rótulos originais permanecem na rastreabilidade; (ii) o cabeçalho de meses da primeira página de cada metade da tabela é aplicado às páginas seguintes da mesma tabela contínua (nas páginas dos blocos de Joinville o cabeçalho de meses não é reimpresso); (iii) o município de Joinville é atribuído pelo contexto do bloco, pois a célula de município fica vazia nas linhas de continuação. A rastreabilidade registra, por observação, PDF e hash, CSV, página, tabela, linha, coluna, rótulo e valor originais. Linhas extraídas e células de tabela não equivalem a ocorrências policiais.

Os módulos [extract.py](scripts/extract.py), [transform.py](scripts/transform.py) e [analysis.py](scripts/analysis.py) são de fase anterior e podem gravar resultados quando chamados como programas. Não são equivalentes ao roteiro atual e não devem ser executados automaticamente. Na SSP, os 45 CSVs brutos intermediários diferem dos quatro CSVs municipais históricos. Uma seleção de snapshots não é deduplicação genérica nem soma de boletins.

## 6. Bibliotecas e tecnologias

Ambiente local conferido: Python **3.12.14**, Pandas **3.0.6**, Matplotlib **3.11.2**, Streamlit **1.66.0**, openpyxl **3.1.5**, pdfplumber **0.11.10**, pypdf **6.21.0**, lxml **6.1.3**, pyarrow **26.0.0**, pytest **8.4.2** e ipykernel **7.4.0**.

Os intervalos de instalação estão em [requirements.txt](requirements.txt); não constituem um arquivo de versões travadas. `ipykernel` é uma dependência adicional para uso interativo e não está declarado nesse arquivo. A validação em ambiente limpo e eventual fixação de versões continuam pendentes. Matplotlib já estava instalado; não foi necessário instalar Plotly.

## 7. Resultados encontrados

Os números Sinesp abaixo foram observados nas execuções autorizadas das etapas 5–10. Esta atualização documental transcreve as evidências registradas; não reexecuta o ETL.

### Cobertura, dimensões e ausências

Foram preservados **900 registros Sinesp** e 14 colunas no original; a cópia analítica tem 900 linhas e dez colunas.

| Ano | Linhas municipais | Meses por série estável |
|---|---:|---|
| 2020 | 132 | janeiro–dezembro |
| 2021 | 132 | janeiro–dezembro |
| 2022 | 132 | janeiro–dezembro |
| 2023 | 132 | janeiro–dezembro |
| 2024 | 132 | janeiro–dezembro |
| 2025 | 144 | janeiro–dezembro; inclui mandados PF |
| 2026 | 96 | janeiro–agosto; inclui mandados PF |

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

As 4.852 células ausentes originais foram preservadas. Na visão analítica, as dez colunas retidas mantêm as mesmas 1.252 ausências e suas posições. Há 20 linhas com total de vítimas informado e detalhamento de sexo incompleto: 16 sem parcelas de sexo e quatro com algumas parcelas; nas quatro, os valores informados coincidem com o total, sem autorizar preenchimento residual.

### Totais publicados por ano

**2020–2025 são anos completos; 2026 contém apenas janeiro–agosto. Não comparar diretamente essa coluna parcial com totais anuais.** Unidade: vítimas, exceto mandados, que usam contagem publicada. PF = Polícia Federal; PRF = Polícia Rodoviária Federal. Não se somam linhas desta tabela.

| Indicador / abrangência | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Feminicídio — Estadual | 3 | 6 | 2 | 2 | 3 | 2 | 0 |
| Homicídio doloso — Estadual | 62 | 62 | 49 | 55 | 36 | 29 | 22 |
| Lesão corporal seguida de morte — Estadual | 0 | 2 | 3 | 1 | 1 | 0 | 1 |
| Mandados — Estadual | 612 | 790 | 884 | 980 | 1035 | 1248 | 821 |
| Mortalidade no trânsito¹ — Estadual | 22 | 21 | 33 | 26 | 34 | 20 | 12 |
| Mortes a esclarecer — Estadual | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| Mortes no trânsito — PRF | 10 | 11 | 13 | 7 | 8 | 13 | 6 |
| Latrocínio — Estadual | 0 | 1 | 3 | 0 | 0 | 0 | 0 |
| Suicídio — Estadual | 43 | 52 | 67 | 44 | 48 | 39 | 27 |
| Tentativa de feminicídio — Estadual | 10 | 4 | 7 | 7 | 10 | 9 | 10 |
| Tentativa de homicídio — Estadual | 98 | 96 | 103 | 101 | 82 | 53 | 68 |
| Mandados — PF | — | — | — | — | — | 8 | 6 |

¹ Morte no trânsito ou em decorrência dele, exceto homicídio doloso. `—` representa falta de cobertura da série, não zero.

### Comparações equivalentes: janeiro–agosto

Todos os valores desta tabela têm oito meses. Homicídio doloso soma 18 em 2025 e **22 em 2026**; tentativa de homicídio soma 37 e 68. As duas tentativas e os dois indicadores de feminicídio/homicídio não são somados.

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

### Estatísticas mensais descritivas

Período observado: janeiro/2020–agosto/2026, com 80 meses por série estável; mandados PF têm 20 meses desde janeiro/2025. As medidas utilizadas possuem valores publicados em todos esses meses. A soma abaixo refere-se a todo o período observado; o desvio-padrão descreve os meses disponíveis (`ddof=0`), sem inferência causal ou amostral.

| Indicador / abrangência | Meses | Soma | Média mensal | Mediana | Mín. | Máx. | DP (ddof=0) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Feminicídio — Estadual | 80 | 18 | 0,23 | 0 | 0 | 3 | 0,55 |
| Homicídio doloso — Estadual | 80 | 315 | 3,94 | 3 | 0 | 19 | 2,80 |
| Lesão corporal seguida de morte — Estadual | 80 | 8 | 0,10 | 0 | 0 | 2 | 0,34 |
| Mandados — Estadual | 80 | 6370 | 79,63 | 80 | 0 | 160 | 26,10 |
| Mortalidade no trânsito¹ — Estadual | 80 | 168 | 2,10 | 2 | 0 | 7 | 1,46 |
| Mortes a esclarecer — Estadual | 80 | 0 | 0,00 | 0 | 0 | 0 | 0,00 |
| Mortes no trânsito — PRF | 80 | 68 | 0,85 | 1 | 0 | 3 | 0,85 |
| Latrocínio — Estadual | 80 | 4 | 0,05 | 0 | 0 | 2 | 0,27 |
| Suicídio — Estadual | 80 | 320 | 4,00 | 4 | 0 | 12 | 2,02 |
| Tentativa de feminicídio — Estadual | 80 | 57 | 0,71 | 0 | 0 | 5 | 0,96 |
| Tentativa de homicídio — Estadual | 80 | 601 | 7,51 | 7,5 | 0 | 16 | 3,01 |
| Mandados — PF | 20 | 14 | 0,70 | 0 | 0 | 4 | 1,10 |

### Quatro gráficos da Etapa 10

As figuras foram renderizadas e inspecionadas em memória. Contêm título, período, eixo de vítimas iniciado em zero, rótulos, fonte MJSP/Sinesp VDE e abrangência Estadual. Nenhum arquivo novo de gráfico foi exportado; as cinco imagens antigas existentes localmente pertencem ao pipeline anterior e ficam fora do primeiro commit.

| Gráfico | Anos, na ordem apresentada | Valores utilizados |
|---|---|---|
| Homicídio doloso anual | 2020, 2021, 2022, 2023, 2024, 2025 | Homicídio doloso: 62, 62, 49, 55, 36, 29 |
| Feminicídio e tentativa anuais | 2020, 2021, 2022, 2023, 2024, 2025 | Feminicídio: 3, 6, 2, 2, 3, 2; Tentativa de feminicídio: 10, 4, 7, 7, 10, 9 |
| Homicídio e tentativa, janeiro–agosto | 2020, 2021, 2022, 2023, 2024, 2025, 2026 | Homicídio doloso: 50, 40, 29, 40, 21, 18, 22; Tentativa de homicídio: 74, 53, 60, 62, 57, 37, 68 |
| Feminicídio e tentativa, janeiro–agosto | 2025, 2026 | Feminicídio: 0, 0; Tentativa de feminicídio: 4, 10 |

### SSP/SC: inspeção e auditoria dos boletins (Etapas 11 e 12)

A inspeção (Etapa 11) encontrou 45 PDFs originais (42 boletins de indicadores e três relatórios de violência doméstica), 762 páginas, 45 CSVs extraídos integralmente, 25.753 linhas tabulares em 11 esquemas de cabeçalho, 126 linhas físicas candidatas relacionadas a Joinville, 294 células de contagens de homicídio e 216 células mensais de violência doméstica. **Linhas extraídas e células de tabela não equivalem a ocorrências policiais**; os dados brutos integrais e os recortes municipais permanecem distintos.

A auditoria (Etapa 12) identificou 58 grupos com republicações: 17 com valores concordantes e 41 com valores divergentes (quatro classificados como possível problema de cabeçalho e 37 sem explicação documental suficiente). Nenhuma revisão histórica específica foi comprovada documentalmente e **nenhuma versão histórica de homicídio foi selecionada como definitiva**. No boletim `2025_02_01-janeiro-1.pdf`, página 8, tabela 1, linha municipal de Joinville, há inconsistências entre os cabeçalhos e os números publicados; não foi comprovado erro de extração CSV e anos ou valores não foram corrigidos por inferência. Os acumulados de fevereiro apresentam problemas de interpretação dos rótulos 28/02 e 29/02 em diferentes anos. Valores de homicídio SSP/SC não são somados entre boletins e não são tratados como série definitiva.

### SSP/SC: violência doméstica em Joinville (Etapas 13.1 a 14.1)

Fonte: relatórios temáticos de violência doméstica da SSP/SC, Joinville/SC, janeiro/2023 a dezembro/2024, nove categorias, unidade publicada "Fato Comunicado" (a definição operacional não consta dos PDFs consultados; não deve ser interpretada automaticamente como vítima, pessoa única ou boletim de ocorrência único). A base analítica (216 linhas × 5 colunas) e a rastreabilidade (216 × 23) foram construídas e validadas em memória (Etapas 13.2 e 13.3: 67 verificações aprovadas; 216 observações conferidas individualmente por três caminhos independentes — CSV, texto do PDF e tabela do PDF; 27 zeros publicados preservados; zero ausências; zero duplicidades; seis arquivos originais com SHA-256 inalterado). Mapeamento das grafias de lesão corporal e associação dos meses às páginas seguintes: decisões metodológicas, sem confirmação oficial (seção 5).

Nesta análise exploratória (Etapa 14.1), todas as somas e comparações são feitas **por categoria**; não há total geral por soma das categorias. As diferenças entre 2023 e 2024 são mudanças nas contagens publicadas, não necessariamente na incidência real.

| Categoria (Fato Comunicado) | 2023 (12 meses) | 2024 (12 meses) | Diferença absoluta | Variação percentual |
|---|---:|---:|---:|---:|
| Ameaça | 1.957 | 2.085 | +128 | +6,54% |
| Calúnia | 109 | 119 | +10 | +9,17% |
| Difamação | 190 | 211 | +21 | +11,05% |
| Estupro | 22 | 30 | +8 | +36,36% |
| Injúria | 541 | 716 | +175 | +32,35% |
| Injúria real | 2 | 6 | +4 | +200,00% |
| Lesão corporal grave ou gravíssima dolosa | 19 | 10 | −9 | −47,37% |
| Lesão corporal leve dolosa | 989 | 959 | −30 | −3,03% |
| Vias de fato | 229 | 281 | +52 | +22,71% |

Estatísticas mensais dos 24 meses (desvio-padrão descritivo, `ddof=0`):

| Categoria | Soma publicada | Média mensal | Mediana | Mín. | Máx. | DP | Meses com zero |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ameaça | 4.042 | 168,42 | 167,5 | 127 | 209 | 22,57 | 0 |
| Calúnia | 228 | 9,50 | 9 | 2 | 17 | 3,71 | 0 |
| Difamação | 401 | 16,71 | 17 | 6 | 24 | 4,57 | 0 |
| Estupro | 52 | 2,17 | 2 | 0 | 5 | 1,40 | 2 |
| Injúria | 1.257 | 52,38 | 51,5 | 33 | 78 | 12,13 | 0 |
| Injúria real | 8 | 0,33 | 0 | 0 | 2 | 0,55 | 17 |
| Lesão corporal grave ou gravíssima dolosa | 29 | 1,21 | 1 | 0 | 4 | 1,12 | 8 |
| Lesão corporal leve dolosa | 1.948 | 81,17 | 82 | 51 | 109 | 12,25 | 0 |
| Vias de fato | 510 | 21,25 | 19,5 | 13 | 32 | 5,59 | 0 |

Os 27 zeros publicados estão distribuídos em Injúria real (17), Lesão corporal grave ou gravíssima dolosa (8) e Estupro (2). Maiores valores mensais (24 meses): Ameaça 209 (janeiro/2024), Lesão corporal leve dolosa 109 (dezembro/2023), Injúria 78 (março/2024), Vias de fato 32 (novembro/2024); Difamação 24 empata em janeiro/2023 e fevereiro/2024, e Estupro 5 empata em janeiro/2024 e julho/2024 (empates preservados na execução). Categorias com poucos casos (Estupro, Injúria real e lesão corporal grave ou gravíssima) variam muito com poucas unidades; seus percentuais devem ser lidos com cautela. Há aumento publicado em sete das nove categorias e redução em duas (lesão corporal leve e lesão corporal grave ou gravíssima); essa descrição não identifica causa.

### SSP/SC: visualizações da violência doméstica (Etapa 14.2)

Seis figuras Matplotlib foram construídas em memória, exclusivamente a partir das tabelas validadas das Etapas 13.2 e 14.1, e **nenhuma imagem foi exportada**. Cada figura traz o município (Joinville/SC), a fonte (SSP/SC), o período (janeiro/2023 a dezembro/2024), a unidade ("fatos comunicados") e a nota de que se trata de contagens publicadas, sem total entre categorias; o eixo vertical começa em zero. Não há percentuais destacados nem número de vítimas.

| Figura (variável) | Conteúdo | Valores plotados (2023 / 2024) |
|---|---|---|
| `fig_anual_maiores_ssp142` | Barras 2023 × 2024: categorias de maiores contagens | Ameaça 1.957 / 2.085; Lesão corporal leve dolosa 989 / 959; Injúria 541 / 716 |
| `fig_anual_intermediarias_ssp142` | Barras 2023 × 2024: contagens intermediárias | Vias de fato 229 / 281; Difamação 190 / 211; Calúnia 109 / 119 |
| `fig_anual_menores_ssp142` | Barras 2023 × 2024: menores contagens | Estupro 22 / 30; Lesão corporal grave ou gravíssima dolosa 19 / 10; Injúria real 2 / 6 |
| `fig_mensal_ameaca_ssp142` | Linhas mensais, janeiro a dezembro | Ameaça, 12 meses de 2023 e 12 de 2024 |
| `fig_mensal_lesao_leve_ssp142` | Linhas mensais, janeiro a dezembro | Lesão corporal leve dolosa, 12 meses de cada ano |
| `fig_mensal_injuria_ssp142` | Linhas mensais, janeiro a dezembro | Injúria, 12 meses de cada ano |

Validação: **79 verificações aprovadas** e **90 valores gráficos conferidos** (18 das barras anuais e 72 dos pontos mensais), lidos dos próprios elementos gráficos e comparados com a tabela da Etapa 14.1 e com os textos publicados na rastreabilidade; os DataFrames de origem permaneceram idênticos. As seis figuras foram inspecionadas visualmente; a inspeção levou à correção de títulos cortados e de rodapés sobrepostos. As figuras ainda **não estão integradas ao Streamlit** e não há deploy público confirmado. As mesmas ressalvas se aplicam: "Fato Comunicado" não representa necessariamente vítimas ou pessoas únicas; o mapeamento de "0 Dolosa" e "- Dolosa" e a aplicação do cabeçalho de meses às tabelas contínuas são decisões metodológicas; não há total geral nem inferência causal.

### Outras fontes: histórico preservado, ainda fora do fluxo analítico atualizado

Os 294 snapshots municipais de homicídio SSP/SC e os demais resultados históricos anteriores à Etapa 12 permanecem como histórico e não constituem série definitiva. Os boletins reapresentam anos e acumulados; datas de atualização podem variar por tabela.

Na Prefeitura, furtos foram 8.865, 8.730 e 8.372 em 2023–2025; roubos foram 933, 593 e 476. São seis totais anuais transcritos e conferidos anteriormente na notícia oficial, ainda sujeitos a esclarecimento da unidade e integração própria. Resultados e gráficos históricos dessas fontes não foram recalculados nesta fase Sinesp.

## 8. Discussão e conclusão

Em anos completos, homicídio doloso passou de 62 vítimas em 2020 para 29 em 2025, com oscilações intermediárias: 49 em 2022 e 55 em 2023. Na comparação janeiro–agosto, passou de 18 em 2025 para 22 em 2026; tentativas de homicídio passaram de 37 para 68. São recortes temporais distintos, com interpretações próprias.

Feminicídio apresentou três vítimas em 2020, seis em 2021 e duas em 2025. Em janeiro–agosto de 2025 e 2026, o total publicado foi zero. Tentativas de feminicídio passaram de quatro para dez na comparação equivalente. Pequenas contagens tornam percentuais instáveis; por isso, os gráficos enfatizam valores absolutos.

Na violência doméstica (SSP/SC, Joinville, 2023–2024), Ameaça é a categoria de maior contagem publicada (1.957 fatos comunicados em 2023 e 2.085 em 2024), seguida por Lesão corporal leve dolosa (989 e 959) e Injúria (541 e 716). Entre 2023 e 2024, sete categorias tiveram aumento nas contagens publicadas e duas, redução (lesão corporal leve e lesão corporal grave ou gravíssima). Trata-se de mudança na contagem publicada, não necessariamente na incidência, e de uma unidade ("Fato Comunicado") sem definição operacional nos PDFs. As diferenças em categorias de poucos casos, como Injúria real (2 para 6) e lesão grave ou gravíssima (19 para 10), refletem poucas unidades.

Latrocínio e lesão seguida de morte têm, respectivamente, quatro e oito vítimas em 80 meses. Zero publicado não demonstra eliminação do fenômeno, ausência de subnotificação ou eficácia de uma política. Diferenças entre Sinesp e SSP não são corrigidas à força. Não há taxas populacionais, previsão, inferência causal ou ranking territorial neste trabalho.

## 9. Aplicação profissional

A aplicação potencial é consulta transparente de indicadores municipais agregados, com fonte, período e unidade. Vítimas, mandados, ocorrências e fatos comunicados precisam de definições independentes. `abrangencia` distingue as séries Estadual/PF/PRF, mas não permite atribuir todo registro à Polícia Civil, Polícia Militar ou Guarda Municipal.

Para uso operacional, seriam necessários dicionários estáveis, atualização versionada, dados territoriais validados e revisão das sobreposições. Não há série municipal estruturada e comparável de atendimentos da Guarda Municipal, bairros, endereços, horários ou corporações individuais nesta base.

## 10. Aplicação Streamlit

Ponto de entrada: [scripts/painel_streamlit.py](scripts/painel_streamlit.py). Há duas páginas locais: [Projeto](dashboard/pages/home.py) e [Qualidade dos dados](dashboard/pages/quality.py). As tabelas e quatro figuras novas do Sinesp e as tabelas, estatísticas e seis figuras da violência doméstica SSP/SC (Etapas 13–14.2) **ainda não foram integradas**. O texto da página Projeto ainda menciona cobertura antiga e resultados pendentes; essa atualização do painel é tarefa futura, não executada aqui.

A página Qualidade consulta arquivos em `dados/processados/sinesp/`, `dados/processados/ssp_sc/` e `dados/processados/prefeitura/` pelo módulo `scripts.analysis`. Sem esses arquivos, a função retorna uma lista vazia e a página apresenta aviso; isso não equivale a um painel analítico funcional.

Como `dados/` ficará fora do Git, o deploy futuro exigirá uma distribuição permitida de dados mínimos: por exemplo, uma base curada pequena com autorização de publicação ou um artefato externo autorizado, versionado e com hash. A escolha, a exportação e a integração ainda dependem de autorização. Não há URL de deploy ou validação pública da aplicação.

## 11. Como executar

Abra **a raiz do projeto** no VS Code. Exemplo PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
# Opcional para Python Interactive, se ainda não estiver instalado:
python -m pip install ipykernel
```

O workspace [configura a .venv e o diretório do Jupyter](.vscode/settings.json) com referências relativas a `${workspaceFolder}`. Se uma janela interativa antiga estiver em outra pasta, reinicie seu kernel e confirme `Path.cwd()`. Não há ajuste manual de `sys.path` no roteiro.

### Restaurar entradas que não ficam no Git

1. **Sinesp:** obtenha os XLSX 2020–2026 no [catálogo oficial](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados), usando `bancovde-ANO.xlsx`. Coloque 2023–2026 em `dados/brutos/sinesp/` e 2020–2022 na subpasta `pendente_validacao_origem/`. Essa pasta mantém nome histórico; a origem foi validada. O padrão oficial de download é `https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/bancovde-ANO.xlsx/@@download/file`.
2. Confira tamanho e SHA-256 contra [o inventário versionado](documentacao/auditoria/inventario_sha256_pre_reorganizacao.csv). O roteiro interrompe se a versão for diferente; nesse caso, documente e revise a nova versão, sem sobrescrever automaticamente a anterior. **Caso conhecido de 2020:** a versão oficial auditada teve células iguais, mas bytes/hash diferentes do original local. Um novo download pode, portanto, não passar no gate de hash atual. Antes de usá-lo, será necessária uma nova auditoria e autorização para registrar a versão aceita no manifesto; não desabilite a verificação. Essa compatibilidade de clone limpo ainda é pendente.
3. **SSP:** obtenha os boletins e relatórios temáticos no portal oficial, preserve as versões/nomes registrados nos inventários e coloque os PDFs em `dados/brutos/ssp_sc/pdfs/`. Os 45 CSVs intermediários esperados ficam em `dados/brutos/ssp_sc/csv_extraidos/`. O [relato da extração integral](documentacao/auditoria/ssp_csv_extraction_etapa_1_1.md) descreve a rastreabilidade, mas **não há uma CLI completa dessa extração integral no fluxo atual**. O módulo antigo `scripts.extract` gera recortes municipais e não substitui esses 45 intermediários. Resolver essa lacuna é pendência de reprodução.
4. **Prefeitura:** conferir a notícia oficial e restaurar as três transcrições em `dados/processados/prefeitura/furto_roubo_joinville_ANO.csv`. O código e os valores estão em `scripts/transform.py`; o comando `python -m scripts.transform --furto-roubo` gera esses arquivos e deve ser executado apenas em uma etapa de geração autorizada. Não foi executado nesta preparação.

### Executar o roteiro e as células

Com todas as entradas locais restauradas:

```powershell
python -m scripts.analise_seguranca_publica
python -m streamlit run scripts/painel_streamlit.py
```

O primeiro comando executa todas as células do roteiro (Etapas 1–14.2), inclusive a preparação da cópia analítica e os quatro gráficos Sinesp em memória, e as etapas SSP/SC, que leem os 45 PDFs e CSVs locais. Não é um comando limitado a imports ou leitura; não o use para uma tarefa restrita à documentação. Ele não exporta os resultados novos.

Para trabalhar **somente Sinesp**, execute as células 1–2 e depois 5–10 no mesmo Python Interactive, com os sete XLSX e a auditoria disponíveis. Isso dispensa a leitura das entradas SSP/Prefeitura das células 3–4. Para trabalhar **somente a violência doméstica SSP/SC**, execute em ordem as células das Etapas 13.1 a 13.3 e depois 14.1 (cada etapa SSP/SC declara em comentário suas pré-condições), sem executar as Etapas 1–12 nem o Sinesp; é preciso ter localmente os três PDFs e CSVs de violência doméstica e o inventário de hashes. Os DataFrames e figuras ficam no kernel para inspeção no Data Viewer; as execuções mais recentes desta sessão foram conferidas em processos Python, sem pressupor que variáveis persistam em outra sessão do VS Code.

### Testes

Os testes de documentação podem ser executados sem ETL (conferem a estrutura do README e a presença das etapas 1–14.2, das subetapas 13.1–13.3, das seis figuras e das rotinas no roteiro, sem executá-lo):

```powershell
python -m pytest tests/test_readme_sections.py -q
```

Os demais testes de integridade dependem do acervo local e de saídas históricas excluídas do Git; não representam um teste de clone limpo apenas com código. O relato antigo de 12 testes aprovados é histórico. Os resultados da preparação documental atual devem ser lidos no relatório da atividade, sem declarar execução recente da suíte completa.

## 12. Estrutura de pastas

```text
README.md                         documentação acadêmica central: 16 seções
requirements.txt                  intervalos de dependências
.gitignore                        dados, segredos, caches e backups fora do Git
.env.example                      exemplo sem credenciais
.vscode/settings.json             .venv e raiz do Python Interactive
scripts/
  analise_seguranca_publica.py     roteiro acadêmico: etapas 1–10 (Sinesp) e 11–14.2 (SSP/SC)
  painel_streamlit.py             entrada do painel
  extract.py, transform.py        módulos anteriores; podem gerar arquivos
  analysis.py, utils.py           análises históricas e resolução de caminhos
  legacy/                        código histórico, fora da execução corrente
dashboard/pages/                 home.py e quality.py
notebooks/                       notebook SSP de inspeção, sem saídas gravadas
tests/                           verificações documentais e do acervo local
documentacao/
  fontes/                        proveniência e métodos por fonte
  auditoria/                     relatórios e metadados/hashes
  analises/                      relato histórico; tabelas/imagens locais ignoradas
  painel/                        reservado para documentação futura
  ESCOPO_PROJETO.md               registro inicial histórico, parcialmente superado
dados/                           acervo local; não versionado
  brutos/sinesp/                  sete XLSX originais
  brutos/ssp_sc/                  PDFs, CSVs intermediários e página de referência
  processados/                   derivados anteriores, sem novas exportações
video/                           reservado; sem arquivo de entrega
backup_pre_migracao_20261016/     cópia local preservada e ignorada
```

Pastas vazias não são preservadas pelo Git. Os diretórios de dados devem ser restaurados durante a preparação local. O notebook SSP está sem outputs, mas ainda contém um caminho antigo `pdfs/csv_extraidos`; deve ser corrigido em tarefa específica antes de ser apresentado como reproduzível. Não foi alterado aqui.

O README de continuidade e seus backups permanecem **fora do repositório**. Nenhum diretório foi reorganizado. O [inventário de migração](documentacao/auditoria/mapa_migracao.csv) documenta os caminhos históricos.

## 13. Limitações e melhorias futuras

- 2026 é parcial e tem cortes diferentes: Sinesp até agosto e SSP até julho. Comparações entre fontes exigem o mesmo intervalo e definições compatíveis.
- O painel ainda não apresenta os resultados Sinesp validados; sua página Projeto contém textos desatualizados.
- A Etapa 12 auditou 58 grupos de períodos repetidos nos boletins SSP/SC, 41 com valores divergentes (37 sem explicação documental suficiente); isso não autoriza exclusão automática, nem soma de snapshots, nem a escolha de uma versão definitiva de homicídios, que permanece pendente. O boletim de janeiro/2025 (página 8) e os rótulos de fevereiro (28/02 e 29/02) seguem como inconsistências documentadas.
- Violência doméstica: "Fato Comunicado" não tem definição operacional nos PDFs (não equivale automaticamente a vítimas, pessoas únicas ou boletins de ocorrência únicos); o mapeamento de "0 Dolosa" e "- Dolosa" e a aplicação do cabeçalho de meses às páginas seguintes são decisões metodológicas, sem confirmação oficial da SSP/SC; 2023 vem de dois relatórios semestrais e 2024 de um relatório anual; categorias de poucos casos geram variações percentuais instáveis; os resultados não sustentam causalidade nem incidência real.
- Próxima prioridade: integrar ao Streamlit os resultados e figuras Sinesp (Etapas 1–10) e SSP/SC (Etapas 13–14.2), que hoje existem apenas em memória no roteiro; em seguida, Prefeitura/SEPROT, deploy e entrega.
- A seleção histórica de homicídios SSP usa o último valor anual por referência e uma edição única para janeiro–julho; precisa de revisão contextual no novo fluxo.
- A Prefeitura requer esclarecimento da unidade, documentação da transcrição e integração própria. Não há cobertura municipal de 2026 nessa série.
- A regra `fillna(0)` no módulo histórico `scripts/analysis.py` não faz parte do roteiro Sinesp atual e precisa de revisão antes de reutilização.
- O script usa tabelas já extraídas da SSP nas primeiras células; a geração integral dos 45 CSVs intermediários ainda não está automatizada no fluxo atual.
- O arquivo Sinesp 2020 foi validado por igualdade de células, apesar de hash diferente da versão oficial examinada; 2021–2022 coincidiram por hash. Nova versão exige nova auditoria.
- Não existem dados territoriais para mapas/rankings por bairro, fonte demográfica validada para taxas ou evidência causal.
- Antes da publicação de dados ou figuras de terceiros: verificar termos de divulgação. Antes do deploy: resolver dados distribuíveis, dependências e execução em ambiente limpo.
- Arquivos em `documentacao/analises/` e o escopo inicial são registros históricos; em caso de divergência, prevalecem o código atual, as evidências registradas e este estado acadêmico atualizado.

## 14. Créditos e referências

Fontes primárias: MJSP/Sinesp VDE, SSP/SC e Prefeitura/SEPROT, citadas na seção 4. [Documentação de fontes](documentacao/fontes/) e [auditoria de origem](documentacao/auditoria/sinesp_origem_2020_2022.csv) preservam a procedência.



Licença do código e permissões de redistribuição dos dados ainda devem ser definidas/documentadas; a ausência de um arquivo de licença não deve ser interpretada como autorização irrestrita.

## 15. Links de entrega

- [Repositório GitHub](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC): público; contém o primeiro commit (etapas Sinesp 1–10), o ajuste de créditos do README e as etapas SSP/SC 11–14.2 com a documentação e o teste documental atualizados (publicados na branch `main`). Isso não representa deploy da aplicação.
- URL Git exata: `https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC.git`.
- Pasta local: repositório Git na branch `main`, com `origin` configurado.
- Aplicação Streamlit publicada: pendente.
- Repositório oficial da turma: pendente.
- Vídeo e link de leitura no Drive: pendentes.
- AVA e demais itens administrativos: pendentes.

Antes de preparar arquivos para versionar, conferir o [gitignore](.gitignore): `dados/`, tabelas/imagens derivadas locais, ambientes, segredos, logs e backups não devem entrar. O notebook de inspeção tem correção de caminho pendente; os testes de acervo exigem arquivos locais.

O envio ao remoto (`push`) depende de autorização separada, após conferência do commit local. Se o destino ganhar histórico antes do envio, revisar a relação com o histórico local, sem sobrescrever ou forçar atualização. Nenhum deploy foi feito.

## 16. Conclusões sustentadas pelas análises

O fluxo Sinesp preservou 900 linhas originais, produziu uma cópia analítica 900 × 10, manteve ausências e abrangências, gerou tabelas descritivas por série e exibiu quatro figuras sem exportação. Homicídio doloso e suas tentativas, feminicídio e suas tentativas permaneceram distintos.

O fluxo SSP/SC inspecionou 45 PDFs/CSVs, auditou 58 grupos de republicações (41 divergentes, sem versão definitiva escolhida) e construiu e validou uma base de violência doméstica de Joinville (216 × 5, com rastreabilidade 216 × 23), da qual se obtiveram estatísticas descritivas por categoria e a comparação 2023 × 2024 em "Fato Comunicado".

A análise sustenta descrições dos valores publicados e comparações temporais equivalentes, com atenção a pequenas contagens. Não sustenta total geral de criminalidade, causalidade, estimativa de subnotificação, equivalência entre "Fato Comunicado" e vítimas, taxa populacional ou distribuição por bairros. A Prefeitura ainda precisa de tratamento próprio; a integração das figuras e tabelas ao Streamlit, o deploy e a entrega final permanecem pendentes.
