import sys
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[2]
if str(_RAIZ) not in sys.path:
    sys.path.insert(0, str(_RAIZ))

import streamlit as st  # noqa: E402

from dashboard import calculos, ui  # noqa: E402
from dashboard.formatacao import fmt_int  # noqa: E402

st.title("Segurança Pública de Joinville/SC — Indicadores Sinesp/MJSP")
st.caption("Projeto acadêmico individual de Visualização de Dados e BI — SENAI/LAB365, Módulo 2, Semana 13")

sinesp, catalogo = ui.carregar_dados_consistentes()
manifesto = ui.carregar_manifesto()
periodo = ui.periodo_sinesp_texto(manifesto)
cobertura = manifesto.get("cobertura", {}).get("sinesp", {})
parcial = cobertura.get("ano_parcial")

st.subheader("Pergunta analítica")
st.markdown(
    "**Como evoluíram, desde janeiro/2020, os indicadores oficiais de segurança pública do Sinesp/MJSP para Joinville/SC, e o que a comparação "
    "entre períodos equivalentes permite — e não permite — afirmar sobre essa evolução?**"
)
c1, c2 = st.columns(2)
with c1:
    st.subheader("Objetivo")
    st.write(
        "Organizar, validar e apresentar de forma transparente as séries mensais municipais publicadas pelo Sinesp/MJSP, com filtros por indicador, "
        "abrangência e período, estatísticas descritivas e comparações entre anos completos e entre períodos equivalentes, sempre com fonte, unidade e limitações explícitas."
    )
with c2:
    st.subheader("Relevância")
    st.write(
        "Estudantes, cidadãos, pesquisadores e gestores podem consultar a evolução de indicadores como homicídio, feminicídio, tentativas, latrocínio, "
        "mortes no trânsito, suicídio e mandados cumpridos em Joinville, de modo reprodutível e auditável, sem confundir registros administrativos com a totalidade dos crimes."
    )

st.subheader("Fonte única e período disponível")
st.markdown(
    f"- **Fonte oficial:** MJSP / Sinesp VDE (base de dados nacional dos gestores estaduais), recorte exato **Joinville/SC** — única fonte deste painel.\n"
    f"- **Período realmente disponível:** **{periodo}**{f' (**{parcial} é parcial**; cada série vai até a sua última competência)' if parcial else ''}.\n"
    f"- **Séries:** {len(catalogo)} combinações indicador × abrangência (Estadual, Polícia Federal e PRF), {fmt_int(len(sinesp))} observações mensais.\n"
    "- **Unidades:** *vítimas* (feminicídio, homicídio doloso, tentativas, lesão seguida de morte, latrocínio, suicídio, mortes no trânsito e a esclarecer) e "
    "*mandados cumpridos* — conceitos distintos que **nunca são somados**."
)
tabela_ultimas = catalogo[["evento", "abrangencia", "fim"]].copy()
atrasadas = tabela_ultimas.loc[tabela_ultimas["fim"] != tabela_ultimas["fim"].max()]
if len(atrasadas):
    st.info("Algumas séries terminam antes das demais: " + "; ".join(f"{r.evento} ({r.abrangencia}) até {r.fim}" for r in atrasadas.itertuples())
            + ". Isso é informado, não corrigido nem preenchido.")

st.subheader("Principais achados (descritivos)")
for achado in calculos.achados_principais(sinesp):
    st.markdown(f"**{achado['titulo']}.** {achado['texto']}")
st.caption("São observações sobre contagens publicadas, não explicações. Nenhuma causa é afirmada.")

st.subheader("Unidades e limitações")
st.markdown(
    "- Os valores são **registros administrativos agregados** publicados pelo Sinesp; não medem toda a criminalidade ocorrida, não estimam subnotificação e não permitem inferir causalidade.\n"
    "- **Sem taxas populacionais** (não há base demográfica oficial compatível neste projeto), sem dados por bairro, rua, horário ou corporação.\n"
    "- **Sem total geral:** indicadores, abrangências e unidades diferentes não são somados.\n"
    "- O último ano de cada série pode ser **parcial** e não é comparado com anos completos; compara-se o mesmo período (janeiro até o último mês publicado).\n"
    "- Zeros publicados são observações; ausência de cobertura (p.ex. PF antes de 2025) não é zero.\n"
    "- Contagens pequenas geram variações percentuais instáveis; observe sempre a magnitude absoluta."
)

st.info(
    "**Situação:** versão local de desenvolvimento preparada para o Streamlit Community Cloud; **não há deploy público confirmado**. Os dados exibidos são uma versão histórica "
    "validada (página *Qualidade e metodologia*); a atualização é manual e controlada e o painel nunca baixa dados."
)
m1, m2, m3 = st.columns(3)
m1.metric("Observações mensais", fmt_int(len(sinesp)), help="Linhas da série mensal (indicador × abrangência × competência)")
m2.metric("Séries", len(catalogo))
m3.metric("Última competência", cobertura.get("ultima_competencia", "—"))
st.caption("Fonte: MJSP / Sinesp VDE. Use a navegação lateral para explorar os indicadores e conferir a qualidade dos dados.")
