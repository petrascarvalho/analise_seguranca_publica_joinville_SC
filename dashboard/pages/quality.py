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

st.title("Qualidade dos dados e metodologia")
st.write(
    "Fonte única **Sinesp/MJSP, Joinville/SC**. Esta página mostra se os arquivos do painel conferem com o manifesto, o que cada série cobre, "
    "como os dados foram tratados e o que não pode ser concluído a partir deles. As linhas são observações mensais agregadas, não ocorrências individuais."
)

sinesp, catalogo = ui.carregar_dados_consistentes()
manifesto = ui.carregar_manifesto()
integridade = ui.verificar_integridade()
cobertura = manifesto.get("cobertura", {})

if integridade["integro"].all():
    st.success(f"Integridade confirmada: os {len(integridade)} arquivos de dados coincidem com o manifesto (versão {manifesto.get('versao', '—')}).")

abas = st.tabs(["Integridade e versão", "Fonte e cobertura", "Métodos e limitações", "Atualização e licenças"])

# ------------------------------------------------------------------------------ integridade e versão
with abas[0]:
    st.subheader("Integridade e hashes (SHA-256)")
    fichas = pd.DataFrame(manifesto["arquivos"])[["arquivo", "linhas", "colunas", "sha256"]]
    fichas = fichas.merge(integridade[["arquivo", "integro"]], on="arquivo", how="left")
    fichas["Integridade"] = fichas["integro"].map({True: "✅ confere com o manifesto", False: "❌ divergente"})
    fichas["linhas"] = fichas["linhas"].map(fmt_int)
    st.dataframe(fichas.drop(columns="integro").rename(columns={"arquivo": "Arquivo", "linhas": "Linhas", "colunas": "Colunas", "sha256": "SHA-256 (fins de linha normalizados)"}), hide_index=True)
    if not integridade["integro"].all():
        st.error("Um ou mais arquivos não coincidem com o manifesto. Os números exibidos podem não corresponder aos dados auditados.")
    st.caption("Verificações feitas ao abrir esta página: esquema e tipos, sem competências repetidas, sem lacunas por série, uma unidade por série, catálogo consistente com os dados e hashes iguais aos do manifesto.")

    st.subheader("Versão, datas e validação")
    datas = manifesto.get("datas", {})
    validacao = manifesto.get("situacao_validacao", {})
    aprovacao = manifesto.get("aprovacao") or {}
    st.markdown(
        f"- **Versão:** `{manifesto.get('versao', '—')}` (versão anterior: `{manifesto.get('versao_anterior') or '—'}`)\n"
        f"- **Data de geração:** {datas.get('gerado_em_utc', '—')} (UTC) · **gerador:** `{manifesto.get('gerador', '—')}`\n"
        f"- **Última consulta à fonte registrada:** {datas.get('ultima_consulta_as_fontes_utc') or 'nenhuma registrada nesta versão'}\n"
        f"- **Situação da validação:** **{validacao.get('status', '—')}** — {validacao.get('descricao', '')}\n"
        f"- **Aprovação:** {('aprovada em ' + aprovacao.get('aprovado_em_utc', '—') + ' (UTC) — ' + aprovacao.get('aprovado_por', '')) if aprovacao else 'versão gerada por procedimento automatizado e validada; sem aprovação registrada'}\n"
        f"- **Última competência disponível:** **{cobertura.get('sinesp', {}).get('ultima_competencia', '—')}**"
        f"{' (ano ' + str(cobertura['sinesp']['ano_parcial']) + ' parcial)' if cobertura.get('sinesp', {}).get('ano_parcial') else ''}"
    )
    st.caption(datas.get("nota", ""))
    for item in validacao.get("verificacoes", []):
        st.markdown(f"  - ✔ {item}")
    informacoes = validacao.get("informacoes") or {}
    if informacoes:
        with st.expander("Resultado detalhado da validação desta versão"):
            st.json(informacoes)
    revisoes = manifesto.get("revisoes_historicas", {})
    if revisoes:
        with st.expander("Revisões históricas e comparação com a versão anterior"):
            for chave, texto in revisoes.items():
                st.markdown(f"- **{chave}:** {texto}")


# ------------------------------------------------------------------------------ fonte e cobertura
with abas[1]:
    st.subheader("Fonte oficial e método de obtenção")
    for fonte in manifesto.get("fontes", []):
        st.markdown(f"**{fonte['nome']}** — {fonte['descricao']}  \n[{fonte['url']}]({fonte['url']})")
        publicacao = fonte.get("publicacao") or {}
        if publicacao.get("pagina_atualizada_em"):
            st.caption(f"Datas informadas pela página da fonte — publicada em {publicacao.get('pagina_publicada_em', '—')}; atualizada em {publicacao['pagina_atualizada_em']} "
                       "(informação da página, não prova alteração de valores).")
    st.markdown("**Método de obtenção:** " + manifesto.get("metodo_de_obtencao", "—"))
    origem = manifesto.get("origem_dos_dados", {})
    with st.expander("SHA-256 e tamanho dos XLSX oficiais usados nesta versão (os originais não são distribuídos)"):
        xlsx = pd.DataFrame([{"Ano": a, "SHA-256": h, "Bytes": fmt_int(origem.get("sinesp_xlsx_bytes", {}).get(a))} for a, h in sorted(origem.get("sinesp_xlsx_sha256", {}).items())])
        st.dataframe(xlsx, hide_index=True)

    # ---------------------------------------------------------------------------- cobertura por indicador
    st.subheader("Cobertura por indicador, zeros e ausências")
    unidades = manifesto.get("unidades", {})
    st.markdown("**Unidades:** " + " · ".join(f"*{u}* = {d}" for u, d in unidades.items()) + ". Vítimas e mandados nunca são somados.")
    cat = catalogo.rename(columns={
        "evento": "Indicador", "abrangencia": "Abrangência", "unidade": "Unidade", "inicio": "Início", "fim": "Última competência", "meses_observados": "Meses",
        "meses_com_valor": "Com valor", "meses_valor_zero": "Zeros publicados", "meses_sem_valor": "Sem valor"})
    st.dataframe(cat[["Indicador", "Abrangência", "Unidade", "Início", "Última competência", "Meses", "Com valor", "Zeros publicados", "Sem valor"]], hide_index=True)
    total_ausentes = int(sinesp["valor"].isna().sum())
    st.markdown(
        f"- **Total:** {fmt_int(len(sinesp))} observações mensais em {len(catalogo)} séries; **valores ausentes:** {total_ausentes} (nunca convertidos em zero); "
        f"**zeros publicados:** {fmt_int(int(sinesp['valor'].eq(0).sum()))}.\n"
        "- Séries com última competência diferente (p.ex. a PRF) são exibidas até a sua última competência, sem preenchimento; a PF só tem linhas a partir da sua primeira competência."
    )


# ------------------------------------------------------------------------------ métodos e limitações
with abas[2]:
    st.subheader("Regras do ETL")
    for regra in manifesto.get("regras_etl", []):
        st.markdown(f"- {regra}")

    st.subheader("Regras das estatísticas e dos gráficos")
    st.markdown(
        "- **Soma** só quando todos os meses presentes têm valor; **desvio-padrão** descritivo (`ddof=0`); média e mediana sobre os meses com valor.\n"
        "- **Variação percentual** só com base positiva (n/a quando a base é zero); a diferença absoluta é sempre informada.\n"
        "- **Anos parciais** nunca são comparados com anos completos: compara-se janeiro até a última competência equivalente.\n"
        "- **Rankings** ordenam séries dentro de uma única unidade, sem total entre indicadores.\n"
        "- Gráficos começam o eixo em zero, usam valores inteiros, mostram fonte e unidade e usam a mesma cor para cada ano."
    )

    # ------------------------------------------------------------------------------------- limitações
    st.subheader("Limitações")
    st.markdown(
        "- Registros administrativos agregados do Sinesp: não medem toda a criminalidade ocorrida nem permitem inferir causalidade.\n"
        "- Sem taxas populacionais (falta base demográfica oficial compatível), sem dados por bairro, rua, horário ou corporação.\n"
        "- As séries Estadual, PF e PRF têm abrangências e coberturas distintas e não são somadas; mandados não são pessoas únicas.\n"
        "- Revisões de valores históricos pela fonte podem ocorrer: são detectadas na preparação de uma atualização e só entram com aprovação específica.\n"
        "- Os XLSX originais não são distribuídos; a reprodução exige baixá-los da fonte oficial.\n"
        "- Contagens pequenas geram variações percentuais instáveis; observe a magnitude absoluta."
    )


# ------------------------------------------------------------------------------ atualização e licenças
with abas[3]:
    st.subheader("Procedimento de atualização dos dados")
    st.markdown(
        "Manual e controlado — o painel **não** baixa dados, não executa ETL e não se atualiza sozinho: **verificar** (consulta metadados da fonte e classifica indícios) → "
        "**preparar** (candidata isolada a partir dos XLSX oficiais, com validação e comparação) → **aprovar** (promoção com versão anterior preservada e reversão). "
        "Uma atualização inválida não substitui a versão ativa. Procedimento completo em `documentacao/analises/ATUALIZACAO_DE_DADOS.md`."
    )
    st.subheader("Condições de reutilização e atribuição")
    for fonte in manifesto.get("fontes", []):
        licenca = fonte.get("licenca", {})
        cat_l, site = licenca.get("catalogo", {}), licenca.get("site", {})
        st.markdown(f"- **Catálogo de dados:** {cat_l.get('licenca', '—')} — confirmada na consulta de {licenca.get('data_consulta', '—')}: **{'sim' if cat_l.get('confirmada_na_consulta') else 'não'}**. {cat_l.get('observacao', '')}")
        st.markdown(f"- **Licença geral do site:** {site.get('licenca', '—')} — {site.get('escopo', '')}")
        st.markdown(f"- **Condições específicas do recurso:** {licenca.get('condicoes_especificas_do_recurso', '—')}")
    st.markdown("**Avaliação de reutilização:** " + manifesto.get("avaliacao_de_reutilizacao", "—"))
    st.markdown("**Atribuição:** " + manifesto.get("atribuicao", "—"))

    with st.expander("Ambiente local (opcional)"):
        acervo = dp.DIRETORIO_DADOS.parents[1] / "dados"
        if acervo.is_dir():
            st.write("O acervo bruto local foi encontrado neste computador. O painel **não** o utiliza.")
        else:
            st.write("O acervo bruto local não está presente neste ambiente — situação esperada em um clone limpo ou em um deploy. O painel funciona normalmente.")
