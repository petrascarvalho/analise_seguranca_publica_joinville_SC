# Atualização controlada dos dados do dashboard

Fonte única: **MJSP / Sinesp VDE**, município de Joinville/SC. Princípio central: **nenhuma atualização pode substituir
valores já auditados sem validação, registro de versão e aprovação explícita.** O painel nunca baixa dados, não executa ETL e
não se atualiza sozinho: ele exibe uma *versão histórica validada* dos arquivos de `dashboard/data_publica/`.

## O que é automático e o que é manual

| Etapa | Automático (código) | Manual (responsável) |
|---|---|---|
| **A — Verificar** | Consulta metadados da fonte e classifica indícios (`python -m scripts.atualizacao_dados verificar`) | Decidir se vale preparar; repetir a verificação quando quiser |
| **B — Preparar** | Lê os XLSX oficiais, executa o ETL, valida, compara e grava uma candidata isolada | Fornecer (ou pedir o download de) **todos** os XLSX; ler o relatório de validação |
| **C — Aprovar** | Preserva a versão anterior, troca o diretório de forma segura e revalida | **Digitar a aprovação** (`--confirmo <id>`; `--aceitar-revisoes` apenas após análise de revisões) |
| **Reverter** | Restaura uma versão preservada | Digitar a confirmação |
| **Publicar** | — | `git add` explícito, commit e push; o Streamlit Community Cloud reimplanta a partir do GitHub |

Não existe atualização automática operacional: nada roda em agendamento; todo o fluxo é acionado por comando.

## Como os dados originais são obtidos

XLSX anuais `bancovde-ANO.xlsx` na página da base VDE
(<https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023>).
O padrão oficial de download é
`https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/bancovde-ANO.xlsx/@@download/file`.
Para a preparação, salvar **todos** os anos (2020 em diante) em uma pasta; o código aceita qualquer subpasta, desde que exista
**exatamente um** arquivo por ano. Esses arquivos **não** vão para o GitHub (`/dados/` e `/atualizacao/` no `.gitignore`).
**Não são usados PDFs nem CSVs de outras fontes.**

## Como os arquivos derivados são gerados

Dois mecanismos, ambos restritos ao Sinesp:

* **Atualização (uso normal):** fluxo A → B → C abaixo (`scripts/atualizacao_dados.py`), que não depende do roteiro acadêmico.
* **Geração inicial reprodutível:** `python -m scripts.gerar_dados_dashboard` extrai do roteiro as etapas Sinesp validadas (1–2 e 5–9),
  executa-as em espaço de nomes isolado, confere valores conhecidos (900 observações até agosto/2026) e grava os CSVs e o manifesto.
  Ele reproduz a versão inicial auditada; para publicações novas, use o fluxo controlado. Antes de sobrescrever, a versão anterior é copiada
  para `atualizacao/versoes/`.

Arquivos ativos: `sinesp_joinville_mensal.csv`, `sinesp_catalogo_indicadores.csv` e `manifesto_dados_publicos.json` (versão, datas,
cobertura por série, unidades, SHA-256, fonte, licenças, método de obtenção e regras de ETL).

## A — Verificar (somente leitura)

```powershell
python -m scripts.atualizacao_dados verificar
```

Grava `atualizacao/verificacoes/verificacao_<UTC>.json` (URL, identificador, data da consulta, evidência e classificação de cada
achado) e **não toca** em `dashboard/data_publica/`. Classificações:

| Classificação | Significado |
|---|---|
| `nenhuma_novidade_identificada` | Nada indica mudança (limitado ao que a fonte expõe) |
| `possivel_nova_competencia` | Arquivo do último ano maior que o auditado, ou arquivo/ano novo |
| `possivel_revisao_de_competencia_historica` | Arquivo de ano já coberto com tamanho diferente do registrado |
| `alteracao_de_esquema_ou_fonte` | Página/API fora do formato ou licença do catálogo alterada |
| `falha_de_consulta` | DNS, tempo esgotado, HTTP 403 etc. **Bloqueios não são contornados** |

Tudo é **indício**: mudar a data da página ou o tamanho de um arquivo não prova que valores mudaram, e nenhuma competência é inventada
a partir de datas. Só o passo B, com o conteúdo, confirma nova competência ou revisão.

### Limitações da fonte (consulta de 27/10/2026)

* **gov.br:** sem API pública documentada (a API REST do portal responde 401) e `HEAD` bloqueado (403). O tamanho vem de `GET` com
  `Range: bytes=0-0` (resposta 206), com identificação honesta (`User-Agent` do projeto). Não há data de modificação por arquivo; a data
  "Atualizado em" é da **página**. A leitura dessa data usa o texto da página (frágil por natureza): se o formato mudar, vira
  `alteracao_de_esquema_ou_fonte`. Os arquivos grandes (~24 MB) podem ser interrompidos durante o download: quedas de conexão são repetidas
  até três vezes; bloqueios HTTP não são repetidos nem contornados e o arquivo passa a ser baixado manualmente.
* **Catálogo do MJSP (`dados.mj.gov.br`):** o domínio **não resolveu (NXDOMAIN)** nas consultas; sem catálogo, a licença do MJSP não é
  monitorada automaticamente.

## B — Preparar (candidata isolada)

```powershell
# com os XLSX oficiais colocados manualmente (TODOS os anos):
python -m scripts.atualizacao_dados preparar --entradas-sinesp <pasta com bancovde-2020.xlsx ... bancovde-2026.xlsx> --relatorio-verificacao atualizacao/verificacoes/<arquivo>.json
# ou, para tentar baixar os XLSX oficiais (pode falhar por bloqueio; não é contornado):
python -m scripts.atualizacao_dados preparar --baixar-sinesp --relatorio-verificacao atualizacao/verificacoes/<arquivo>.json
```

Cria `atualizacao/staging/<id>/` com `dados/` (CSVs + manifesto candidatos + `LEIAME.md`), `relatorio_validacao.json` e
`comparacao_sinesp.csv`. A versão ativa **não é alterada**. O ETL aplica as regras do projeto: filtro exato `SC`/`JOINVILLE`; vítimas em
`total_vitima`, mandados em `total`; ausência preservada (campo vazio), zero publicado mantido; datas pelo serial Excel (1900) com dia 1
e ano igual ao do arquivo; linhas repetidas somadas **somente** em *Tentativa de homicídio* e *Estupro* (nota metodológica oficial), sem
deduplicação genérica. Com os originais auditados, a candidata é idêntica byte a byte aos dados ativos (verificado).

* **Erros (bloqueiam a promoção):** esquema do XLSX alterado; indicador novo/renomeado; abrangência ausente; valor negativo, fracionário ou
  não numérico; data inválida; linhas repetidas em indicador **sem** nota oficial de soma; série nova ou ausente; lacuna de competências;
  competência histórica removida; unidade alterada; falha de integridade/esquema na releitura pelos mesmos validadores do painel.
* **Avisos (exigem `--aceitar-revisoes`):** valores históricos **alterados** (revisão da fonte); linhas múltiplas somadas conforme nota oficial.
  `--aceitar-revisoes` **nunca** deve ser usado para contornar um alerta não resolvido: se houver revisão, pare e analise
  `comparacao_sinesp.csv`.
* **Informação (não bloqueia):** novas competências, séries com última competência diferente (por exemplo, a PRF costuma terminar antes),
  ausências, zeros, arquivos de origem com hash diferente do registrado.

Arquivos de anos anteriores **não** são assumidos como inalterados: todos devem ser fornecidos e são recomparados. Em caso de falha, a
candidata parcial é removida e a ativa permanece intacta.

Comparar versões: `python -m scripts.atualizacao_dados comparar <id>` (relatório + diferenças `novo`/`removido`/`alterado`).

## C — Aprovar e promover

```powershell
python -m scripts.atualizacao_dados aprovar <id> --confirmo <id> --aprovado-por "<quem aprovou>"
```

Só promove se a confirmação for **igual ao id**, a candidata não tiver erros, a versão ativa não tiver mudado desde a preparação e a
releitura dos arquivos (esquema + SHA-256) passar. A versão anterior é copiada para `atualizacao/versoes/<versão>/`; a troca é feita por
renomeação de diretórios (`data_publica.novo` → `data_publica`) com reversão automática se qualquer passo falhar; depois da troca o
diretório é revalidado (se falhar, volta atrás). O manifesto da nova versão registra `versao`, `versao_anterior`, `aprovacao` (data, quem,
se aceitou revisões) e a cobertura. A data de aprovação é a do momento da promoção: nunca é inventada.

## Reverter

```powershell
python -m scripts.atualizacao_dados versoes
python -m scripts.atualizacao_dados reverter <versao> --confirmo <versao>
```

Restaura a versão preservada (também revalidada) e preserva a que foi substituída.

## Do GitHub ao Streamlit

1. Promovida a versão, revisar `git status` e `git diff`.
2. `git add` **explícito** dos arquivos de `dashboard/data_publica/` (2 CSVs, manifesto e `LEIAME.md`); nunca `git add .`.
3. Commit e `git push origin main` (autorização do responsável).
4. O Streamlit Community Cloud reimplanta a partir do GitHub; se necessário, reiniciar o app para limpar o `st.cache_data`.
5. Conferir em <https://seguranca-publica-joinville-sinesp.streamlit.app/>, na página *Qualidade e metodologia*, a versão, a última competência por série e o SHA-256 dos arquivos (lista completa em [DEPLOY_STREAMLIT.md](DEPLOY_STREAMLIT.md)).

`atualizacao/` (entradas baixadas, candidatas, versões anteriores e verificações) é **local** e está no `.gitignore`.

## Estado em 27/10/2026 (informativo)

* A verificação real apontou indícios de nova competência e de revisão (tamanhos de arquivos diferentes). A preparação com os sete XLSX
  oficiais baixados nesse dia gerou a candidata `20261027T114400Z`: **911 observações; 11 novas competências (2026-09); nenhuma
  revisão, remoção ou mudança de unidade em valores históricos de Joinville**; os sete arquivos têm hash diferente dos auditados
  anteriormente (republicação pela fonte), mas os valores de Joinville coincidem; a série *Mortes no trânsito — PRF* ainda termina em 2026-08.
* A candidata foi promovida por autorização condicionada do responsável (sem `--aceitar-revisoes`), em 2026-10-27T11:45:19Z (UTC). A versão
  anterior (`20261027T045449Z`, até 2026-08) foi preservada em `atualizacao/versoes/` e pode ser restaurada com o comando de reversão.
