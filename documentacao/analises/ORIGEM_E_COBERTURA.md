# Origem e cobertura dos dados

Fonte única: **Sinesp VDE / Ministério da Justiça e Segurança Pública (MJSP)** — base nacional enviada pelos gestores estaduais. O projeto usa só o recorte exato `uf = SC` e `municipio = JOINVILLE`.

## Onde estão os arquivos oficiais

| Item | Endereço |
|---|---|
| Página oficial da base | <https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023> |
| Catálogo de downloads | <https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados> |
| Download direto (ano) | `https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/bancovde-ANO.xlsx/@@download/file` |

Os sete XLSX (`bancovde-2020.xlsx` a `bancovde-2026.xlsx`, ~24 MB cada, 14 colunas) ficam em `dados/brutos/sinesp/`, fora do Git:

- `oficial_20261027/` — edição republicada em 27/10/2026, usada pela base aprovada (SHA-256 no manifesto);
- raiz da pasta (2023–2026) e `pendente_validacao_origem/` (2020–2022) — edição auditada em agosto/2026.

Os arquivos originais nunca são alterados. A procedência de 2020–2022 foi validada contra os arquivos oficiais ([evidência por arquivo, com tamanho e SHA-256](../auditoria/sinesp_origem_2020_2022.csv)): 2021 e 2022 têm tamanho e hash iguais aos oficiais; em 2020 os hashes diferem, mas a comparação de todas as linhas e células foi idêntica.

## O que o recorte de Joinville contém

| Ano | Linhas de Joinville | Cobertura |
|---|---:|---|
| 2020 – 2024 | 132 por ano | janeiro–dezembro |
| 2025 | 144 | janeiro–dezembro (inclui mandados da Polícia Federal) |
| 2026 | 107 | janeiro–setembro (PRF até agosto) |

Total: **911 observações** em **12 séries** (indicador × abrangência: Estadual, Polícia Federal e Polícia Rodoviária Federal). As 14 colunas de origem são `uf`, `municipio`, `evento`, `data_referencia`, `agente`, `arma`, `faixa_etaria`, `feminino`, `masculino`, `nao_informado`, `total_vitima`, `total`, `total_peso` e `abrangencia`; agente, arma, faixa etária e peso estão vazios em todo o recorte, o que impede análises por essas dimensões.

## Regras de leitura

- **Zero e ausência:** o MJSP explica que o valor zero representa ausência de ocorrência. Valores vazios não são convertidos em zero.
- **Unidades:** `total_vitima` mede vítimas; `total` mede mandados cumpridos. Nunca são somados.
- **Duplicidade:** nenhuma linha é apagada; só *Tentativa de homicídio* e *Estupro* podem ter mais de uma linha por mês, somadas conforme a nota metodológica oficial.
- **Não existem** nos arquivos de Joinville: furto, roubo em geral, estupro e tráfico de drogas.

As regras de tratamento e as estatísticas estão em [METODOLOGIA.md](METODOLOGIA.md); a rotina de leitura é `src/pipeline/transform.py` e o passo a passo, `scripts/etl_sinesp.py`.
