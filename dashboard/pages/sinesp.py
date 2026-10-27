import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard import calculos, graficos, ui  # noqa: E402
from dashboard.formatacao import NOMES_MESES, fmt_dec, fmt_dif, fmt_int, fmt_pct  # noqa: E402

st.title("Indicadores Sinesp / MJSP — Joinville/SC")
sinesp, catalogo = ui.carregar_dados_consistentes()
_ini, _fim = sinesp.assign(c=sinesp["ano"] * 100 + sinesp["mes"])["c"].agg(["min", "max"])
st.caption(f"Fonte: MJSP / Sinesp VDE. Município de Joinville/SC, {NOMES_MESES[int(_ini) % 100 - 1]}/{int(_ini) // 100} a {NOMES_MESES[int(_fim) % 100 - 1]}/{int(_fim) // 100}. "
           "Contagens mensais publicadas (agregadas).")
ui.mostrar_versao_dos_dados()

# ------------------------------------------------------------------------------------------ filtros
eventos = sorted(catalogo["evento"].unique())
f1, f2, f3 = st.columns([2.4, 1.4, 1.6])
evento = f1.selectbox("Indicador", eventos, index=eventos.index("Homicídio doloso") if "Homicídio doloso" in eventos else 0)
abrangencias = catalogo.loc[catalogo["evento"].eq(evento), "abrangencia"].tolist()
abrangencia = f2.selectbox("Abrangência", abrangencias, help="Estadual, Polícia Federal e PRF são séries distintas e não são somadas.")
anos_disponiveis = sorted(int(a) for a in sinesp["ano"].unique())
ano_ini, ano_fim = f3.select_slider("Período (anos)", options=anos_disponiveis, value=(anos_disponiveis[0], anos_disponiveis[-1]))
anos_sel = list(range(ano_ini, ano_fim + 1))

ficha = catalogo.loc[catalogo["evento"].eq(evento) & catalogo["abrangencia"].eq(abrangencia)].iloc[0]
serie = calculos.serie_sinesp(sinesp, evento, abrangencia)
unidade = ficha["unidade"]
unidade_curta = unidade.split(" (")[0]
st.markdown(f"**Unidade:** {unidade} · **Natureza:** {ficha['natureza']} · **Cobertura da série:** {ficha['inicio']} a {ficha['fim']}")
if abrangencia == "Polícia Federal":
    st.warning(f"Mandados da Polícia Federal só aparecem a partir de {NOMES_MESES[int(ficha['inicio'][5:]) - 1]}/{ficha['inicio'][:4]}; os anos anteriores não têm cobertura (ausência de série, e não zero).")
if abrangencia == "Polícia Rodoviária Federal":
    st.info("A série da PRF pode terminar em competência diferente das demais; ela é apresentada até a sua última competência, sem preenchimento.")
ano_final_serie, mes_final_serie = calculos.ultima_competencia_da_serie(serie)
serie_parcial = mes_final_serie < 12
nome_periodo = f"janeiro–{NOMES_MESES[mes_final_serie - 1]}" if serie_parcial else "ano completo (12 meses)"
if serie_parcial and ano_fim == ano_final_serie:
    st.info(ui.aviso_ano_parcial(ano_final_serie, mes_final_serie))

anual = calculos.tabela_anual_sinesp(serie)
anual_sel = anual.loc[anual["ano"].isin(anos_sel)].sort_values("ano")
completos = anual_sel.loc[anual_sel["cobertura"].eq("ano completo") & anual_sel["soma"].notna()]
periodo = calculos.comparacao_periodo_sinesp(serie, mes_final_serie)
periodo_sel = periodo.loc[periodo["ano"].isin(anos_sel) & periodo["soma"].notna()].sort_values("ano")
serie_sel = serie.loc[serie["ano"].isin(anos_sel)]

# ------------------------------------------------------------------------------------- indicadores
st.subheader("Resumo")
k1, k2, k3 = st.columns(3)
if len(completos):
    ultimo = completos.iloc[-1]
    delta = None
    if len(completos) > 1:
        anterior = completos.iloc[-2]
        delta = f"{fmt_dif(int(ultimo['soma']) - int(anterior['soma']))} vs {int(anterior['ano'])}" if int(anterior["ano"]) == int(ultimo["ano"]) - 1 else None
    k1.metric(f"Último ano completo: {int(ultimo['ano'])} ({unidade_curta})", fmt_int(ultimo["soma"]), delta=delta, delta_color="off",
              help="Soma dos 12 meses publicados. A diferença compara apenas com o ano completo imediatamente anterior.")
else:
    k1.metric("Último ano completo", "—", help="Nenhum ano completo no período selecionado.")
if len(periodo_sel) and serie_parcial:
    ult_p = periodo_sel.iloc[-1]
    ant = periodo_sel.loc[periodo_sel["ano"].eq(int(ult_p["ano"]) - 1)]
    delta_p = f"{fmt_dif(int(ult_p['soma']) - int(ant.iloc[0]['soma']))} vs {nome_periodo} de {int(ult_p['ano']) - 1}" if len(ant) else None
    k2.metric(f"{nome_periodo.capitalize()} de {int(ult_p['ano'])} ({unidade_curta})", fmt_int(ult_p["soma"]), delta=delta_p, delta_color="off",
              help=f"Períodos equivalentes: os dois anos têm os mesmos {mes_final_serie} meses.")
else:
    k2.metric(nome_periodo.capitalize(), "—", help="A série tem o último ano completo: não há período parcial a comparar.")
resumo = calculos.resumo_serie_sinesp(serie_sel)
k3.metric("Meses com valor publicado", f"{resumo['meses_com_valor']} de {resumo['meses_observados']}",
          help=f"Meses com valor zero publicado: {resumo['meses_valor_zero']}. Meses sem valor: {resumo['meses_sem_valor']} (nunca preenchidos).")

abas = st.tabs(["Evolução", "Comparações", "Estatísticas descritivas", "Ranking por indicador", "Figuras da Etapa 10", "Indicadores e interpretação"])

# ------------------------------------------------------------------------------------------ evolução
with abas[0]:
    figura = graficos.figura_serie_anual_sinesp(sinesp, evento, abrangencia, anos_sel)
    if figura is None:
        st.info("Não há ano completo no período selecionado para a série anual. Use as abas de comparações ou a série mensal abaixo.")
    else:
        ui.mostrar_figura(figura, "Evolução anual — somente anos completos (12 meses). Eixo vertical iniciado em zero.")
    mensal = graficos.figura_mensal_sinesp(sinesp, evento, abrangencia, anos_sel)
    if mensal is not None:
        ui.mostrar_figura(mensal, "Evolução mensal: uma linha por ano, com a mesma cor em todas as figuras. Valores publicados, sem preenchimento.")
    variacoes = calculos.variacoes_anuais(serie.loc[serie["ano"].isin(anos_sel)])
    st.markdown("**Variação entre anos completos consecutivos**")
    if variacoes.empty:
        st.caption("Não há dois anos completos consecutivos no período selecionado.")
    else:
        tabela = pd.DataFrame({
            "Ano anterior": variacoes["ano_anterior"], "Ano": variacoes["ano"], f"Total anterior ({unidade_curta})": variacoes["valor_anterior"].map(fmt_int),
            f"Total ({unidade_curta})": variacoes["valor"].map(fmt_int), "Diferença absoluta": variacoes["diferenca_absoluta"].map(fmt_dif),
            "Variação %": variacoes["variacao_percentual"].map(fmt_pct)})
        st.dataframe(tabela, hide_index=True)
        st.caption("Variação percentual só é calculada com base positiva (n/a = base zero). Em contagens pequenas, observe a diferença absoluta. Não indica causa.")

# ------------------------------------------------------------------------------------------ comparações
with abas[1]:
    st.markdown("**Anos completos**")
    tabela = anual_sel[["ano", "cobertura", "meses_presentes", "meses_com_valor", "soma"]].copy()
    tabela["soma"] = tabela["soma"].map(fmt_int)
    tabela.columns = ["Ano", "Cobertura", "Meses presentes", "Meses com valor", f"Soma ({unidade_curta})"]
    st.dataframe(tabela, hide_index=True)
    if serie_parcial:
        st.caption(f"A linha de {ano_final_serie} é parcial ({nome_periodo}) e não deve ser comparada com anos completos. Sem total entre indicadores ou abrangências.")
    anos_completos = [int(a) for a in completos["ano"]]
    if len(anos_completos) >= 2:
        ca, cb = st.columns(2)
        ano_a = ca.selectbox("Ano A (completo)", anos_completos, index=0, key="ano_a")
        ano_b = cb.selectbox("Ano B (completo)", anos_completos, index=len(anos_completos) - 1, key="ano_b")
        comparacao = calculos.comparar_anos_completos(serie, ano_a, ano_b)
        if comparacao is not None and ano_a != ano_b:
            st.markdown(f"**{ano_a} × {ano_b}:** {fmt_int(comparacao['valor_a'])} × {fmt_int(comparacao['valor_b'])} {unidade_curta} · diferença {fmt_dif(comparacao['diferenca_absoluta'])} · "
                        f"variação {fmt_pct(comparacao['variacao_percentual'])}" + (" (percentual não aplicável: base zero)" if pd.isna(comparacao["variacao_percentual"]) else ""))
    st.markdown("**Períodos equivalentes (janeiro até a última competência da série)**")
    if serie_parcial:
        figura = graficos.figura_periodo_sinesp(sinesp, evento, abrangencia, anos_sel, mes_final_serie)
        if figura is None:
            st.info(f"Não há período {nome_periodo} completo no intervalo selecionado para esta série.")
        else:
            ui.mostrar_figura(figura, f"Períodos de igual duração ({mes_final_serie} meses). Cores por ano consistentes.")
            tabela = periodo_sel[["ano", "periodo", "meses_com_valor", "soma"]].copy()
            tabela["soma"] = tabela["soma"].map(fmt_int)
            tabela.columns = ["Ano", "Período", "Meses com valor", f"Soma ({unidade_curta})"]
            st.dataframe(tabela, hide_index=True)
        r = calculos.comparacao_ultimo_periodo_sinesp(serie)
        if r is not None:
            st.markdown(f"**{r['periodo'].capitalize()}, {r['ano_atual']} × {r['ano_anterior']}:** {fmt_int(r['valor_atual'])} × {fmt_int(r['valor_anterior'])} · "
                        f"diferença {fmt_dif(r['diferenca_absoluta'])} · variação {fmt_pct(r['variacao_percentual'])}"
                        + (" (percentual não aplicável: base zero)" if pd.isna(r["variacao_percentual"]) else ""))
            st.caption("Variação descritiva entre períodos equivalentes; em contagens pequenas, observe a magnitude absoluta. Não indica causa.")
    else:
        st.caption("O último ano desta série está completo; não há período parcial a comparar.")

# ------------------------------------------------------------------------------------------ estatísticas
with abas[2]:
    est = calculos.estatisticas_por_ano(serie_sel)
    st.caption(f"Estatísticas descritivas dos valores MENSAIS de cada ano ({unidade_curta}). Desvio-padrão descritivo (ddof=0); zero publicado é observação, ausência nunca é preenchida.")
    exib = pd.DataFrame({
        "Ano": est["ano"], "Cobertura": est["cobertura"], "Meses": est["meses_observados"], "Soma do ano": est["soma"].map(fmt_int),
        "Média mensal": est["media_mensal"].map(fmt_dec), "Mediana": est["mediana_mensal"].map(fmt_dec), "Mín.": est["minimo"].map(fmt_int),
        "Máx.": est["maximo"].map(fmt_int), "Desvio-padrão": est["desvio_padrao_ddof0"].map(fmt_dec), "Meses com zero": est["meses_valor_zero"]})
    st.dataframe(exib, hide_index=True)
    st.markdown("**Todo o período selecionado**")
    geral = pd.DataFrame([{
        "Meses observados": resumo["meses_observados"], "Média mensal": fmt_dec(resumo["media_mensal"]), "Mediana": fmt_dec(resumo["mediana_mensal"]),
        "Mínimo": fmt_int(resumo["minimo"]), "Máximo": fmt_int(resumo["maximo"]), "Desvio-padrão (ddof=0)": fmt_dec(resumo["desvio_padrao_ddof0"]),
        "Meses com zero": resumo["meses_valor_zero"], "Meses sem valor": resumo["meses_sem_valor"]}])
    st.dataframe(geral, hide_index=True)
    st.caption("A soma do ano só aparece quando todos os meses presentes têm valor. Em séries com muitos zeros, a média e a mediana descrevem contagens pequenas.")

# ---------------------------------------------------------------------------------------------- ranking
with abas[3]:
    comuns = calculos.anos_completos_comuns(sinesp)
    if not comuns:
        st.info("Nenhum ano está completo em todas as séries presentes.")
    else:
        ano_rank = st.selectbox("Ano completo", comuns, index=len(comuns) - 1, key="ano_rank")
        unidade_rank = st.radio("Unidade (os rankings não misturam unidades)", sorted(sinesp["unidade"].unique()), horizontal=True, key="unidade_rank")
        ranking = calculos.ranking_por_unidade(sinesp, int(ano_rank), unidade_rank)
        if ranking.empty:
            st.info("Nenhuma série com ano completo nesta unidade.")
        else:
            figura = graficos.figura_ranking_sinesp(ranking, int(ano_rank))
            ui.mostrar_figura(figura, "Ordenação das séries dentro de uma única unidade. Não há total entre indicadores nem entre abrangências.")
            tabela = ranking.rename(columns={"evento": "Indicador", "abrangencia": "Abrangência", "unidade": "Unidade", "soma": f"Total de {int(ano_rank)}"})
            tabela[f"Total de {int(ano_rank)}"] = tabela[f"Total de {int(ano_rank)}"].map(fmt_int)
            st.dataframe(tabela, hide_index=True)
        st.caption("Séries com cobertura diferente (p.ex. PF a partir de 2025) só entram nos anos em que estão completas.")

# ---------------------------------------------------------------------------------- figuras Etapa 10
with abas[4]:
    st.write("As quatro figuras da Etapa 10 do roteiro, recriadas a partir dos dados curados (vítimas, abrangência Estadual; anos completos 2020–2025 e janeiro–agosto de 2020 a 2026). "
             "Elas são fixas e independem dos filtros acima.")
    try:
        figuras = graficos.figuras_sinesp_etapa10(sinesp)
    except ValueError as erro:
        st.error(f"Figuras indisponíveis: {erro}")
        figuras = {}
    nomes = list(figuras)
    for i in range(0, len(nomes), 2):
        colunas = st.columns(2)
        for coluna, nome in zip(colunas, nomes[i:i + 2]):
            with coluna:
                ui.mostrar_figura(figuras[nome])

# ----------------------------------------------------------------------------------- indicadores
with abas[5]:
    st.caption("Catálogo das séries (indicador × abrangência) com unidade, medida de origem, cobertura e limitações.")
    cat = catalogo.rename(columns={
        "evento": "Indicador", "abrangencia": "Abrangência", "unidade": "Unidade", "natureza": "Natureza", "medida_origem": "Medida de origem",
        "inicio": "Início", "fim": "Fim", "meses_observados": "Meses", "meses_com_valor": "Com valor", "meses_valor_zero": "Zeros publicados",
        "meses_sem_valor": "Sem valor", "limitacoes": "Limitações"})
    st.dataframe(cat, hide_index=True)
    st.markdown("**Como interpretar (observado × hipótese)**")
    st.markdown(
        "- **Observado:** valores publicados pelo Sinesp para Joinville (contagens mensais agregadas) e as diferenças calculadas entre eles.\n"
        "- **Não é afirmado:** causa das variações, efeito de políticas ou de ações policiais, subnotificação ou o total de crimes ocorridos.\n"
        "- **Hipóteses metodológicas:** nenhuma é assumida; variações pequenas em contagens baixas podem refletir poucas unidades.\n"
        "- **Vítimas × mandados:** conceitos distintos, nunca somados. Feminicídio e tentativa são séries separadas e não se somam a homicídio.\n"
        "- **Zero publicado** é uma observação; ausência de série (p.ex. PF antes de 2025) não é zero.\n"
        "- Linhas da base original são observações mensais agregadas, não ocorrências individuais."
    )
