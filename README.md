# Segurança Pública de Joinville

Projeto acadêmico individual de Visualização de Dados e BI — SENAI/LAB365, Módulo 2, Semana 13. Estado documentado em 26/10/2026 para preparação do primeiro commit. As etapas Sinesp 1–10 foram implementadas; os resultados mais recentes foram verificados nas execuções anteriores desta sessão, sem reexecutar o ETL durante esta atualização documental.

## 1. Título e resumo

**Análise dos indicadores públicos de segurança de Joinville/SC, 2020–2026.** O projeto utiliza Python/Pandas, dados oficiais e visualizações Matplotlib para descrever séries municipais, preservando fonte, unidade, abrangência institucional e período. O produto final previsto inclui painel Streamlit, documentação, repositório e apresentação acadêmica.

Sinesp: janeiro/2020 a agosto/2026; SSP/SC: homicídios anuais de 2020–2025 e acumulados até julho/2026, além de violência doméstica em 2023–2024; Prefeitura/SEPROT: furtos e roubos anuais de 2023–2025. Cada indicador possui cobertura própria. Não há um total geral de criminalidade obtido somando essas fontes.

## 2. Problema, objetivo e importância

**Pergunta analítica:** como evoluíram os indicadores oficiais disponíveis de criminalidade registrada em Joinville entre 2020 e 2026, e quais limites das fontes afetam sua interpretação?

O objetivo é produzir uma análise municipal reproduzível, com origens auditáveis, estatísticas adequadas às unidades e comparação de períodos equivalentes. O público inclui estudantes, cidadãos, pesquisadores e gestores. Os dados descrevem registros informados/publicados; não medem toda a criminalidade ocorrida nem demonstram efeitos causais de políticas públicas.

## 3. Escopo e resultados esperados

O escopo inclui feminicídio, tentativa de feminicídio, violência doméstica e suas categorias disponíveis, homicídio doloso, tentativa de homicídio, latrocínio, lesão corporal seguida de morte, furtos e roubos. Suicídio, mortes a esclarecer, trânsito e mandados são indicadores complementares; atividade policial não é contagem de crimes ou de vítimas únicas.

Requisitos acadêmicos registrados: trabalho individual do SENAI/LAB365, Módulo 2, Semana 13; ETL em Python, EDA, estatísticas, gráficos com fontes, painel interativo Streamlit, README, repositório dedicado, publicação da aplicação, vídeo de até três minutos e envio dos links ao AVA/repositório da turma conforme enunciado. O prazo informado é **30/10/2026 às 22h, horário de Brasília**, sujeito a comunicados posteriores. Regras finais de visibilidade do repositório, divulgação e marcações do vídeo devem ser conferidas no enunciado vigente antes da entrega.

As etapas Sinesp 1–10 estão implementadas e foram executadas em memória. A próxima etapa prevista é a **inspeção orientada dos dados SSP/SC**. Publicação, integração analítica ao Streamlit, exportações e entrega final permanecem pendentes.

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
| 11. Exportação | Pendente; desativada | Exige autorização específica |
| 12. Releitura de exportações | Pendente; desativada | Não houve exportação nova das etapas 5–10 |

A chave observacional mantém UF, município, evento, competência e abrangência; agente, arma e faixa etária permanecem disponíveis na camada original. Na última reconstrução houve zero duplicidade exata e zero repetição nas chaves que incluem abrangência. O controle sem abrangência identificou 20 grupos/40 linhas de mandados estaduais e PF, preservados separadamente.

As dez colunas analíticas são `uf`, `municipio`, `evento`, `data_referencia`, `feminino`, `masculino`, `nao_informado`, `total_vitima`, `total` e `abrangencia`. Agente, arma, faixa etária e peso não foram incluídos nessa cópia porque estão 100% ausentes; continuam intactos no original.

Datas: sistema Excel 1900 confirmado nos sete arquivos, origem `1899-12-30`, sem `errors="coerce"`. Foram validados seriais inteiros, ano do arquivo, primeiro dia do mês, cobertura e correspondência com o leitor Excel. O Pandas instalado produziu `datetime64[s]`. As cinco contagens passaram de `float64` para `Int64` anulável, após verificar valores finitos, inteiros e não negativos. As posições de ausência foram preservadas.

O catálogo auxiliar tem 12 combinações evento/abrangência, com medida, unidade, natureza e limitações. As estatísticas não misturam vítimas com mandados; somas temporais usam apenas a medida apropriada. Desvio-padrão descritivo usa `ddof=0`; médias/medianas informam seus meses de observação. Nenhum valor ausente foi convertido em zero.

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

### Outras fontes: histórico preservado, ainda fora do fluxo analítico atualizado

A SSP possui 510 linhas municipais históricas: 294 snapshots de homicídio e 216 observações mensais de nove categorias domésticas em 2023–2024. Os boletins reapresentam anos e acumulados; datas de atualização podem variar por tabela. A inspeção metodológica da nova sequência SSP é a próxima tarefa.

Na Prefeitura, furtos foram 8.865, 8.730 e 8.372 em 2023–2025; roubos foram 933, 593 e 476. São seis totais anuais transcritos e conferidos anteriormente na notícia oficial, ainda sujeitos a esclarecimento da unidade e integração própria. Resultados e gráficos históricos dessas fontes não foram recalculados nesta fase Sinesp.

## 8. Discussão e conclusão

Em anos completos, homicídio doloso passou de 62 vítimas em 2020 para 29 em 2025, com oscilações intermediárias: 49 em 2022 e 55 em 2023. Na comparação janeiro–agosto, passou de 18 em 2025 para 22 em 2026; tentativas de homicídio passaram de 37 para 68. São recortes temporais distintos, com interpretações próprias.

Feminicídio apresentou três vítimas em 2020, seis em 2021 e duas em 2025. Em janeiro–agosto de 2025 e 2026, o total publicado foi zero. Tentativas de feminicídio passaram de quatro para dez na comparação equivalente. Pequenas contagens tornam percentuais instáveis; por isso, os gráficos enfatizam valores absolutos.

Latrocínio e lesão seguida de morte têm, respectivamente, quatro e oito vítimas em 80 meses. Zero publicado não demonstra eliminação do fenômeno, ausência de subnotificação ou eficácia de uma política. Diferenças entre Sinesp e SSP não são corrigidas à força. Não há taxas populacionais, previsão, inferência causal ou ranking territorial neste trabalho.

## 9. Aplicação profissional

A aplicação potencial é consulta transparente de indicadores municipais agregados, com fonte, período e unidade. Vítimas, mandados, ocorrências e fatos comunicados precisam de definições independentes. `abrangencia` distingue as séries Estadual/PF/PRF, mas não permite atribuir todo registro à Polícia Civil, Polícia Militar ou Guarda Municipal.

Para uso operacional, seriam necessários dicionários estáveis, atualização versionada, dados territoriais validados e revisão das sobreposições. Não há série municipal estruturada e comparável de atendimentos da Guarda Municipal, bairros, endereços, horários ou corporações individuais nesta base.

## 10. Aplicação Streamlit

Ponto de entrada: [scripts/painel_streamlit.py](scripts/painel_streamlit.py). Há duas páginas locais: [Projeto](dashboard/pages/home.py) e [Qualidade dos dados](dashboard/pages/quality.py). As tabelas e quatro figuras novas do Sinesp **ainda não foram integradas**. O texto da página Projeto ainda menciona cobertura antiga e resultados pendentes; essa atualização do painel é tarefa futura, não executada aqui.

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

O primeiro comando executa as células 1–10, inclusive a preparação da cópia analítica e os quatro gráficos em memória. Não é um comando limitado a imports ou leitura; não o use para uma tarefa restrita à documentação. Ele não exporta os resultados novos. As etapas 11–12 permanecem comentadas.

Para trabalhar **somente Sinesp**, execute as células 1–2 e depois 5–10 no mesmo Python Interactive, com os sete XLSX e a auditoria disponíveis. Isso dispensa a leitura das entradas SSP/Prefeitura das células 3–4. Os DataFrames e figuras ficam no kernel para inspeção no Data Viewer; as execuções mais recentes desta sessão foram conferidas em processos Python, sem pressupor que variáveis persistam em outra sessão do VS Code.

### Testes

Os testes de documentação podem ser executados sem ETL:

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
  analise_seguranca_publica.py     roteiro acadêmico: etapas 1–10; 11–12 pendentes
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
- Próxima etapa: inspeção dos CSVs/PDFs SSP, contexto das tabelas, unidades, datas de atualização e versões. O histórico registra 58 grupos de períodos repetidos, 41 com valores divergentes; isso não autoriza exclusão automática.
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

- [Repositório GitHub de destino](https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC): existente e público, com lista de branches vazia na consulta de preparação. Isso não representa publicação do código local.
- URL Git exata: `https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC.git`.
- Pasta local: ainda sem `.git` na inspeção desta preparação; nenhum remote local configurado.
- Aplicação Streamlit publicada: pendente.
- Repositório oficial da turma: pendente.
- Vídeo e link de leitura no Drive: pendentes.
- AVA e demais itens administrativos: pendentes.

O usuário realizará o primeiro commit e o envio pela interface do VS Code. Antes de preparar os arquivos, conferir o [gitignore](.gitignore): `dados/`, tabelas/imagens derivadas locais, ambientes, segredos, logs e backups não devem entrar. O notebook de inspeção tem correção de caminho pendente; os testes de acervo exigem arquivos locais.

Sequência manual: abrir esta pasta no VS Code; inicializar pelo Controle do Código-Fonte; revisar os arquivos selecionados; configurar `origin` com a URL exata acima; fazer commit com mensagem que descreva o estado real; publicar a branch escolhida. Se o destino ganhar histórico antes do envio, revisar a relação com o histórico local, sem sobrescrever ou forçar atualização. Nenhum commit, push ou deploy foi feito nesta preparação.

## 16. Conclusões sustentadas pelas análises

O fluxo Sinesp preservou 900 linhas originais, produziu uma cópia analítica 900 × 10, manteve ausências e abrangências, gerou tabelas descritivas por série e exibiu quatro figuras sem exportação. Homicídio doloso e suas tentativas, feminicídio e suas tentativas permaneceram distintos.

A análise sustenta descrições dos valores publicados e comparações temporais equivalentes, com atenção a pequenas contagens. Não sustenta total geral de criminalidade, causalidade, estimativa de subnotificação, taxa populacional ou distribuição por bairros. SSP/SC e Prefeitura possuem acervo e resultados históricos, mas ainda precisam avançar em etapas próprias antes de integração e entrega final.
