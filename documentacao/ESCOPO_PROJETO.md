# Segurança pública de Joinville — escopo do projeto

Documento inicial, elaborado em 16/10/2026 a partir do escopo não oficial de Visualização de Dados e BI T1, atualizado em 09/10/2026. Requisitos administrativos e prazos dependem da publicação oficial.

## Pergunta orientadora

Como evoluíram os indicadores disponíveis de criminalidade registrada em Joinville entre 2023 e 2025, o que os dados parciais de 2026 permitem observar e quais informações públicas descrevem a atuação da Guarda Municipal?

## Objetivo, público e relevância

Organizar e apresentar indicadores oficiais agregados em uma aplicação de BI, permitindo que estudantes, cidadãos e gestores consultem evolução temporal e diferenças entre categorias, com períodos e limitações explícitos. A solução descreve registros publicados; não mede toda a criminalidade ocorrida nem demonstra o efeito causal de políticas públicas.

## Cobertura pretendida, condicionada aos dados disponíveis

- Furtos e roubos totais: histórico anual de 2023–2025 já localizado em publicação oficial.
- Furtos e roubos de veículos: histórico anual de 2023–2025 já localizado.
- Furtos e roubos em residências: comparação de 2024–2025 já localizada.
- Vítimas de homicídio: anos completos de 2023–2025 e janeiro–julho de 2023–2026.
- Guarda Municipal: balanços por categoria e períodos efetivamente publicados, em seção independente.
- Outros indicadores de segurança: incluir somente quando houver fonte, unidade de contagem, território e período identificáveis. Não apresentar esta seleção como cobertura de toda a segurança pública.

2026 deverá ter seção própria, explicitamente parcial. Furtos e roubos municipais de 2026 e acumulado anual da Guarda continuam sem série oficial validada neste levantamento. Dados ausentes não equivalem a zero. Categorias de veículos e residências não serão somadas aos totais gerais. Atendimentos da Guarda não serão somados a crimes registrados.

Ficam fora do escopo: identificação de pessoas, microdados pessoais, previsões sem suporte, rankings de bairros sem base adequada, comparação entre efetividade das corporações e afirmações causais.

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
| Coleta | Arquivos originais e documentação da obtenção | XLSX oficiais do Sinesp de 2023 a 2026 baixados em `dados/brutos/`; outras fontes a avaliar |
| ETL | Código Python e registro das decisões | Não iniciado; usuário instruiu não tratar nem limpar dados |
| EDA e estatística | Exploração e comparações reproduzíveis | Não iniciadas como pipeline |
| Visualização | Gráficos dos indicadores disponíveis | Não iniciada |
| BI | Aplicação Streamlit | Não iniciada |
| Documentação | README completo, dependências e execução | A elaborar ao longo das etapas |
| Entrega | Repositório, deploy, vídeo e links | Pendente; nenhuma publicação realizada |

## Restrição de coleta vigente

O usuário autorizou baixar arquivos originais em XLSX além de CSV e pediu começar pela coleta, sem tratamento ou limpeza. Os XLSX anuais do Sinesp de 2023 a 2026 foram baixados sem alteração; origem e hashes estão em `documentacao/fontes/ORIGEM_SINESP.md`. A autorização de coleta não inicia a etapa de ETL.

O escopo completo exige ETL posteriormente; apenas coletar arquivos não atende à entrega final. A leitura do escopo não foi usada para iniciar transformações contra a orientação expressa do usuário.

## Fontes já localizadas

- Prefeitura, criminalidade 2023–2025: https://www.joinville.sc.gov.br/noticias/indices-de-criminalidade-tem-reducao-em-joinville-pelo-terceiro-ano-consecutivo/
- SSP/SC, boletins: https://ssp.sc.gov.br/segurancaemnumeros/
- SSP/SC, julho de 2026: https://ssp.sc.gov.br/wp-content/uploads/2026/08/2026-julho.pdf
- SEPROT, balanço publicado em novembro de 2025: https://www.joinville.sc.gov.br/noticias/seprot-apresenta-relatorio-de-acoes-para-os-conselhos-comunitarios-de-seguranca/
- Guarda Municipal, publicação de outubro de 2026: https://www.joinville.sc.gov.br/noticias/tecnologia-da-prefeitura-de-joinville-ajuda-a-encontrar-possiveis-responsaveis-por-assalto-a-joalheria/
- Sinesp, bases anuais em XLSX, conteúdo ainda não inspecionado: https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023

## Organização proposta para a implementação futura

- `dados/brutos/`: arquivos originais preservados.
- `dados/processados/`: resultados reproduzíveis da futura ETL.
- `src/`: coleta, transformação e cálculo de indicadores.
- `notebooks/`: exploração, se utilizada.
- `painel_streamlit.py`: aplicação Streamlit na implementação atual.
- `documentacao/`: metodologia e evidências de validação.
- `README.md`, `requirements.txt` e `.gitignore`: documentação e reprodução.

Adaptação implementada no projeto: o ponto de entrada do Streamlit chama-se `painel_streamlit.py`, na raiz, para evitar conflito com o nome da biblioteca. A proposta original previa outro nome para esse arquivo; a lista acima descreve a implementação atual.

## Critérios de conclusão

A análise deverá apresentar todos os indicadores disponíveis selecionados, sem se limitar a homicídios; separar anos completos de períodos parciais; identificar fontes e lacunas; permitir reproduzir os resultados; funcionar em Streamlit com pelo menos uma interação útil e atender às entregas acadêmicas aplicáveis.

## Pontos administrativos a confirmar na versão oficial

O documento combina exigências de repositório pessoal e publicação no repositório da turma com uma regra de GitHub privado. Também cita vídeo em rede social e disponibilização no Google Drive, além de planejamento no Trello. Registrar os diferentes itens e confirmar o procedimento oficial; não presumir que um substitui o outro. Prazo e rubrica final de avaliação estão a definir. A fonte não oficial não autoriza por si só publicações, envio de mensagens ou marcações em redes sociais.
