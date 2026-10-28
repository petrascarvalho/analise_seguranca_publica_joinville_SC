# Segurança Pública de Joinville — Visualização de Dados e Business Intelligence

**Curso:** SENAI/SC — LAB365 | Módulo 2 — Semana 13
**Aluno:** Petras Ruben Carvalho
**Projeto:** Análise dos indicadores oficiais do Sinesp/MJSP em Joinville/SC (janeiro/2020 a setembro/2026)

Este repositório reúne o tratamento, a análise e a visualização dos indicadores de segurança pública que o **Ministério da Justiça e Segurança Pública (Sinesp/MJSP)** publica para **Joinville/SC**. O projeto usa uma fonte única, oficial e auditável, e é formado por três partes:

| Parte | Onde está | O que faz |
|---|---|---|
| **ETL** (script principal) | [`scripts/etl_sinesp.py`](scripts/etl_sinesp.py) | Lê os XLSX oficiais, trata, valida, analisa e exporta os resultados em 18 etapas comentadas |
| **Painel Streamlit** (script principal) | [`scripts/painel_streamlit.py`](scripts/painel_streamlit.py) | Dashboard de três páginas: Projeto, Indicadores Sinesp e Qualidade e metodologia |
| **Notebook** | [`notebooks/analise_sinesp.ipynb`](notebooks/analise_sinesp.ipynb) | A mesma análise em formato de relatório, com tabelas e gráficos |

**Aplicação publicada:** <https://seguranca-publica-joinville-sinesp.streamlit.app/>

---

## 1. Título e resumo

**Análise dos indicadores oficiais de segurança pública do Sinesp/MJSP em Joinville/SC, 2020–2026.**

Python, Pandas e Matplotlib transformam os arquivos anuais do Sinesp em **911 observações** mensais de **12 séries** (indicador × abrangência), de janeiro/2020 a setembro/2026. Cada série mantém sua unidade (vítimas ou mandados cumpridos), sua abrangência (Estadual, Polícia Federal ou Polícia Rodoviária Federal) e sua cobertura. Não existe um "total geral de criminalidade": indicadores, unidades e abrangências diferentes nunca são somados.

## 2. Problema, objetivo e importância

**Pergunta analítica:** como evoluíram, desde janeiro/2020, os indicadores oficiais do Sinesp/MJSP para Joinville/SC, e o que a comparação entre períodos equivalentes permite — e não permite — afirmar?

**Objetivo:** produzir uma análise municipal reproduzível, com origem auditável, estatísticas adequadas a contagens mensais e comparações justas entre períodos de mesma duração.

**Importância:** estudantes, cidadãos, pesquisadores e gestores podem consultar a evolução dos indicadores com fonte, unidade e limites explícitos. Os dados são registros administrativos: não medem toda a criminalidade e não demonstram efeitos de políticas públicas.

## 3. Escopo e resultados esperados

**No escopo (fonte única Sinesp/MJSP, Joinville/SC):** homicídio doloso e tentativa, feminicídio e tentativa, lesão corporal seguida de morte, latrocínio, suicídio, mortes a esclarecer, mortes no trânsito (Estadual e PRF) e mandados de prisão cumpridos (Estadual e Polícia Federal).

**Fora do escopo:** furtos, roubos em geral, estupro e tráfico (não existem nos arquivos do Sinesp para Joinville), atendimentos da Guarda Municipal, taxas populacionais, dados por bairro ou horário, previsões e inferência causal. O trabalho anterior com a **SSP/SC e Prefeitura/SEPROT** é histórico e está **fora do escopo**: não alimenta o painel e está indexado em [historico/ssp_sc/LEIAME.md](historico/ssp_sc/LEIAME.md) (último commit com a página da SSP/SC no painel: `bad9723`).

**Resultados esperados:** ETL reproduzível, análise exploratória e estatística descritiva, gráficos com fonte e unidade, painel interativo publicado, documentação e vídeo de até três minutos. Prazo informado: **30/10/2026, 22h (Brasília)**. O planejamento no Trello foi **dispensado por orientação do professor**.

## 4. Fonte e autorização

| Item | Descrição |
|---|---|
| Fonte | [Sinesp VDE / MJSP](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023) — base nacional dos gestores estaduais |
| Arquivos | `bancovde-2020.xlsx` a `bancovde-2026.xlsx` (um por ano, 14 colunas, ~24 MB cada) |
| Recorte | `uf = SC` e `municipio = JOINVILLE` (filtro exato) |
| Medidas | vítimas em `total_vitima`; mandados cumpridos em `total` |
| Versão dos dados | `20261027T114400Z` (inclui setembro/2026; SHA-256 de cada arquivo no manifesto) |

Os XLSX ficam em `dados/brutos/sinesp/`, fora do Git. O repositório publica apenas arquivos **mínimos, agregados e derivados** (`dashboard/data_publica/`). Detalhes de origem: [documentacao/analises/ORIGEM_E_COBERTURA.md](documentacao/analises/ORIGEM_E_COBERTURA.md).

**Condições de reutilização (consulta de 27/10/2026):** o catálogo `dados.mj.gov.br` seria "Creative Commons Atribuição", segundo o responsável, mas esse registro **não pôde ser confirmado** (o domínio não resolveu); o rodapé do portal gov.br declara CC BY-ND 3.0 (licença geral do site). Nenhuma proibição específica foi encontrada, mas também não há autorização específica explícita. É uma avaliação técnica, não parecer jurídico; a atribuição da fonte aparece no painel.

## 5. Pipeline e metodologia

Os dados passam por quatro camadas, cada uma em uma pasta:

| Camada | Pasta | No Git? |
|---|---|---|
| Bruto | `dados/brutos/sinesp/` — XLSX oficiais, sem alteração | Não |
| Processado | `dados/processados/sinesp/` — recorte de Joinville e base analítica gerados pelo ETL | Não |
| Aprovado para o painel | `dashboard/data_publica/` — 2 CSVs + manifesto com SHA-256 | Sim |

**ETL ([`scripts/etl_sinesp.py`](scripts/etl_sinesp.py)).** Células `# %%` para o VS Code. Cada etapa tem objetivo, explicação, resultado esperado e uma conferência:

| Etapas | O que fazem |
|---|---|
| 01–03 | Bibliotecas, pastas e localização dos sete XLSX, com conferência do SHA-256 |
| 04–07 | Leitura (só SC/JOINVILLE, 911 linhas), inspeção, dicionário das colunas e duplicidades — nenhuma linha é apagada |
| 08–12 | Datas do Excel, escolha da medida, ausências como `<NA>` (nunca zero), tipos e consolidação mensal |
| 13 | Validação e comparação com a base publicada (mesmo SHA-256) |
| 14–16 | Estatísticas, análise exploratória e gráficos |
| 17–18 | Exportação somente para `dados/processados/sinesp/` e conclusões |

Sem os XLSX, o ETL roda em **modo demonstração** (usa a base publicada e não exporta nada). A base do painel **nunca** é sobrescrita pelo ETL: ela só muda pelo fluxo controlado de atualização (seção 10).

**Regras principais:** filtro exato SC/JOINVILLE; nenhum valor ausente vira zero e zeros publicados são mantidos; vítimas e mandados nunca são somados; só *Tentativa de homicídio* e *Estupro* podem ter parcelas somadas no mesmo mês, como manda a nota oficial; o ano parcial (2026) só é comparado com o mesmo período dos anos anteriores. Detalhes: [documentacao/analises/METODOLOGIA.md](documentacao/analises/METODOLOGIA.md).

**Notebook ([`notebooks/analise_sinesp.ipynb`](notebooks/analise_sinesp.ipynb)).** Mesma sequência em formato de relatório: fonte, leitura, tratamento, duplicidades, ausências e zeros, cobertura, estatísticas, gráficos, conclusões e limitações. Usa as mesmas funções do ETL e do painel, sem repetir cálculos.

**Módulos auxiliares.** `src/pipeline/` (leitura dos XLSX, caminhos, verificação da fonte, manifesto e atualização controlada) e `dashboard/` (cálculos, gráficos e componentes do painel). O roteiro antigo, [historico/scripts/analise_seguranca_publica.py](historico/scripts/analise_seguranca_publica.py), é **histórico** (primeiras etapas Sinesp e trabalho da SSP/SC) e não faz parte da entrega.

## 6. Bibliotecas e tecnologias

| Ferramenta | Uso |
|---|---|
| Python 3.12, VS Code | Desenvolvimento e execução |
| Pandas 3.0 | Leitura, tratamento, validação e estatísticas |
| Matplotlib 3.11 | Todos os gráficos |
| Streamlit 1.66 | Painel interativo |
| lxml, openpyxl | Leitura das planilhas oficiais; XLSX sintéticos nos testes |
| pytest | Testes automatizados |
| ipykernel | Notebook e células `# %%` (instalar à parte) |
| Git e GitHub | Versionamento e publicação |

As faixas de versão estão em [requirements.txt](requirements.txt).

## 7. Resultados encontrados

A versão auditada inicial tinha **900 registros Sinesp** (até agosto/2026). Em 27/10/2026 o Sinesp publicou setembro/2026 e a base passou a **911 observações**, com 12 séries, 0 valores ausentes e 401 zeros publicados — **11 observações novas e nenhum valor histórico alterado**.

| Indicador (Estadual, vítimas) | Anos completos | Mesmo período |
|---|---|---|
| Homicídio doloso | 62 em 2020 → 29 em 2025 | 21 em jan–set/2025 → **25 em 2026**; 18 em jan–ago/2025 → 22 em janeiro–agosto de 2026 |
| Tentativa de homicídio | 98 em 2020 → 53 em 2025 | 43 → 77 (jan–set) |
| Feminicídio | 3 em 2020 → 2 em 2025 | 2 → 0 (jan–set) |
| Tentativa de feminicídio | 10 em 2020 → 9 em 2025 | 5 → 12 (jan–set) |

- Em homicídio doloso, janeiro/2020 (10) e janeiro/2023 (19) ficam acima do limite superior de Tukey (9,5). O método IQR só é informativo em 5 das 12 séries; nas demais, zeros e contagens baixas impedem a leitura.
- Latrocínio e lesão corporal seguida de morte somam 4 e 8 vítimas em 81 meses.

Tabelas completas por ano, por período equivalente e estatísticas mensais: [documentacao/analises/RESULTADOS.md](documentacao/analises/RESULTADOS.md) (conferidas automaticamente com a base pelos testes).

## 8. Discussão e conclusão

Homicídio doloso caiu de 62 vítimas em 2020 para 29 em 2025, com oscilações intermediárias (49 em 2022, 55 em 2023). Em 2026, o mesmo período mostra alta em relação a 2025 (de 21 para 25 em janeiro–setembro), e as tentativas de homicídio quase dobraram (43 para 77). Em contagens pequenas, a diferença absoluta informa mais que o percentual. Zero publicado não prova eliminação do fenômeno nem eficácia de política.

## 9. Aplicação profissional

O painel mostra como publicar indicadores municipais com transparência: fonte, período e unidade explícitos, comparações justas e um fluxo de atualização que detecta revisões da fonte antes de aceitá-las. Para uso operacional faltariam dados territoriais, base demográfica para taxas e séries de outras instituições — por exemplo, não há série comparável de atendimentos da Guarda Municipal nesta base.

## 10. Aplicação Streamlit

O painel tem **três páginas** e usa somente `dashboard/data_publica/` (não lê `dados/`, não executa o ETL e não acessa a rede):

| Página | Conteúdo |
|---|---|
| **Projeto** | Pergunta, indicadores de destaque, gráfico principal e acesso às análises |
| **Indicadores Sinesp** | Filtros (Categoria → Indicador → Abrangência; Período → Meses), resumo e cinco abas: Evolução, Comparações, Padrões e tendência, Estatística e outliers, Indicadores e interpretação |
| **Qualidade e metodologia** | Integridade (SHA-256), cobertura, métodos, limitações, atualização e licenças |

Cada gráfico tem a tabela com os valores usados. A chave **Visualização compacta (celular)** gera figuras estreitas com os mesmos números. Guia de uso: [documentacao/painel/USO_DO_PAINEL.md](documentacao/painel/USO_DO_PAINEL.md).

**Publicação:** Aplicação Streamlit publicada: <https://seguranca-publica-joinville-sinesp.streamlit.app/>. **Deploy realizado** no Streamlit Community Cloud a partir da branch `main` ([documentacao/painel/DEPLOY_STREAMLIT.md](documentacao/painel/DEPLOY_STREAMLIT.md)); o aplicativo reflete o último commit enviado ao GitHub. A revisão visual em navegador e em dispositivos móveis reais ainda está pendente.

**Atualização dos dados:** manual e controlada — verificar → preparar → aprovar ([documentacao/analises/ATUALIZACAO_DE_DADOS.md](documentacao/analises/ATUALIZACAO_DE_DADOS.md)). **Não há atualização automática operacional.**

```bat
python -m src.pipeline.atualizacao_dados verificar
python -m src.pipeline.atualizacao_dados preparar --entradas-sinesp <pasta com os XLSX>
python -m src.pipeline.atualizacao_dados aprovar <id> --confirmo <id>
```

**Testes:** suíte ativa com **234 testes aprovados** (`.\.venv\Scripts\python.exe -m pytest tests -q`) — integridade, totais, filtros, setas do resumo, gráficos, modo compacto, estatísticas, atualização controlada, ETL e notebook. Suíte histórica com 12 testes (`.\.venv\Scripts\python.exe -m pytest tests_historicos -q`), que dependem do acervo local.

## 11. Como executar

No **Prompt de Comando (CMD)** do Windows, na pasta do projeto:

```bat
:: 1. Ambiente e dependências
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pip install ipykernel

:: 2. ETL (lê dados/brutos/sinesp e grava só em dados/processados/sinesp)
.\.venv\Scripts\python.exe -m scripts.etl_sinesp

:: 3. Painel (abre em http://localhost:8501)
.\.venv\Scripts\python.exe -m streamlit run scripts/painel_streamlit.py

:: 4. Testes
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m pytest tests_historicos -q
```

**Notebook:** abra `notebooks/analise_sinesp.ipynb` no VS Code, escolha o kernel da `.venv` e use *Run All*.

**Arquivos fora do Git:** para refazer o ETL, baixe os sete `bancovde-ANO.xlsx` do [catálogo oficial](https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados) e salve em `dados/brutos/sinesp/`. Sem eles, o ETL e o notebook rodam em modo demonstração, e o painel funciona normalmente.

## 12. Estrutura de pastas

```text
Seguranca Publica Joinville/
├── README.md
├── requirements.txt
├── scripts/
│   ├── etl_sinesp.py            ← script principal 1: ETL e análise (18 etapas)
│   └── painel_streamlit.py      ← script principal 2: entrada do painel
├── notebooks/
│   └── analise_sinesp.ipynb
├── src/pipeline/                módulos auxiliares (leitura dos XLSX, atualização controlada, manifesto)
├── dashboard/
│   ├── pages/                   home.py, sinesp.py, quality.py
│   ├── calculos.py, graficos.py, dados_publicos.py, formatacao.py, ui.py
│   └── data_publica/            base aprovada: 2 CSVs + manifesto
├── dados/                       (local, fora do Git)
│   ├── brutos/sinesp/           XLSX oficiais
│   └── processados/sinesp/      saídas do ETL
├── documentacao/
│   ├── analises/                METODOLOGIA, ORIGEM_E_COBERTURA, RESULTADOS, ATUALIZACAO_DE_DADOS
│   ├── painel/                  USO_DO_PAINEL, DEPLOY_STREAMLIT e imagens/
│   └── auditoria/               evidência de origem dos XLSX 2020–2022
├── tests/                       suíte ativa
├── tests_historicos/            suíte histórica
├── ferramentas/                 gerador das imagens de revisão
└── historico/                   material anterior, fora da entrega (ver historico/LEIAME.md)
```

## 13. Limitações e melhorias futuras

- 2026 é parcial (até setembro; PRF até agosto) e só é comparado com o mesmo período dos anos anteriores.
- Registros administrativos agregados: não medem toda a criminalidade, não estimam subnotificação e não sustentam causalidade.
- Sem taxas populacionais, dados por bairro ou horário, nem total entre indicadores.
- A fonte pode revisar valores históricos; a atualização controlada detecta revisões e só as aceita com aprovação.
- Melhorias possíveis: fixar versões das dependências, definir a licença do código e incluir taxas por habitante quando houver base demográfica compatível.

## 14. Créditos e referências

- Ministério da Justiça e Segurança Pública — Sinesp VDE, base de dados dos gestores estaduais (seção 4).
- Notas metodológicas do Sinesp VDE, disponíveis na página oficial da base.
- Documentação técnica deste projeto em [documentacao/](documentacao/).

## 15. Links de entrega

- Repositório GitHub: <https://github.com/petrascarvalho/analise_seguranca_publica_joinville_SC> (branch `main`).
- Aplicação Streamlit publicada: <https://seguranca-publica-joinville-sinesp.streamlit.app/>.
- Repositório oficial da turma: pendente.
- Vídeo (até três minutos): pendente.
- AVA: pendente.
- Trello: dispensado por orientação do professor.

## 16. Conclusões sustentadas pelas análises

O ETL reconstrói, a partir dos XLSX oficiais, exatamente a base publicada (911 observações, mesmo SHA-256 do manifesto), sem apagar linhas, sem converter ausências em zero e sem misturar unidades. A análise sustenta descrições dos valores publicados e comparações entre períodos equivalentes; não sustenta total geral de criminalidade, causalidade, subnotificação ou taxas populacionais.
