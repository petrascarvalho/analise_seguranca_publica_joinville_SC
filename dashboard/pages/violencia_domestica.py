"""Seção "VIOLÊNCIA DOMÉSTICA — SSP/SC": exploração separada, em validação, com filtro próprio de categoria.

Regras desta seção (não negociáveis):
    • "Fato Comunicado" NÃO tem definição operacional confirmada: não é vítima, pessoa única nem ocorrência única.
    • Categorias nunca são somadas entre si e os números nunca são misturados com os indicadores de vítimas do Sinesp.
    • O acervo completo da SSP/SC (PDFs e boletins) não é publicado; esta seção usa só as 216 observações já conferidas.
    • Sem o arquivo local (por exemplo, no Streamlit Cloud), a seção informa a limitação e mostra apenas a figura exploratória já versionada.
"""

import sys
from pathlib import Path

# Pasta do projeto: entra no caminho de importação para o Python achar o pacote dashboard.
_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard import dados_ssp, graficos, ui  # noqa: E402
from dashboard.formatacao import ABREV_MESES, fmt_dif, fmt_int  # noqa: E402

ui.secao("VIOLÊNCIA DOMÉSTICA — SSP/SC", "violencia-domestica",
         "Exploração separada do Sinesp: dados da Secretaria de Estado da Segurança Pública de SC (SSP/SC) para o município de Joinville, de janeiro/2023 a dezembro/2024.")
st.warning("**Fonte em validação.** Não foi identificada uma definição operacional de “Fato Comunicado” nos documentos analisados; por isso a unidade não deve "
           "ser lida como vítimas, pessoas ou ocorrências únicas. Não some categorias nem compare estes números com os do Sinesp.")

try:
    # Lê o CSV local da SSP/SC (216 linhas) e confere as regras; devolve None se o arquivo não existir (ex.: no Streamlit Cloud).
    vd = dados_ssp.carregar_violencia_domestica()
# Se o arquivo existir mas violar alguma regra, mostra o erro e st.stop() interrompe a página.
except dados_ssp.ErroDadosSsp as erro:
    st.error(f"**Dados da SSP/SC inválidos.** {erro} Nenhum valor foi preenchido ou estimado.")
    st.stop()

if vd is None:
    # Sem o CSV local (clone limpo, Streamlit Cloud): não há dado para filtrar. Mostra só a figura exploratória que já está no repositório.
    st.info("Os dados detalhados de violência doméstica da SSP/SC não estão disponíveis nesta versão pública do painel: as condições de reutilização da fonte "
            "ainda não foram avaliadas formalmente e os relatórios completos não são divulgados. Abaixo, uma figura-resumo com os totais anuais por categoria.")
    if dados_ssp.FIGURA_ESTATICA.is_file():
        # st.image mostra a figura-resumo já salva (PNG); é o que aparece no Streamlit Cloud, onde o CSV não existe.
        st.image(str(dados_ssp.FIGURA_ESTATICA), caption="Fatos comunicados por categoria, 2023 × 2024 (SSP/SC). Unidade em validação; não integra os indicadores Sinesp.")
else:
    # ------------------------------------------------------------------------------------------ filtro próprio e cards
    # As 9 categorias, sem repetição e em ordem alfabética: opções do filtro desta seção.
    categorias = sorted(vd["categoria"].unique())
    with st.container(border=True):
        st.markdown("**Filtro desta seção** — independente dos filtros do Sinesp.")
        # Filtro próprio da seção (key diferente dos filtros do Sinesp, por isso um não altera o outro).
        escolha = st.selectbox("Categoria (SSP/SC)", ["Todas as categorias"] + categorias, key="vd_categoria",
                               help="“Todas” compara cada categoria com ela mesma em 2023 e 2024; uma categoria específica mostra os 24 meses.")
    # None significa "todas as categorias".
    categoria = None if escolha == "Todas as categorias" else escolha

    # groupby junta as linhas de mesma categoria e ano; sum() soma os 12 meses; unstack põe os anos (2023, 2024) em colunas.
    totais = vd.groupby(["categoria", "ano"])["valor"].sum().unstack("ano")   # soma dos 12 meses de cada categoria e ano; nunca entre categorias
    if categoria is None:
        ui.cartoes_html([
            {"titulo": "Período", "valor": "2023–2024", "detalhe": "SSP/SC · Joinville", "base": "Janeiro/2023 a dezembro/2024 (24 meses)."},
            {"titulo": "Registros", "valor": fmt_int(len(vd)), "detalhe": f"{len(categorias)} categorias × 24 meses", "base": "Sem registros repetidos e sem valores ausentes."},
            # 27 = valores zero entre as 216 combinações de categoria e mês (9 categorias × 24 meses); não são 27 meses distintos
            {"titulo": "Valores zero informados", "valor": fmt_int(int(vd["valor"].eq(0).sum())), "detalhe": f"nas {len(categorias)} categorias, 2023–2024",
             "base": "Em " + fmt_int(int(vd["valor"].eq(0).sum())) + " combinações de categoria e mês, a fonte informou valor zero. Zero informado não significa ausência de dados e não permite concluir que não houve vítimas no município."},
            {"titulo": "Unidade", "valor": "Em validação", "detalhe": "Fato Comunicado", "base": "Definição não identificada nos documentos analisados."},
        ])
    else:
        # Total da categoria escolhida em cada ano (.loc[linha, coluna]).
        a23, a24 = int(totais.loc[categoria, 2023]), int(totais.loc[categoria, 2024])
        # Conta os meses com valor zero só da categoria escolhida: eq(0) marca True nos zeros e sum() conta os True.
        zeros_categoria = int(vd.loc[vd["categoria"].eq(categoria), "valor"].eq(0).sum())
        ui.cartoes_html([
            {"titulo": f"{categoria} — 2023", "valor": fmt_int(a23), "detalhe": "fatos comunicados · 12 meses", "base": "Soma dos 12 meses publicados."},
            {"titulo": f"{categoria} — 2024", "valor": fmt_int(a24), "detalhe": "fatos comunicados · 12 meses", "variacao": f"{fmt_dif(a24 - a23)} vs 2023",
             "diferenca": a24 - a23, "base": "Comparado com 2023 (ano completo)."},
            # Zeros só da categoria escolhida (valor de cada um dos 24 meses); o total de 27 vale só para "Todas as categorias"
            {"titulo": "Valores zero informados", "valor": "Nenhum" if zeros_categoria == 0 else fmt_int(zeros_categoria),
             "detalhe": "valor zero nesta categoria, 2023–2024" if zeros_categoria == 0 else "nesta categoria, em 24 meses",
             "base": "Nenhum dos 24 meses desta categoria teve valor zero informado pela fonte." if zeros_categoria == 0
                     else f"Em {fmt_int(zeros_categoria)} dos 24 meses desta categoria, a fonte informou valor zero. Zero informado não significa ausência de dados e não permite concluir que não houve vítimas no município."},
        ])

    # ------------------------------------------------------------------------------------------ gráfico e tabela
    # Todas as categorias: barras horizontais 2023 x 2024; uma categoria: duas linhas com os 24 meses.
    figura = graficos.figura_violencia_domestica_ssp(vd, categoria)
    if categoria is None:
        tabela = totais.reset_index().rename(columns={"categoria": "Categoria", 2023: "2023", 2024: "2024"})
        # Subtrai as colunas inteiras de uma vez (2024 - 2023) e formata com sinal (+128, −9).
        tabela["Diferença 2024 − 2023"] = (totais[2024] - totais[2023]).map(fmt_dif).to_numpy()
        tabela = tabela.sort_values("2024", ascending=False)  # ordena pelo número; só depois formata o texto
        tabela["2023"] = tabela["2023"].map(fmt_int)
        tabela["2024"] = tabela["2024"].map(fmt_int)
        legenda = "Total anual de cada categoria (soma dos 12 meses). As categorias não são somadas entre si."
    else:
        # Tabela mês x ano da categoria: pivot põe os anos em colunas; reindex garante os 12 meses em ordem.
        mensal = vd.loc[vd["categoria"].eq(categoria)].pivot(index="mes", columns="ano", values="valor").reindex(range(1, 13))
        tabela = pd.DataFrame({"Mês": ABREV_MESES, "2023": mensal[2023].map(fmt_int).to_numpy(), "2024": mensal[2024].map(fmt_int).to_numpy()})
        legenda = f"{categoria}: valor publicado em cada mês."
    ui.mostrar_figura(figura, legenda, tabela)
    if categoria is None:
        st.caption("Leitura simples: descreve os registros publicados; não mostra variação no número de vítimas nem explica causas.")

# ------------------------------------------------------------------------------------------ fonte e limitações
with st.expander("Fonte, procedência e limitações da SSP/SC"):
    st.markdown(
        "- **Fonte:** SSP/SC — Segurança em Números, relatórios de violência doméstica (1º e 2º semestres de 2023 e ano de 2024), bloco do município de Joinville.\n"
        "- **Conferência:** os 216 registros (9 categorias × 24 meses, com 27 zeros) foram extraídos dos relatórios em PDF e **conferidos um a um** com as tabelas "
        "oficiais (159 verificações, todas aprovadas).\n"
        "- **Unidade em validação:** não foi identificada uma definição operacional de “Fato Comunicado” nos documentos analisados (isso não significa que a "
        "definição não exista na SSP/SC); por isso a unidade não é interpretada como vítimas, pessoas ou ocorrências únicas e não se soma entre categorias.\n"
        "- **Separação metodológica:** estes números não são comparáveis automaticamente com as vítimas do Sinesp e não existe união das duas fontes.\n"
        "- **Reutilização:** as condições de reutilização da SSP/SC não foram avaliadas formalmente; os relatórios completos (inclusive boletins de homicídio, "
        "com versões divergentes entre si) não são publicados neste painel."
    )
