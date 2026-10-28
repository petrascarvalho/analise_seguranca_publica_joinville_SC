"""Testes dos dados curados do dashboard (fonte única Sinesp/MJSP) e dos cálculos — sem Streamlit e sem acervo bruto."""

import json
import re
import shutil

import pandas as pd
import pytest

from dashboard import calculos
from dashboard import dados_publicos as dp
from src.pipeline.utils import project_path

README = project_path("README.md")

# README: rótulo da linha -> (evento, abrangência) do arquivo curado.
ROTULOS_README = {
    "Feminicídio — Estadual": ("Feminicídio", "Estadual"),
    "Homicídio doloso — Estadual": ("Homicídio doloso", "Estadual"),
    "Lesão corporal seguida de morte — Estadual": ("Lesão corporal seguida de morte", "Estadual"),
    "Mandados — Estadual": ("Mandado de prisão cumprido", "Estadual"),
    "Mortalidade no trânsito¹ — Estadual": ("Morte no trânsito ou em decorrência dele (exceto homicídio doloso)", "Estadual"),
    "Mortes a esclarecer — Estadual": ("Mortes a esclarecer (sem indício de crime)", "Estadual"),
    "Mortes no trânsito — PRF": ("Mortes no trânsito", "Polícia Rodoviária Federal"),
    "Latrocínio — Estadual": ("Roubo seguido de morte (latrocínio)", "Estadual"),
    "Suicídio — Estadual": ("Suicídio", "Estadual"),
    "Tentativa de feminicídio — Estadual": ("Tentativa de feminicídio", "Estadual"),
    "Tentativa de homicídio — Estadual": ("Tentativa de homicídio", "Estadual"),
    "Mandados — PF": ("Mandado de prisão cumprido", "Polícia Federal"),
}
ULTIMA_COMPETENCIA_ATIVA = "2026-09"  # versão ativa aprovada na Etapa 18 (setembro/2026 publicado pelo Sinesp)


@pytest.fixture(scope="module")
def sinesp():
    return dp.carregar_sinesp()


@pytest.fixture(scope="module")
def catalogo():
    return dp.carregar_catalogo_sinesp()


def _tabela_readme(titulo: str) -> dict:
    """Lê do README a primeira tabela depois do título; devolve {rótulo: [valores por ano 2020..2026 ou None]}."""
    linhas = README.read_text(encoding="utf-8").splitlines()
    inicio = next(i for i, linha in enumerate(linhas) if linha.startswith(titulo))
    tabela = {}
    for linha in linhas[inicio:]:
        if linha.startswith("|") and not linha.startswith("|---") and "Indicador / abrangência" not in linha:
            celulas = [c.strip() for c in linha.strip("|").split("|")]
            tabela[celulas[0]] = [None if c == "—" else int(c.replace(".", "")) for c in celulas[1:]]
        elif tabela and not linha.startswith("|"):
            break
    return tabela


def _tabela_readme_decimal(titulo: str) -> dict:
    """Tabela de estatísticas do README: {rótulo: (meses, soma, média, mediana, mín., máx., desvio)} com vírgula decimal."""
    linhas = README.read_text(encoding="utf-8").splitlines()
    inicio = next(i for i, linha in enumerate(linhas) if linha.startswith(titulo))
    tabela = {}
    for linha in linhas[inicio:]:
        if linha.startswith("|") and not linha.startswith("|---") and "Indicador / abrangência" not in linha:
            c = [x.strip() for x in linha.strip("|").split("|")]
            numero = lambda t: float(t.replace(".", "").replace(",", "."))
            tabela[c[0]] = (int(c[1]), int(c[2]), numero(c[3]), numero(c[4]), int(c[5]), int(c[6]), numero(c[7]))
        elif tabela and not linha.startswith("|"):
            break
    return tabela


# ------------------------------------------------------------------ integridade dos arquivos mínimos
def test_arquivos_de_dados_ativos_sao_apenas_os_do_sinesp():
    assert dp.ARQUIVOS_DE_DADOS == ("sinesp_joinville_mensal.csv", "sinesp_catalogo_indicadores.csv")
    permitidos = set(dp.ARQUIVOS_DE_DADOS) | {dp.ARQ_MANIFESTO, "LEIAME.md"}
    presentes = {p.name for p in dp.DIRETORIO_DADOS.iterdir() if p.is_file()}
    assert presentes == permitidos, presentes ^ permitidos  # sem CSVs de outras fontes, PDFs, XLSX ou brutos
    assert not any("ssp" in nome.lower() or "domestic" in nome.lower() for nome in presentes)


def test_arquivos_batem_com_o_manifesto_e_dimensoes(sinesp, catalogo):
    integridade = dp.verificar_integridade()
    assert set(integridade["arquivo"]) == set(dp.ARQUIVOS_DE_DADOS) and integridade["integro"].all(), integridade
    manifesto = dp.carregar_manifesto()
    for ficha in manifesto["arquivos"]:
        quadro = pd.read_csv(dp.DIRETORIO_DADOS / ficha["arquivo"], dtype=str, keep_default_na=False)
        assert (len(quadro), quadro.shape[1]) == (ficha["linhas"], ficha["colunas"]) and list(quadro.columns) == ficha["esquema"]
    assert {f["arquivo"]: f["linhas"] for f in manifesto["arquivos"]} == {dp.ARQ_SINESP: 911, dp.ARQ_SINESP_CATALOGO: 12}
    assert sinesp.shape == (911, 6) and catalogo.shape == (12, 12)
    dp.validar_consistencia(sinesp, catalogo)


def test_manifesto_v3_fonte_unica_versao_datas_validacao_licencas_e_origem():
    manifesto = dp.carregar_manifesto()
    assert manifesto["schema_manifesto"] == 3 and re.fullmatch(r"\d{8}T\d{6}Z", manifesto["versao"])
    assert re.fullmatch(r"\d{8}T\d{6}Z", manifesto["versao_anterior"])  # versão anterior preservada e rastreável
    assert manifesto["situacao_validacao"]["status"] == "aprovado" and manifesto["situacao_validacao"]["erros"] == []
    aprovacao = manifesto["aprovacao"]  # data de aprovação real, registrada pela promoção (não inventada)
    assert aprovacao["aprovado_em_utc"].endswith("Z") and aprovacao["aceitou_revisoes"] is False and aprovacao["candidata"] == manifesto["versao"]
    datas = manifesto["datas"]
    assert datas["gerado_em_utc"].endswith("Z") and datas["ultima_consulta_as_fontes_utc"] and "competência estatística" in datas["nota"]
    cobertura = manifesto["cobertura"]
    assert cobertura["sinesp"]["primeira_competencia"] == "2020-01" and cobertura["sinesp"]["ultima_competencia"] == ULTIMA_COMPETENCIA_ATIVA
    assert cobertura["sinesp"]["ano_parcial"] == 2026 and set(cobertura) == {"sinesp", "series"}
    assert len(cobertura["series"]) == 12
    fins = {(s["evento"], s["abrangencia"]): s["ultima_competencia"] for s in cobertura["series"]}
    assert fins[("Mortes no trânsito", "Polícia Rodoviária Federal")] == "2026-08"  # PRF defasada, registrada por série
    assert sum(1 for f in fins.values() if f == "2026-09") == 11
    assert {u for u in manifesto["unidades"]} == {dp.UNIDADE_VITIMAS, dp.UNIDADE_MANDADOS}
    assert [f["id"] for f in manifesto["fontes"]] == ["sinesp_vde"]  # fonte única
    fonte = manifesto["fontes"][0]
    assert fonte["url"].startswith("https://www.gov.br/mj/") and len(fonte["recursos"]) == 7 and fonte["licenca"]["data_consulta"] == "2026-10-27"
    mj = fonte["licenca"]
    assert mj["catalogo"]["confirmada_na_consulta"] is False and "NXDOMAIN" in mj["catalogo"]["observacao"]  # não declara licença não confirmada
    assert "CC BY-ND 3.0" in mj["site"]["licenca"] and mj["site"]["confirmada_na_consulta"] is True
    assert "Nenhuma proibição específica" in manifesto["avaliacao_de_reutilizacao"] and "NÃO há autorização específica" in manifesto["avaliacao_de_reutilizacao"]
    assert "MJSP" in manifesto["atribuicao"] and "SSP" not in manifesto["atribuicao"]
    assert any("Recorte exato" in r for r in manifesto["regras_etl"]) and "XLSX" in manifesto["metodo_de_obtencao"]
    origem = manifesto["origem_dos_dados"]
    assert set(origem) == {"sinesp_xlsx_sha256", "sinesp_xlsx_bytes"}
    assert set(origem["sinesp_xlsx_sha256"]) == {str(a) for a in range(2020, 2027)} == set(origem["sinesp_xlsx_bytes"])
    assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in origem["sinesp_xlsx_sha256"].values())
    texto = json.dumps(manifesto, ensure_ascii=False).lower()
    assert "ssp_" not in texto and "violência doméstica" not in texto and "violencia_domestica" not in texto  # nenhuma dependência operacional de outras fontes


def test_arquivos_minimos_nao_contem_dados_pessoais():
    for nome in dp.ARQUIVOS_DE_DADOS:
        texto = (dp.DIRETORIO_DADOS / nome).read_text(encoding="utf-8")
        assert not re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto) and "@" not in texto


# --------------------------------------------------------------------------------------- Sinesp
def test_cobertura_por_serie_unidades_e_chaves(sinesp, catalogo):
    assert list(sinesp.columns) == dp.COLUNAS_SINESP
    assert not sinesp.duplicated(["evento", "abrangencia", "ano", "mes"]).any()
    assert sinesp["valor"].notna().all()  # se algum dia houver ausência, deve permanecer <NA> (testado abaixo)
    chaves = sinesp["ano"] * 100 + sinesp["mes"]
    assert chaves.min() == 202001 and chaves.max() == 202609
    assert sinesp.groupby(["evento", "abrangencia"]).ngroups == 12
    unidades = sinesp.groupby("evento")["unidade"].unique()
    assert set(unidades["Mandado de prisão cumprido"]) == {dp.UNIDADE_MANDADOS}
    assert all(set(u) == {dp.UNIDADE_VITIMAS} for evento, u in unidades.items() if evento != "Mandado de prisão cumprido")
    fim = sinesp.groupby(["evento", "abrangencia"]).apply(lambda s: int((s["ano"] * 100 + s["mes"]).max()), include_groups=False)
    assert fim[("Mortes no trânsito", "Polícia Rodoviária Federal")] == 202608
    assert (fim.drop(("Mortes no trânsito", "Polícia Rodoviária Federal")) == 202609).all()
    pf = sinesp[sinesp["abrangencia"].eq("Polícia Federal")]
    assert (pf["ano"] * 100 + pf["mes"]).min() == 202501 and len(pf) == 21  # sem linhas antes de 2025: ausência de cobertura, não zero
    cat = catalogo.set_index(["evento", "abrangencia"])
    assert cat.loc[("Mortes no trânsito", "Polícia Rodoviária Federal"), "fim"] == "2026-08" and int(cat["meses_observados"].astype(int).sum()) == 911


def test_historico_preservado_na_atualizacao_para_setembro(sinesp):
    """Os 900 valores da versão anterior (até 2026-08) permanecem idênticos; só 11 observações de 2026-09 foram acrescentadas."""
    anterior = sinesp[sinesp["ano"] * 100 + sinesp["mes"] <= 202608]
    assert len(anterior) == 900 and len(sinesp) - len(anterior) == 11
    anual = calculos.tabela_anual_sinesp(sinesp)
    h = anual[anual["evento"].eq("Homicídio doloso")].sort_values("ano")
    assert h["soma"].astype(int).tolist()[:6] == [62, 62, 49, 55, 36, 29]  # anos completos inalterados
    ate_agosto = calculos.comparacao_periodo_sinesp(sinesp, 8)
    assert ate_agosto[ate_agosto["evento"].eq("Homicídio doloso")].sort_values("ano")["soma"].astype(int).tolist() == [50, 40, 29, 40, 21, 18, 22]


def test_totais_anuais_e_janeiro_agosto_iguais_as_tabelas_do_readme(sinesp):
    esperado = _tabela_readme("| Indicador / abrangência | 2020")
    assert len(esperado) == 12
    anual = calculos.tabela_anual_sinesp(sinesp)
    for rotulo, valores in esperado.items():
        evento, abrangencia = ROTULOS_README[rotulo]
        parte = anual[anual["evento"].eq(evento) & anual["abrangencia"].eq(abrangencia)].set_index("ano")
        for ano, valor in zip(range(2020, 2026), valores[:6]):  # anos completos (2026 é parcial e não consta como total anual)
            if valor is None:
                assert ano not in parte.index
            else:
                assert int(parte.loc[ano, "soma"]) == valor and parte.loc[ano, "cobertura"] == "ano completo", f"{rotulo} {ano}"
    linhas = README.read_text(encoding="utf-8").splitlines()
    inicio = next(i for i, l in enumerate(linhas) if l.startswith("### Comparações equivalentes: janeiro–agosto"))
    tabela = {}
    for linha in linhas[inicio:]:
        if linha.startswith("|") and not linha.startswith("|---") and "Indicador / abrangência" not in linha:
            celulas = [c.strip() for c in linha.strip("|").split("|")]
            tabela[celulas[0]] = [None if c == "—" else int(c) for c in celulas[1:]]
        elif tabela and not linha.startswith("|"):
            break
    assert len(tabela) == 12
    periodo = calculos.comparacao_periodo_sinesp(sinesp, 8)
    for rotulo, valores in tabela.items():
        evento, abrangencia = ROTULOS_README[rotulo]
        parte = periodo[periodo["evento"].eq(evento) & periodo["abrangencia"].eq(abrangencia)].set_index("ano")["soma"]
        for ano, valor in zip(range(2020, 2027), valores):
            if valor is None:
                assert ano not in parte.index
            else:
                assert int(parte.loc[ano]) == valor, f"{rotulo} jan–ago {ano}"
    # janeiro–setembro: a PRF ainda não tem setembro/2026 (a tabela traz '—' em 2026 e a série não entra nesse período)
    setembro = _tabela_readme("### Comparações equivalentes: janeiro–setembro")
    assert len(setembro) == 12
    periodo9 = calculos.comparacao_periodo_sinesp(sinesp, 9)
    for rotulo, valores in setembro.items():
        evento, abrangencia = ROTULOS_README[rotulo]
        parte = periodo9[periodo9["evento"].eq(evento) & periodo9["abrangencia"].eq(abrangencia)].set_index("ano")["soma"].dropna()
        for ano, valor in zip(range(2020, 2027), valores):
            if valor is None:
                assert ano not in parte.index, f"{rotulo} jan–set {ano}"
            else:
                assert int(parte.loc[ano]) == valor, f"{rotulo} jan–set {ano}"
    # estatísticas mensais do README
    estatisticas = _tabela_readme_decimal("| Indicador / abrangência | Meses")
    assert len(estatisticas) == 12
    for rotulo, (meses, soma, media, mediana, minimo, maximo, desvio) in estatisticas.items():
        evento, abrangencia = ROTULOS_README[rotulo]
        resumo = calculos.resumo_serie_sinesp(calculos.serie_sinesp(sinesp, evento, abrangencia))
        assert (resumo["meses_observados"], int(resumo["soma"]), int(resumo["minimo"]), int(resumo["maximo"])) == (meses, soma, minimo, maximo), rotulo
        assert round(float(resumo["media_mensal"]), 2) == media and round(float(resumo["mediana_mensal"]), 2) == mediana, rotulo
        assert round(float(resumo["desvio_padrao_ddof0"]), 2) == desvio, rotulo


def test_ano_parcial_por_serie_e_periodo_equivalente(sinesp):
    anual = calculos.tabela_anual_sinesp(sinesp)
    cobertura_2026 = anual[anual["ano"] == 2026].set_index(["evento", "abrangencia"])["cobertura"]
    assert cobertura_2026[("Suicídio", "Estadual")] == "parcial janeiro–setembro"
    assert cobertura_2026[("Mortes no trânsito", "Polícia Rodoviária Federal")] == "parcial janeiro–agosto"  # série defasada
    assert anual[(anual["ano"] <= 2025)]["cobertura"].isin(["ano completo"]).all()
    suicidio = calculos.serie_sinesp(sinesp, "Suicídio", "Estadual")
    comparacao = calculos.comparacao_ultimo_periodo_sinesp(suicidio)
    esperado_2025 = int(sinesp[(sinesp["evento"] == "Suicídio") & (sinesp["ano"] == 2025) & (sinesp["mes"] <= 9)]["valor"].sum())
    esperado_2026 = int(sinesp[(sinesp["evento"] == "Suicídio") & (sinesp["ano"] == 2026)]["valor"].sum())
    assert comparacao["periodo"] == "janeiro–setembro" and int(comparacao["valor_anterior"]) == esperado_2025 and int(comparacao["valor_atual"]) == esperado_2026
    prf = calculos.comparacao_ultimo_periodo_sinesp(calculos.serie_sinesp(sinesp, "Mortes no trânsito", "Polícia Rodoviária Federal"))
    assert prf["periodo"] == "janeiro–agosto"  # cada série compara no seu próprio período equivalente
    todas = calculos.comparacao_ultimo_periodo_todas_as_series(sinesp)
    assert len(todas) == 12 and set(todas["periodo"]) == {"janeiro–setembro", "janeiro–agosto"}
    homicidio = todas[todas["evento"] == "Homicídio doloso"].iloc[0]
    assert int(homicidio["valor_atual"]) == 25 and homicidio["ano_atual"] == 2026  # 22 até agosto + 3 em setembro
    completo = sinesp[(sinesp["evento"] == "Suicídio") & (sinesp["ano"] <= 2025)]
    assert calculos.comparacao_ultimo_periodo_sinesp(completo) is None  # último ano completo: nada a comparar como parcial


def test_variacao_percentual_nao_aplicavel_com_base_zero(sinesp):
    assert pd.isna(calculos.variacao(0, 3)[1]) and calculos.variacao(0, 3)[0] == 3
    assert pd.isna(calculos.variacao(pd.NA, 3)[0])
    assert calculos.variacao(50, 40) == (-10, -20.0)
    sintetica = pd.DataFrame({"ano": [2025] * 3 + [2026] * 3, "mes": [1, 2, 3] * 2, "evento": "X", "abrangencia": "Estadual", "unidade": "vítimas",
                              "valor": pd.array([0, 0, 0, 1, 0, 2], dtype="Int64")})
    resultado = calculos.comparacao_ultimo_periodo_sinesp(sintetica)  # ano anterior com total zero: percentual não aplicável, diferença informada
    assert resultado["periodo"] == "janeiro–março" and int(resultado["diferenca_absoluta"]) == 3 and pd.isna(resultado["variacao_percentual"])


def test_estatisticas_descritivas_por_ano_e_geral(sinesp):
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    est = calculos.estatisticas_por_ano(serie).set_index("ano")
    valores_2023 = serie[serie["ano"] == 2023]["valor"].astype(float)
    assert int(est.loc[2023, "soma"]) == 55 and est.loc[2023, "meses_observados"] == 12
    assert est.loc[2023, "media_mensal"] == pytest.approx(valores_2023.mean()) and est.loc[2023, "mediana_mensal"] == pytest.approx(valores_2023.median())
    assert est.loc[2023, "desvio_padrao_ddof0"] == pytest.approx(valores_2023.std(ddof=0))  # descritivo, ddof=0
    assert est.loc[2023, "minimo"] == valores_2023.min() and est.loc[2023, "maximo"] == valores_2023.max()
    assert est.loc[2026, "cobertura"] == "parcial janeiro–setembro" and est.loc[2026, "meses_observados"] == 9
    geral = calculos.resumo_serie_sinesp(serie)
    assert geral["meses_observados"] == 81 and geral["soma"] == 62 + 62 + 49 + 55 + 36 + 29 + 25


def test_variacoes_anuais_so_entre_anos_completos_consecutivos(sinesp):
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    v = calculos.variacoes_anuais(serie)
    assert v["ano"].tolist() == [2021, 2022, 2023, 2024, 2025]  # 2026 (parcial) fora
    assert v["valor"].astype(int).tolist() == [62, 49, 55, 36, 29]
    assert v["diferenca_absoluta"].astype(int).tolist() == [0, -13, 6, -19, -7]
    assert float(v.loc[v["ano"] == 2022, "variacao_percentual"].iloc[0]) == pytest.approx(round(-13 / 62 * 100, 2))
    pf = calculos.serie_sinesp(sinesp, "Mandado de prisão cumprido", "Polícia Federal")
    assert calculos.variacoes_anuais(pf).empty  # PF só tem 2025 completo: sem anos consecutivos


def test_comparar_anos_completos_e_recusa_de_ano_parcial(sinesp):
    serie = calculos.serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    c = calculos.comparar_anos_completos(serie, 2020, 2025)
    assert (int(c["valor_a"]), int(c["valor_b"]), int(c["diferenca_absoluta"])) == (62, 29, -33) and c["variacao_percentual"] == pytest.approx(-53.23)
    assert calculos.comparar_anos_completos(serie, 2025, 2026) is None  # 2026 parcial nunca é comparado com ano completo
    assert calculos.comparar_anos_completos(serie, 2019, 2025) is None


def test_ranking_por_unidade_nao_mistura_unidades_nem_soma(sinesp):
    rank = calculos.ranking_por_unidade(sinesp, 2025, dp.UNIDADE_VITIMAS)
    assert set(rank["unidade"]) == {dp.UNIDADE_VITIMAS} and rank["soma"].is_monotonic_decreasing and len(rank) == 10
    assert rank.iloc[0]["soma"] >= rank.iloc[-1]["soma"]
    mandados = calculos.ranking_por_unidade(sinesp, 2025, dp.UNIDADE_MANDADOS)
    assert set(mandados["abrangencia"]) == {"Estadual", "Polícia Federal"} and set(mandados["unidade"]) == {dp.UNIDADE_MANDADOS}
    assert calculos.ranking_por_unidade(sinesp, 2026, dp.UNIDADE_VITIMAS).empty  # ano parcial: sem ranking
    assert calculos.anos_completos_comuns(sinesp)[-1] == 2025 and 2026 not in calculos.anos_completos_comuns(sinesp)


def test_achados_principais_sao_descritivos_e_vem_dos_dados(sinesp):
    achados = calculos.achados_principais(sinesp)
    texto = " ".join(a["titulo"] + " " + a["texto"] for a in achados)
    assert "62 vítimas em 2020 para 29 em 2025" in texto and "janeiro–setembro" in texto and "Maiores contagens de vítimas em 2025" in texto
    assert "sem total entre indicadores" in texto and "causa" in texto.lower() and "causou" not in texto.lower()
    assert len(achados) == 4


def test_soma_com_valor_ausente_permanece_ausente_e_nao_vira_zero(sinesp):
    ausente = sinesp.copy()
    mascara = (ausente["evento"] == "Suicídio") & (ausente["ano"] == 2021) & (ausente["mes"] == 3)
    ausente.loc[mascara, "valor"] = pd.NA
    anual = calculos.tabela_anual_sinesp(ausente)
    linha = anual[(anual["evento"] == "Suicídio") & (anual["ano"] == 2021)].iloc[0]
    assert linha["meses_com_valor"] == 11 and linha["meses_presentes"] == 12 and pd.isna(linha["soma"])  # nada de soma parcial
    assert pd.isna(calculos.comparacao_periodo_sinesp(ausente, 8).query("evento == 'Suicídio' and ano == 2021")["soma"].iloc[0])
    assert calculos.variacoes_anuais(calculos.serie_sinesp(ausente, "Suicídio", "Estadual")).query("ano in (2021, 2022)").empty
    como_texto = ausente.astype("object").where(ausente.notna(), "").astype(str)  # como no CSV: ausência = campo vazio
    assert dp.validar_sinesp(como_texto)["valor"].isna().sum() == 1  # o carregador também preserva a ausência


# ------------------------------------------------------------------------- falhas explícitas
def _copiar_dados(tmp_path):
    destino = tmp_path / "data_publica"
    shutil.copytree(dp.DIRETORIO_DADOS, destino)
    return destino


def test_arquivo_ausente_gera_erro_explicito(tmp_path):
    with pytest.raises(dp.ErroDados, match="não encontrado"):
        dp.carregar_sinesp(tmp_path)
    with pytest.raises(dp.ErroDados, match="Manifesto não encontrado"):
        dp.carregar_manifesto(tmp_path)


def test_esquema_incompativel_gera_erro_explicito(tmp_path):
    destino = _copiar_dados(tmp_path)
    caminho = destino / dp.ARQ_SINESP
    caminho.write_text(caminho.read_text(encoding="utf-8").replace("ano,mes,evento", "ano,mes,indicador", 1), encoding="utf-8", newline="\n")
    with pytest.raises(dp.ErroDados, match="Esquema inesperado"):
        dp.carregar_sinesp(destino)


@pytest.mark.parametrize("antigo, novo, trecho", [
    ("2020,1,Feminicídio,Estadual,vítimas,0", "2020,1,Feminicídio,Estadual,vítimas,-3", "valor inválido"),
    ("2020,1,Feminicídio,Estadual,vítimas,0", "2020,1,Feminicídio,Estadual,vítimas,3,5", "valor inválido|Esquema|malformado|ilegível"),
    ("2020,1,Feminicídio,Estadual,vítimas,0", "2020,13,Feminicídio,Estadual,vítimas,0", "mês fora de 1–12"),
    ("2020,1,Feminicídio,Estadual,vítimas,0", "2019,1,Feminicídio,Estadual,vítimas,0", "ano fora de"),
    ("2020,1,Feminicídio,Estadual,vítimas,0", "2020,2,Feminicídio,Estadual,vítimas,0", "repetidas"),
    ("2020,1,Feminicídio,Estadual,vítimas,0", "2020,1,Feminicídio,Estadual,mandados,0", "mais de uma unidade"),
    ("2020,1,Feminicídio,Estadual,vítimas,0", ",1,Feminicídio,Estadual,vítimas,0", "valor vazio"),
    ("2020,1,Feminicídio,Estadual,vítimas,0", "2020,1,,Estadual,vítimas,0", "campo 'evento' vazio"),
])
def test_valores_invalidos_geram_erro_explicito(tmp_path, antigo, novo, trecho):
    destino = _copiar_dados(tmp_path)
    caminho = destino / dp.ARQ_SINESP
    texto = caminho.read_text(encoding="utf-8")
    assert antigo in texto
    caminho.write_text(texto.replace(antigo, novo, 1), encoding="utf-8", newline="\n")
    with pytest.raises((dp.ErroDados, pd.errors.ParserError), match=trecho):
        dp.carregar_sinesp(destino)


def test_lacuna_de_competencias_na_serie_e_erro_explicito(tmp_path):
    destino = _copiar_dados(tmp_path)
    caminho = destino / dp.ARQ_SINESP
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    alvo = next(l for l in linhas if l.startswith("2020,3,Feminicídio,Estadual,"))
    caminho.write_text("\n".join(l for l in linhas if l != alvo) + "\n", encoding="utf-8", newline="\n")  # remove uma competência do meio da série
    with pytest.raises(dp.ErroDados, match="lacuna"):
        dp.carregar_sinesp(destino)


def test_catalogo_inconsistente_e_detectado(tmp_path, sinesp):
    destino = _copiar_dados(tmp_path)
    caminho = destino / dp.ARQ_SINESP_CATALOGO
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    caminho.write_text("\n".join(linhas[:-1]) + "\n", encoding="utf-8", newline="\n")  # remove uma série do catálogo
    with pytest.raises(dp.ErroDados, match="séries diferentes"):
        dp.validar_consistencia(sinesp, dp.carregar_catalogo_sinesp(destino))
    adulterado = pd.read_csv(dp.DIRETORIO_DADOS / dp.ARQ_SINESP_CATALOGO, dtype=str, keep_default_na=False)
    adulterado.loc[0, "meses_valor_zero"] = "999"
    with pytest.raises(dp.ErroDados, match="inconsistente"):
        dp.validar_consistencia(sinesp, adulterado)


def test_integridade_detecta_arquivo_alterado(tmp_path):
    destino = _copiar_dados(tmp_path)
    caminho = destino / dp.ARQ_SINESP
    caminho.write_text(caminho.read_text(encoding="utf-8").replace("2020,2,Feminicídio,Estadual,vítimas,0", "2020,2,Feminicídio,Estadual,vítimas,9", 1), encoding="utf-8", newline="\n")
    resultado = dp.verificar_integridade(destino).set_index("arquivo")
    assert not resultado.loc[dp.ARQ_SINESP, "integro"] and resultado.drop(dp.ARQ_SINESP)["integro"].all()


def test_hash_normalizado_ignora_fim_de_linha_do_checkout():
    assert dp.sha256_normalizado(b"a,b\r\n1,2\r\n") == dp.sha256_normalizado(b"a,b\n1,2\n")
    manifesto = json.loads((dp.DIRETORIO_DADOS / dp.ARQ_MANIFESTO).read_text(encoding="utf-8"))
    conteudo = (dp.DIRETORIO_DADOS / dp.ARQ_SINESP).read_bytes().replace(b"\n", b"\r\n")
    assert dp.sha256_normalizado(conteudo) == next(f["sha256"] for f in manifesto["arquivos"] if f["arquivo"] == dp.ARQ_SINESP)


# ---------------------------------------------------------------------------- independência do acervo
def test_codigo_ativo_nao_depende_do_acervo_do_roteiro_nem_de_outras_fontes():
    codigos = list(project_path("dashboard").rglob("*.py")) + [project_path("scripts", "painel_streamlit.py")] + [
        project_path("src", "pipeline", p) for p in ("fontes_oficiais.py", "atualizacao_dados.py", "versionamento_dados.py")]
    for caminho in codigos:
        texto = caminho.read_text(encoding="utf-8")
        assert not re.search(r"\b[A-Za-z]:[\\/]", texto), caminho  # nenhum caminho absoluto de Windows
        assert "dados/processados" not in texto and "dados/brutos/ssp" not in texto and "scripts.analysis" not in texto, caminho
        assert not re.search(r"ssp_sc|violencia_domestica|fatos_comunicados|Fato Comunicado|SEPROT|seprot", texto), caminho
        assert "analise_seguranca_publica" not in texto, caminho
