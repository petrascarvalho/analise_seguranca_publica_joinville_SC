# Dados mínimos do dashboard

Arquivos pequenos, **agregados e derivados**, usados pelo painel Streamlit em `dashboard/pages/`. Permitem que o painel
funcione em um clone limpo, sem a pasta `dados/` (acervo bruto local, fora do Git). Contêm somente contagens estatísticas
municipais e metadados de rastreabilidade (nomes de arquivos, páginas, linhas e colunas). **Não** contêm PDFs, XLSX nacionais,
CSVs brutos, dados pessoais ou informações protegidas.

Atribuição: **MJSP / Sinesp VDE** (Ministério da Justiça e Segurança Pública) e **SSP/SC — Segurança em Números**
(Secretaria de Estado da Segurança Pública de Santa Catarina). Tabelas e gráficos são elaborações próprias do projeto.

## Arquivos

| Arquivo | Conteúdo | Linhas × colunas |
|---|---|---|
| `sinesp_joinville_mensal.csv` | Séries mensais Sinesp/MJSP de Joinville/SC (`ano, mes, evento, abrangencia, unidade, valor`) | 900 × 6 |
| `sinesp_catalogo_indicadores.csv` | 12 séries (indicador × abrangência): unidade, natureza, medida de origem, cobertura, meses com valor/zero/sem valor, limitações | 12 × 12 |
| `ssp_violencia_domestica_joinville.csv` | Violência doméstica SSP/SC, Joinville (`municipio, ano, mes, categoria, fatos_comunicados`) | 216 × 5 |
| `ssp_violencia_domestica_rastreabilidade.csv` | Origem de cada observação: relatório (PDF), página, tabela, linha, coluna, rótulo original, mês do cabeçalho e valor textual | 216 × 12 |
| `manifesto_dados_publicos.json` | Versão e versão anterior, datas, situação da validação, cobertura (última competência), fontes e licenças verificadas, consulta às fontes, SHA-256 e tamanhos dos arquivos derivados e dos originais | — |

UTF-8, separador vírgula, fins de linha LF. O SHA-256 é calculado sobre o conteúdo com fins de linha normalizados para LF.
Quatro datas distintas: **consulta** às fontes, **publicação** (informada pela fonte), **competência estatística** (período
dos dados) e **geração** da versão derivada.

## Origem e critérios de seleção

* **Sinesp/MJSP** — base analítica validada (Etapas 5–9 do roteiro): vítimas em `total_vitima`; mandados em `total`. As séries
  Estadual, Polícia Federal (mandados, desde 01/2025) e PRF (mortes no trânsito) permanecem separadas. Ausência de cobertura é
  ausência de linhas (não zero); valor ausente seria campo vazio; zeros publicados são mantidos.
* **SSP/SC** — base analítica validada (Etapas 13.2–13.3, 67 verificações aprovadas). Unidade "Fato Comunicado". As grafias
  "0 Dolosa" e "- Dolosa" das lesões corporais foram unificadas por decisão metodológica do projeto, sem confirmação oficial; os
  rótulos originais estão na rastreabilidade. Os meses seguem a estrutura contínua das tabelas dos PDFs.
* **Não incluídos:** homicídios SSP/SC (série histórica não resolvida), Prefeitura/SEPROT, dados por bairro, rua, horário ou corporação.

## Geração e atualização

* Geração inicial: `python -m scripts.gerar_dados_dashboard` (requer o acervo bruto local; reprodutível: duas execuções
  independentes produziram CSVs idênticos byte a byte).
* Novas publicações oficiais: fluxo **verificar → preparar → aprovar** (`python -m scripts.atualizacao_dados`), manual e controlado,
  com versão anterior preservada e reversão. Ver [`documentacao/ATUALIZACAO_DE_DADOS.md`](../../documentacao/ATUALIZACAO_DE_DADOS.md).
  O painel exibe uma **versão histórica validada** e nunca baixa dados nem executa ETL.

## Condições de reutilização das fontes (consulta de 27/10/2026)

Diferenciam-se a licença de um **catálogo de dados**, a licença **geral do site** e as condições **específicas** de cada documento.

| Fonte | Catálogo de dados | Licença geral do site | Condições específicas do recurso |
|---|---|---|---|
| **MJSP / Sinesp VDE** | `dados.mj.gov.br`: informado pelo responsável como "Creative Commons Atribuição"; **não confirmado** — o domínio não resolveu (NXDOMAIN) | Rodapé do portal gov.br: "Creative Commons Atribuição-SemDerivações 3.0 Não Adaptada" (CC BY-ND 3.0) | Nenhuma proibição, restrição ou exigência de citação específica encontrada na página da base VDE nem no Termo de Uso do portal |
| **SSP/SC — Segurança em Números** | `dados.sc.gov.br`: "Outra (Aberta)" (`other-open`; "satisfaz a Definição de Aberto"), confirmado pela API CKAN; o único recurso é um link HTML para a página | Rodapé de `ssp.sc.gov.br`: "Copyright © 2023 Todos os Direitos Reservados SC - Governo de Santa Catarina" | Nenhuma encontrada; a divergência entre o site (direitos reservados) e o catálogo (aberta) não foi esclarecida com a SSP/SC |

**Avaliação.** Nenhuma proibição específica aplicável a estes arquivos derivados foi encontrada, e **não há autorização
específica explícita**. Os arquivos reúnem apenas valores estatísticos públicos agregados por município e metadados de
rastreabilidade; os documentos oficiais integrais não são redistribuídos. A licença do catálogo do MJSP não pôde ser confirmada,
e o CC BY-ND 3.0 do rodapé do portal (SemDerivações) é a licença **geral do site**, de aplicação a bases de dados não esclarecida.
Recomenda-se, por prudência, confirmar o uso com o MJSP (estatistica@mj.gov.br) e com a SSP/SC. A atribuição das fontes é obrigatória.
Isto é uma avaliação técnica do projeto, **não parecer jurídico**.
