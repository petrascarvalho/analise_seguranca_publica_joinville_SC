"""Seções "Qualidade dos dados" e "Fontes, metodologia e limitações", escritas para o público em geral.

Os detalhes técnicos (código de conferência dos arquivos, identificador da versão) ficam em um bloco recolhido no fim da primeira seção.
O passo a passo para reproduzir o projeto fica no README.md, não aqui.
"""

import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from dashboard import ui  # noqa: E402
from dashboard.formatacao import fmt_competencia, fmt_int, fmt_mes_extenso  # noqa: E402

sinesp, catalogo = ui.carregar_dados_consistentes()
manifesto = ui.carregar_manifesto()
integridade = ui.verificar_integridade()
cobertura = manifesto.get("cobertura", {}).get("sinesp", {})
primeira, ultima = cobertura.get("primeira_competencia", ""), cobertura.get("ultima_competencia", "")
periodo = ui.periodo_sinesp_texto(manifesto)
atualizacao = ui.data_da_atualizacao(manifesto)

# ------------------------------------------------------------------------------------------ 1. qualidade dos dados
ui.secao("Qualidade dos dados", "qualidade", "O que foi conferido, até quando vão os dados e o que ainda exige cuidado na leitura.")

if integridade["integro"].all():
    st.info(f"Conferência concluída: os {len(integridade)} arquivos de dados usados pelo painel coincidem com o registro da base de {atualizacao}.", icon="✅")

# Quatro cards com o essencial; cada card é um dicionário (ver ui.cartoes_html).
ui.cartoes_html([
    {"titulo": "Arquivos conferidos", "valor": f"{int(integridade['integro'].sum())} de {len(integridade)}", "detalhe": "dados do painel × registro da versão",
     "base": "Cada arquivo é comparado com o registro da versão."},
    {"titulo": "Base atualizada em", "valor": atualizacao, "detalhe": "Sinesp/MJSP · Joinville/SC", "base": "Atualização manual, depois de conferência."},
    {"titulo": "Último mês disponível nesta base", "valor": fmt_competencia(ultima, curto=True), "detalhe": f"Dados a partir de {fmt_competencia(primeira, curto=True)}",
     "base": f"{fmt_mes_extenso(ultima)}. A série da PRF termina em agosto de 2026; os mandados da PF começam em 2025."},
    {"titulo": "Valores ausentes", "valor": fmt_int(int(sinesp["valor"].isna().sum())), "detalhe": f"Zeros informados: {fmt_int(int(sinesp['valor'].eq(0).sum()))}",
     "base": "Ausência nunca é trocada por zero."},
])

st.subheader("Sobre os dados apresentados")
st.markdown(
    f"- **Fonte dos dados:** Sinesp/MJSP (Sistema Nacional de Estatísticas de Segurança Pública, do Ministério da Justiça e Segurança Pública).\n"
    f"- **Município analisado:** Joinville/SC. {ui.NOTA_ABRANGENCIA_CURTA}\n"
    f"- **Base atualizada em:** {atualizacao}. Pode não incluir publicações mais recentes da fonte.\n"
    f"- **Período do Sinesp:** {periodo} (último mês disponível nesta base: {fmt_mes_extenso(ultima)}). A série da Polícia Rodoviária Federal vai até agosto de 2026.\n"
    f"- **Ano de 2026 parcial:** só se compara com o mesmo período dos anos anteriores, nunca com anos completos.\n"
    f"- **Zero informado e ausência são diferentes:** zero é um número publicado pela fonte; ausência é a falta de informação e nunca é preenchida.\n"
    f"- **Conferências do projeto:** os dados passaram por verificações de consistência (formato das colunas, repetições, meses faltando, unidades e "
    f"comparação com o registro da versão). É uma conferência interna do projeto: **não é uma aprovação ou certificação oficial do governo**."
)

with st.expander("Detalhes técnicos de conferência (opcional)"):
    st.markdown(f"Identificador da versão dos dados: `{manifesto.get('versao', '—')}`. Cada arquivo tem um código de conferência (SHA-256); se o arquivo mudar, "
                "o código muda e o painel avisa.")
    fichas = pd.DataFrame(manifesto["arquivos"])[["arquivo", "linhas", "colunas", "sha256"]]
    fichas = fichas.merge(integridade[["arquivo", "integro"]], on="arquivo", how="left")
    fichas["Conferência"] = fichas["integro"].map({True: "✅ confere", False: "❌ diverge"})
    fichas["linhas"] = fichas["linhas"].map(fmt_int)
    st.dataframe(fichas.drop(columns="integro").rename(columns={"arquivo": "Arquivo", "linhas": "Linhas", "colunas": "Colunas", "sha256": "Código de conferência (SHA-256)"}),
                 hide_index=True)
if not integridade["integro"].all():
    st.error("Um ou mais arquivos não coincidem com o registro da versão. Os números exibidos podem não corresponder aos dados conferidos.")

# ------------------------------------------------------------------------------------------ 2. fontes, metodologia e limitações
ui.secao("Fontes, metodologia e limitações", "metodologia", "De onde vêm os números, como foram tratados e o que eles não permitem afirmar.")
abas = st.tabs(["Origem dos dados", "Como os números são tratados", "Limitações"])

# ------------------------------------------------------------------ origem dos dados
with abas[0]:
    st.subheader("Sinesp/MJSP")
    st.markdown("As informações foram obtidas em bases oficiais do Sinesp/MJSP. Foram selecionados os registros referentes ao município de Joinville/SC "
                "e realizadas etapas de organização, tratamento e conferência. Os arquivos originais completos não são redistribuídos por este painel.")
    st.info(ui.NOTA_ABRANGENCIA)
    for fonte in manifesto.get("fontes", []):
        st.markdown(f"**Página oficial:** [{fonte['nome']}]({fonte['url']})")
        publicacao = fonte.get("publicacao") or {}
        if publicacao.get("pagina_atualizada_em"):
            st.caption(f"Datas informadas pela própria página da fonte: publicada em {publicacao.get('pagina_publicada_em', '—')} e atualizada em "
                       f"{publicacao['pagina_atualizada_em']}. São datas da página; não indicam, por si, mudança nos números.")

    st.subheader("Cobertura por indicador")
    st.markdown("**Unidades:** *vítimas* (número de vítimas registradas) e *mandados cumpridos* (contagem publicada de mandados de prisão cumpridos). "
                "As duas unidades nunca são somadas.")
    tabela = catalogo.rename(columns={
        "evento": "Indicador", "abrangencia": "Abrangência", "unidade": "Unidade", "meses_observados": "Meses", "meses_com_valor": "Com valor",
        "meses_valor_zero": "Zeros informados", "meses_sem_valor": "Sem valor"})
    tabela["Início"] = tabela["inicio"].map(lambda c: fmt_competencia(c, curto=True))
    tabela["Última competência"] = tabela["fim"].map(lambda c: fmt_competencia(c, curto=True))
    st.dataframe(tabela[["Indicador", "Abrangência", "Unidade", "Início", "Última competência", "Meses", "Com valor", "Zeros informados", "Sem valor"]], hide_index=True)
    st.markdown(
        f"- **Total:** {fmt_int(len(sinesp))} registros mensais em {len(catalogo)} séries; **valores ausentes:** {int(sinesp['valor'].isna().sum())} "
        f"(nunca trocados por zero); **zeros informados:** {fmt_int(int(sinesp['valor'].eq(0).sum()))}.\n"
        "- Séries que terminam em meses diferentes (como a PRF) aparecem só até o último mês disponível, sem preenchimento; a Polícia Federal só tem registros "
        "a partir do início da sua série."
    )

    st.subheader("SSP/SC — violência doméstica (fonte separada)")
    st.markdown(
        "- **Origem:** relatórios oficiais de violência doméstica da Secretaria de Estado da Segurança Pública de SC (“Segurança em Números”), com os "
        "números do município de Joinville em 2023 e 2024. Os números foram lidos dos relatórios em PDF e conferidos nas tabelas oficiais.\n"
        "- **Situação:** fonte **em validação**. A unidade “Fato Comunicado” não tem definição oficial confirmada: não equivale a vítimas, pessoas ou ocorrências "
        "únicas e não é comparável com o Sinesp.\n"
        "- **Uso:** as categorias não são somadas e os números são mostrados em seção separada. As condições de reutilização da fonte não foram avaliadas "
        "formalmente; por isso os relatórios completos não são publicados."
    )

# ------------------------------------------------------------------ como os números são tratados
with abas[1]:
    st.subheader("Do dado oficial ao painel")
    st.markdown(
        "- **Seleção:** foram mantidos somente os registros de Joinville/SC.\n"
        "- **Datas e medidas:** cada registro é ligado a um mês. Vítimas e mandados cumpridos são medidas diferentes e nunca são somados.\n"
        "- **Ausência e zero:** campo vazio continua vazio; zero informado continua zero.\n"
        "- **Repetições:** nenhum registro é apagado. Linhas repetidas no mesmo mês só são somadas nos dois casos em que a nota oficial do Sinesp prevê "
        "(tentativa de homicídio e estupro), com aviso.\n"
        "- **Conferências:** verificação do formato, de meses faltando, de unidades diferentes na mesma série e de mudanças nos valores já publicados."
    )
    st.subheader("Regras dos números e dos gráficos")
    st.markdown(
        "- **Totais anuais** só existem quando todos os 12 meses têm valor. Os anos parciais nunca são comparados com anos completos: compara-se janeiro até o "
        "mesmo mês nos dois anos.\n"
        "- **Variação percentual** só é calculada quando o ponto de partida é maior que zero; a diferença em números absolutos sempre aparece, pois em "
        "contagens pequenas o percentual engana.\n"
        "- **Rankings** comparam indicadores só dentro da mesma unidade, sem somar indicadores diferentes.\n"
        "- **Gráficos** começam do zero, mostram a fonte, a unidade e o período, e usam o mesmo tom de azul para o mesmo ano.\n"
        "- **Estatísticas** (média, mediana, desvio-padrão) descrevem os meses publicados; não são previsões.\n"
        "- **Limites de referência (IQR)** são um critério estatístico aplicado a cada série para destacar meses diferentes dos demais. Não são metas, limites legais "
        "nem parâmetros oficiais de segurança pública, e um mês fora deles não indica, por si só, problema ou mudança real.\n"
        "- **Mediana de cada mês do ano** compara os mesmos meses de anos completos; com poucos anos, não permite afirmar que exista um padrão sazonal."
    )

# ------------------------------------------------------------------ limitações
with abas[2]:
    st.subheader("O que estes números não mostram")
    st.markdown(
        "- São registros administrativos agregados: não medem toda a criminalidade ocorrida e não permitem apontar causas.\n"
        "- Não há taxas por habitante (falta uma base de população compatível), nem dados por bairro, rua, horário ou corporação.\n"
        "- As séries “Estadual”, “Polícia Federal” e “Polícia Rodoviária Federal” têm coberturas diferentes e não são somadas. Mandados não são pessoas únicas.\n"
        "- A fonte pode revisar números já publicados; revisões só entram no painel depois de conferidas.\n"
        "- Contagens pequenas geram variações percentuais instáveis: observe sempre a diferença em números absolutos.\n"
        "- **SSP/SC (violência doméstica):** fonte separada e em validação; “Fato Comunicado” não tem definição oficial confirmada, não é vítima nem ocorrência "
        "única e não se soma ao Sinesp. Detalhes na seção própria."
    )

# ------------------------------------------------------------------------------------------ fonte, atualização e condições de uso
st.divider()
ui.mostrar_versao_dos_dados()
