# Deploy no Streamlit Community Cloud

**Deploy realizado.** Aplicação publicada em <https://seguranca-publica-joinville-sinesp.streamlit.app/>, reconstruída a partir da branch
`main` a cada push. Este documento registra a configuração usada e a conferência pós-deploy.

## Configuração do app

| Campo | Valor |
|---|---|
| Repositório | `petrascarvalho/analise_seguranca_publica_joinville_SC` |
| Branch | `main` |
| Arquivo principal | `scripts/painel_streamlit.py` |
| Python | 3.12 (versão usada nos testes; escolher em *Advanced settings*) |
| Dependências | `requirements.txt` na raiz |
| Segredos | nenhum (não há credenciais, tokens nem `.streamlit/secrets.toml`) |

## O que o app precisa no clone público

* `dashboard/` (páginas, módulos e `dashboard/data_publica/` com 2 CSVs do Sinesp, o manifesto e o `LEIAME.md`);
* `scripts/painel_streamlit.py` (entrada; não depende de outros módulos além de `dashboard/`);
* `.streamlit/config.toml` (tema claro com as cores dos gráficos);
* nenhuma pasta `dados/` (acervo bruto): o painel não a utiliza. Testes automatizados cobrem a execução em um clone sem ela.

Caminhos são relativos ao arquivo (`Path(__file__)`), não há caminhos absolutos do Windows nem dependência do kernel Interactive.
A entrada insere a raiz do projeto em `sys.path` para que o pacote `dashboard` seja importável no deploy. O painel não acessa a rede.

## Dependências

O painel usa **Streamlit, Pandas e Matplotlib**. `requirements.txt` também lista pacotes do ETL e dos testes (openpyxl, pdfplumber,
pypdf, lxml, pyarrow, pytest); o Cloud os instalará, o que só aumenta o tempo de build. Versões testadas localmente: Streamlit 1.66.0,
Pandas 3.0.6, Matplotlib 3.11.2, Python 3.12. As faixas de `requirements.txt` não foram testadas em versões mais antigas.

## Passos executados (e para refazer o deploy)

1. Confirmar que `main` e `origin/main` estão iguais e que o commit contém `dashboard/data_publica/` com os dois CSVs e o manifesto.
2. Em <https://share.streamlit.io>, *Create app* → repositório, branch e arquivo principal acima.
3. Aguardar o build; abrir as três páginas (**Projeto**, **Indicadores Sinesp**, **Qualidade e metodologia**); conferir *Qualidade e
   metodologia* (SHA-256 dos arquivos = manifesto; última competência 2026-09; PRF 2026-08).
4. A URL real está registrada no README (`## 15. Links de entrega`).

## Conferência pós-deploy

Após cada push em `main` o Cloud reconstrói o aplicativo (alguns minutos). Conferir, em <https://seguranca-publica-joinville-sinesp.streamlit.app/>:

* as **três páginas** na barra lateral (Projeto, Indicadores Sinesp, Qualidade e metodologia) e nenhuma mensagem de erro;
* em *Qualidade e metodologia*: arquivos com "confere com o manifesto", versão `20261027T114400Z`, última competência 2026-09 (PRF 2026-08);
* em *Indicadores Sinesp*: indicador padrão Homicídio doloso/Estadual, KPIs de 2025 (29) e janeiro–setembro de 2026 (25);
* se o aplicativo estiver "dormindo" (inatividade), acioná-lo e aguardar a reativação; se a versão exibida for antiga, reiniciar o app para limpar o `st.cache_data`.

Se o build falhar, verificar `requirements.txt` (Python 3.12) antes de qualquer alteração no código.

## Verificação visual

Os testes automatizados (`AppTest`) e as capturas locais em navegador sem interface (Chrome headless, desktop e tela estreita) não
substituem a inspeção no aplicativo publicado e em um celular real, que deve ser feita manualmente antes de divulgar o link.

## Atualização dos dados depois do deploy

Ver [ATUALIZACAO_DE_DADOS.md](../analises/ATUALIZACAO_DE_DADOS.md): promover a nova versão localmente, commitar os arquivos de
`dashboard/data_publica/` e fazer push; o Cloud reimplanta automaticamente.
