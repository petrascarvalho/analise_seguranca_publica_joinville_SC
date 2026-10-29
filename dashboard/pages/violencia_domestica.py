"""Seção "VIOLÊNCIA DOMÉSTICA — SSP/SC": exploração separada, em validação, com filtro próprio de categoria.

Regras desta seção (não negociáveis):
    • "Fato Comunicado" NÃO tem definição operacional confirmada: não é vítima, pessoa única nem ocorrência única.
    • Categorias nunca são somadas entre si e os números nunca são misturados com os indicadores de vítimas do Sinesp.
    • O acervo completo da SSP/SC (PDFs e boletins) não é publicado; esta seção usa só as 216 observações já conferidas.
    • Sem o arquivo local (por exemplo, no Streamlit Cloud), a seção informa a limitação e mostra apenas a figura exploratória já versionada.
"""

import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard import dados_ssp, graficos, ui  # noqa: E402
from dashboard.formatacao import ABREV_MESES, fmt_dif, fmt_int  # noqa: E402

ui.secao("VIOLÊNCIA DOMÉSTICA — SSP/SC", "violencia-domestica",
         "Exploração separada do Sinesp: Secretaria de Estado da Segurança Pública de SC, município de Joinville, janeiro/2023 a dezembro/2024.")
st.warning("**Fonte em validação.** A unidade “Fato Comunicado” não tem definição operacional confirmada nos documentos disponíveis: não a interprete como "
           "vítimas, pessoas ou ocorrências únicas, não some categorias e não compare estes números com os indicadores do Sinesp.")

try:
    vd = dados_ssp.carregar_violencia_domestica()
except dados_ssp.ErroDadosSsp as erro:
    st.error(f"**Dados da SSP/SC inválidos.** {erro} Nenhum valor foi preenchido ou estimado.")
    st.stop()

if vd is None:
    # Sem o CSV local (clone limpo, Streamlit Cloud): não há dado para filtrar. Mostra só a figura exploratória que já está no repositório.
    st.info("Os dados detalhados de violência doméstica da SSP/SC não estão disponíveis nesta versão pública do painel: as condições de reutilização da fonte "
            "ainda não foram avaliadas formalmente e os relatórios completos não são divulgados. Abaixo, uma figura-resumo com os totais anuais por categoria.")
    if dados_ssp.FIGURA_ESTATICA.is_file():
        st.image(str(dados_ssp.FIGURA_ESTATICA), caption="Fatos comunicados por categoria, 2023 × 2024 (SSP/SC). Unidade em validação; não integra os indicadores Sinesp.")
else:
    # ------------------------------------------------------------------------------------------ filtro próprio e cards
    categorias = sorted(vd["categoria"].unique())
    with st.container(border=True):
        st.markdown("**Filtro desta seção** — independente dos filtros do Sinesp.")
        escolha = st.selectbox("Categoria (SSP/SC)", ["Todas as categorias"] + categorias, key="vd_categoria",
                               help="“Todas” compara cada categoria com ela mesma em 2023 e 2024; uma categoria específica mostra os 24 meses.")
    categoria = None if escolha == "Todas as categorias" else escolha

    totais = vd.groupby(["categoria", "ano"])["valor"].sum().unstack("ano")   # soma dos 12 meses de cada categoria e ano; nunca entre categorias
    if categoria is None:
        ui.cartoes_html([
            {"titulo": "Período", "valor": "2023–2024", "detalhe": "SSP/SC · Joinville", "base": "Janeiro/2023 a dezembro/2024 (24 meses)."},
            {"titulo": "Registros", "valor": fmt_int(len(vd)), "detalhe": f"{len(categorias)} categorias × 24 meses", "base": "Sem registros repetidos e sem valores ausentes."},
            {"titulo": "Zeros publicados", "valor": fmt_int(int(vd["valor"].eq(0).sum())), "detalhe": "meses com 0 fatos comunicados", "base": "Zero informado é um número publicado, não ausência."},
            {"titulo": "Unidade", "valor": "Em validação", "detalhe": "Fato Comunicado", "base": "Sem definição oficial nos documentos da fonte."},
        ])
    else:
        a23, a24 = int(totais.loc[categoria, 2023]), int(totais.loc[categoria, 2024])
        ui.cartoes_html([
            {"titulo": f"{categoria} — 2023", "valor": fmt_int(a23), "detalhe": "fatos comunicados · 12 meses", "base": "Soma dos 12 meses publicados."},
            {"titulo": f"{categoria} — 2024", "valor": fmt_int(a24), "detalhe": "fatos comunicados · 12 meses", "variacao": f"{fmt_dif(a24 - a23)} vs 2023",
             "diferenca": a24 - a23, "base": "Comparado com 2023 (ano completo)."},
            {"titulo": "Meses com zero", "valor": fmt_int(int(vd.loc[vd["categoria"].eq(categoria), "valor"].eq(0).sum())), "detalhe": "de 24 meses",
             "base": "Zero informado é um número publicado."},
        ])

    # ------------------------------------------------------------------------------------------ gráfico e tabela
    figura = graficos.figura_violencia_domestica_ssp(vd, categoria)
    if categoria is None:
        tabela = totais.reset_index().rename(columns={"categoria": "Categoria", 2023: "2023", 2024: "2024"})
        tabela["Diferença 2024 − 2023"] = (totais[2024] - totais[2023]).map(fmt_dif).to_numpy()
        tabela = tabela.sort_values("2024", ascending=False).assign(**{"2023": lambda t: t["2023"].map(fmt_int), "2024": lambda t: t["2024"].map(fmt_int)})
        legenda = "Total anual de cada categoria (soma dos 12 meses). As categorias não são somadas entre si."
    else:
        mensal = vd.loc[vd["categoria"].eq(categoria)].pivot(index="mes", columns="ano", values="valor").reindex(range(1, 13))
        tabela = pd.DataFrame({"Mês": ABREV_MESES, "2023": mensal[2023].map(fmt_int).to_numpy(), "2024": mensal[2024].map(fmt_int).to_numpy()})
        legenda = f"{categoria}: valor publicado em cada mês."
    ui.mostrar_figura(figura, legenda, tabela)
    if categoria is None:
        st.caption("Leitura exploratória: descreve registros publicados; não demonstra variação do número de vítimas nem explica causas.")

# ------------------------------------------------------------------------------------------ fonte e limitações
with st.expander("Fonte, procedência e limitações da SSP/SC"):
    st.markdown(
        "- **Fonte:** SSP/SC — Segurança em Números, relatórios de violência doméstica (1º e 2º semestres de 2023 e ano de 2024), bloco do município de Joinville.\n"
        "- **Conferência:** os 216 registros (9 categorias × 24 meses, com 27 zeros) foram extraídos dos relatórios em PDF e **conferidos um a um** com as tabelas "
        "oficiais (159 verificações, todas aprovadas).\n"
        "- **Unidade em validação:** “Fato Comunicado” não tem definição oficial confirmada; por isso não é interpretado como vítimas, pessoas ou "
        "ocorrências únicas, e não se soma entre categorias.\n"
        "- **Separação metodológica:** estes números não são comparáveis automaticamente com as vítimas do Sinesp e não existe união das duas fontes.\n"
        "- **Reutilização:** as condições de reutilização da SSP/SC não foram avaliadas formalmente; os relatórios completos (inclusive boletins de homicídio, "
        "com versões divergentes entre si) não são publicados neste painel."
    )
