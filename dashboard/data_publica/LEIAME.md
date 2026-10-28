# Dados mínimos do dashboard

Arquivos pequenos, **agregados e derivados**, usados pelo painel Streamlit em `dashboard/pages/`. Permitem que o painel
funcione em um clone limpo, sem a pasta `dados/` (acervo bruto local, fora do Git). Contêm somente contagens estatísticas
municipais publicadas pelo Sinesp/MJSP para Joinville/SC e metadados de rastreabilidade. **Não** contêm XLSX nacionais,
CSVs brutos, dados pessoais ou informações protegidas.

**Fonte única: MJSP / Sinesp VDE** (Ministério da Justiça e Segurança Pública — base de dados nacional dos gestores estaduais).
Tabelas e gráficos são elaborações próprias do projeto. Os dados da SSP/SC e da Prefeitura/SEPROT são trabalho histórico,
**fora do escopo** deste produto e destes arquivos (ver `historico/ssp_sc/LEIAME.md`).

## Arquivos

| Arquivo | Conteúdo | Linhas × colunas |
|---|---|---|
| `sinesp_joinville_mensal.csv` | Séries mensais Sinesp/MJSP de Joinville/SC (`ano, mes, evento, abrangencia, unidade, valor`), janeiro/2020 a setembro/2026 | 911 × 6 |
| `sinesp_catalogo_indicadores.csv` | 12 séries (indicador × abrangência): unidade, natureza, medida de origem, cobertura, meses com valor/zero/sem valor, limitações | 12 × 12 |
| `manifesto_dados_publicos.json` | Versão e versão anterior, datas, situação da validação e da aprovação, cobertura por série (primeira e última competência), unidades, fonte oficial e licenças verificadas, consulta à fonte, método de obtenção, regras de ETL, SHA-256 e tamanhos dos arquivos derivados e dos XLSX oficiais de origem | — |

UTF-8, separador vírgula, fins de linha LF. O SHA-256 é calculado sobre o conteúdo com fins de linha normalizados para LF.
Quatro datas distintas: **consulta** à fonte, **publicação** (informada pela fonte), **competência estatística** (período
dos dados) e **geração** da versão derivada. Nenhuma delas é usada para inferir a outra.

## Versão ativa

* Versão `20261027T114400Z` (anterior: `20261027T045449Z`), aprovada em 2026-10-27T11:45:19Z (UTC) sem aceitar revisões históricas.
* Cobertura: **2020-01 a 2026-09**; 2026 é parcial. A série *Mortes no trânsito* da PRF termina em **2026-08**; as demais, em 2026-09.
  A série *Mandado de prisão cumprido — Polícia Federal* começa em 2025-01 (antes disso não há cobertura: ausência de série, não zero).
* 911 observações mensais em 12 séries; 0 valores ausentes; 401 zeros publicados (mantidos). Valor ausente seria campo vazio — nunca zero.
* Em relação à versão anterior, entraram **somente 11 observações novas (setembro/2026)**; nenhum valor histórico de Joinville foi alterado ou removido.
  Os sete XLSX oficiais baixados em 27/10/2026 têm hashes diferentes dos usados na versão anterior (republicação pela fonte), sem mudança em valores de Joinville.

## Origem e regras de tratamento

* **Vítimas** (`total_vitima`) e **mandados cumpridos** (`total`) são unidades distintas e nunca são somadas. As abrangências
  Estadual, Polícia Federal e Polícia Rodoviária Federal são séries separadas.
* Filtro exato `SC` / `JOINVILLE`; datas de referência convertidas do serial Excel (origem 1899-12-30, primeiro dia do mês, ano igual ao do arquivo).
* Ausência de cobertura é ausência de linhas; valor ausente é campo vazio; zeros publicados são mantidos.
* Em *Tentativa de homicídio* e *Estupro*, meses com mais de uma linha são somados porque a nota metodológica oficial os trata como parcelas; não há deduplicação genérica.
* A soma anual só é calculada quando todos os meses presentes têm valor; variação percentual só com base positiva.
* A lista completa de regras fica em `regras_etl` no manifesto e na página *Qualidade e metodologia* do painel.

## Geração e atualização

* Geração inicial reprodutível: `python -m historico.scripts.gerar_dados_dashboard` (requer os XLSX oficiais auditados em `dados/brutos/sinesp/`).
* Novas publicações oficiais: fluxo **verificar → preparar → aprovar** (`python -m src.pipeline.atualizacao_dados`), manual e controlado,
  com versão anterior preservada e reversão. Ver o [`README.md`](../../README.md) do projeto (seção 10).
  O painel exibe uma **versão histórica validada** e nunca baixa dados nem executa ETL.

## Condições de reutilização da fonte (consulta de 27/10/2026)

Diferenciam-se a licença de um **catálogo de dados**, a licença **geral do site** e as condições **específicas** do recurso.

| Fonte | Catálogo de dados | Licença geral do site | Condições específicas do recurso |
|---|---|---|---|
| **MJSP / Sinesp VDE** | `dados.mj.gov.br`: informado pelo responsável como "Creative Commons Atribuição"; **não confirmado** — o domínio não resolveu (NXDOMAIN) | Rodapé do portal gov.br: "Creative Commons Atribuição-SemDerivações 3.0 Não Adaptada" (CC BY-ND 3.0) | Nenhuma proibição, restrição ou exigência de citação específica encontrada na página da base VDE nem no Termo de Uso do portal |

**Avaliação.** Nenhuma proibição específica aplicável a estes arquivos derivados foi encontrada, e **não há autorização
específica explícita**. Os arquivos reúnem apenas valores estatísticos públicos agregados por município e metadados de
rastreabilidade; os XLSX oficiais integrais não são redistribuídos. A licença do catálogo do MJSP não pôde ser confirmada,
e o CC BY-ND 3.0 do rodapé do portal (SemDerivações) é a licença **geral do site**, de aplicação a bases de dados não esclarecida.
Recomenda-se, por prudência, confirmar o uso com o MJSP (estatistica@mj.gov.br). A atribuição da fonte é obrigatória.
Isto é uma avaliação técnica do projeto, **não parecer jurídico**.
