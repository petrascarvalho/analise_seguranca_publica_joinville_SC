# Segurança pública de Joinville — escopo do projeto

Escopo vigente a partir da Etapa 18 (27/10/2026). O documento substitui o escopo inicial de 16/10/2026, que previa várias fontes
(Sinesp, SSP/SC, Prefeitura/SEPROT e Guarda Municipal). Requisitos administrativos e prazos dependem da publicação oficial.

## Decisão de escopo

O produto entregue usa **exclusivamente dados do Sinesp/MJSP para Joinville/SC**. SSP/SC e Prefeitura/SEPROT foram trabalhos
exploratórios e auditorias anteriores: permanecem **registrados como histórico, fora do escopo e fora do dashboard**. O código, os testes e
os dados dessas fontes são recuperáveis pelo histórico Git (commit `bad9723`) e pelo arquivo local descrito em `historico/ssp_sc/LEIAME.md`.

Motivo: homogeneidade metodológica. O Sinesp fornece uma série mensal única, com unidades e abrangências definidas, que pode ser atualizada por
um fluxo reprodutível e verificável a partir dos XLSX oficiais, sem depender de PDFs de boletins republicados com divergências nem de
transcrições de notícias.

## Pergunta orientadora

Como evoluíram, desde janeiro/2020, os indicadores oficiais de segurança pública do Sinesp/MJSP para Joinville/SC, e o que a comparação entre
períodos equivalentes permite — e não permite — afirmar sobre essa evolução?

## Objetivo, público e relevância

Organizar, validar e apresentar de forma transparente as séries mensais municipais publicadas pelo Sinesp/MJSP, com filtros por indicador,
abrangência e período, estatísticas descritivas e comparações entre anos completos e entre períodos equivalentes, sempre com fonte, unidade e
limitações explícitas. O público inclui estudantes, cidadãos, pesquisadores e gestores. A solução descreve registros publicados; não mede toda
a criminalidade ocorrida nem demonstra o efeito causal de políticas públicas.

## Cobertura

Doze séries (indicador × abrangência), janeiro/2020 a setembro/2026 (2026 parcial; a série da PRF termina em agosto/2026):

* **Vítimas:** feminicídio, tentativa de feminicídio, homicídio doloso, tentativa de homicídio, lesão corporal seguida de morte, latrocínio,
  suicídio, mortes a esclarecer, morte no trânsito (Estadual) e mortes no trânsito (Polícia Rodoviária Federal);
* **Mandados cumpridos (contagem publicada):** Estadual e Polícia Federal (esta a partir de janeiro/2025).

Vítimas e mandados são conceitos distintos e nunca são somados; abrangências também não. Não há total geral de criminalidade.

Ficam fora do escopo: furtos, roubos e Guarda Municipal; dados da SSP/SC e da Prefeitura/SEPROT; taxas populacionais; dados por bairro, rua,
horário ou corporação; identificação de pessoas, microdados pessoais, previsões sem suporte, rankings territoriais e afirmações causais.

## Requisitos do documento de referência

1. Documentar objetivo, relevância, público, escopo e resultados esperados.
2. Documentar fonte, responsável, endereço, período, campos, licença/termos, data de acesso e método de obtenção reproduzível.
3. Implementar ETL em Python e registrar decisões de transformação, preservando dados brutos.
4. Realizar análise exploratória e estatísticas descritivas adequadas aos dados.
5. Criar gráficos com títulos, eixos, unidades, legendas e fontes.
6. Desenvolver aplicação Streamlit com navegação clara, interação útil, fontes, períodos e mensagens para lacunas ou erros.
7. Disponibilizar código reproduzível, dependências e instruções sem caminhos absolutos obrigatórios.
8. Manter repositório individual dedicado e histórico real de desenvolvimento.
9. Publicar no serviço oficial do Streamlit e verificar o acesso.
10. Preparar documentação, conclusão, discussão de uso profissional e vídeo de até três minutos.

## Etapas e situação atual

| Etapa | Entrega | Situação |
|---|---|---|
| Planejamento | Pergunta, objetivo e delimitação | Registrados neste documento |
| Coleta | XLSX oficiais do Sinesp (2020–2026) | Obtidos da fonte oficial; origem e hashes em `documentacao/fontes/ORIGEM_SINESP.md` e no manifesto |
| ETL | Código Python e registro das decisões | Implementado (roteiro acadêmico e `scripts/atualizacao_dados.py`); regras no manifesto |
| EDA e estatística | Exploração e comparações reproduzíveis | Implementadas (etapas 5–10 do roteiro e página *Indicadores Sinesp*) |
| Visualização | Gráficos dos indicadores | Implementada (Matplotlib; quatro figuras da Etapa 10 e figuras filtráveis) |
| BI | Aplicação Streamlit | Implementada: três páginas (Projeto, Indicadores Sinesp, Qualidade e metodologia) |
| Documentação | README, roteiro `scripts/analise_sinesp.py`, dependências, execução, atualização | Concluída (Etapa 19: pós-deploy) |
| Deploy | Streamlit Community Cloud | **Realizado:** <https://seguranca-publica-joinville-sinesp.streamlit.app/> (revisão visual e aperfeiçoamento dos gráficos pendentes) |
| Entrega | Vídeo, repositório da turma e AVA | **Pendentes** |

O planejamento no Trello foi **dispensado por orientação do professor**.

## Organização do repositório

Ver a seção 12 do `README.md`. Em resumo: `scripts/` (roteiro, ETL de atualização, entrada do painel), `dashboard/` (páginas, módulos e
`data_publica/`), `tests/` (suíte ativa), `tests_historicos/` (testes dependentes do acervo local), `historico/ssp_sc/` (índice do trabalho
histórico), `documentacao/`. O acervo bruto (`dados/`) e as candidatas de atualização (`atualizacao/`) são locais e ficam fora do Git.

## Critérios de conclusão

A análise deve apresentar os indicadores Sinesp disponíveis para Joinville, separar anos completos de períodos parciais, identificar fonte e
lacunas, permitir reproduzir os resultados, funcionar em Streamlit com filtros úteis e atender às entregas acadêmicas aplicáveis.

## Pontos administrativos a confirmar na versão oficial

O documento de referência combina exigências de repositório pessoal e publicação no repositório da turma com uma regra de GitHub
privado. Também cita vídeo em rede social e disponibilização no Google Drive. Registrar os diferentes itens e confirmar o procedimento
oficial; não presumir que um substitui o outro. Prazo e rubrica final de avaliação estão a definir. Nenhum link de entrega é inventado.
