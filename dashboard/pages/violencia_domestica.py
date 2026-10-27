import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard import calculos, graficos, ui  # noqa: E402
from dashboard.dados_publicos import CATEGORIAS_VD  # noqa: E402
from dashboard.formatacao import ABREV_MESES, fmt_dec, fmt_dif, fmt_int, fmt_pct  # noqa: E402

st.title("Violência doméstica — Joinville/SC (SSP/SC)")
st.caption("Fonte: SSP/SC, relatórios de violência doméstica. Joinville/SC, janeiro/2023 a dezembro/2024 · 9 categorias · 216 observações mensais.")
st.warning(ui.AVISO_FATO_COMUNICADO)

vd = ui.carregar_violencia_domestica()
ui.mostrar_versao_dos_dados("ssp")

# ------------------------------------------------------------------------------------------ filtros
f1, f2, f3 = st.columns([3, 1.4, 1.8])
categorias = f1.multiselect("Categoria", list(CATEGORIAS_VD), default=list(CATEGORIAS_VD),
                            help="Cada categoria é tratada separadamente; não há total geral.")
anos = f2.multiselect("Ano", [2023, 2024], default=[2023, 2024])
mes_ini, mes_fim = f3.select_slider("Meses", options=list(range(1, 13)), value=(1, 12), format_func=lambda m: ABREV_MESES[m - 1])

if not categorias or not anos:
    st.info("Selecione ao menos uma categoria e um ano.")
    st.stop()
meses_txt = "12 meses" if (mes_ini, mes_fim) == (1, 12) else f"{ABREV_MESES[mes_ini - 1]} a {ABREV_MESES[mes_fim - 1]}"
st.caption(f"Seleção: {len(categorias)} categoria(s) · ano(s) {', '.join(map(str, sorted(anos)))} · meses: {meses_txt}")

recorte = calculos.filtrar_vd(vd, categorias, anos, mes_ini, mes_fim)

abas = st.tabs(["Resumo", "Comparação 2023 × 2024", "Evolução mensal", "Estatísticas", "Tabela detalhada", "Notas metodológicas"])

# ---------------------------------------------------------------------------------------------- resumo
with abas[0]:
    if len(categorias) == 1:
        categoria = categorias[0]
        colunas = st.columns(len(anos))
        soma_ano = {a: int(recorte.loc[recorte["ano"].eq(a), "fatos_comunicados"].sum()) for a in anos}
        for coluna, ano in zip(colunas, sorted(anos)):
            delta = None
            if len(anos) == 2 and ano == 2024:
                delta = f"{fmt_dif(soma_ano[2024] - soma_ano[2023])} vs 2023"
            coluna.metric(f"{categoria} — {ano} ({meses_txt}; fatos comunicados)", fmt_int(soma_ano[ano]), delta=delta, delta_color="off")
        ext = calculos.extremos_vd(vd, categoria, anos)
        st.caption(f"Maior valor mensal no período de anos selecionado: {fmt_int(ext['maximo'])} ({', '.join(ext['competencias_maximo'])}); "
                   f"menor: {fmt_int(ext['minimo'])} ({', '.join(ext['competencias_minimo'][:6])}{'…' if len(ext['competencias_minimo']) > 6 else ''}).")
    else:
        st.caption(f"Contagem publicada por categoria e ano ({meses_txt}; fatos comunicados). Cada linha é uma categoria independente — não há linha de total.")
        acumulado = calculos.acumulado_por_categoria_ano(recorte)
        tabela = acumulado.pivot(index="categoria", columns="ano", values="soma").reindex([c for c in CATEGORIAS_VD if c in categorias])
        tabela.columns = [f"{a}" for a in tabela.columns]
        st.dataframe(tabela.apply(lambda s: s.map(fmt_int)))

# ---------------------------------------------------------------------------- comparação 2023 × 2024
with abas[1]:
    if set(anos) != {2023, 2024}:
        st.info("A comparação 2023 × 2024 exige os dois anos selecionados.")
    else:
        comparacao = calculos.comparacao_anual_vd(vd, categorias, mes_ini, mes_fim)
        st.caption(f"Acumulado dos mesmos meses nos dois anos ({meses_txt}). A variação percentual só é calculada quando 2023 > 0. "
                   "Em categorias de poucos casos, percentuais altos refletem poucas unidades.")
        exibicao = pd.DataFrame({
            "Categoria": comparacao["categoria"], "2023": comparacao["acumulado_2023"].map(fmt_int), "2024": comparacao["acumulado_2024"].map(fmt_int),
            "Diferença (2024 − 2023)": comparacao["diferenca_absoluta"].map(fmt_dif), "Variação %": comparacao["variacao_percentual"].map(fmt_pct)})
        st.dataframe(exibicao, hide_index=True)
        st.caption("As diferenças representam mudanças nas contagens publicadas, não necessariamente mudanças na incidência real da violência.")
        # Figuras 1–3 da Etapa 14.2, adaptadas às categorias e meses selecionados.
        for nome, (grupo, titulo) in graficos.GRUPOS_VD.items():
            selecionadas = [c for c in grupo if c in categorias]
            if not selecionadas:
                continue
            sufixo = "" if len(selecionadas) == len(grupo) else " (categorias selecionadas)"
            figura = graficos.figura_anual_vd(comparacao, selecionadas, titulo + sufixo, mes_inicial=mes_ini, mes_final=mes_fim)
            ui.mostrar_figura(figura)
        if (mes_ini, mes_fim) == (1, 12) and len(categorias) == len(CATEGORIAS_VD):
            st.caption("Com todos os filtros no padrão, as três figuras acima são as figuras anuais aprovadas na Etapa 14.2.")

# ---------------------------------------------------------------------------------- evolução mensal
with abas[2]:
    aprovadas = [c for c in graficos.CATEGORIAS_MENSAIS_VD.values() if c in categorias]
    opcoes = aprovadas + [c for c in categorias if c not in aprovadas]
    categoria_mensal = st.selectbox("Categoria da série mensal", opcoes,
                                    format_func=lambda c: f"{c} (figura da Etapa 14.2)" if c in graficos.CATEGORIAS_MENSAIS_VD.values() else c)
    comparativo = calculos.comparativo_mensal_vd(vd, categoria_mensal)
    ui.mostrar_figura(graficos.figura_mensal_vd(comparativo, categoria_mensal),
                      "Janeiro a dezembro de 2023 e 2024. Cada categoria é plotada isoladamente, com eixo iniciado em zero.")
    st.caption(f"Tabela mensal — {categoria_mensal} (fatos comunicados):")
    comp_exib = comparativo.loc[comparativo["mes"].between(mes_ini, mes_fim)].copy()
    comp_exib["mes"] = comp_exib["mes"].map(lambda m: ABREV_MESES[m - 1])
    comp_exib.columns = ["Mês", "2023", "2024", "Diferença (2024 − 2023)"]
    comp_exib["2023"], comp_exib["2024"] = comp_exib["2023"].map(fmt_int), comp_exib["2024"].map(fmt_int)
    comp_exib["Diferença (2024 − 2023)"] = comp_exib["Diferença (2024 − 2023)"].map(fmt_dif)
    st.dataframe(comp_exib, hide_index=True)

# ------------------------------------------------------------------------------------- estatísticas
with abas[3]:
    est = calculos.estatisticas_vd(vd, categorias, anos, mes_ini, mes_fim)
    st.caption(f"Estatísticas descritivas mensais por categoria ({meses_txt}; ano(s): {', '.join(map(str, sorted(anos)))}). Desvio-padrão descritivo (ddof=0).")
    exib = pd.DataFrame({
        "Categoria": est["categoria"], "Soma publicada": est["soma_publicada"].map(fmt_int), "Média mensal": est["media_mensal"].map(fmt_dec),
        "Mediana": est["mediana_mensal"].map(fmt_dec), "Mín.": est["minimo"].map(fmt_int), "Máx.": est["maximo"].map(fmt_int),
        "Desvio-padrão": est["desvio_padrao_ddof0"].map(fmt_dec), "Meses": est["meses_observados"], "Meses com zero": est["meses_com_zero"]})
    st.dataframe(exib, hide_index=True)
    st.caption("Zero publicado é uma observação (não ausência). Não há total entre categorias.")

# ----------------------------------------------------------------------------------------- tabela
with abas[4]:
    tabela = recorte.sort_values(["categoria", "ano", "mes"]).copy()
    tabela["categoria"] = pd.Categorical(tabela["categoria"], categories=list(CATEGORIAS_VD), ordered=True)
    tabela = tabela.sort_values(["categoria", "ano", "mes"])
    st.caption(f"{len(tabela)} observações na seleção (Joinville/SC; unidade: fato comunicado).")
    st.dataframe(tabela[["ano", "mes", "categoria", "fatos_comunicados"]].rename(columns={
        "ano": "Ano", "mes": "Mês", "categoria": "Categoria", "fatos_comunicados": "Fatos comunicados"}), hide_index=True)
    with st.expander("Rastreabilidade das observações (arquivo, página, tabela, linha e rótulo originais)"):
        rastreio = ui.carregar_rastreio_vd()
        sel = rastreio.loc[rastreio["categoria"].isin(categorias) & rastreio["ano"].isin(anos) & rastreio["mes"].between(mes_ini, mes_fim)]
        st.dataframe(sel, hide_index=True)
        st.caption("Os rótulos originais “0 Dolosa” e “- Dolosa” são preservados aqui; a unificação na coluna Categoria é decisão metodológica do projeto.")

# ------------------------------------------------------------------------------------------- notas
with abas[5]:
    st.markdown(ui.AVISO_FATO_COMUNICADO)
    st.markdown(ui.AVISO_METODOLOGICO_VD)
    st.markdown(
        "- Os valores vêm de 216 células de tabelas de três relatórios da SSP/SC (1º e 2º semestres de 2023 e ano de 2024), conferidas contra os PDFs.\n"
        "- Os 27 zeros publicados foram mantidos como zero; não há valores ausentes.\n"
        "- 2023 vem de dois relatórios semestrais e 2024 de um relatório anual; a definição da contagem entre eles não está documentada.\n"
        "- Sem causalidade, taxas populacionais, dados territoriais ou número de vítimas."
    )
