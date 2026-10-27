# Preparação do deploy no Streamlit Community Cloud

**Nenhum deploy foi feito e não existe URL pública.** Este roteiro só prepara a publicação, que depende de autorização
separada do responsável.

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

* `dashboard/` (páginas, módulos e `dashboard/data_publica/` com 4 CSVs, o manifesto e o `LEIAME.md`);
* `scripts/__init__.py` e `scripts/utils.py` (usados pela entrada);
* nenhuma pasta `dados/` (acervo bruto): o painel não a utiliza. Testes automatizados cobrem a execução em um clone sem ela.

Caminhos são relativos ao arquivo (`Path(__file__)`), não há caminhos absolutos do Windows nem dependência do kernel
Interactive. A entrada insere a raiz do projeto em `sys.path` para que `scripts` e `dashboard` sejam importáveis no deploy.

## Dependências

O painel usa **Streamlit, Pandas e Matplotlib**. `requirements.txt` também lista pacotes do ETL (openpyxl, pdfplumber, pypdf,
lxml, pyarrow, pytest); o Cloud os instalará, o que só aumenta o tempo de build. Versões testadas localmente: Streamlit 1.66.0,
Pandas 3.0.6, Matplotlib 3.11.2, Python 3.12. As faixas de `requirements.txt` não foram testadas em versões mais antigas.

## Passos (quando autorizado)

1. Confirmar que `main` e `origin/main` estão iguais e que o commit contém `dashboard/data_publica/`.
2. Em <https://share.streamlit.io>, *Create app* → repositório, branch e arquivo principal acima.
3. Aguardar o build; abrir as quatro páginas; conferir *Qualidade dos dados* (SHA-256 dos arquivos = manifesto).
4. Só então registrar a URL real no README (`## 15. Links de entrega`).

## Verificação visual

Os testes automatizados (`AppTest`) e a inicialização do servidor não substituem a inspeção visual em desktop e celular.
Ela deve ser feita manualmente no navegador antes de divulgar o link.

## Atualização dos dados depois do deploy

Ver [ATUALIZACAO_DE_DADOS.md](ATUALIZACAO_DE_DADOS.md): promover a nova versão localmente, commitar os arquivos de
`dashboard/data_publica/` e fazer push; o Cloud reimplanta automaticamente.
