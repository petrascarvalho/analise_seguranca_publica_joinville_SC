import re

from src.pipeline.utils import project_path

URL_STREAMLIT = "https://seguranca-publica-joinville-sinesp.streamlit.app/"
# Etapa 26: pacote público e histórico documentados no README único.
DOCUMENTOS_ATIVOS = {
    "README.md": ("README.md",),
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
    for directory in ("scripts", "src", "dashboard", "notebooks", "documentacao", "dados", "tests", "tests_historicos"):
        assert not list(project_path(directory).rglob("README.md"))
    assert not list(project_path("documentacao").rglob("*.md"))  # nenhum guia separado: tudo no README


def test_etl_e_notebook_sao_os_roteiros_principais_e_o_antigo_e_historico():
    etl = _ler("scripts", "etl_sinesp.py")
    assert "# %%" in etl and "ETAPA 01" in etl and "ETAPA 18" in etl
    assert project_path("notebooks", "analise_seguranca_publica_joinville.ipynb").is_file()
    assert not project_path("scripts", "analise_sinesp.py").exists()  # renomeado para etl_sinesp.py
    assert project_path("src", "pipeline", "ssp_sc.py").is_file()  # extração autônoma
    assert sorted(p.name for p in project_path("scripts").glob("*.py")) == ["etl_sinesp.py", "painel_streamlit.py"]  # só os dois pontos principais
    readme = _ler("README.md")
    assert "scripts/etl_sinesp.py" in readme and "-m scripts.etl_sinesp" in readme
    assert "notebooks/analise_seguranca_publica_joinville.ipynb" in readme and "dados/processados/sinesp" in readme
    assert r".\.venv\Scripts\python.exe" in readme  # comandos testados no Windows
    assert "git show 5702724:<caminho>" in readme and "arquivo_etapa26" in readme


def test_readme_separa_o_sinesp_validado_do_acervo_ssp_em_validacao():
    readme = _ler("README.md")
    for esperado in (
        "fonte única", "Sinesp/MJSP", "Joinville/SC", "SSP/SC e Prefeitura/SEPROT", "fora do escopo", "bad9723",
        "Indicadores Sinesp", "Qualidade e metodologia", "três páginas",
        # Etapa 24: SSP/SC preservada e em validação, fora do painel; nada apresentado como definitivo
        "em validação", "Fato Comunicado", "não tem definição oficial", "41 têm versões diferentes", "src/pipeline/ssp_sc.py",
        "src/pipeline/consolidacao.py", "pd.concat", "não foi gravada", "1.127 linhas",
    ):
        assert esperado in readme, esperado
    for proibido in ("quatro páginas", "4 páginas", "Violência doméstica SSP/SC**:", "várias fontes", "múltiplas fontes"):
        assert proibido not in readme, proibido
    # Pendências de entrega continuam pendentes; nenhum link inventado; Trello dispensado.
    publicada = (f"Aplicação Streamlit publicada: <{URL_STREAMLIT}>", f"Aplicação Streamlit publicada: [{URL_STREAMLIT}]({URL_STREAMLIT})")  # os dois links Markdown valem
    assert any(texto in readme for texto in publicada) and "Aplicação Streamlit publicada: pendente" not in readme
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
        "--aceitar-revisoes", "scripts/painel_streamlit.py", "não pôde ser confirmado", "CC BY-ND",
        "Deploy realizado", "-m pytest tests -q", "tests/test_integridade_acervo.py",
        "20261027T114400Z",
    ):
        assert expected in readme, expected
    assert re.search(r"\*\*\d+ testes aprovados\*\*", readme), "o README deve informar a contagem de testes da suíte ativa"
    assert URL_STREAMLIT in readme
    for imagem in re.findall(r"\((documentacao/graficos/[^)]+)\)", readme):  # imagens citadas existem
        assert project_path(*imagem.split("/")).is_file(), imagem
    assert not project_path("dashboard", "data_publica", "LEIAME.md").exists()
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


def test_dados_publicos_e_documentacao_citam_o_mesmo_estado_dos_dados():
    from dashboard import dados_publicos as dp

    manifesto = dp.carregar_manifesto()
    readme = _ler("README.md")
    assert manifesto["versao"] in readme
    assert manifesto["aprovacao"]["aprovado_em_utc"] in readme
    assert "911 × 6" in readme and "12 × 12" in readme
    assert "2020-01 a 2026-09" in readme and "2026-08" in readme


def test_links_relativos_do_readme_e_notebook_existem():
    import json
    from urllib.parse import unquote

    notebook = project_path("notebooks", "analise_seguranca_publica_joinville.ipynb")
    texto_nb = "\n".join("".join(c["source"]) for c in json.loads(notebook.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "markdown")
    for raiz, texto in ((project_path(), _ler("README.md")), (notebook.parent, texto_nb)):
        for destino in re.findall(r"\]\(([^)]+)\)", texto):
            if "://" in destino or destino.startswith("#"):
                continue
            caminho = unquote(destino.split("#", 1)[0])
            assert (raiz / caminho).is_file(), destino
