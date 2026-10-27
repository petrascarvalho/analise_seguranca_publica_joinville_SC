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
    for stage in (11, 12):
        assert f"ETAPA {stage} — Planejamento" in pipeline
    assert "from scripts import transform" in pipeline
    assert "read_excel(" in pipeline and "read_csv(" in pipeline
    assert "data_referencia_joinville_20" in pipeline
    assert "ssp_contexto_pagina_8" in pipeline
    assert "df_sinesp_joinville_analitico" in pipeline
    assert "fig_homicidio_anual_sinesp" in pipeline
    assert "fig_mulher_jan_ago_sinesp" in pipeline


def test_app_has_project_and_data_quality_navigation():
    app = project_path("scripts", "painel_streamlit.py").read_text(encoding="utf-8")
    assert 'project_path("dashboard", "pages", "home.py")' in app
    assert 'project_path("dashboard", "pages", "quality.py")' in app
    assert project_path("dashboard", "pages", "home.py").is_file()
    assert project_path("dashboard", "pages", "quality.py").is_file()
