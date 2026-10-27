from scripts.utils import project_path


def test_readme_has_all_16_academic_items_and_real_results():
    readme = project_path("README.md").read_text(encoding="utf-8")
    for number in range(1, 17):
        assert f"## {number}. " in readme
    assert "900 registros Sinesp" in readme
    assert "22 em 2026" in readme
    assert "atendimentos da Guarda Municipal" in readme
    for directory in ("scripts", "dashboard", "notebooks", "documentacao", "dados", "tests", "video"):
        assert not list(project_path(directory).rglob("README.md"))


def test_main_script_exposes_authorized_stages_and_keeps_exports_inactive():
    pipeline = project_path("scripts", "analise_seguranca_publica.py").read_text(encoding="utf-8")
    assert "# %%" in pipeline
    for stage in range(1, 11):
        assert f"ETAPA {stage} " in pipeline
    # Etapas SSP/SC: 11 e 12 deixaram de ser planejamento de exportação; 13.x e 14.1 foram implementadas.
    assert "ETAPA 11 — Inspeção dos dados brutos SSP/SC" in pipeline
    assert "ETAPA 12 — Auditoria das inconsistências SSP/SC" in pipeline
    for stage in (
        "ETAPA 13.1 — Inspeção e exibição dos dados brutos de violência doméstica",
        "ETAPA 13.2 — Construção da base analítica de violência doméstica",
        "ETAPA 13.3 — Validação integral da base analítica de violência doméstica",
        "ETAPA 14.1 — Análise exploratória e estatísticas descritivas da violência doméstica",
    ):
        assert f"# # {stage}" in pipeline
    # Etapas futuras não podem aparecer como implementadas.
    assert "ETAPA 14.2" not in pipeline
    assert "from scripts import transform" in pipeline
    assert "read_excel(" in pipeline and "read_csv(" in pipeline
    assert "data_referencia_joinville_20" in pipeline
    assert "ssp_contexto_pagina_8" in pipeline
    assert "df_sinesp_joinville_analitico" in pipeline
    assert "fig_homicidio_anual_sinesp" in pipeline
    assert "fig_mulher_jan_ago_sinesp" in pipeline
    # Bases analíticas da violência doméstica SSP/SC e rotinas da EDA da Etapa 14.1.
    for name in (
        "df_violencia_domestica_joinville_ssp132",
        "rastreabilidade_violencia_domestica_ssp132",
        "conferencia_valores_ssp133",
        "resumo_validacoes_ssp133",
        "estatisticas_24_meses_eda141",
        "comparacao_anual_eda141",
        "extremos_eda141",
        "verificacoes_quadro_eda141",
    ):
        assert name in pipeline
    # O roteiro continua sem exportar arquivos: nenhuma linha ativa (não comentada) grava dados ou figuras.
    for line in pipeline.splitlines():
        code = line.split("#", 1)[0]
        for call in (".to_csv(", ".to_excel(", ".to_parquet(", ".savefig("):
            assert call not in code


def test_readme_documents_ssp_stages_and_keeps_pending_items_pending():
    readme = project_path("README.md").read_text(encoding="utf-8")
    for expected in (
        "45 PDFs", "25.753", "58 grupos", "41 com valores divergentes",
        "216 linhas × 5 colunas", "216 × 23", "67 verificações aprovadas", "Fato Comunicado",
        "27 zeros publicados",
    ):
        assert expected in readme
    # Etapa 14.2 e o deploy permanecem pendentes; não pode haver link de aplicação publicada.
    assert "14.2" in readme
    assert "Aplicação Streamlit publicada: pendente." in readme
    assert "streamlit.app" not in readme


def test_app_has_project_and_data_quality_navigation():
    app = project_path("scripts", "painel_streamlit.py").read_text(encoding="utf-8")
    assert 'project_path("dashboard", "pages", "home.py")' in app
    assert 'project_path("dashboard", "pages", "quality.py")' in app
    assert project_path("dashboard", "pages", "home.py").is_file()
    assert project_path("dashboard", "pages", "quality.py").is_file()
