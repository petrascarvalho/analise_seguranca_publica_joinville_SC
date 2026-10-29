"""Etapa 31: identidade azul e branca, cards uniformes, carregador da SSP/SC e proteção contra publicação indevida.

Estes testes não substituem a inspeção visual no navegador (feita à parte, com capturas), mas garantem as regras que a sustentam.
"""

import re
import tomllib

import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from apoio_painel import cartoes
from dashboard import dados_publicos as dp
from dashboard import dados_ssp, graficos, ui
from src.pipeline.utils import project_path


# ------------------------------------------------------------------------------------------------- tema e cores
def _tema() -> dict:
    return tomllib.loads(project_path(".streamlit", "config.toml").read_text(encoding="utf-8"))["theme"]


def test_tema_tem_fundo_azul_claro_e_azul_principal_da_bandeira():
    tema = _tema()
    assert tema["backgroundColor"] == "#EAF4FC" and ui.FUNDO == "#EAF4FC"
    assert tema["secondaryBackgroundColor"] == "#DCECF9" and tema["borderColor"] == "#BFD6EB"
    bandeira = project_path("dashboard", "assets", "bandeira_joinville.svg").read_text(encoding="utf-8").lower()
    assert tema["primaryColor"].lower() == ui.AZUL_BANDEIRA.lower() == "#074ea2" and 'fill="#074ea2"' in bandeira  # o azul vem do SVG do projeto
    comentarios = project_path(".streamlit", "config.toml").read_text(encoding="utf-8").lower()
    assert "proposta" in comentarios and "não são códigos cromáticos oficiais" in comentarios  # a paleta não é apresentada como oficial


def test_css_aplica_fundo_azul_claro_e_cards_brancos_sem_larguras_fixas():
    css = ui.CSS
    assert f"background: {ui.FUNDO}" in css and f".cartao {{ background: {ui.CARTAO}" in css and ui.CARTAO == "#FFFFFF"
    assert "repeat(auto-fit, minmax(" in css  # reorganiza em tablet e celular sem rolagem horizontal
    assert not re.search(r"(?<![-\w])width:\s*\d+px", css), "o CSS não pode fixar larguras em pixels (max-width é só um limite)"
    assert css.count("{") == css.count("}")


def test_css_dos_cards_usa_grid_com_cinco_linhas_comuns_para_alinhar_alturas_e_posicoes():
    css = ui.CSS
    assert "display: grid" in css and "grid-template-rows: subgrid" in css and "grid-row: span 5" in css  # cards da mesma linha dividem as alturas
    for classe in ("cartao-titulo", "cartao-detalhe", "cartao-valor", "cartao-variacao", "cartao-base"):
        assert f".{classe}" in css
    assert "overflow-wrap: anywhere" in css  # nenhuma informação cortada
    assert "display: flex; flex-direction: column" in css  # alternativa para navegadores sem subgrid


def _cartoes_variados():
    from dashboard import ui as interface

    interface.cartoes_html([
        {"titulo": "Título curto", "valor": "1"},
        {"titulo": "Um título bem mais longo que ocupa duas linhas em telas estreitas e continua sem ser cortado", "valor": "29", "detalhe": "Estadual · vítimas",
         "variacao": "−7 vs 2024", "diferenca": -7, "base": "Texto de base também longo, com várias palavras, para testar a quebra de linha do card.", "ajuda": "Dica & <teste>"},
        {"titulo": "Com alta", "valor": "25", "variacao": "+4 vs 2025", "diferenca": 4},
        {"titulo": "Sem diferença", "valor": "0", "variacao": "0 vs 2024", "diferenca": 0},
    ])


def test_todos_os_cards_tem_a_mesma_estrutura_de_cinco_campos_mesmo_com_textos_diferentes():
    app = AppTest.from_function(_cartoes_variados, default_timeout=60).run()
    assert not app.exception
    corpo = app.get("html")[0].proto.body
    blocos = corpo.split('<div class="cartao" ')[1:]
    assert len(blocos) == 4
    for bloco in blocos:  # todos têm título, detalhe, valor, variação e base, nessa ordem (campos vazios continuam ocupando a linha)
        assert re.findall(r'class="cartao-(\w+)"', bloco) == ["titulo", "detalhe", "valor", "variacao", "base"]
    lista = cartoes(app)
    assert [c.direction for c in lista] == ["NONE", "DOWN", "UP", "NONE"]  # seta pelo sinal da diferença; sem diferença: sem seta
    assert lista[1].ajuda == "Dica & <teste>" and "&lt;teste&gt;" in corpo  # texto escapado: nada de HTML injetado


def test_pagina_unica_tem_cards_do_sinesp_com_abrangencia_e_valores_preservados():
    app = AppTest.from_file(str(project_path("scripts", "painel_streamlit.py")), default_timeout=180).run()
    assert not app.exception and not app.error
    lista = cartoes(app)
    assert [c.value for c in lista][:10] == ["2020–2026", "911", "12", "set/2026", "29", "25", "77", "29", "25", "81 de 81"]
    sinesp_cards = lista[7:10]
    assert all(c.detalhe == "Homicídio doloso · Estadual" for c in sinesp_cards)  # a abrangência continua explícita em cada card


# ------------------------------------------------------------------------------------------------- SSP/SC: carregador
def _csv_ssp(caminho, *, unidade="Fato Comunicado", repetir=False, ausente=False, incompleto=False):
    linhas = []
    for categoria in ("Ameaça", "Injúria"):
        for ano in (2023, 2024):
            for mes in range(1, 13):
                linhas.append({"ano": ano, "mes": mes, "indicador": f"Violência doméstica — {categoria}", "unidade": unidade, "valor": mes})
    quadro = pd.DataFrame(linhas)
    if repetir:
        quadro = pd.concat([quadro, quadro.iloc[[0]]])
    if ausente:
        quadro.loc[3, "valor"] = None
    if incompleto:
        quadro = quadro.iloc[:-1]
    quadro.to_csv(caminho, index=False, encoding="utf-8")
    return caminho


def test_carregador_ssp_aceita_grade_completa_e_devolve_categorias_sem_o_prefixo(tmp_path, monkeypatch):
    monkeypatch.setattr(dados_ssp, "CAMINHOS", [_csv_ssp(tmp_path / "vd.csv")])
    dados = dados_ssp.carregar_violencia_domestica()
    assert list(dados.columns) == ["ano", "mes", "categoria", "valor"] and len(dados) == 48
    assert sorted(dados["categoria"].unique()) == ["Ameaça", "Injúria"] and dados["valor"].dtype == "int64"


@pytest.mark.parametrize("defeito, trecho", [({"unidade": "Vítimas"}, "Unidade inesperada"), ({"repetir": True}, "repetida"),
                                              ({"ausente": True}, "ausentes"), ({"incompleto": True}, "incompleta")])
def test_carregador_ssp_recusa_dados_fora_das_regras_sem_preencher_nada(tmp_path, monkeypatch, defeito, trecho):
    monkeypatch.setattr(dados_ssp, "CAMINHOS", [_csv_ssp(tmp_path / "vd.csv", **defeito)])
    with pytest.raises(dados_ssp.ErroDadosSsp, match=trecho):
        dados_ssp.carregar_violencia_domestica()


def test_carregador_ssp_sem_arquivo_devolve_none_e_nao_depende_de_caminho_do_computador(tmp_path, monkeypatch):
    monkeypatch.setattr(dados_ssp, "CAMINHOS", [tmp_path / "nao_existe.csv"])
    assert dados_ssp.carregar_violencia_domestica() is None
    texto = project_path("dashboard", "dados_ssp.py").read_text(encoding="utf-8")
    assert not re.search(r"\b[A-Za-z]:[\\/]", texto) and "Path(__file__)" in texto  # caminhos relativos à raiz do projeto


def test_dados_ssp_locais_conferem_com_os_valores_auditados_quando_existem():
    if dados_ssp.caminho_disponivel() is None:
        pytest.skip("CSV local da SSP/SC ausente (clone limpo)")
    dados = dados_ssp.carregar_violencia_domestica()
    assert len(dados) == 216 and dados["categoria"].nunique() == 9 and dados[["ano", "mes"]].drop_duplicates().shape[0] == 24
    assert int(dados["valor"].eq(0).sum()) == 27  # zeros publicados
    totais = dados.groupby(["categoria", "ano"])["valor"].sum().unstack("ano")
    for categoria, (a2023, a2024) in {"Ameaça": (1957, 2085), "Lesão corporal leve dolosa": (989, 959), "Injúria": (541, 716), "Vias de fato": (229, 281),
                                      "Difamação": (190, 211), "Calúnia": (109, 119), "Estupro": (22, 30),
                                      "Lesão corporal grave ou gravíssima dolosa": (19, 10), "Injúria real": (2, 6)}.items():
        assert (int(totais.loc[categoria, 2023]), int(totais.loc[categoria, 2024])) == (a2023, a2024), categoria  # valores oficiais conferidos


# ------------------------------------------------------------------------------------------------- publicação e separação
def test_csv_da_ssp_sc_nao_foi_publicado_em_data_publica_e_o_sinesp_nao_mudou():
    arquivos = sorted(p.name for p in dp.DIRETORIO_DADOS.iterdir())
    assert arquivos == sorted([dp.ARQ_SINESP, dp.ARQ_SINESP_CATALOGO, dp.ARQ_MANIFESTO])  # nenhum arquivo SSP/SC publicado sem autorização
    assert dp.verificar_integridade()["integro"].all() and dp.carregar_manifesto()["versao"] == "20261027T114400Z"
    sinesp = dp.carregar_sinesp()
    assert len(sinesp) == 911 and sinesp[["evento", "abrangencia"]].drop_duplicates().shape[0] == 12 and int(sinesp["valor"].eq(0).sum()) == 401
    assert int(sinesp["valor"].isna().sum()) == 0


def test_figura_ssp_identifica_fonte_periodo_e_unidade_em_validacao_sem_sugerir_comparacao_com_sinesp(tmp_path, monkeypatch):
    monkeypatch.setattr(dados_ssp, "CAMINHOS", [_csv_ssp(tmp_path / "vd.csv")])
    dados = dados_ssp.carregar_violencia_domestica()
    for categoria in (None, "Ameaça"):
        figura = graficos.figura_violencia_domestica_ssp(dados, categoria)
        textos = " ".join(" ".join(t.get_text().split()) for t in figura.texts)  # junta as quebras de linha do texto
        assert "Fato Comunicado" in textos and "definição em validação" in textos and "SSP/SC" in textos and "2023–2024" in textos
        assert "não integra os indicadores Sinesp" in textos
    totais = dados.groupby(["categoria", "ano"])["valor"].sum().unstack("ano")
    barras = [int(b.get_width()) for b in graficos.figura_violencia_domestica_ssp(dados).axes[0].patches]
    assert sorted(barras) == sorted(int(v) for v in totais.to_numpy().ravel())  # as barras são exatamente os totais por categoria e ano
    for cor in (graficos.COR_SSP_2023, graficos.COR_SSP_2024):
        r, g, b = (int(cor[i:i + 2], 16) for i in (1, 3, 5))
        assert b > g > r, cor  # paleta azul


# ------------------------------------------------------------------------------------------------- linguagem para o público
TERMOS_TECNICOS = re.compile(r"\.py\b|python|scripts[/\\]|\bsrc[/\\.]|dashboard[/\\]|README|\bETL\b|Etapa \d|ddof|pandas|XLSX|total_vitima|notebook|pytest|manifest|session_state|Sturges|`",
                             re.IGNORECASE)
COMPETENCIA_ISO = re.compile(r"(?<![\d.,-])20\d\d-(0[1-9]|1[0-2])(?![\d-])")  # 2026-09 deve aparecer como "setembro/2026" ou "set/2026"


def _todos_os_textos_da_pagina(app) -> list:
    """Texto visível da página única, inclusive de cada aba de análise e da categoria da SSP/SC; sem o bloco recolhido de detalhes técnicos."""
    from apoio_painel import textos_visiveis

    textos = textos_visiveis(app)
    for aba in ("Comparações", "Meses e tendência", "Estatísticas e meses incomuns", "Indicadores e como interpretar"):
        app.session_state["aba_analise"] = aba
        app.run()
        textos += textos_visiveis(app)
    if "vd_categoria" in [s.key for s in app.selectbox]:
        app.selectbox(key="vd_categoria").select("Ameaça").run()
        textos += textos_visiveis(app)
    # O bloco "Detalhes técnicos de conferência (opcional)" é recolhido e pode citar o identificador da versão e o código SHA-256.
    return [t for t in textos if not t.startswith("Identificador da versão dos dados") and "SHA-256" not in t and not re.fullmatch(r"[0-9a-f]{64}", t)]


def test_texto_visivel_nao_expoe_codigo_caminhos_comandos_nem_jargao_de_implementacao():
    app = AppTest.from_file(str(project_path("scripts", "painel_streamlit.py")), default_timeout=300).run()
    assert not app.exception and not app.error
    textos = _todos_os_textos_da_pagina(app)
    assert len(textos) > 300  # a varredura realmente passou por todas as seções e abas
    achados = sorted({t[:120] for t in textos if TERMOS_TECNICOS.search(t)})
    assert not achados, achados
    datas_tecnicas = sorted({t[:120] for t in textos if COMPETENCIA_ISO.search(t)})
    assert not datas_tecnicas, datas_tecnicas
    for sigla_interna in ("2026-10-27T", "UTC", "NXDOMAIN", "gerador", "staging", "candidat"):
        assert not [t for t in textos if sigla_interna in t], sigla_interna


def test_abrangencia_estadual_e_explicada_sem_sugerir_total_de_santa_catarina():
    app = AppTest.from_file(str(project_path("scripts", "painel_streamlit.py")), default_timeout=180).run()
    corpo = " ".join(m.value for m in app.markdown) + " ".join(c.value for c in app.caption) + " ".join(i.value for i in app.info)
    completa = "identifica a classificação institucional da série na fonte; **não é um total do estado de Santa Catarina**"
    curta = "“Estadual” é a classificação institucional da série, **não um total de Santa Catarina**"
    assert corpo.count(completa) == 2  # explicação completa só na Apresentação e na metodologia
    assert corpo.count(curta) == 2  # aviso curto na seção Sinesp e em "Sobre os dados apresentados"
    assert "Os indicadores do Sinesp foram selecionados para o município de **Joinville/SC**" in corpo
    texto_sem_notas = corpo.replace(completa, "").replace(curta, "")
    assert "total do estado" not in texto_sem_notas and "total de Santa Catarina" not in texto_sem_notas


def test_transparencia_preservada_no_texto_publico():
    app = AppTest.from_file(str(project_path("scripts", "painel_streamlit.py")), default_timeout=180).run()
    corpo = " ".join(textos for textos in [m.value for m in app.markdown] + [c.value for c in app.caption] + [i.value for i in app.info] + [w.value for w in app.warning])
    for trecho in ("2026 é parcial", "Zero informado e ausência são diferentes", "Fato Comunicado", "em validação", "não é uma aprovação ou certificação oficial do governo",
                   "nunca somadas", "Sinesp/MJSP", "não deve ser lida como vítimas, pessoas ou ocorrências únicas"):
        assert trecho in corpo or trecho.replace("nunca somadas", "nunca são somadas") in corpo, trecho


def _texto_de_um_estado(app, abas=("Evolução", "Meses e tendência", "Estatísticas e meses incomuns")) -> list:
    from apoio_painel import textos_visiveis

    textos = []
    for aba in abas:
        app.session_state["aba_analise"] = aba
        app.run()
        assert not app.exception and not app.error, aba
        textos += textos_visiveis(app)
    return [t for t in textos if not t.startswith("Identificador da versão dos dados") and "SHA-256" not in t and not re.fullmatch(r"[0-9a-f]{64}", t)]


def _conferir_linguagem(textos, cenario):
    proibidos = re.compile(r"\bNone\b|\bnan\b|<NA>|\bNaN\b|Último mês publicado|última competência disponível|Pontos fora|outliers?\b|sazonalidade, exploratório", re.IGNORECASE)
    achados = sorted({t[:110] for t in textos if TERMOS_TECNICOS.search(t) or COMPETENCIA_ISO.search(t) or proibidos.search(t)})
    assert not achados, (cenario, achados)


def test_textos_condicionais_de_todos_os_filtros_seguem_a_linguagem_publica():
    """Não basta o estado inicial: percorre cada série, o filtro de meses, o de anos, o modo compacto e cada categoria da SSP/SC."""
    app = AppTest.from_file(str(project_path("scripts", "painel_streamlit.py")), default_timeout=300).run()
    for serie in app.selectbox(key="serie").options:  # as 12 séries (inclui PF e PRF, com avisos próprios)
        app.selectbox(key="serie").select(serie).run()
        _conferir_linguagem(_texto_de_um_estado(app), serie)
    app.selectbox(key="serie").select("Homicídio doloso — Estadual").run()
    for meses in ((4, 6), (10, 12)):  # meses ainda não publicados em 2026 geram textos próprios
        app.select_slider(key="periodo_meses").set_value(meses).run()
        _conferir_linguagem(_texto_de_um_estado(app), f"meses {meses}")
    app.select_slider(key="periodo_meses").set_value((1, 12)).run()
    app.select_slider(key="periodo_anos").set_value((2022, 2024)).run()
    _conferir_linguagem(_texto_de_um_estado(app), "anos 2022-2024")
    app.toggle(key="modo_compacto").set_value(True).run()
    _conferir_linguagem(_texto_de_um_estado(app), "compacto")
    app.toggle(key="modo_compacto").set_value(False).run()
    from apoio_painel import textos_visiveis

    for categoria in app.selectbox(key="vd_categoria").options:
        app.selectbox(key="vd_categoria").select(categoria).run()
        assert not app.exception and not app.error, categoria
        textos = [x for x in textos_visiveis(app) if not x.startswith("Identificador da versão dos dados") and "SHA-256" not in x and not re.fullmatch(r"[0-9a-f]{64}", x)]
        _conferir_linguagem(textos, f"SSP/SC {categoria}")
        assert any("Fato Comunicado" in t and "não foi identificada uma definição operacional de “Fato Comunicado”" in t for t in textos), categoria  # a ressalva nunca some


def test_ressalvas_preservadas_em_cada_estado_dos_filtros():
    app = AppTest.from_file(str(project_path("scripts", "painel_streamlit.py")), default_timeout=300).run()
    avisos = lambda a: " ".join([w.value for w in a.warning] + [i.value for i in a.info])  # noqa: E731
    assert "2026 contém apenas janeiro a setembro" in avisos(app)  # ano parcial
    app.selectbox(key="serie").select("Mandado de prisão cumprido — Polícia Federal").run()
    assert "antes disso não há série (e isso não significa zero)" in avisos(app)  # ausência de série ≠ zero
    app.selectbox(key="serie").select("Mortes no trânsito — Polícia Rodoviária Federal").run()
    assert "2026 contém apenas janeiro a agosto" in avisos(app) and "sem preencher os meses que faltam" in avisos(app)
    cartao = [c for c in cartoes(app) if c.titulo == "Meses com valor publicado"][0]
    assert "Meses sem informação: 0 (nunca preenchidos)" in cartao.base and "Zeros informados:" in cartao.base  # zero ≠ ausência


# ------------------------------------------------------------------------------------------------- gráficos temporais e títulos
def test_serie_mensal_ssp_e_linha_com_marcadores_e_rotulos_so_no_modo_completo(tmp_path, monkeypatch):
    monkeypatch.setattr(dados_ssp, "CAMINHOS", [_csv_ssp(tmp_path / "vd.csv")])
    dados = dados_ssp.carregar_violencia_domestica()
    figura = graficos.figura_violencia_domestica_ssp(dados, "Ameaça")
    linhas = {l.get_gid(): l for l in figura.axes[0].lines}
    assert set(linhas) == {"linha_ssp_2023", "linha_ssp_2024"} and all(l.get_marker() == "o" for l in linhas.values())
    assert [int(v) for v in linhas["linha_ssp_2023"].get_ydata()] == list(range(1, 13))  # os 12 valores publicados, sem preencher nada
    assert not figura.axes[0].patches
    rotulos = [t.get_text() for t in figura.axes[0].texts if t.get_text().isdigit()]
    assert len(rotulos) == 24  # 2 anos × 12 meses, escritos nos pontos
    with graficos.modo_compacto():
        compacta = graficos.figura_violencia_domestica_ssp(dados, "Ameaça")
    assert not [t for t in compacta.axes[0].texts if t.get_text().isdigit()]  # no celular, sem rótulos para não sobrecarregar


def test_icone_de_ancora_dos_titulos_fica_oculto_e_os_links_do_indice_continuam():
    assert '[data-testid="stHeaderActionElements"] { display: none !important; }' in ui.CSS
    entrada = project_path("scripts", "painel_streamlit.py").read_text(encoding="utf-8")
    for ancora in ("#apresentacao", "#indicadores", "#violencia-domestica", "#qualidade", "#metodologia"):
        assert f"]({ancora})" in entrada
    app = AppTest.from_file(str(project_path("scripts", "painel_streamlit.py")), default_timeout=180).run()
    titulos = [h.value for h in app.title] + [h.value for h in app.header]
    assert not [t for t in titulos if re.search(r"\bT\b|🔗|#", t)], titulos  # nenhum "T" solto nem símbolo de âncora no texto
