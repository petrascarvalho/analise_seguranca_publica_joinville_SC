import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard import dados_publicos as dp  # noqa: E402
from dashboard import ui  # noqa: E402
from dashboard.formatacao import fmt_int  # noqa: E402

st.title("Qualidade, cobertura e rastreabilidade dos dados")
st.write(
    "Esta página descreve os **arquivos mínimos e agregados** usados pelo painel, sua cobertura, unidades, ausências e limitações. "
    "Ela funciona sem o acervo bruto local. As contagens de linhas são observações mensais agregadas, não ocorrências individuais."
)

manifesto = ui.carregar_manifesto()
integridade = ui.verificar_integridade()

st.subheader("Arquivos de exibição e integridade")
fichas = pd.DataFrame(manifesto["arquivos"])[["arquivo", "linhas", "colunas", "sha256"]]
fichas = fichas.merge(integridade[["arquivo", "integro"]], on="arquivo", how="left")
fichas["Integridade (SHA-256)"] = fichas["integro"].map({True: "✅ confere com o manifesto", False: "❌ divergente"})
fichas["linhas"] = fichas["linhas"].map(fmt_int)
st.dataframe(fichas.drop(columns="integro").rename(columns={"arquivo": "Arquivo", "linhas": "Linhas", "colunas": "Colunas", "sha256": "SHA-256 (fins de linha normalizados)"}),
             hide_index=True)
if not integridade["integro"].all():
    st.error("Um ou mais arquivos não coincidem com o manifesto. Os números exibidos podem não corresponder aos dados auditados.")
datas = manifesto.get("datas", {})
st.caption(f"Manifesto da versão `{manifesto.get('versao', '—')}` (versão anterior: `{manifesto.get('versao_anterior') or '—'}`), gerada em {datas.get('gerado_em_utc', '—')} (UTC) por "
           f"`{manifesto.get('gerador', '—')}`. Situação da validação: **{manifesto.get('situacao_validacao', {}).get('status', '—')}**.")
st.caption(datas.get("nota", ""))
cob = manifesto.get("cobertura", {})
st.markdown("**Última competência nos dados:** "
            f"Sinesp {cob.get('sinesp', {}).get('ultima_competencia', '—')}"
            f"{' (ano ' + str(cob['sinesp']['ano_parcial']) + ' parcial)' if cob.get('sinesp', {}).get('ano_parcial') else ''}"
            f" · SSP/SC violência doméstica {cob.get('ssp_violencia_domestica', {}).get('ultima_competencia', '—')}.")
st.info("**Atualização dos dados:** manual e controlada (verificar → preparar → aprovar). O painel não baixa dados nem executa ETL: exibe uma versão histórica validada. "
        "Veja `documentacao/ATUALIZACAO_DE_DADOS.md` no repositório.")
revisoes = manifesto.get("revisoes_historicas", {})
if revisoes:
    with st.expander("Revisões históricas e versão anterior"):
        for chave, texto in revisoes.items():
            st.markdown(f"- **{chave}:** {texto}")

sinesp = ui.carregar_sinesp()
catalogo = ui.carregar_catalogo()
vd = ui.carregar_violencia_domestica()

c1, c2 = st.columns(2)
with c1:
    st.subheader("Sinesp / MJSP")
    st.markdown(
        f"- **Cobertura:** {ui.periodo_sinesp_texto(manifesto)}"
        f"{' (' + str(cob['sinesp']['ano_parcial']) + ' parcial)' if cob.get('sinesp', {}).get('ano_parcial') else ''}; {fmt_int(len(sinesp))} observações mensais em {len(catalogo)} séries "
        f"(indicador × abrangência).\n"
        f"- **Valores ausentes:** {int(sinesp['valor'].isna().sum())} (nunca convertidos em zero). **Zeros publicados:** {fmt_int(int(sinesp['valor'].eq(0).sum()))}.\n"
        "- **Unidades:** vítimas e mandados cumpridos, mantidos separados. **Abrangências:** Estadual, Polícia Federal (mandados, desde 01/2025) e PRF (mortes no trânsito).\n"
        "- Ausência de cobertura de uma série (ex.: PF antes de 2025) não é zero."
    )
with c2:
    st.subheader("SSP/SC — violência doméstica")
    st.markdown(
        f"- **Cobertura:** janeiro/2023 a dezembro/2024; {fmt_int(len(vd))} observações (9 categorias × 24 meses).\n"
        f"- **Valores ausentes:** 0. **Zeros publicados:** {int(vd['fatos_comunicados'].eq(0).sum())}.\n"
        f"- **Unidade:** {dp.UNIDADE_VD}; não equivale a vítimas, pessoas únicas ou boletins de ocorrência únicos.\n"
        "- Três relatórios de origem (1º e 2º semestres de 2023; ano de 2024)."
    )

st.subheader("Cobertura e ausências por série Sinesp")
cat = catalogo.rename(columns={
    "evento": "Indicador", "abrangencia": "Abrangência", "unidade": "Unidade", "inicio": "Início", "fim": "Fim", "meses_observados": "Meses",
    "meses_com_valor": "Com valor", "meses_valor_zero": "Zeros publicados", "meses_sem_valor": "Sem valor"})
st.dataframe(cat[["Indicador", "Abrangência", "Unidade", "Início", "Fim", "Meses", "Com valor", "Zeros publicados", "Sem valor"]], hide_index=True)

st.subheader("Fontes, condições de uso e rastreabilidade")
for fonte in manifesto.get("fontes", []):
    st.markdown(f"**{fonte['nome']}** — {fonte['descricao']}  \n[{fonte['url']}]({fonte['url']})  \n*Condições de reutilização:* {fonte['condicoes_de_reutilizacao']}")
    licenca = fonte.get("licenca", {})
    if licenca:
        with st.expander(f"Licenças verificadas — {fonte['nome']} (consulta de {licenca.get('data_consulta', '—')})"):
            cat, site = licenca.get("catalogo", {}), licenca.get("site", {})
            st.markdown(f"- **Catálogo de dados:** {cat.get('licenca', '—')} — confirmada na consulta: **{'sim' if cat.get('confirmada_na_consulta') else 'não'}**. {cat.get('observacao', '')}")
            st.markdown(f"- **Licença geral do site:** {site.get('licenca', '—')} — {site.get('escopo', '')}")
            st.markdown(f"- **Condições específicas do recurso:** {licenca.get('condicoes_especificas_do_recurso', '—')}")
    consulta = fonte.get("consulta", {})
    if consulta.get("data_consulta_utc"):
        achados = ", ".join(sorted({a["classificacao"].replace("_", " ") for a in consulta.get("achados", [])})) or "nenhum"
        st.caption(f"Última verificação registrada: {consulta['data_consulta_utc']} (UTC); achados: {achados}")
st.markdown("**Avaliação de reutilização:** " + manifesto.get("avaliacao_de_reutilizacao", "—"))
st.markdown("**Atribuição:** " + manifesto.get("atribuicao", "—"))
st.markdown("**Critérios de seleção e geração**")
for criterio in manifesto.get("criterios", []):
    st.markdown(f"- {criterio}")
origem = manifesto.get("origem_dos_dados", {})
with st.expander("SHA-256 dos arquivos de origem usados na geração (os originais não são distribuídos)"):
    st.write("XLSX Sinesp (por ano):")
    st.dataframe(pd.DataFrame(sorted(origem.get("sinesp_xlsx_sha256", {}).items()), columns=["Ano", "SHA-256"]), hide_index=True)
    st.write("PDFs SSP/SC de violência doméstica:")
    st.dataframe(pd.DataFrame(sorted(origem.get("ssp_pdf_sha256", {}).items()), columns=["Arquivo", "SHA-256"]), hide_index=True)
with st.expander("Rastreabilidade da violência doméstica (216 observações: arquivo, página, tabela, linha, coluna)"):
    rastreio = ui.carregar_rastreio_vd()
    resumo = rastreio.groupby("arquivo_pdf").agg(observacoes=("categoria", "size"), paginas=("pagina_pdf", lambda s: ", ".join(sorted(set(s), key=int)))).reset_index()
    st.dataframe(resumo.rename(columns={"arquivo_pdf": "Relatório (PDF)", "observacoes": "Observações", "paginas": "Páginas das células"}), hide_index=True)

st.subheader("Limitações metodológicas")
st.markdown(
    "- **Sinesp:** observações mensais agregadas; sem taxas populacionais; 2026 parcial; indicadores diferentes (e vítimas × mandados) nunca são somados.\n"
    "- **SSP/SC (violência doméstica):** 'Fato Comunicado' sem definição operacional; grafias “0 Dolosa”/“- Dolosa” unificadas por decisão metodológica do projeto "
    "(sem confirmação oficial); meses atribuídos pela estrutura contínua das tabelas dos PDFs.\n"
    "- **Fora do painel:** Prefeitura/SEPROT (furtos e roubos 2023–2025) e série histórica de homicídios SSP/SC (boletins republicados com 41 divergências em 58 grupos, sem versão definitiva escolhida).\n"
    "- Não há dados por bairro, rua, horário ou corporação.\n"
    "- Os dados brutos (XLSX do Sinesp, PDFs e CSVs da SSP/SC) **não** estão publicados no repositório."
)

with st.expander("Ambiente local (opcional)"):
    acervo = dp.DIRETORIO_DADOS.parents[1] / "dados"
    if acervo.is_dir():
        st.write("O acervo bruto local foi encontrado neste computador. O painel **não** o utiliza.")
        contagens = {p.name: sum(1 for _ in p.rglob("*") if _.is_file()) for p in sorted(acervo.iterdir()) if p.is_dir()}
        st.write({nome: f"{n} arquivo(s)" for nome, n in contagens.items()})
    else:
        st.write("O acervo bruto local não está presente neste ambiente — situação esperada em um clone limpo ou em um deploy. O painel funciona normalmente.")
