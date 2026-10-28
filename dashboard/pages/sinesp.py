"""Página "Indicadores Sinesp": filtros, resumo, gráficos e tabelas da série escolhida.

Comandos do Streamlit usados nesta página (o arquivo é executado de novo a cada interação):
    • st.toggle — chave liga/desliga (modo compacto); o valor fica em st.session_state["modo_compacto"].
    • st.selectbox — lista suspensa (categoria, indicador, abrangência); devolve a opção escolhida.
    • st.select_slider — controle deslizante de intervalo (anos e meses); devolve (início, fim).
    • st.metric — cartão com um número e a diferença em relação ao período anterior (delta).
    • st.tabs — abas; o conteúdo de cada uma fica dentro de "with abas[i]:".
    • st.dataframe — tabela interativa; st.pyplot — mostra uma figura do Matplotlib; st.expander — seção recolhível.
    • st.info, st.warning e st.caption — mensagens e notas metodológicas.

Os números vêm de dashboard/calculos.py e as figuras de dashboard/graficos.py; esta página só organiza a apresentação.
"""

import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard import calculos, graficos, ui  # noqa: E402
from dashboard.formatacao import ABREV_MESES, NOMES_MESES, fmt_dec, fmt_dif, fmt_int, fmt_pct  # noqa: E402

st.title("Indicadores Sinesp / MJSP — Joinville/SC")
sinesp, catalogo = ui.carregar_dados_consistentes()
_ini, _fim = sinesp.assign(c=sinesp["ano"] * 100 + sinesp["mes"])["c"].agg(["min", "max"])
st.caption(f"Fonte: MJSP / Sinesp VDE. Município de Joinville/SC, {NOMES_MESES[int(_ini) % 100 - 1]}/{int(_ini) // 100} a {NOMES_MESES[int(_fim) % 100 - 1]}/{int(_fim) // 100}. "
           "Contagens mensais publicadas (agregadas). Escolha a série nos filtros e navegue pelas abas.")
st.toggle("Visualização compacta (celular)", key="modo_compacto",
          help="Gráficos mais estreitos, com fontes maiores, menos marcas nos eixos e os textos explicativos abaixo da imagem. A aplicação não detecta o tamanho "
               "da tela: ative em telas pequenas. Os números e as tabelas são os mesmos nos dois modos.")
graficos.definir_modo_compacto(ui.modo_compacto())  # vale para todas as figuras criadas nesta execução

# ------------------------------------------------------------------------------------------ filtros
catalogo = catalogo.assign(categoria=catalogo["natureza"].str.split(":").str[0].str.strip())
# Linha 1 dos filtros: Categoria → Indicador → Abrangência. A categoria (natureza do indicador) filtra a lista de indicadores, e o indicador
# define as abrangências disponíveis. Cada st.selectbox mostra uma lista suspensa e devolve a opção escolhida; a "key" identifica o
# controle e mantém a escolha entre as interações.
caixa_filtros = st.container(border=True)  # filtros num bloco com borda; conteúdo e chaves não mudam
caixa_filtros.markdown("**Filtros**")
f1, f2, f3 = caixa_filtros.columns([1.4, 2.4, 1.6])
categorias = ["Todas"] + sorted(catalogo["categoria"].unique())
categoria = f1.selectbox("Categoria", categorias, key="categoria", help="Natureza do indicador no catálogo (criminal, atividade policial, complementar). Filtra a lista de indicadores.")
eventos = sorted(catalogo.loc[catalogo["categoria"].eq(categoria) | (categoria == "Todas"), "evento"].unique())
evento = f2.selectbox("Indicador", eventos, key="indicador", index=eventos.index("Homicídio doloso") if "Homicídio doloso" in eventos else 0)
abrangencias = catalogo.loc[catalogo["evento"].eq(evento), "abrangencia"].tolist()
abrangencia = f3.selectbox("Abrangência", abrangencias, key="abrangencia", help="Estadual, Polícia Federal e PRF são séries distintas e não são somadas.")
anos_disponiveis = sorted(int(a) for a in sinesp["ano"].unique())
g1, g2 = caixa_filtros.columns(2)  # linha 2: anos e meses
ano_ini, ano_fim = g1.select_slider("Período (anos)", options=anos_disponiveis, value=(anos_disponiveis[0], anos_disponiveis[-1]))
anos_sel = list(range(ano_ini, ano_fim + 1))
mes_ini, mes_fim = g2.select_slider("Meses", options=list(range(1, 13)), value=(1, 12), format_func=lambda m: ABREV_MESES[m - 1],
                                    help="Vale para o resumo, o mapa de calor, a evolução mensal, as estatísticas, o boxplot, a distribuição e os outliers. "
                                         "Totais anuais, comparações de anos completos, média móvel, acumulado e sazonalidade usam sempre os 12 meses.")
filtro_meses = (mes_ini, mes_fim) != (1, 12)
meses_sel = list(range(mes_ini, mes_fim + 1))
_MESES_TEXTO = "janeiro–dezembro (12 meses)" if not filtro_meses else f"{NOMES_MESES[mes_ini - 1]}–{NOMES_MESES[mes_fim - 1]} ({len(meses_sel)} meses)"
st.markdown(f"**Filtros ativos:** categoria **{categoria}** · indicador **{evento}** · abrangência **{abrangencia}** · anos **{ano_ini}–{ano_fim}** · meses **{_MESES_TEXTO}**"
            f" · visualização **{'compacta' if ui.modo_compacto() else 'completa'}**")


def aviso_ano_completo() -> None:
    """Identifica as análises que usam os 12 meses mesmo com o filtro de meses ativo (nunca somam alguns meses como total anual)."""
    if filtro_meses:
        st.caption("Análise de ano completo (12 meses): não usa o filtro de meses. Totais anuais são sempre a soma dos 12 meses.")

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
serie_mes = serie_sel.loc[serie_sel["mes"].isin(meses_sel)]  # período (anos) e meses escolhidos
sinesp_mes = sinesp.loc[sinesp["mes"].isin(meses_sel)]
if filtro_meses:
    st.caption(f"Filtro de meses ativo: {ABREV_MESES[mes_ini - 1]}–{ABREV_MESES[mes_fim - 1]}. Valem para os resultados mensais; anos completos e acumulados continuam com os 12 meses.")

# ------------------------------------------------------------------------------------- indicadores
st.subheader("Resumo")
k1, k2, k3 = st.container(border=True).columns(3)  # os três números do recorte, num bloco destacado
soma_meses = calculos.soma_no_periodo(serie, mes_ini, mes_fim)
soma_meses = soma_meses.loc[soma_meses["ano"].isin(anos_sel) & soma_meses["soma"].notna()]
if filtro_meses:  # com filtro de meses, o KPI principal é a soma desses meses no último ano em que todos foram publicados
    if len(soma_meses):
        ultimo_m = soma_meses.iloc[-1]
        anterior_m = soma_meses.loc[soma_meses["ano"].eq(int(ultimo_m["ano"]) - 1)]
        dif_m = int(ultimo_m["soma"]) - int(anterior_m.iloc[0]["soma"]) if len(anterior_m) else None
        delta_m = f"{fmt_dif(dif_m)} vs {int(ultimo_m['ano']) - 1}" if dif_m is not None else None
        k1.metric(f"{ABREV_MESES[mes_ini - 1]}–{ABREV_MESES[mes_fim - 1]} de {int(ultimo_m['ano'])} ({unidade_curta})", fmt_int(ultimo_m["soma"]), delta=delta_m, delta_color="off", delta_arrow=ui.direcao_da_seta(dif_m),
                  help="Soma dos meses selecionados; só entra o ano com todos esses meses publicados. A diferença compara com o mesmo intervalo do ano anterior.")
    else:
        k1.metric("Soma dos meses selecionados", "—", help="Nenhum ano do período tem todos os meses selecionados publicados.")
elif len(completos):
    ultimo = completos.iloc[-1]
    delta, dif_anual = None, None
    if len(completos) > 1:
        anterior = completos.iloc[-2]
        if int(anterior["ano"]) == int(ultimo["ano"]) - 1:
            dif_anual = int(ultimo["soma"]) - int(anterior["soma"])
            delta = f"{fmt_dif(dif_anual)} vs {int(anterior['ano'])}"
    k1.metric(f"Último ano completo: {int(ultimo['ano'])} ({unidade_curta})", fmt_int(ultimo["soma"]), delta=delta, delta_color="off", delta_arrow=ui.direcao_da_seta(dif_anual),
              help="Soma dos 12 meses publicados. A diferença compara apenas com o ano completo imediatamente anterior.")
else:
    k1.metric("Último ano completo", "—", help="Nenhum ano completo no período selecionado.")
if filtro_meses:
    k2.metric("Meses filtrados", f"{len(meses_sel)} de 12", help="Intervalo de meses escolhido no filtro.")
elif len(periodo_sel) and serie_parcial:
    ult_p = periodo_sel.iloc[-1]
    ant = periodo_sel.loc[periodo_sel["ano"].eq(int(ult_p["ano"]) - 1)]
    dif_p = int(ult_p["soma"]) - int(ant.iloc[0]["soma"]) if len(ant) else None
    delta_p = f"{fmt_dif(dif_p)} vs {nome_periodo} de {int(ult_p['ano']) - 1}" if dif_p is not None else None
    k2.metric(f"{nome_periodo.capitalize()} de {int(ult_p['ano'])} ({unidade_curta})", fmt_int(ult_p["soma"]), delta=delta_p, delta_color="off", delta_arrow=ui.direcao_da_seta(dif_p),
              help=f"Períodos equivalentes: os dois anos têm os mesmos {mes_final_serie} meses.")
else:
    k2.metric(nome_periodo.capitalize(), "—", help="A série tem o último ano completo: não há período parcial a comparar.")
resumo = calculos.resumo_serie_sinesp(serie_mes)
k3.metric("Meses com valor publicado", f"{resumo['meses_com_valor']} de {resumo['meses_observados']}",
          help=f"Meses com valor zero publicado: {resumo['meses_valor_zero']}. Meses sem valor: {resumo['meses_sem_valor']} (nunca preenchidos).")

# Abas com execução preguiçosa (Streamlit 1.66): só a aba selecionada é calculada e desenhada (cada figura leva ~0,3 s para virar PNG).
abas = st.tabs(["Evolução", "Comparações", "Padrões e tendência", "Estatística e outliers", "Indicadores e interpretação"], key="aba_analise", on_change="rerun")

# ------------------------------------------------------------------------------ tabelas verificáveis dos gráficos
def _num(valor) -> str:
    return fmt_int(valor) if pd.notna(valor) and float(valor) == int(float(valor)) else fmt_dec(valor)


def tabela_ano_mes(quadro: pd.DataFrame) -> pd.DataFrame:
    exibicao = quadro.copy()
    exibicao.columns = list(ABREV_MESES)
    exibicao = exibicao.apply(lambda coluna: coluna.map(fmt_int))
    return exibicao.rename_axis("Ano").reset_index()


def tabela_quartis(quadro: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "Ano": quadro["ano"], "Cobertura": quadro["cobertura"], "Meses": quadro["n"], "Mín.": quadro["minimo"].map(_num), "Q1": quadro["q1"].map(_num),
        "Mediana": quadro["mediana"].map(_num), "Q3": quadro["q3"].map(_num), "Máx.": quadro["maximo"].map(_num), "IQR": quadro["iqr"].map(_num),
        "Limite inferior": quadro["limite_inferior"].map(_num), "Limite superior": quadro["limite_superior"].map(_num),
        "Bigode inferior": quadro["bigode_inferior"].map(_num), "Bigode superior": quadro["bigode_superior"].map(_num),
        "Pontos fora": quadro.apply(lambda r: "IQR = 0 (não interpretado)" if r["iqr_zero"] else (", ".join(_num(v) for v in r["valores_fora"]) or "—"), axis=1)})



# ------------------------------------------------------------------------------------------------ 1. evolução
with abas[0]:
    if abas[0].open:
        st.caption("Como o indicador muda ao longo do tempo: total de cada ano completo e valores mês a mês. Os totais anuais usam sempre os 12 meses.")
        st.markdown("**Total por ano**")
        aviso_ano_completo()
        figura = graficos.figura_serie_anual_sinesp(sinesp, evento, abrangencia, anos_sel)
        if figura is None:
            st.info("Não há ano completo no período selecionado para a série anual. Use a série mensal, a média móvel ou o acumulado abaixo.")
        else:
            tabela = completos[["ano", "soma"]].assign(soma=lambda t: t["soma"].map(fmt_int)).rename(columns={"ano": "Ano", "soma": f"Soma ({unidade_curta})"})
            ui.mostrar_figura(figura, "Evolução anual — somente anos completos (12 meses). Eixo vertical iniciado em zero.", tabela)
        st.divider()
        st.markdown("**Valores mensais**")
        anos_mensal = anos_sel
        if ui.modo_compacto() and len(anos_sel) > 3:  # muitas linhas em tela estreita: o usuário escolhe, com aviso explícito (nada é ocultado em silêncio)
            anos_mensal = st.multiselect("Anos exibidos na evolução mensal", anos_sel, default=anos_sel[-3:], key=f"anos_mensal_{anos_sel[0]}_{anos_sel[-1]}",
                                         help="No modo compacto, três anos por vez deixam o gráfico legível. Inclua outros anos quando quiser.")
            st.caption(f"Exibindo {len(anos_mensal)} de {len(anos_sel)} anos do período selecionado ({', '.join(str(a) for a in anos_mensal) or 'nenhum'}). "
                       "Os demais anos continuam na tabela da série e nos demais gráficos.")
        mensal = graficos.figura_mensal_sinesp(sinesp_mes, evento, abrangencia, anos_mensal) if anos_mensal else None
        if not anos_mensal:
            st.info("Selecione ao menos um ano para ver a evolução mensal.")
        if mensal is not None:
            ui.mostrar_figura(mensal, "Evolução mensal: uma linha por ano, com a mesma cor em todas as figuras. Valores publicados, sem preenchimento.",
                              tabela_ano_mes(calculos.quadro_ano_mes(serie_mes.loc[serie_mes["ano"].isin(anos_mensal)])))
        st.divider()
        variacoes = calculos.variacoes_anuais(serie.loc[serie["ano"].isin(anos_sel)])
        aviso_ano_completo()
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

# ------------------------------------------------------------------------------------------------ 2. comparações
with abas[1]:
    if abas[1].open:
        st.caption("Comparações entre anos completos, entre períodos de igual duração (o ano parcial só se compara com o mesmo intervalo dos anos anteriores) e com as demais séries da mesma unidade.")
        aviso_ano_completo()
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
        aviso_ano_completo()
        st.divider()
        st.markdown("**Períodos equivalentes (janeiro até a última competência da série)**")
        if serie_parcial:
            tabela = periodo_sel[["ano", "periodo", "meses_com_valor", "soma"]].copy()
            tabela["soma"] = tabela["soma"].map(fmt_int)
            tabela.columns = ["Ano", "Período", "Meses com valor", f"Soma ({unidade_curta})"]
            figura = graficos.figura_periodo_sinesp(sinesp, evento, abrangencia, anos_sel, mes_final_serie)
            if figura is None:
                st.info(f"Não há período {nome_periodo} completo no intervalo selecionado para esta série.")
            else:
                ui.mostrar_figura(figura, f"Períodos de igual duração ({mes_final_serie} meses). Cores por ano consistentes.", tabela)
            r = calculos.comparacao_ultimo_periodo_sinesp(serie)
            if r is not None:
                st.markdown(f"**{r['periodo'].capitalize()}, {r['ano_atual']} × {r['ano_anterior']}:** {fmt_int(r['valor_atual'])} × {fmt_int(r['valor_anterior'])} · "
                            f"diferença {fmt_dif(r['diferenca_absoluta'])} · variação {fmt_pct(r['variacao_percentual'])}"
                            + (" (percentual não aplicável: base zero)" if pd.isna(r["variacao_percentual"]) else ""))
                st.caption("Variação descritiva entre períodos equivalentes; em contagens pequenas, observe a magnitude absoluta. Não indica causa.")
        else:
            st.caption("O último ano desta série está completo; não há período parcial a comparar.")
        st.divider()
        st.markdown("**Posição da série entre as demais (mesma unidade)**")
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
                tabela = ranking.rename(columns={"evento": "Indicador", "abrangencia": "Abrangência", "unidade": "Unidade", "soma": f"Total de {int(ano_rank)}"})
                tabela[f"Total de {int(ano_rank)}"] = tabela[f"Total de {int(ano_rank)}"].map(fmt_int)
                figura = graficos.figura_ranking_sinesp(ranking, int(ano_rank), destaque=(evento, abrangencia))
                ui.mostrar_figura(figura, "Ordenação das séries dentro de uma única unidade; a barra laranja é a série selecionada. Não há total entre indicadores nem entre abrangências.", tabela)
            st.caption("Séries com cobertura diferente (p.ex. PF a partir de 2025) só entram nos anos em que estão completas.")

# ------------------------------------------------------------------------------ 3. padrões e tendência (secundária)
with abas[2]:
    if abas[2].open:
        st.caption("Leituras complementares da série: cobertura mês a mês, tendência de 12 meses, acumulado no ano e perfil mensal. São análises exploratórias.")
        st.markdown("**Mapa de calor (ano × mês)**")
        figura = graficos.figura_mapa_calor_sinesp(sinesp_mes, evento, abrangencia, anos_sel)
        if figura is None:
            st.info("Nenhum mês publicado no período selecionado.")
        else:
            ui.mostrar_figura(figura, "Mapa de calor ano × mês. Células cinza: mês sem valor publicado (não preenchido).",
                              tabela_ano_mes(calculos.quadro_ano_mes(serie_mes)))
        st.divider()
        st.markdown("**Tendência (média móvel de 12 meses)**")
        aviso_ano_completo()
        figura = graficos.figura_media_movel_sinesp(sinesp, evento, abrangencia, anos_sel)
        if figura is None:
            st.info("A média móvel de 12 meses exige 12 meses seguidos com valor no período selecionado.")
        else:
            movel = calculos.media_movel(serie_sel)
            tabela = pd.DataFrame({"Ano": movel["ano"], "Mês": movel["mes"], "Valor mensal": movel["valor"].map(fmt_int), "Média móvel de 12 meses": movel["media_movel"].map(fmt_dec)})
            ui.mostrar_figura(figura, "Tendência: a média móvel só existe quando os 12 meses da janela têm valor.", tabela)
        st.divider()
        st.markdown("**Acumulado no ano**")
        aviso_ano_completo()
        figura = graficos.figura_acumulado_sinesp(sinesp, evento, abrangencia, anos_sel)
        if figura is not None:
            acumulado = calculos.acumulado_no_ano(serie_sel)
            quadro_acumulado = acumulado.pivot(index="ano", columns="mes", values="acumulado").reindex(columns=range(1, 13)).astype("Int64")
            ui.mostrar_figura(figura, "Acumulado no ano: compare os anos no mesmo mês; anos parciais terminam no último mês publicado.", tabela_ano_mes(quadro_acumulado))
        st.divider()
        aviso_ano_completo()
        st.markdown("**Sazonalidade (exploratória)**")
        perfil = calculos.perfil_sazonal(serie_sel)
        usados = perfil.attrs.get("anos_usados", [])
        if len(usados) < 2:
            st.info("Sazonalidade não avaliada: são necessários pelo menos 2 anos completos no período selecionado (o ano parcial não entra).")
        else:
            figura = graficos.figura_sazonalidade_sinesp(sinesp, evento, abrangencia, anos_sel)
            tabela = pd.DataFrame({"Mês": [NOMES_MESES[int(m) - 1] for m in perfil["mes"]], "Anos": perfil["n_anos"], "Média": perfil["media"].map(fmt_dec),
                                   "Mediana": perfil["mediana"].map(fmt_dec), "Mín.": perfil["minimo"].map(fmt_int), "Máx.": perfil["maximo"].map(fmt_int),
                                   "Índice (média do mês ÷ média geral)": perfil["indice"].map(fmt_dec)})
            ui.mostrar_figura(figura, f"Mediana de cada mês usando só os anos completos {usados[0]}–{usados[-1]} ({len(usados)} anos). 2026 é parcial e não entra; nenhum mês é inventado.", tabela)
            st.caption("Limitação: com poucos anos completos, o perfil descreve esses anos e não demonstra sazonalidade; um mês pode destoar por um único ano.")

# ------------------------------------------------------------------------------ 4. estatística e outliers (secundária)
with abas[3]:
    if abas[3].open:
        st.caption("Estatísticas dos valores mensais (média, mediana, dispersão), distribuição e pontos fora dos limites de Tukey. Descrevem os números publicados; não explicam causas.")
        st.markdown("**Estatística descritiva**")
        est = calculos.estatisticas_por_ano(serie_mes) if len(serie_mes) else calculos.estatisticas_por_ano(serie_sel)
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
        st.divider()
        st.markdown("**Boxplot e distribuição**")
        figura = graficos.figura_boxplot_anual_sinesp(sinesp_mes, evento, abrangencia, anos_sel)
        if figura is not None:
            ui.mostrar_figura(figura, "Boxplot: resumo de cinco números dos valores mensais de cada ano. Anos com IQR = 0 têm caixa degenerada.", tabela_quartis(calculos.quartis_por_ano(serie_mes)))
        figura = graficos.figura_distribuicao_sinesp(sinesp_mes, evento, abrangencia, anos_sel)
        if figura is not None:
            frequencias = calculos.distribuicao_frequencias(serie_mes)
            tabela = pd.DataFrame({"Faixa do valor mensal": frequencias["rotulo"], "Meses": frequencias["n_meses"], "% dos meses": frequencias["percentual"].map(fmt_dec)})
            ui.mostrar_figura(figura, f"Distribuição em faixas de contagem (largura {frequencias.attrs.get('largura', 1)}; regra de Sturges). O zero publicado é faixa própria e o maior valor está na última faixa; "
                                      f"a soma das faixas é {int(frequencias['n_meses'].sum())} meses.", tabela)
        st.divider()
        st.markdown("**Pontos fora dos limites (IQR)**")
        st.caption("Pontos fora dos limites de Tukey (Q1 − 1,5·IQR; Q3 + 1,5·IQR) nos valores mensais da série e do período selecionados. "
                   "São atípicos estatísticos, não anomalias: o método só é apresentado como informativo quando a série permite.")
        diagnostico = calculos.diagnostico_outliers_iqr(serie_mes)
        if diagnostico["interpretavel"]:
            st.info(f"Método informativo. {diagnostico['mensagem']}")
        else:
            st.warning(f"Método IQR não informativo para esta série ({diagnostico['rotulo']}). {diagnostico['mensagem']}")
        figura = graficos.figura_outliers_iqr_sinesp(sinesp_mes, evento, abrangencia, anos_sel)
        if figura is not None:
            limites = pd.DataFrame([{"Meses com valor": diagnostico["n"], "Q1": _num(diagnostico["q1"]), "Mediana": _num(diagnostico["mediana"]), "Q3": _num(diagnostico["q3"]),
                                     "IQR": _num(diagnostico["iqr"]), "Limite inferior": _num(diagnostico["limite_inferior"]), "Limite superior": _num(diagnostico["limite_superior"]),
                                     "Zeros publicados": f"{diagnostico['zeros']} ({fmt_dec((diagnostico['proporcao_zeros'] or 0) * 100, 0)}%)",
                                     "Pontos fora (interpretáveis)": diagnostico["n_fora"] if diagnostico["interpretavel"] else "não interpretados"}])
            ui.mostrar_figura(figura, "Série mensal com os limites de Tukey. Os pontos só são destacados quando o método é informativo.", limites)
            if diagnostico["interpretavel"] and diagnostico["n_fora"]:
                fora = diagnostico["fora"]
                st.dataframe(pd.DataFrame({"Ano": fora["ano"], "Mês": [NOMES_MESES[int(m) - 1] for m in fora["mes"]], "Valor": fora["valor"].map(fmt_int), "Posição": fora["direcao"]}), hide_index=True)
        with st.expander("Diagnóstico do método IQR em todas as séries (cada uma na sua unidade)"):
            todas = calculos.diagnostico_outliers_todas_as_series(sinesp)
            st.dataframe(pd.DataFrame({
                "Indicador": todas["evento"], "Abrangência": todas["abrangencia"], "Unidade": todas["unidade"], "Meses": todas["meses"], "Q1": todas["q1"].map(_num),
                "Q3": todas["q3"].map(_num), "IQR": todas["iqr"].map(_num), "Zeros": todas["zeros"], "Método": todas["classificacao"],
                "Pontos fora": todas["pontos_fora"].map(fmt_int)}), hide_index=True)
            st.caption("Período completo de cada série. O diagnóstico não compara séries entre si: mandados (contagem publicada) e vítimas têm unidades distintas.")

# ------------------------------------------------------------------------------------------------ 5. indicadores
with abas[4]:
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
        "- **Pontos fora dos limites (IQR)** são atípicos estatísticos, não anomalias; **sazonalidade** com poucos anos completos é apenas exploratória.\n"
        "- Linhas da base original são observações mensais agregadas, não ocorrências individuais."
    )

# ---------------------------------------------------------------------------------- figuras Etapa 10
with st.expander("Material histórico (Etapa 10) — independente dos filtros", expanded=False):
    st.warning("**Material histórico, independente dos filtros desta página** (categoria, indicador, abrangência, anos e meses não alteram estas quatro figuras).")
    st.write("As quatro figuras da Etapa 10 do roteiro, recriadas a partir dos dados curados (vítimas, abrangência Estadual; anos completos 2020–2025 e janeiro–agosto de 2020 a 2026). "
             "Elas são fixas e independem dos filtros acima.")
    mostrar_etapa10 = st.checkbox("Mostrar as quatro figuras", key="mostrar_etapa10", help="Gerar as figuras leva alguns segundos; por isso elas só são desenhadas quando você pedir.")
    try:
        figuras = graficos.figuras_sinesp_etapa10(sinesp) if mostrar_etapa10 else {}
    except ValueError as erro:
        st.error(f"Figuras indisponíveis: {erro}")
        figuras = {}
    nomes = list(figuras)
    if ui.modo_compacto():
        for nome in nomes:
            ui.mostrar_figura(figuras[nome])
    else:
        for i in range(0, len(nomes), 2):
            colunas = st.columns(2)
            for coluna, nome in zip(colunas, nomes[i:i + 2]):
                with coluna:
                    ui.mostrar_figura(figuras[nome])

# ---------------------------------------------------------------------------------- versão e fonte dos dados
st.divider()
ui.mostrar_versao_dos_dados()
