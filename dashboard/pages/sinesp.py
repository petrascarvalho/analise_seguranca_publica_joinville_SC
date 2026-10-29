"""Seção "Indicadores Sinesp": filtros, cards, gráficos e tabelas da série escolhida.

Comandos do Streamlit usados nesta seção (o arquivo é executado de novo a cada interação):
    • st.selectbox — lista suspensa (Indicador); devolve a opção escolhida.
    • st.select_slider — controle deslizante de intervalo (anos e meses); devolve (início, fim).
    • st.button / st.toggle — botão "Restaurar filtros" e chave liga/desliga do modo compacto (st.session_state["modo_compacto"]).
    • ui.cartoes_html — linha de cards brancos de mesma altura (CSS Grid, definido em dashboard/ui.py).
    • st.tabs — abas; o conteúdo de cada uma fica dentro de "with abas[i]:".
    • st.dataframe — tabela interativa; st.pyplot — figura do Matplotlib; st.expander — seção recolhível.

Os números vêm de dashboard/calculos.py e as figuras de dashboard/graficos.py; esta seção só organiza a apresentação.
A abrangência (Estadual, Polícia Federal, PRF) não é um filtro: ela faz parte do nome do indicador, como em "Homicídio doloso — Estadual".
"""

import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard import calculos, graficos, ui  # noqa: E402
from dashboard.formatacao import ABREV_MESES, NOMES_MESES, fmt_competencia, fmt_dec, fmt_dif, fmt_int, fmt_pct  # noqa: E402

sinesp, catalogo = ui.carregar_dados_consistentes()
_ini, _fim = sinesp.assign(c=sinesp["ano"] * 100 + sinesp["mes"])["c"].agg(["min", "max"])
ui.secao("Indicadores Sinesp — Joinville/SC", "indicadores",
         f"Fonte: MJSP / Sinesp VDE, Joinville/SC, {NOMES_MESES[int(_ini) % 100 - 1]}/{int(_ini) // 100} a {NOMES_MESES[int(_fim) % 100 - 1]}/{int(_fim) // 100}. "
         "Contagens mensais publicadas pela fonte. Escolha o indicador, o período e os meses; os resultados aparecem nas abas abaixo.")
st.caption("Todos os números são de Joinville/SC. " + ui.NOTA_ABRANGENCIA_CURTA)

# ------------------------------------------------------------------------------------------ filtros
# Cada série (indicador × abrangência) vira uma opção "Indicador — Abrangência". Assim não existe um filtro de abrangência redundante,
# e a abrangência continua visível em todos os títulos, legendas e tabelas.
catalogo = catalogo.assign(serie=catalogo["evento"] + " — " + catalogo["abrangencia"])
series = sorted(catalogo["serie"])
SERIE_PADRAO = "Homicídio doloso — Estadual"


def restaurar_filtros():
    """Volta ao indicador, ao período e aos meses iniciais (a preferência de visualização compacta é mantida)."""
    st.session_state["serie"] = SERIE_PADRAO
    for chave in ("periodo_anos", "periodo_meses"):
        st.session_state.pop(chave, None)  # sem a escolha guardada, cada controle recomeça com o seu valor inicial (todo o período, 12 meses)


with st.container(border=True):
    st.markdown("**Filtros** — os resultados são atualizados ao selecionar.")
    f1, f2, f3 = st.columns([2.2, 1.5, 1.5])
    st.session_state.setdefault("serie", SERIE_PADRAO)  # indicador inicial (sem "index=", para não conflitar com o botão Restaurar filtros)
    serie_escolhida = f1.selectbox("Indicador", series, key="serie",
                                   help="Cada opção é um indicador com a sua abrangência. Estadual, Polícia Federal e PRF são séries distintas e não são somadas.")
    ficha = catalogo.loc[catalogo["serie"].eq(serie_escolhida)].iloc[0]
    evento, abrangencia = ficha["evento"], ficha["abrangencia"]
    serie = calculos.serie_sinesp(sinesp, evento, abrangencia)
    # Filtro dependente: os anos oferecidos são os da série escolhida (a PF, por exemplo, só existe desde 2025).
    anos_disponiveis = sorted(int(a) for a in serie["ano"].unique())
    anterior = st.session_state.get("periodo_anos")
    if anterior is not None and not (anterior[0] in anos_disponiveis and anterior[1] in anos_disponiveis):
        del st.session_state["periodo_anos"]  # a escolha não existe nesta série: o controle recomeça com o período inteiro (value abaixo)
    ano_ini, ano_fim = f2.select_slider("Período (anos)", options=anos_disponiveis, value=(anos_disponiveis[0], anos_disponiveis[-1]), key="periodo_anos")
    mes_ini, mes_fim = f3.select_slider("Meses", options=list(range(1, 13)), value=(1, 12), key="periodo_meses", format_func=lambda m: ABREV_MESES[m - 1],
                                        help="Vale para os cards, o mapa de calor, a evolução mensal, as estatísticas e a análise de meses incomuns. "
                                             "Totais anuais, comparações de anos completos, média móvel, acumulado e perfil por mês do ano usam sempre os 12 meses.")
    anos_sel = list(range(ano_ini, ano_fim + 1))
    b1, b2 = st.columns([1, 2.2], vertical_alignment="center")
    b1.button("Restaurar filtros", on_click=restaurar_filtros, width="stretch", type="primary",
              help="Retorna ao indicador, ao período e aos meses iniciais; mantém a preferência de visualização.")
    b2.toggle("Visualização compacta (celular)", key="modo_compacto",
              help="Gráficos mais estreitos, com letras maiores, menos marcas nos eixos e os textos explicativos abaixo da imagem. O painel não detecta o tamanho "
                   "da tela: ative em telas pequenas. Os números e as tabelas são os mesmos nos dois modos.")
graficos.definir_modo_compacto(ui.modo_compacto())  # vale para todas as figuras criadas nesta execução
filtro_meses = (mes_ini, mes_fim) != (1, 12)
meses_sel = list(range(mes_ini, mes_fim + 1))
_MESES_TEXTO = "janeiro–dezembro (12 meses)" if not filtro_meses else f"{NOMES_MESES[mes_ini - 1]}–{NOMES_MESES[mes_fim - 1]} ({len(meses_sel)} meses)"


def aviso_ano_completo() -> None:
    """Identifica as análises que usam os 12 meses mesmo com o filtro de meses ativo (nunca somam alguns meses como total anual)."""
    if filtro_meses:
        st.caption("Análise de ano completo (12 meses): não usa o filtro de meses. Os totais anuais são sempre a soma dos 12 meses.")


unidade = ficha["unidade"]
unidade_curta = unidade.split(" (")[0]
# Recorte ativo: o que está sendo analisado (indicador com abrangência, período, unidade e cobertura da série), num único bloco de texto.
st.markdown(f"**Recorte ativo:** indicador **{serie_escolhida}** · anos **{ano_ini}–{ano_fim}** · meses **{_MESES_TEXTO}**"
            f" · visualização **{'compacta' if ui.modo_compacto() else 'completa'}**  \n"
            f"**Unidade:** {unidade} · **Tipo de indicador:** {ficha['natureza']} · **Período da série:** {fmt_competencia(ficha['inicio'])} a {fmt_competencia(ficha['fim'])}")
if abrangencia == "Polícia Federal":
    st.warning(f"Os mandados da Polícia Federal só aparecem a partir de {fmt_competencia(ficha['inicio'])}; antes disso não há série (e isso não significa zero).")
if abrangencia == "Polícia Rodoviária Federal":
    st.info("A série da PRF termina em um mês diferente das demais; ela é mostrada só até o último mês disponível, sem preencher os meses que faltam.")
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
    st.caption(f"Filtro de meses ativo: {ABREV_MESES[mes_ini - 1]}–{ABREV_MESES[mes_fim - 1]}. Vale para os resultados mensais; anos completos e acumulados continuam usando os 12 meses.")

# ------------------------------------------------------------------------------------- cards do indicador
st.subheader("Resumo do indicador escolhido")
cards = []   # cada card é um dicionário: titulo, valor, detalhe, variacao, diferenca, ajuda (ver ui.cartoes_html)
detalhe = f"{evento} · {abrangencia}"
soma_meses = calculos.soma_no_periodo(serie, mes_ini, mes_fim)
soma_meses = soma_meses.loc[soma_meses["ano"].isin(anos_sel) & soma_meses["soma"].notna()]
if filtro_meses:  # com filtro de meses, o card principal é a soma desses meses no último ano em que todos foram publicados
    if len(soma_meses):
        ultimo_m = soma_meses.iloc[-1]
        anterior_m = soma_meses.loc[soma_meses["ano"].eq(int(ultimo_m["ano"]) - 1)]
        dif_m = int(ultimo_m["soma"]) - int(anterior_m.iloc[0]["soma"]) if len(anterior_m) else None
        cards.append({"titulo": f"{ABREV_MESES[mes_ini - 1]}–{ABREV_MESES[mes_fim - 1]} de {int(ultimo_m['ano'])} ({unidade_curta})", "detalhe": detalhe,
                      "valor": fmt_int(ultimo_m["soma"]), "variacao": f"{fmt_dif(dif_m)} vs {int(ultimo_m['ano']) - 1}" if dif_m is not None else "", "diferenca": dif_m,
                      "ajuda": "Soma dos meses escolhidos; só entra o ano que tem todos esses meses publicados. A diferença compara com os mesmos meses do ano anterior."})
    else:
        cards.append({"titulo": "Soma dos meses selecionados", "detalhe": detalhe, "valor": "—", "ajuda": "Nenhum ano do período tem todos os meses selecionados publicados."})
elif len(completos):
    ultimo = completos.iloc[-1]
    variacao, dif_anual = "", None
    if len(completos) > 1:
        anterior = completos.iloc[-2]
        if int(anterior["ano"]) == int(ultimo["ano"]) - 1:
            dif_anual = int(ultimo["soma"]) - int(anterior["soma"])
            variacao = f"{fmt_dif(dif_anual)} vs {int(anterior['ano'])}"
    cards.append({"titulo": f"Último ano completo: {int(ultimo['ano'])} ({unidade_curta})", "detalhe": detalhe, "valor": fmt_int(ultimo["soma"]),
                  "variacao": variacao, "diferenca": dif_anual, "ajuda": "Soma dos 12 meses publicados. A diferença compara apenas com o ano completo anterior."})
else:
    cards.append({"titulo": "Último ano completo", "detalhe": detalhe, "valor": "—", "ajuda": "Nenhum ano completo no período selecionado."})
if filtro_meses:
    cards.append({"titulo": "Meses filtrados", "detalhe": detalhe, "valor": f"{len(meses_sel)} de 12", "ajuda": "Intervalo de meses escolhido no filtro."})
elif len(periodo_sel) and serie_parcial:
    ult_p = periodo_sel.iloc[-1]
    ant = periodo_sel.loc[periodo_sel["ano"].eq(int(ult_p["ano"]) - 1)]
    dif_p = int(ult_p["soma"]) - int(ant.iloc[0]["soma"]) if len(ant) else None
    cards.append({"titulo": f"{nome_periodo.capitalize()} de {int(ult_p['ano'])} ({unidade_curta})", "detalhe": detalhe, "valor": fmt_int(ult_p["soma"]),
                  "variacao": f"{fmt_dif(dif_p)} vs {nome_periodo} de {int(ult_p['ano']) - 1}" if dif_p is not None else "", "diferenca": dif_p,
                  "ajuda": f"Períodos equivalentes: os dois anos são comparados nos mesmos {mes_final_serie} meses."})
else:
    cards.append({"titulo": nome_periodo.capitalize(), "detalhe": detalhe, "valor": "—", "ajuda": "O último ano da série está completo: não há período parcial para comparar."})
resumo = calculos.resumo_serie_sinesp(serie_mes)
cards.append({"titulo": "Meses com valor publicado", "detalhe": detalhe, "valor": f"{resumo['meses_com_valor']} de {resumo['meses_observados']}",
              "base": f"Zeros informados: {resumo['meses_valor_zero']}. Meses sem informação: {resumo['meses_sem_valor']} (nunca preenchidos)."})
ui.cartoes_html(cards)

# Abas com execução preguiçosa (Streamlit 1.66): só a aba selecionada é calculada e desenhada (cada figura leva ~0,3 s para virar PNG).
abas = st.tabs(["Evolução", "Comparações", "Meses e tendência", "Estatísticas e meses incomuns", "Indicadores e como interpretar"], key="aba_analise", on_change="rerun")

# ------------------------------------------------------------------------------ tabelas verificáveis dos gráficos
def _num(valor) -> str:
    return fmt_int(valor) if pd.notna(valor) and float(valor) == int(float(valor)) else fmt_dec(valor)


def _texto_das_faixas(frequencias: pd.DataFrame) -> str:
    """Descreve como as faixas da distribuição foram montadas (o zero informado é faixa própria; a última faixa pode ser menor)."""
    largura = int(frequencias.attrs.get("largura", 1))
    positivas = frequencias.loc[frequencias["inicio"] > 0, "rotulo"].tolist()
    zero = "O zero informado é uma faixa própria. " if (frequencias["inicio"] == 0).any() else ""
    if largura == 1 or len(positivas) < 2:
        return f"{zero}Cada valor inteiro forma uma faixa."
    return (f"{zero}Os demais valores foram agrupados em intervalos de mesma largura ({', '.join(positivas[:3])}…); "
            "a última faixa pode ser menor, porque termina no maior valor observado.")


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
        "Menor valor dentro dos limites": quadro["bigode_inferior"].map(_num), "Maior valor dentro dos limites": quadro["bigode_superior"].map(_num),
        "Meses fora": quadro.apply(lambda r: "IQR = 0 (não interpretado)" if r["iqr_zero"] else (", ".join(_num(v) for v in r["valores_fora"]) or "—"), axis=1)})



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
            ui.mostrar_figura(mensal, "Evolução mensal: uma barra por ano, sempre com o mesmo tom de azul. Valores publicados, sem preenchimento.",
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
            st.caption("A variação percentual só é calculada quando o ponto de partida é maior que zero (n/a = não se aplica). Em contagens pequenas, observe a diferença em números absolutos. Não indica causa.")

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
        st.markdown("**Períodos equivalentes (janeiro até o último mês disponível da série)**")
        if serie_parcial:
            tabela = periodo_sel[["ano", "periodo", "meses_com_valor", "soma"]].copy()
            tabela["soma"] = tabela["soma"].map(fmt_int)
            tabela.columns = ["Ano", "Período", "Meses com valor", f"Soma ({unidade_curta})"]
            figura = graficos.figura_periodo_sinesp(sinesp, evento, abrangencia, anos_sel, mes_final_serie)
            if figura is None:
                st.info(f"Não há período {nome_periodo} completo no intervalo selecionado para esta série.")
            else:
                ui.mostrar_figura(figura, f"Períodos de igual duração ({mes_final_serie} meses). Cada ano tem sempre o mesmo tom de azul.", tabela)
            r = calculos.comparacao_ultimo_periodo_sinesp(serie)
            if r is not None:
                st.markdown(f"**{r['periodo'].capitalize()}, {r['ano_atual']} × {r['ano_anterior']}:** {fmt_int(r['valor_atual'])} × {fmt_int(r['valor_anterior'])} · "
                            f"diferença {fmt_dif(r['diferenca_absoluta'])} · variação {fmt_pct(r['variacao_percentual'])}"
                            + (" (percentual não aplicável: base zero)" if pd.isna(r["variacao_percentual"]) else ""))
                st.caption("Variação entre períodos equivalentes; em contagens pequenas, observe a diferença em números absolutos. Não indica causa.")
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
                ui.mostrar_figura(figura, "Ordem dos indicadores dentro de uma única unidade; a barra mais escura é o indicador escolhido. Não existe total entre indicadores nem entre abrangências.", tabela)
            st.caption("Séries com cobertura diferente (por exemplo, a Polícia Federal a partir de 2025) só entram nos anos em que estão completas.")

# ------------------------------------------------------------------------------ 3. padrões e tendência (secundária)
with abas[2]:
    if abas[2].open:
        st.caption("Leituras complementares: mês a mês, tendência de 12 meses, acumulado no ano e perfil por mês do ano. São leituras para explorar os números, não conclusões.")
        st.markdown("**Mapa de calor (ano × mês)**")
        figura = graficos.figura_mapa_calor_sinesp(sinesp_mes, evento, abrangencia, anos_sel)
        if figura is None:
            st.info("Nenhum mês com informação no período escolhido.")
        else:
            ui.mostrar_figura(figura, "Mapa de calor (ano × mês): quanto mais escuro, maior o valor. Células cinza: mês sem informação (não preenchido).",
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
            ui.mostrar_figura(figura, "Tendência: a média móvel de 12 meses suaviza as oscilações e só existe quando os 12 meses têm valor.", tabela)
        st.divider()
        st.markdown("**Acumulado no ano**")
        aviso_ano_completo()
        figura = graficos.figura_acumulado_sinesp(sinesp, evento, abrangencia, anos_sel)
        if figura is not None:
            acumulado = calculos.acumulado_no_ano(serie_sel)
            quadro_acumulado = acumulado.pivot(index="ano", columns="mes", values="acumulado").reindex(columns=range(1, 13)).astype("Int64")
            ui.mostrar_figura(figura, "Acumulado no ano: compare os anos no mesmo mês; os anos parciais terminam no último mês disponível.", tabela_ano_mes(quadro_acumulado))
        st.divider()
        aviso_ano_completo()
        st.markdown("**Mediana de cada mês do ano**")
        perfil = calculos.perfil_sazonal(serie_sel)
        usados = perfil.attrs.get("anos_usados", [])
        if len(usados) < 2:
            st.info("Esta comparação entre meses do ano precisa de pelo menos 2 anos completos no período escolhido (o ano parcial não entra).")
        else:
            figura = graficos.figura_sazonalidade_sinesp(sinesp, evento, abrangencia, anos_sel)
            tabela = pd.DataFrame({"Mês": [NOMES_MESES[int(m) - 1] for m in perfil["mes"]], "Anos": perfil["n_anos"], "Média": perfil["media"].map(fmt_dec),
                                   "Mediana": perfil["mediana"].map(fmt_dec), "Mín.": perfil["minimo"].map(fmt_int), "Máx.": perfil["maximo"].map(fmt_int),
                                   "Índice (média do mês ÷ média geral)": perfil["indice"].map(fmt_dec)})
            ui.mostrar_figura(figura, f"Para cada mês (janeiro, fevereiro…), a mediana dos anos completos {usados[0]}–{usados[-1]} ({len(usados)} anos). O ano parcial não entra.", tabela)
            st.caption("Cuidado: com poucos anos completos, este quadro descreve apenas esses anos e não prova que exista um padrão sazonal; um mês pode destoar por causa de um único ano.")

# ------------------------------------------------------------------------------ 4. estatística e outliers (secundária)
with abas[3]:
    if abas[3].open:
        st.caption("Estatísticas dos valores mensais (média, mediana, variação), distribuição dos valores e meses incomuns. Descrevem os números publicados; não explicam causas.")
        with st.expander("O que significam estes termos?"):
            st.markdown(
                "- **Média:** soma dos valores dividida pelo número de meses. **Mediana:** valor do meio quando os meses são colocados em ordem; é menos afetada por meses muito altos.\n"
                "- **Desvio-padrão:** mede o quanto os meses variam em torno da média (quanto maior, mais os valores oscilam).\n"
                "- **Quartis (Q1 e Q3):** Q1 deixa 25% dos meses abaixo dele e Q3 deixa 75% abaixo. **IQR:** a distância entre Q1 e Q3.\n"
                "- **Limites de referência:** Q1 − 1,5 × IQR e Q3 + 1,5 × IQR (critério estatístico de Tukey). Servem para destacar meses diferentes dos demais "
                "**da própria série**. **Não são metas, limites legais nem parâmetros oficiais de segurança pública**, e um mês fora deles não prova erro, anomalia ou mudança real.\n"
                "- **Gráfico de caixa (boxplot):** a caixa vai de Q1 a Q3, o traço é a mediana e os pontos são meses fora dos limites de referência.\n"
                "- **Média móvel de 12 meses:** média do mês e dos 11 anteriores; suaviza as oscilações."
            )
        st.markdown("**Estatísticas dos meses de cada ano**")
        est = calculos.estatisticas_por_ano(serie_mes) if len(serie_mes) else calculos.estatisticas_por_ano(serie_sel)
        st.caption(f"Estatísticas dos valores MENSAIS de cada ano ({unidade_curta}).")
        exib = pd.DataFrame({
            "Ano": est["ano"], "Cobertura": est["cobertura"], "Meses": est["meses_observados"], "Soma do ano": est["soma"].map(fmt_int),
            "Média mensal": est["media_mensal"].map(fmt_dec), "Mediana": est["mediana_mensal"].map(fmt_dec), "Mín.": est["minimo"].map(fmt_int),
            "Máx.": est["maximo"].map(fmt_int), "Desvio-padrão": est["desvio_padrao_ddof0"].map(fmt_dec), "Meses com zero": est["meses_valor_zero"]})
        st.dataframe(exib, hide_index=True)
        st.markdown("**Todo o período escolhido**")
        geral = pd.DataFrame([{
            "Meses observados": resumo["meses_observados"], "Média mensal": fmt_dec(resumo["media_mensal"]), "Mediana": fmt_dec(resumo["mediana_mensal"]),
            "Mínimo": fmt_int(resumo["minimo"]), "Máximo": fmt_int(resumo["maximo"]), "Desvio-padrão": fmt_dec(resumo["desvio_padrao_ddof0"]),
            "Meses com zero": resumo["meses_valor_zero"], "Meses sem valor": resumo["meses_sem_valor"]}])
        st.dataframe(geral, hide_index=True)
        st.caption("A soma do ano só aparece quando todos os meses presentes têm informação. Em séries com muitos zeros, a média e a mediana descrevem contagens pequenas.")
        st.divider()
        st.markdown("**Gráfico de caixa (boxplot) e distribuição dos valores**")
        figura = graficos.figura_boxplot_anual_sinesp(sinesp_mes, evento, abrangencia, anos_sel)
        if figura is not None:
            ui.mostrar_figura(figura, "Gráfico de caixa: resume os valores mensais de cada ano (menor, Q1, mediana, Q3 e maior). Em anos com IQR = 0 a caixa vira um traço, porque quase todos os meses têm o mesmo valor.", tabela_quartis(calculos.quartis_por_ano(serie_mes)))
        figura = graficos.figura_distribuicao_sinesp(sinesp_mes, evento, abrangencia, anos_sel)
        if figura is not None:
            frequencias = calculos.distribuicao_frequencias(serie_mes)
            tabela = pd.DataFrame({"Faixa do valor mensal": frequencias["rotulo"], "Meses": frequencias["n_meses"], "% dos meses": frequencias["percentual"].map(fmt_dec)})
            ui.mostrar_figura(figura, f"Quantos meses tiveram valores dentro de cada faixa. {_texto_das_faixas(frequencias)} "
                                      f"A soma das faixas é {int(frequencias['n_meses'].sum())} meses.", tabela)
        st.divider()
        st.markdown("**Meses fora dos limites de referência (IQR)**")
        st.caption("Meses fora do comportamento típico da própria série, segundo um critério estatístico (limites de referência), no período escolhido. "
                   "Não são parâmetros oficiais de segurança pública nem anomalias comprovadas; o critério só é destacado quando é útil para a série.")
        diagnostico = calculos.diagnostico_outliers_iqr(serie_mes)
        if diagnostico["interpretavel"]:
            st.info("Para esta série, o critério estatístico é útil: meses fora dos limites de referência são incomuns em relação aos demais. "
                    "Isso não prova erro, anomalia ou mudança real, e em séries com tendência os limites podem representar pouco.")
        else:
            st.warning(f"O critério dos limites de referência (IQR) não ajuda a interpretar esta série ({diagnostico['rotulo']}). "
                       "Nenhum mês é apontado como incomum, e valores acima do limite não indicam anomalia.")
        figura = graficos.figura_outliers_iqr_sinesp(sinesp_mes, evento, abrangencia, anos_sel)
        if figura is not None:
            limites = pd.DataFrame([{"Meses com valor": diagnostico["n"], "Q1": _num(diagnostico["q1"]), "Mediana": _num(diagnostico["mediana"]), "Q3": _num(diagnostico["q3"]),
                                     "IQR": _num(diagnostico["iqr"]), "Limite inferior": _num(diagnostico["limite_inferior"]), "Limite superior": _num(diagnostico["limite_superior"]),
                                     "Zeros informados": f"{diagnostico['zeros']} ({fmt_dec((diagnostico['proporcao_zeros'] or 0) * 100, 0)}%)",
                                     "Meses fora dos limites": diagnostico["n_fora"] if diagnostico["interpretavel"] else "não interpretados"}])
            ui.mostrar_figura(figura, "Série mensal com os limites de referência. Os meses fora deles só são destacados quando o critério é útil para a série.", limites)
            if diagnostico["interpretavel"] and diagnostico["n_fora"]:
                fora = diagnostico["fora"]
                st.dataframe(pd.DataFrame({"Ano": fora["ano"], "Mês": [NOMES_MESES[int(m) - 1] for m in fora["mes"]], "Valor": fora["valor"].map(fmt_int), "Posição": fora["direcao"]}), hide_index=True)
        with st.expander("Limites de referência (IQR) em todas as séries, cada uma na sua unidade"):
            todas = calculos.diagnostico_outliers_todas_as_series(sinesp)
            st.dataframe(pd.DataFrame({
                "Indicador": todas["evento"], "Abrangência": todas["abrangencia"], "Unidade": todas["unidade"], "Meses": todas["meses"], "Q1": todas["q1"].map(_num),
                "Q3": todas["q3"].map(_num), "IQR": todas["iqr"].map(_num), "Zeros": todas["zeros"], "Método": todas["classificacao"],
                "Meses fora": todas["pontos_fora"].map(fmt_int)}), hide_index=True)
            st.caption("Período completo de cada série. As séries não são comparadas entre si: mandados e vítimas têm unidades diferentes.")

# ------------------------------------------------------------------------------------------------ 5. indicadores
with abas[4]:
    st.caption("Lista dos indicadores disponíveis, com abrangência, unidade, período coberto e cuidados de leitura.")
    cat = catalogo.rename(columns={
        "evento": "Indicador", "abrangencia": "Abrangência", "unidade": "Unidade", "natureza": "Tipo", "meses_observados": "Meses", "meses_com_valor": "Com valor",
        "meses_valor_zero": "Zeros informados", "meses_sem_valor": "Sem valor", "limitacoes": "Cuidados de leitura"})
    cat["Início"] = catalogo["inicio"].map(lambda c: fmt_competencia(c, curto=True))
    cat["Fim"] = catalogo["fim"].map(lambda c: fmt_competencia(c, curto=True))
    st.dataframe(cat[["Indicador", "Abrangência", "Unidade", "Tipo", "Início", "Fim", "Meses", "Com valor", "Zeros informados", "Sem valor", "Cuidados de leitura"]], hide_index=True)
    st.markdown("**Como interpretar estes números**")
    st.markdown(
        "- **O que os números mostram:** valores publicados pelo Sinesp para Joinville (contagens mensais) e as diferenças calculadas entre eles.\n"
        "- **O que eles não afirmam:** a causa das variações, o efeito de políticas ou de ações policiais, os casos não registrados ou o total de crimes ocorridos.\n"
        "- **Contagens pequenas:** uma diferença de poucas unidades pode ser só oscilação natural; observe sempre os números absolutos.\n"
        "- **Vítimas e mandados** são medidas diferentes e nunca são somados. Feminicídio e tentativa são séries separadas e não se somam a homicídio.\n"
        "- **Zero informado** é um número publicado; a falta de uma série (por exemplo, a Polícia Federal antes de 2025) não significa zero.\n"
        "- **Meses fora dos limites de referência** são apenas incomuns em comparação com os demais; o **perfil por mês do ano**, com poucos anos completos, é só exploratório.\n"
        "- Cada linha dos dados é um total mensal, não uma ocorrência individual."
    )

# ---------------------------------------------------------------------------------- figuras Etapa 10
with st.expander("Quatro gráficos de referência (fixos, não mudam com os filtros)", expanded=False):
    st.warning("**Estes quatro gráficos são fixos:** o indicador, os anos e os meses escolhidos acima não os alteram.")
    st.write("Mostram vítimas de homicídio doloso, tentativa de homicídio, feminicídio e tentativa de feminicídio (abrangência Estadual, Joinville/SC), em anos completos de 2020 a 2025 e no período de janeiro a agosto de 2020 a 2026.")
    mostrar_etapa10 = st.checkbox("Mostrar os quatro gráficos", key="mostrar_etapa10", help="Gerar os gráficos leva alguns segundos; por isso eles só são desenhados quando você pedir.")
    try:
        figuras = graficos.figuras_sinesp_etapa10(sinesp) if mostrar_etapa10 else {}
    except ValueError as erro:
        st.error(f"Gráficos indisponíveis: {erro}")
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
