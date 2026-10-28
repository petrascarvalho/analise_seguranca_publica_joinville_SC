"""Testes HISTÓRICOS: etapas SSP/SC (11–14.2) que permanecem no roteiro acadêmico, fora do escopo do produto.

Não fazem parte da suíte ativa (``tests/``). Executar com ``python -m pytest tests_historicos -q``.
"""

from src.pipeline.utils import project_path


def test_roteiro_preserva_as_etapas_historicas_ssp_sc():
    pipeline = project_path("historico", "scripts", "analise_seguranca_publica.py").read_text(encoding="utf-8")
    assert "ETAPA 11 — Inspeção dos dados brutos SSP/SC" in pipeline
    assert "ETAPA 12 — Auditoria das inconsistências SSP/SC" in pipeline
    for stage in (
        "ETAPA 13.1 — Inspeção e exibição dos dados brutos de violência doméstica",
        "ETAPA 13.2 — Construção da base analítica de violência doméstica",
        "ETAPA 13.3 — Validação integral da base analítica de violência doméstica",
        "ETAPA 14.1 — Análise exploratória e estatísticas descritivas da violência doméstica",
    ):
        assert f"# # {stage}" in pipeline
    assert "# # ETAPA 14.2 — Visualizações da violência doméstica de Joinville" in pipeline
    for figure in (
        "fig_anual_maiores_ssp142", "fig_anual_intermediarias_ssp142", "fig_anual_menores_ssp142",
        "fig_mensal_ameaca_ssp142", "fig_mensal_lesao_leve_ssp142", "fig_mensal_injuria_ssp142",
        "conferencia_visualizacoes_viz142",
    ):
        assert figure in pipeline
    assert "ETAPA 14.3" not in pipeline
    assert "ssp_contexto_pagina_8" in pipeline
    for name in (
        "df_violencia_domestica_joinville_ssp132", "rastreabilidade_violencia_domestica_ssp132", "conferencia_valores_ssp133",
        "resumo_validacoes_ssp133", "estatisticas_24_meses_eda141", "comparacao_anual_eda141", "extremos_eda141", "verificacoes_quadro_eda141",
    ):
        assert name in pipeline


def test_documentacao_historica_ssp_sc_esta_indexada():
    indice = project_path("historico", "ssp_sc", "LEIAME.md").read_text(encoding="utf-8")
    assert "bad9723" in indice and "Fora do escopo do produto entregue" in indice
    for caminho in ("historico/ssp_sc/documentacao/SSP_SC.md", "historico/ssp_sc/documentacao/CSV_COMPLEMENTARES.md", "historico/ssp_sc/documentacao/ssp_csv_extraction_etapa_1_1.md"):
        assert caminho in indice and project_path(*caminho.split("/")).is_file()


def test_roteiro_antigo_preserva_as_etapas_sinesp_1_a_10_sem_exportar_arquivos():
    pipeline = project_path("historico", "scripts", "analise_seguranca_publica.py").read_text(encoding="utf-8")
    assert "# %%" in pipeline
    for stage in range(1, 11):
        assert f"ETAPA {stage} " in pipeline
    assert "from src.pipeline import transform" in pipeline and "df_sinesp_joinville_analitico" in pipeline
    assert "fig_homicidio_anual_sinesp" in pipeline and "fig_mulher_jan_ago_sinesp" in pipeline
    for line in pipeline.splitlines():
        code = line.split("#", 1)[0]
        for call in (".to_csv(", ".to_excel(", ".to_parquet(", ".savefig("):
            assert call not in code
