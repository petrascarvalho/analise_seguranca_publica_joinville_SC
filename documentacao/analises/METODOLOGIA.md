# Metodologia, indicadores e rastreabilidade

Complemento do `README.md`. Aqui ficam os detalhes de método que não cabem no README: como a base é construída, o que cada
indicador significa, como as estatísticas são calculadas e como conferir que os números publicados são os da fonte oficial.

## 1. Fonte e cobertura

| Item | Descrição |
|---|---|
| Fonte | Sinesp VDE / Ministério da Justiça e Segurança Pública — base nacional dos gestores estaduais |
| Arquivos | `bancovde-2020.xlsx` a `bancovde-2026.xlsx` (um por ano, 14 colunas, ~24 MB cada) |
| Recorte | UF `SC`, município `JOINVILLE` (filtro exato) |
| Período | janeiro/2020 a setembro/2026; a série da PRF termina em agosto/2026; mandados da Polícia Federal só desde janeiro/2025 |
| Base aprovada | 911 observações mensais, 12 séries, 0 valores ausentes, 401 zeros publicados — versão `20261027T114400Z` |

Os XLSX ficam em `dados/brutos/sinesp/` e não vão para o GitHub. A pasta guarda duas edições oficiais, sem duplicar arquivos:
`oficial_20261027/` (edição usada pela base aprovada; hashes no manifesto) e a raiz + `pendente_validacao_origem/` (edição auditada em
agosto/2026, usada pelo roteiro histórico e pelos testes históricos). Origem e verificações: [ORIGEM_E_COBERTURA.md](ORIGEM_E_COBERTURA.md).

## 2. Indicadores (12 séries)

| Indicador | Abrangência | Unidade | Natureza |
|---|---|---|---|
| Homicídio doloso; Tentativa de homicídio; Feminicídio; Tentativa de feminicídio; Lesão corporal seguida de morte; Roubo seguido de morte (latrocínio) | Estadual | vítimas | criminal |
| Suicídio; Mortes a esclarecer (sem indício de crime); Morte no trânsito ou em decorrência dele (exceto homicídio doloso) | Estadual | vítimas | complementar |
| Mortes no trânsito | Polícia Rodoviária Federal | vítimas | complementar |
| Mandado de prisão cumprido | Estadual; Polícia Federal | mandados cumpridos | atividade policial |

Vítimas vêm da coluna `total_vitima`; mandados, da coluna `total`. São unidades diferentes e **nunca são somadas**, assim como abrangências
diferentes. Furto, roubo em geral, estupro e tráfico de drogas **não existem** nos arquivos do Sinesp para Joinville; a investigação de
fontes municipais e as divergências encontradas foram arquivadas em `historico/indicadores_complementares/` (nada disso entra na base).

## 3. Regras do ETL (`scripts/etl_sinesp.py`)

1. **Leitura:** a função `ler_sinesp_xlsx` percorre o XML da planilha e guarda só as linhas de SC/JOINVILLE; recusa o arquivo se as 14
   colunas mudarem.
2. **Data:** o serial do Excel (dias desde 30/12/1899) precisa ser inteiro, cair no dia 1 do mês e no ano do arquivo.
3. **Medida:** vítimas em `total_vitima`; mandados em `total`.
4. **Ausência × zero:** célula vazia vira `<NA>` (nunca zero); zero publicado é mantido como observação.
5. **Duplicidade:** nenhuma linha é apagada. Linhas repetidas na mesma competência só são somadas em *Tentativa de homicídio* e *Estupro*,
   como manda a nota metodológica oficial; em qualquer outro indicador, a repetição interrompe o processo.
6. **Validação:** colunas, chaves sem repetição, meses consecutivos por série, uma unidade por série e valores inteiros não negativos.
7. **Rastreabilidade:** o CSV gerado em memória tem o mesmo SHA-256 registrado no manifesto da base publicada.
8. **Exportação controlada:** o ETL grava só em `dados/processados/sinesp/` (`etl_recorte_joinville_bruto.csv`, `etl_sinesp_joinville_mensal.csv`,
   `etl_catalogo_series.csv`, `etl_relatorio.json`). A base do painel (`dashboard/data_publica/`) só muda pelo fluxo controlado descrito em
   [ATUALIZACAO_DE_DADOS.md](ATUALIZACAO_DE_DADOS.md).

| Camada | Onde fica | Conteúdo |
|---|---|---|
| Arquivo bruto | `dados/brutos/sinesp/` | XLSX oficiais, sem alteração |
| Base transformada | `dados/processados/sinesp/etl_recorte_joinville_bruto.csv` | 911 linhas de Joinville, 14 colunas originais |
| Base analítica validada | `dados/processados/sinesp/etl_sinesp_joinville_mensal.csv` | 911 observações × 6 colunas, igual à publicada |
| Base publicada | `dashboard/data_publica/` | 2 CSVs + manifesto com SHA-256, usados pelo Streamlit |

## 4. Estatísticas e gráficos

- **Somas anuais** só para anos completos (12 meses com valor); 2026 é comparado apenas com o mesmo período dos anos anteriores
  (janeiro até o último mês publicado da série).
- **Média, mediana, mínimo, máximo e desvio-padrão** sobre os valores mensais; o desvio usa `ddof=0` (descreve os meses, sem inferência).
- **Variação percentual** só com base positiva; a diferença absoluta é sempre informada.
- **Quartis e IQR** por interpolação linear; limites de Tukey Q1 − 1,5·IQR e Q3 + 1,5·IQR. O método só é tratado como informativo quando a
  série tem ao menos 12 meses, valores diferentes entre si, IQR > 0, menos de 50% de zeros e Q3 > 1 — hoje, em 5 das 12 séries.
- **Distribuição** por faixas: o zero publicado é faixa própria; os demais valores, faixas de largura igual (regra de Sturges).
- **Perfil mensal**: mediana de cada mês, usando somente anos completos (2020–2025).
- **Gráficos** (Matplotlib, em `dashboard/graficos.py`): barras para evolução anual, mensal e períodos equivalentes; linhas para média móvel e
  acumulado; mapa de calor, boxplot, distribuição e outliers. Cada gráfico tem uma tabela de apoio com os mesmos números.

## 5. Principais resultados

- Homicídio doloso (Estadual): 62 vítimas em 2020 e 29 em 2025 (anos completos); 21 em janeiro–setembro de 2025 e 25 no mesmo período de 2026.
- Tentativa de homicídio: 43 (jan–set/2025) e 77 (jan–set/2026).
- Janeiro/2020 (10) e janeiro/2023 (19) ficam acima do limite superior de Tukey (9,5) na série de homicídio doloso.

## 6. Limitações

- Registros administrativos agregados: não medem toda a criminalidade, não estimam subnotificação e não indicam causa.
- Sem taxas populacionais, sem dados por bairro, rua, horário ou corporação; sem total geral entre indicadores, abrangências ou unidades.
- 2026 é parcial; a PRF termina antes das demais séries; poucas contagens geram percentuais instáveis.
- A fonte pode revisar valores históricos; a atualização controlada detecta revisões e só as aceita com aprovação explícita.
- Condições de reutilização: licença do catálogo do MJSP não confirmada; o portal gov.br declara CC BY-ND 3.0 no rodapé. Avaliação técnica,
  não parecer jurídico.
