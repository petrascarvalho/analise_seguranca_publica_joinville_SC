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
    assert [c.value for c in lista][:10] == ["2020–2026", "911", "12", "2026-09", "29", "25", "77", "29", "25", "81 de 81"]
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
