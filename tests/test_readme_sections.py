import re

from src.pipeline.utils import project_path

URL_STREAMLIT = "https://seguranca-publica-joinville-sinesp.streamlit.app/"
DOCUMENTOS_ATIVOS = {
    "README.md": ("README.md",),
    "ESCOPO_PROJETO.md": ("documentacao", "analises", "ESCOPO_PROJETO.md"),
    "ATUALIZACAO_DE_DADOS.md": ("documentacao", "analises", "ATUALIZACAO_DE_DADOS.md"),
    "DEPLOY_STREAMLIT.md": ("documentacao", "painel", "DEPLOY_STREAMLIT.md"),
    "LEIAME.md": ("dashboard", "data_publica", "LEIAME.md"),
}


def _ler(*partes) -> str:
    return project_path(*partes).read_text(encoding="utf-8")


def test_readme_has_all_16_academic_items_and_real_results():
    readme = _ler("README.md")
    for number in range(1, 17):
        assert f"## {number}. " in readme
    assert "900 registros Sinesp" in readme and "911 observações" in readme
    assert "25 em 2026" in readme and "22 em janeiro–agosto de 2026" in readme
    assert "janeiro/2020 a setembro/2026" in readme
    assert "atendimentos da Guarda Municipal" in readme
    for directory in ("scripts", "dashboard", "notebooks", "documentacao", "dados", "tests", "tests_historicos", "video"):
        assert not list(project_path(directory).rglob("README.md"))


def test_etl_e_notebook_sao_os_roteiros_principais_e_o_antigo_e_historico():
    etl = _ler("scripts", "etl_sinesp.py")
    assert "# %%" in etl and "ETAPA 01" in etl and "ETAPA 18" in etl
    assert project_path("notebooks", "analise_sinesp.ipynb").is_file()
    assert not project_path("scripts", "analise_sinesp.py").exists()  # renomeado para etl_sinesp.py
    assert project_path("historico", "scripts", "analise_seguranca_publica.py").is_file()  # roteiro antigo preservado (histórico SSP/SC)
    assert sorted(p.name for p in project_path("scripts").glob("*.py")) == ["etl_sinesp.py", "painel_streamlit.py"]  # só os dois pontos principais
    readme = _ler("README.md")
    assert "scripts/etl_sinesp.py" in readme and "-m scripts.etl_sinesp" in readme
    assert "notebooks/analise_sinesp.ipynb" in readme and "dados/processados/sinesp" in readme
    assert r".\.venv\Scripts\python.exe" in readme  # comandos testados no Windows
    assert "histórico" in readme.split("historico/scripts/analise_seguranca_publica.py", 1)[1][:400].lower()


def test_readme_declara_fonte_unica_sinesp_e_trata_ssp_e_prefeitura_como_historico():
    readme = _ler("README.md")
    for esperado in (
        "fonte única", "Sinesp/MJSP", "Joinville/SC", "SSP/SC e Prefeitura/SEPROT", "fora do escopo", "historico/ssp_sc/LEIAME.md", "bad9723",
        "Indicadores Sinesp", "Qualidade e metodologia", "três páginas",
    ):
        assert esperado in readme, esperado
    for proibido in ("quatro páginas", "4 páginas", "Violência doméstica SSP/SC**:", "várias fontes", "múltiplas fontes"):
        assert proibido not in readme, proibido
    # Pendências de entrega continuam pendentes; nenhum link inventado; Trello dispensado.
    assert f"Aplicação Streamlit publicada: <{URL_STREAMLIT}>" in readme and "Aplicação Streamlit publicada: pendente" not in readme
    assert "revisão visual" in readme and "dispositivos móveis" in readme  # deploy feito; revisão visual e celular não afirmados
    assert "Trello" in readme and "dispensad" in readme
    for pendente in ("Repositório oficial da turma: pendente", "Vídeo", "AVA"):
        assert pendente in readme, pendente


def test_navegacao_documentada_tem_tres_paginas_e_sem_pagina_ssp():
    app = _ler("scripts", "painel_streamlit.py")
    for page in ("home.py", "sinesp.py", "quality.py"):
        assert f'_RAIZ / "dashboard" / "pages" / "{page}"' in app
        assert project_path("dashboard", "pages", page).is_file()
    assert app.count("st.Page(") == 3 and "st.navigation(" in app
    assert not project_path("dashboard", "pages", "violencia_domestica.py").exists()


def test_readme_documenta_atualizacao_controlada_licencas_testes_e_deploy_sem_inventar_url():
    readme = _ler("README.md")
    for expected in (
        "python -m src.pipeline.atualizacao_dados verificar", "aprovar <id> --confirmo <id>", "Não há atualização automática operacional",
        "documentacao/analises/ATUALIZACAO_DE_DADOS.md", "documentacao/painel/DEPLOY_STREAMLIT.md", "não pôde ser confirmado", "CC BY-ND",
        "Deploy realizado", "-m pytest tests -q", "-m pytest tests_historicos -q",
        "20261027T114400Z",
    ):
        assert expected in readme, expected
    assert re.search(r"\*\*\d+ testes aprovados\*\*", readme), "o README deve informar a contagem de testes da suíte ativa"
    for documento in ("analises/ATUALIZACAO_DE_DADOS.md", "painel/DEPLOY_STREAMLIT.md", "analises/METODOLOGIA.md", "painel/USO_DO_PAINEL.md"):
        assert project_path("documentacao", *documento.split("/")).is_file()
    for documento in ("README.md", "documentacao/painel/DEPLOY_STREAMLIT.md", "documentacao/analises/ESCOPO_PROJETO.md"):
        assert URL_STREAMLIT in _ler(*documento.split("/")), documento
    assert "streamlit.app" not in _ler("dashboard", "data_publica", "LEIAME.md")  # dados mínimos não dependem da URL
    regras = [l.strip() for l in project_path(".gitignore").read_text(encoding="utf-8").splitlines() if l.strip() and not l.lstrip().startswith("#")]
    assert "/atualizacao/" in regras and "/dados/" in regras  # entradas/candidatas locais e acervo bruto ficam fora do Git
    assert "README_IA*.md" in regras
    assert not any(r.rstrip("/") in ("dashboard/data_publica", "/dashboard/data_publica", "data_publica") for r in regras)  # os dados mínimos são versionáveis


def test_documentos_ativos_nao_apresentam_outras_fontes_como_parte_do_produto():
    for nome, partes in DOCUMENTOS_ATIVOS.items():
        texto = _ler(*partes)
        assert "Sinesp" in texto, nome
        for proibido in ("quatro páginas", "4 páginas", "ssp_violencia_domestica", "violencia_domestica.py", "Fato Comunicado\" é"):
            if nome == "README.md" and proibido in ("violencia_domestica.py",):
                continue  # o README cita o arquivo removido somente na seção de histórico
            assert proibido not in texto, (nome, proibido)
    for nome in ("ATUALIZACAO_DE_DADOS.md", "DEPLOY_STREAMLIT.md"):  # procedimentos operacionais: só Sinesp
        assert "SSP" not in _ler(*DOCUMENTOS_ATIVOS[nome]) and "Prefeitura" not in _ler(*DOCUMENTOS_ATIVOS[nome]), nome
    leiame = _ler(*DOCUMENTOS_ATIVOS["LEIAME.md"])  # dados mínimos: SSP/SC e Prefeitura só como histórico fora do escopo
    assert leiame.count("SSP/SC") == 1 and "fora do escopo" in leiame


def test_dados_publicos_e_documentacao_citam_o_mesmo_estado_dos_dados():
    from dashboard import dados_publicos as dp

    manifesto = dp.carregar_manifesto()
    leiame = _ler("dashboard", "data_publica", "LEIAME.md")
    readme = _ler("README.md")
    for texto in (leiame, readme):
        assert manifesto["versao"] in texto
    assert manifesto["aprovacao"]["aprovado_em_utc"] in leiame
    assert "911 × 6" in leiame and "12 × 12" in leiame
    assert "2020-01 a 2026-09" in leiame and "2026-08" in leiame
    assert project_path("historico", "ssp_sc", "LEIAME.md").is_file()
