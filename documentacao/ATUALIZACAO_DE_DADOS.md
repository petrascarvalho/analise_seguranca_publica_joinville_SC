# Atualização controlada dos dados do dashboard

Princípio central: **nenhuma atualização pode substituir valores já auditados sem validação, registro de
versão e aprovação explícita.** O painel nunca baixa dados, não executa ETL e não se atualiza sozinho: ele
exibe uma *versão histórica validada* dos arquivos de `dashboard/data_publica/`.

## O que é automático e o que é manual

| Etapa | Automático (código) | Manual (responsável) |
|---|---|---|
| **A — Verificar** | Consulta metadados das fontes e classifica indícios (`python -m scripts.atualizacao_dados verificar`) | Decidir se vale preparar; repetir a verificação quando quiser |
| **B — Preparar** | Lê os XLSX oficiais, executa o ETL, valida, compara e grava uma candidata isolada | Fornecer (ou pedir o download de) **todos** os XLSX; ler o relatório de validação |
| **C — Aprovar** | Preserva a versão anterior, troca o diretório de forma segura e revalida | **Digitar a aprovação** (`--confirmo <id>`; `--aceitar-revisoes` se houver revisões) |
| **Reverter** | Restaura uma versão preservada | Digitar a confirmação |
| **SSP/SC (violência doméstica)** | Só detecta indícios (novos relatórios/formatos) | **Auditoria manual** antes de qualquer incorporação (não há ETL automático para novos relatórios) |
| **Publicar** | — | `git add` explícito, commit e push; o Streamlit Community Cloud reimplanta a partir do GitHub |

Não existe atualização automática operacional: nada roda em agendamento; todo o fluxo é acionado por comando.

## Como os dados originais são obtidos

* **Sinesp/MJSP:** XLSX anuais `bancovde-ANO.xlsx` na página da base VDE
  (<https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023>).
  Salvar em `dados/brutos/sinesp/` (2020–2022 na subpasta `pendente_validacao_origem/`). O código aceita
  qualquer subpasta, desde que exista **exatamente um** arquivo por ano.
* **SSP/SC:** relatórios de violência doméstica (PDF) publicados em <https://ssp.sc.gov.br/segurancaemnumeros/>;
  os três auditados estão em `dados/brutos/ssp_sc/pdfs/` com os CSVs extraídos em `csv_extraidos/`.

Esses arquivos **não** vão para o GitHub (`/dados/` no `.gitignore`).

## Como os quatro arquivos derivados são gerados

`python -m scripts.gerar_dados_dashboard` (requer o acervo bruto local) extrai do roteiro acadêmico as etapas
validadas, executa-as em espaço de nomes isolado, confere valores conhecidos e grava
`sinesp_joinville_mensal.csv`, `sinesp_catalogo_indicadores.csv`, `ssp_violencia_domestica_joinville.csv`,
`ssp_violencia_domestica_rastreabilidade.csv` e o `manifesto_dados_publicos.json` (versão, datas, cobertura, SHA-256,
fontes, licenças verificadas). Antes de sobrescrever, a versão anterior é copiada para `atualizacao/versoes/`.
`--relatorio-verificacao <json>` registra no manifesto o resultado de uma verificação das fontes.

Para **atualizações**, use o fluxo A → B → C abaixo (ele não depende do roteiro, cujo portão de hash só aceita os
originais auditados).

## A — Verificar (somente leitura)

```powershell
python -m scripts.atualizacao_dados verificar
```

Grava `atualizacao/verificacoes/verificacao_<UTC>.json` (URL, identificador, data da consulta, evidência e
classificação de cada achado) e **não toca** em `dashboard/data_publica/`. Classificações:

| Classificação | Significado |
|---|---|
| `nenhuma_novidade_identificada` | Nada indica mudança (limitado ao que a fonte expõe) |
| `possivel_nova_competencia` | Arquivo do último ano maior que o auditado, ou arquivo/ano novo |
| `possivel_revisao_de_competencia_historica` | Arquivo de ano já coberto com tamanho diferente do auditado |
| `alteracao_de_esquema_ou_fonte` | Página/API fora do formato, licença do catálogo mudou, relatório em outro formato (ex.: XLSX) ou removido |
| `falha_de_consulta` | DNS, tempo esgotado, HTTP 403 etc. **Bloqueios não são contornados** |

Tudo é **indício**: mudar a data da página ou o tamanho de um arquivo não prova que valores mudaram, e nenhuma
competência é inventada a partir de datas. Só o passo B, com o conteúdo, confirma nova competência ou revisão.

### Limitações por fonte (consulta de 27/10/2026)

* **Sinesp (gov.br):** sem API pública documentada (a API REST do portal responde 401) e `HEAD` bloqueado (403). O tamanho
  vem de `GET` com `Range: bytes=0-0` (resposta 206), com identificação honesta (`User-Agent` do projeto). Não há data de
  modificação por arquivo; a data "Atualizado em" é da **página**. A leitura dessa data usa o texto da página (frágil por
  natureza): se o formato mudar, vira `alteracao_de_esquema_ou_fonte`.
* **Catálogo do MJSP (`dados.mj.gov.br`):** o domínio **não resolveu (NXDOMAIN)** nas consultas; sem catálogo, a licença do MJSP
  não é monitorada automaticamente.
* **SSP/SC:** o catálogo CKAN (`dados.sc.gov.br`) tem API, mas só aponta para a página; novos relatórios são identificados pela
  API REST de mídia do WordPress da SSP/SC (busca por `DOMESTICA`). Relatórios novos podem ter formato diferente.

## B — Preparar (candidata isolada)

```powershell
# com os XLSX oficiais colocados manualmente (TODOS os anos):
python -m scripts.atualizacao_dados preparar --entradas-sinesp dados/brutos/sinesp --relatorio-verificacao atualizacao/verificacoes/<arquivo>.json
# ou, para tentar baixar os XLSX oficiais (pode falhar por bloqueio; não é contornado):
python -m scripts.atualizacao_dados preparar --baixar-sinesp --relatorio-verificacao atualizacao/verificacoes/<arquivo>.json
```

Cria `atualizacao/staging/<id>/` com `dados/` (CSVs + manifesto candidatos + `LEIAME.md`), `relatorio_validacao.json` e
`comparacao_sinesp.csv`. A versão ativa **não é alterada**. O ETL independente (`scripts/atualizacao_dados.py`) aplica as
mesmas regras do roteiro: vítimas em `total_vitima`, mandados em `total`, ausência preservada (campo vazio), zero publicado
mantido, datas pelo serial Excel (1900) com dia 1 e ano igual ao do arquivo. **Com os originais auditados, a candidata é
idêntica byte a byte aos dados ativos** (verificado). Validações:

* **Erros (bloqueiam a promoção):** esquema do XLSX alterado; indicador novo/renomeado; abrangência ausente; valor
  negativo/fracionário/não numérico; data inválida; linhas repetidas na mesma competência em indicador **sem** nota oficial
  de soma (sem deduplicação genérica); série nova ou ausente; lacuna de competências; competência histórica removida;
  unidade alterada; falha de integridade/esquema na releitura pelos mesmos validadores do painel.
* **Avisos (exigem `--aceitar-revisoes`):** valores históricos **alterados** (revisão); séries com última competência
  diferente; linhas múltiplas somadas conforme nota oficial ("Tentativa de Homicídio" e "Estupro"); indícios de novos
  relatórios SSP/SC (não incorporados).
* **Informação:** novas competências, ausências, zeros, arquivos de origem com hash diferente do auditado.

Arquivos de anos anteriores **não** são assumidos como inalterados: todos devem ser fornecidos e são recomparados.
Em caso de falha, a candidata parcial é removida e a ativa permanece intacta.

Comparar versões: `python -m scripts.atualizacao_dados comparar <id>` (relatório + diferenças `novo`/`removido`/`alterado`).

## C — Aprovar e promover

```powershell
python -m scripts.atualizacao_dados aprovar <id> --confirmo <id> [--aceitar-revisoes]
```

Só promove se a confirmação for **igual ao id**, a candidata não tiver erros, a versão ativa não tiver mudado desde a
preparação e a releitura dos arquivos (esquema + SHA-256) passar. A versão anterior é copiada para
`atualizacao/versoes/<versão>/`; a troca é feita por renomeação de diretórios (`data_publica.novo` → `data_publica`) com
reversão automática se qualquer passo falhar; depois da troca o diretório é revalidado (se falhar, volta atrás). O manifesto
da nova versão registra `versao`, `versao_anterior`, `aprovacao` (data, quem, aceitou revisões) e a cobertura.

## Reverter

```powershell
python -m scripts.atualizacao_dados versoes
python -m scripts.atualizacao_dados reverter <versao> --confirmo <versao>
```

Restaura a versão preservada (também revalidada) e preserva a que foi substituída.

## SSP/SC: novos relatórios de violência doméstica

Não há incorporação automática. Ao identificar relatório novo (ou XLSX), é preciso, manualmente: conferir categorias originais
e a definição de "Fato Comunicado"; cabeçalhos e competências; município e páginas de continuação; possíveis revisões
históricas; manter a equivalência metodológica de "0 Dolosa"/"- Dolosa" (decisão do projeto, **não** confirmação oficial); e
repetir as auditorias (Etapas 11–13.3 do roteiro) antes de gerar nova versão. Relatórios de homicídios SSP/SC (série
histórica ainda não consolidada) não se misturam com a violência doméstica.

## Do GitHub ao Streamlit

1. Promovida a versão, revisar `git status` e `git diff`.
2. `git add` **explícito** dos arquivos de `dashboard/data_publica/` (4 CSVs, manifesto, `LEIAME.md`); nunca `git add .`.
3. Commit e `git push origin main` (autorização do responsável).
4. O Streamlit Community Cloud reimplanta a partir do GitHub; se necessário, reiniciar o app para limpar o `st.cache_data`.
5. Conferir na página *Qualidade dos dados* a versão, a última competência e o SHA-256 dos arquivos.

`atualizacao/` (entradas baixadas, candidatas, versões anteriores e verificações) é **local** e está no `.gitignore`.

## Estado verificado em 27/10/2026 (informativo)

* Verificação real: indícios de nova competência (arquivo Sinesp 2026 maior) e de revisão (tamanhos diferentes em 2020–2025);
  três PDFs de violência doméstica com tamanho igual ao auditado; **dois novos recursos XLSX** de violência doméstica na SSP/SC;
  `dados.mj.gov.br` fora do ar (NXDOMAIN).
* Preparação real com os XLSX oficiais baixados nesse dia: **911 observações; 11 novas competências (2026-09); nenhuma
  revisão de valores históricos de Joinville**; os 7 arquivos têm hash diferente dos auditados, mas os valores das séries de
  Joinville coincidem; a série *Mortes no trânsito — PRF* ainda termina em 2026-08. A candidata **não foi promovida**.
