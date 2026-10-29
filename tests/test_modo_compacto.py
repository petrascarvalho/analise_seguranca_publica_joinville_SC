"""Etapa 20.2 — modo compacto (celular): mesmos números que o modo completo, textos dentro da figura, filtros e estado preservados.

Não substituem a inspeção visual em um navegador ou em um celular real.
"""

import threading

import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

from dashboard import calculos, graficos
from dashboard import dados_publicos as dp
from apoio_painel import cartoes, escolher_serie
from src.pipeline.utils import project_path
from test_estatistica_visual import SERIES_REAIS, _caixas_dos_textos

ANOS = list(range(2020, 2027))
FUNCOES = ["mapa_calor", "media_movel", "acumulado", "boxplot_anual", "distribuicao", "sazonalidade", "outliers_iqr", "serie_anual", "mensal", "periodo"]


@pytest.fixture(scope="module")
def sinesp():
    return dp.carregar_sinesp()


def _construir(sinesp, nome, evento, abrangencia, compacto):
    funcao = getattr(graficos, f"figura_{nome}_sinesp")
    with graficos.modo_compacto(compacto):
        if nome == "periodo":
            return funcao(sinesp, evento, abrangencia, ANOS, calculos.mes_final_da_serie(calculos.serie_sinesp(sinesp, evento, abrangencia)))
        return funcao(sinesp, evento, abrangencia, ANOS)


def _assinatura(figura) -> dict:
    """Números desenhados, por tipo de elemento: dados das linhas, alturas das barras e matriz do mapa de calor."""
    eixo = figura.axes[0]
    linhas = {}
    for i, linha in enumerate(eixo.lines):
        chave = linha.get_gid() or f"linha{i}"
        if chave.startswith(("zero_", "sem_valor_")):  # marcações discretas só do modo compacto (testadas à parte)
            continue
        linhas[chave] = np.round(np.array(linha.get_ydata(), dtype="float64"), 9).tolist()
    barras = [round(float(b.get_height()), 9) for b in eixo.patches]
    matriz = [np.ma.filled(i.get_array().astype("float64"), np.nan).tolist() for i in eixo.images]
    return {"linhas": linhas, "barras": barras, "matriz": matriz}


# ------------------------------------------------------------------------------------------ contexto do modo compacto
def test_modo_compacto_e_local_ao_contexto_e_volta_ao_padrao():
    assert graficos.esta_compacto() is False
    with graficos.modo_compacto():
        assert graficos.esta_compacto() is True
        with graficos.modo_compacto(False):
            assert graficos.esta_compacto() is False
        assert graficos.esta_compacto() is True
    assert graficos.esta_compacto() is False
    graficos.definir_modo_compacto(True)
    resultado = []
    outro = threading.Thread(target=lambda: resultado.append(graficos.esta_compacto()))  # outra thread (outra sessão): começa no padrão
    outro.start()
    outro.join()
    assert resultado == [False] and graficos.esta_compacto() is True
    graficos.definir_modo_compacto(False)


# ------------------------------------------------------------------------------------------------- mesmos números
@pytest.mark.parametrize("evento, abrangencia", [("Homicídio doloso", "Estadual"), ("Mandado de prisão cumprido", "Estadual"), ("Mortes no trânsito", "Polícia Rodoviária Federal"),
                                                 ("Feminicídio", "Estadual"), ("Roubo seguido de morte (latrocínio)", "Estadual"),
                                                 ("Mortes a esclarecer (sem indício de crime)", "Estadual"), ("Mandado de prisão cumprido", "Polícia Federal")])
def test_modo_compacto_desenha_os_mesmos_numeros_que_o_modo_completo(sinesp, evento, abrangencia):
    for nome in FUNCOES:
        completa = _construir(sinesp, nome, evento, abrangencia, False)
        compacta = _construir(sinesp, nome, evento, abrangencia, True)
        assert (completa is None) == (compacta is None), nome
        if completa is None:
            continue
        a, c = _assinatura(completa), _assinatura(compacta)
        if nome == "mapa_calor":  # compacto: transposto (meses nas linhas); os números são os mesmos
            assert np.array(a["matriz"][0]).shape == tuple(reversed(np.array(c["matriz"][0]).shape)), nome
            np.testing.assert_array_equal(np.array(a["matriz"][0]).T, np.array(c["matriz"][0]))
            continue
        assert a["barras"] == c["barras"], nome
        assert a["matriz"] == c["matriz"], nome
        assert set(a["linhas"]) == set(c["linhas"]), nome
        for chave in a["linhas"]:
            np.testing.assert_allclose(a["linhas"][chave], c["linhas"][chave], equal_nan=True, err_msg=f"{nome}/{chave}")
        assert completa.sinesp_notas == compacta.sinesp_notas, nome  # as mesmas notas, só que em outro lugar da tela


def test_ranking_compacto_tem_os_mesmos_valores_e_destaque(sinesp):
    ranking = calculos.ranking_por_unidade(sinesp, 2025, dp.UNIDADE_VITIMAS)
    figuras = {}
    for compacto in (False, True):
        with graficos.modo_compacto(compacto):
            figuras[compacto] = graficos.figura_ranking_sinesp(ranking, 2025, destaque=("Homicídio doloso", "Estadual"))
    larguras = {k: [b.get_width() for b in f.axes[0].patches if b.get_gid() == "ranking"] for k, f in figuras.items()}
    assert larguras[False] == larguras[True] == ranking["soma"].astype(float).tolist()[::1] or sorted(larguras[False]) == sorted(larguras[True])
    assert figuras[True].get_figwidth() == pytest.approx(4.4)
    rotulos = [t.get_text() for t in figuras[True].axes[0].get_yticklabels()]
    assert all(len(linha) <= 26 for r in rotulos for linha in r.split("\n")) and any("PRF" in r for r in rotulos)  # rótulos curtos, sem perder a abrangência


def test_etapa_10_no_modo_compacto_mantem_os_valores_aprovados(sinesp):
    with graficos.modo_compacto():
        figuras = graficos.figuras_sinesp_etapa10(sinesp)
    linhas = figuras["fig_homicidio_anual_sinesp"].axes[0].lines
    assert list(linhas[0].get_ydata()) == [62, 62, 49, 55, 36, 29]
    assert figuras["fig_homicidio_anual_sinesp"].get_figwidth() == pytest.approx(4.4)
    assert [int(b.get_height()) for b in figuras["fig_mulher_anual_sinesp"].axes[0].patches[:6]] == [3, 6, 2, 2, 3, 2]


# ------------------------------------------------------------------------------------ textos e limites da figura compacta
@pytest.mark.parametrize("evento, abrangencia", SERIES_REAIS)
def test_figura_compacta_e_estreita_sem_texto_longo_e_sem_cortes(sinesp, evento, abrangencia):
    for nome in ("mapa_calor", "media_movel", "acumulado", "boxplot_anual", "distribuicao", "sazonalidade", "outliers_iqr"):
        figura = _construir(sinesp, nome, evento, abrangencia, True)
        if figura is None:
            continue
        assert figura.get_figwidth() == pytest.approx(4.4) and figura.get_figheight() == pytest.approx(6.4), nome
        textos_na_imagem = [t.get_text() for t in figura.texts]
        assert all(len(linha) <= 44 for texto in textos_na_imagem for linha in texto.split("\n")), (nome, textos_na_imagem)  # nada de parágrafos na imagem
        assert not any("Fonte" in t for t in textos_na_imagem)  # a fonte aparece uma única vez: completa, como texto nativo abaixo da figura
        assert figura.sinesp_notas["interpretacao"] and "Abrangência" in figura.sinesp_notas["rodape"] and "Unidade" in figura.sinesp_notas["rodape"]
        caixa = figura.bbox
        caixas = _caixas_dos_textos(figura)
        for artista, retangulo in caixas:
            assert retangulo.x0 >= -1 and retangulo.y0 >= -1 and retangulo.x1 <= caixa.x1 + 1 and retangulo.y1 <= caixa.y1 + 1, (nome, evento, artista.get_text()[:40])
        legenda = figura.axes[0].get_legend()
        if legenda is not None:  # legenda abaixo do gráfico: não pode tocar no rótulo do eixo nem na fonte
            textos_legenda = [c for a, c in caixas if a in legenda.get_texts()]
            outros = [c for a, c in caixas if a is figura.axes[0].xaxis.label or a in figura.texts]
            assert not any(l.overlaps(o) for l in textos_legenda for o in outros), (nome, evento)


def test_series_com_muitos_zeros_no_modo_compacto(sinesp):
    zerada = _construir(sinesp, "mapa_calor", "Mortes a esclarecer (sem indício de crime)", "Estadual", True)
    assert any("Série sem variação" in t.get_text() for t in zerada.axes[0].texts)
    assert all(len(linha) <= 31 for t in zerada.axes[0].texts if "Série sem variação" in t.get_text() for linha in t.get_text().split("\n"))  # banner quebrado em linhas
    matriz = zerada.axes[0].images[0].get_array()
    assert np.ma.getmaskarray(matriz).sum() == 3 and (np.ma.filled(matriz, -1)[~np.ma.getmaskarray(matriz)] == 0).all()  # 78 zeros publicados; 3 meses sem valor (cinza)
    latrocinio = _construir(sinesp, "outliers_iqr", "Roubo seguido de morte (latrocínio)", "Estadual", True)
    assert any("pouco úteis" in t.get_text().replace("\n", " ") for t in latrocinio.axes[0].texts)
    assert not [l for l in latrocinio.axes[0].lines if l.get_gid() in ("limite_superior", "pontos_atipicos")]
    distribuicao = _construir(sinesp, "distribuicao", "Mortes a esclarecer (sem indício de crime)", "Estadual", True)
    assert [int(b.get_height()) for b in distribuicao.axes[0].patches if b.get_gid() == "frequencia"] == [81]


def test_mapa_de_calor_compacto_distingue_zero_de_mes_sem_valor_e_mostra_os_12_meses(sinesp):
    figura = _construir(sinesp, "mapa_calor", "Homicídio doloso", "Estadual", True)
    eixo = figura.axes[0]
    tabela = calculos.quadro_ano_mes(calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual"))
    matriz = eixo.images[0].get_array()
    assert [t.get_text() for t in eixo.get_yticklabels()] == list(("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"))
    assert [t.get_text() for t in eixo.get_xticklabels()] == [str(a) for a in tabela.index]
    assert matriz[2, 3] == 0 and not np.ma.getmaskarray(matriz)[2, 3]  # março/2023 = zero publicado
    assert np.ma.getmaskarray(matriz)[9:, 6].all()  # out–dez/2026: sem valor (cinza)
    assert sorted(t.get_text() for t in eixo.texts if t.get_text() != "") == sorted(str(int(v)) for v in tabela.to_numpy().ravel() if pd.notna(v))


def test_acumulado_compacto_traz_valor_final_na_legenda_inclusive_prf_ate_agosto(sinesp):
    figura = _construir(sinesp, "acumulado", "Homicídio doloso", "Estadual", True)
    legenda = [t.get_text() for t in figura.axes[0].get_legend().get_texts()]
    assert legenda == ["2020: 62", "2021: 62", "2022: 49", "2023: 55", "2024: 36", "2025: 29", "2026 (parcial, até set): 25"]
    assert not [a for a in figura.axes[0].texts if a.get_gid() == "rotulo_final"]  # sem rótulos soltos no gráfico
    prf = _construir(sinesp, "acumulado", "Mortes no trânsito", "Polícia Rodoviária Federal", True)
    assert "2026 (parcial, até ago): 6" in [t.get_text() for t in prf.axes[0].get_legend().get_texts()]
    mensal = _construir(sinesp, "mensal", "Mortes no trânsito", "Polícia Rodoviária Federal", True)
    assert len([b for b in mensal.axes[0].patches if b.get_gid() == "mensal_2026"]) == 8  # 2026 da PRF: janeiro a agosto (barras)
    assert [t.get_text() for t in mensal.axes[0].get_xticklabels()] == ["Jan", "Mar", "Jun", "Set", "Dez"]


def test_outliers_compacto_mantem_diagnostico_e_pontos(sinesp):
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    d = calculos.diagnostico_outliers_iqr(serie)
    figura = _construir(sinesp, "outliers_iqr", "Homicídio doloso", "Estadual", True)
    linhas = {l.get_gid(): np.array(l.get_ydata(), dtype=float) for l in figura.axes[0].lines if l.get_gid()}
    assert linhas["limite_superior"].tolist() == [d["limite_superior"]] * 2 and linhas["mediana"].tolist() == [d["mediana"]] * 2
    assert linhas["pontos_atipicos"].tolist() == [10.0, 19.0] and d["interpretavel"] and d["n_fora"] == 2
    assert [t.get_text() for t in figura.axes[0].get_legend().get_texts()] == ["Valor mensal", "Q1 a Q3", "Mediana", "Limite superior", "Limite inferior (n/a)", "Fora dos limites (2)"]
    assert "Conjunto de referência: 81 meses" in figura.sinesp_notas["interpretacao"]  # os detalhes extensos vão para o texto abaixo do gráfico


def test_criar_figuras_nao_altera_os_dados(sinesp):
    antes = sinesp.copy(deep=True)
    for compacto in (False, True):
        for nome in FUNCOES:
            _construir(sinesp, nome, "Homicídio doloso", "Estadual", compacto)
    pd.testing.assert_frame_equal(sinesp, antes)
    assert dp.verificar_integridade()["integro"].all() and sinesp.shape == (911, 6)


# ---------------------------------------------------------------------------------------------------------- página
def _aba(app, nome):
    """A página executa só a aba selecionada (st.tabs com on_change="rerun"): seleciona a aba e executa de novo."""
    app.session_state["aba_analise"] = nome
    return app.run()


def _em_cada_aba(app):
    """Percorre as quatro abas de análise e devolve, a cada uma, o app já executado com ela selecionada."""
    for nome in ("Evolução", "Comparações", "Meses e tendência", "Estatísticas e meses incomuns"):
        yield nome, _aba(app, nome)


def _pagina():
    return AppTest.from_file(str(project_path("dashboard", "pages", "sinesp.py")), default_timeout=180).run()


def test_alternancia_do_modo_compacto_preserva_filtros_e_abas():
    app = _pagina()
    assert [t.label for t in app.toggle] == ["Visualização compacta (celular)"] and app.toggle[0].value is False  # padrão: completo (desktop)
    assert not app.exception and not app.error
    escolher_serie(app, "Mandado de prisão cumprido", "Polícia Federal")
    app.select_slider[0].set_value((2025, 2026)).run()
    app.toggle[0].set_value(True).run()
    assert app.toggle[0].value is True and not app.exception and not app.error
    assert (app.selectbox(key="serie").value, app.select_slider[0].value) == ("Mandado de prisão cumprido — Polícia Federal", (2025, 2026))  # filtros mantidos
    escolher_serie(app, "Suicídio", "Estadual")
    assert app.toggle[0].value is True  # o modo permanece durante as interações
    app.toggle[0].set_value(False).run()
    assert app.toggle[0].value is False and not app.exception
    assert [t.label for t in app.tabs] == ["Evolução", "Comparações", "Meses e tendência", "Estatísticas e meses incomuns", "Indicadores e como interpretar"]


def test_modo_compacto_na_pagina_move_o_texto_explicativo_para_componentes_nativos():
    app = _pagina()
    legendas = " ".join(c.value for c in app.caption)
    assert "Cada linha acumula" not in legendas  # completo: o texto está dentro da imagem
    app.toggle[0].set_value(True).run()
    assert not app.exception and not app.error
    legendas, tukey, tabelas = "", False, 0
    for nome, aba in _em_cada_aba(app):  # cada aba só executa quando selecionada
        assert not aba.exception and not aba.error, nome
        legendas += " ".join(c.value for c in aba.caption)
        tukey |= any("limites de referência" in c.value for c in aba.caption)
        tabelas += sum(1 for e in aba.expander if e.label == "Valores usados neste gráfico (tabela)")
    assert "Cada linha acumula os meses de um ano" in legendas and "Fonte: MJSP / Sinesp VDE | Abrangência: Estadual | Unidade: vítimas" in legendas
    assert tukey
    assert tabelas >= 9  # as tabelas de apoio continuam nos dois modos
    app = _aba(app, "Evolução")
    metricas = [m.value for m in cartoes(app)][:2]
    app.toggle[0].set_value(False).run()
    assert [m.value for m in cartoes(app)][:2] == metricas == ["29", "25"]  # mesmos resultados nos dois modos


def test_prf_no_modo_compacto_oferece_selecao_de_anos_sem_ocultar_em_silencio():
    app = _pagina()
    app.toggle[0].set_value(True).run()
    escolher_serie(app, "Mortes no trânsito", "Polícia Rodoviária Federal")
    assert not app.exception and not app.error
    assert [m.label for m in app.multiselect] == ["Anos exibidos na evolução mensal"] and app.multiselect[0].value == [2024, 2025, 2026]
    assert any("Exibindo 3 de 7 anos do período selecionado (2024, 2025, 2026)" in c.value for c in app.caption)  # filtro ativo identificado
    app.multiselect[0].set_value(list(range(2020, 2027))).run()
    assert not app.exception and any("Exibindo 7 de 7" in c.value for c in app.caption)
    app.multiselect[0].set_value([]).run()
    assert any("Selecione ao menos um ano" in i.value for i in app.info) and not app.exception
    assert any("2026 contém apenas janeiro a agosto" in i.value for i in app.info)  # PRF: última competência agosto/2026
    app.toggle[0].set_value(False).run()
    assert not app.multiselect  # no modo completo não há seletor: todos os anos são exibidos


def test_modo_compacto_roda_em_todas_as_series_sem_erro():
    app = _pagina()
    app.toggle[0].set_value(True).run()
    for evento, abrangencia in [("Roubo seguido de morte (latrocínio)", "Estadual"), ("Mortes a esclarecer (sem indício de crime)", "Estadual"),
                                ("Mandado de prisão cumprido", "Polícia Federal"), ("Feminicídio", "Estadual"), ("Homicídio doloso", "Estadual")]:
        escolher_serie(app, evento, abrangencia)
        assert not app.exception and not app.error, (evento, abrangencia)


# ===================================================================================== Etapa 20.7 — ajustes finais de apresentação
def _linhas(figura, prefixo):
    return [l for l in figura.axes[0].lines if (l.get_gid() or "").startswith(prefixo)]


def test_mensal_compacto_distingue_zero_publicado_de_mes_sem_valor_sem_barras_artificiais(sinesp):
    with graficos.modo_compacto():
        figura = graficos.figura_mensal_sinesp(sinesp, "Homicídio doloso", "Estadual", [2022, 2025, 2026])
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    for ano in (2022, 2025, 2026):
        zeros = int(((serie["ano"] == ano) & (serie["valor"] == 0)).sum())
        marcas = _linhas(figura, f"zero_{ano}")
        assert len(marcas) == zeros, ano  # uma marca por zero publicado
        barras = [b for b in figura.axes[0].patches if b.get_gid() == f"mensal_{ano}"]
        assert len(barras) == int(((serie["ano"] == ano) & serie["valor"].notna()).sum())  # nenhuma barra criada para mês sem valor
    assert len(_linhas(figura, "sem_valor_2026")) == 3 and not _linhas(figura, "sem_valor_2025")  # out–dez/2026 ainda não publicados; 2025 completo
    for marca in _linhas(figura, "sem_valor_2026"):
        assert marca.get_marker() == "x" and list(marca.get_ydata()) == [0]
    assert all(m.get_marker() == "_" and list(m.get_ydata()) == [0] for m in _linhas(figura, "zero_2022"))  # zero ≠ ausência: marcas diferentes
    with graficos.modo_compacto(False):
        completa = graficos.figura_mensal_sinesp(sinesp, "Homicídio doloso", "Estadual", [2022, 2025, 2026])
    assert not _linhas(completa, "zero_") and not _linhas(completa, "sem_valor_")  # o modo completo (desktop) não muda


def test_mensal_compacto_legenda_cronologica_e_ano_parcial_identificado(sinesp):
    with graficos.modo_compacto():
        prf = graficos.figura_mensal_sinesp(sinesp, "Mortes no trânsito", "Polícia Rodoviária Federal", [2026, 2024, 2025])
        hom = graficos.figura_mensal_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    assert [t.get_text() for t in prf.axes[0].get_legend().get_texts()] == ["2024", "2025", "2026 (parcial)", "Zero publicado", "Sem valor (×)"]
    assert len([b for b in prf.axes[0].patches if b.get_gid() == "mensal_2026"]) == 8  # PRF: janeiro a agosto
    textos = [t.get_text() for t in hom.axes[0].get_legend().get_texts()]
    assert textos[:7] == ["2020", "2021", "2022", "2023", "2024", "2025", "2026 (parcial)"]
    assert "ano parcial" in hom.sinesp_notas["interpretacao"].lower() and "2026 vai até o último mês disponível" in hom.sinesp_notas["interpretacao"]
    cores = {a: b.get_facecolor() for a in (2024, 2025) for b in prf.axes[0].patches if b.get_gid() == f"mensal_{a}"}
    assert cores[2024] != cores[2025]  # cores por ano preservadas


def test_ajuste_compacto_remove_espaco_em_branco_sem_cortar_nada_nem_mudar_numeros(sinesp):
    caixas = pytest.importorskip("test_estatistica_visual")._caixas_dos_textos
    for nome in ("serie_anual", "mensal", "distribuicao", "boxplot_anual", "mapa_calor", "outliers_iqr", "acumulado"):
        funcao = getattr(graficos, f"figura_{nome}_sinesp")
        with graficos.modo_compacto():
            figura = funcao(sinesp, "Homicídio doloso", "Estadual", ANOS)
            altura_antes = figura.get_figheight()
            antes = {l.get_gid(): list(l.get_ydata()) for l in figura.axes[0].lines}
            barras_antes = [b.get_height() for b in figura.axes[0].patches]
            graficos.ajustar_compacto(figura)
        assert figura.get_figheight() < altura_antes, nome  # imagem mais curta
        assert figura.get_figwidth() == pytest.approx(4.4)
        assert {l.get_gid(): list(l.get_ydata()) for l in figura.axes[0].lines} == antes and [b.get_height() for b in figura.axes[0].patches] == barras_antes
        limite = figura.bbox
        for artista, retangulo in caixas(figura):
            assert retangulo.x0 >= -1 and retangulo.y0 >= -1 and retangulo.x1 <= limite.x1 + 1 and retangulo.y1 <= limite.y1 + 1, (nome, artista.get_text()[:40])
        altura = figura.get_figheight()
        graficos.ajustar_compacto(figura)  # idempotente
        assert figura.get_figheight() == altura
    completa = graficos.figura_serie_anual_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    graficos.ajustar_compacto(completa)
    assert (completa.get_figwidth(), completa.get_figheight()) == (10, 6.2)  # desktop não é alterado


def test_fonte_completa_aparece_uma_unica_vez_no_modo_compacto(sinesp):
    with graficos.modo_compacto():
        figura = graficos.figura_serie_anual_sinesp(sinesp, "Homicídio doloso", "Estadual", ANOS)
    assert not any("MJSP" in t.get_text() or "Fonte" in t.get_text() for t in figura.texts)  # fora da imagem
    rodape = figura.sinesp_notas["rodape"]
    assert "MJSP / Sinesp VDE" in rodape and "Abrangência: Estadual" in rodape and "Unidade: vítimas" in rodape
    app = _pagina_compacta()
    fontes = [c.value for c in app.caption if c.value.startswith("Fonte: MJSP / Sinesp VDE | Abrangência")]
    assert fontes and all("Unidade:" in f for f in fontes)  # texto nativo, completo
    assert len(fontes) == len(set(range(len(fontes))))  # uma por figura exibida (sem repetição dentro do mesmo gráfico)
    legendas = [c.value for c in app.caption]
    for i, c in enumerate(legendas[:-1]):
        assert not (c.startswith("Fonte: MJSP") and legendas[i + 1].startswith("Fonte: MJSP")), i  # nunca duas fontes seguidas


def _pagina_compacta():
    app = AppTest.from_file(str(project_path("dashboard", "pages", "sinesp.py")), default_timeout=180).run()
    app.toggle[0].set_value(True).run()
    return app


def test_controles_da_pagina_em_ordem_clara_e_numeros_dos_filtros_inalterados():
    app = AppTest.from_file(str(project_path("dashboard", "pages", "sinesp.py")), default_timeout=180).run()
    assert [t.label for t in app.toggle] == ["Visualização compacta (celular)"]
    assert [s.label for s in app.selectbox] == ["Indicador"]  # linha 1: um único filtro de série (a abrangência vai no nome)
    assert [s.label for s in app.select_slider][:2] == ["Período (anos)", "Meses"]  # linha 2
    assert [m.value for m in cartoes(app)][:3] == ["29", "25", "81 de 81"]  # resultados aprovados
    app.select_slider[1].set_value((1, 3)).run()
    assert any(m.label.startswith("Jan–Mar de 2026") and m.value == "11" for m in cartoes(app)) and not app.exception
