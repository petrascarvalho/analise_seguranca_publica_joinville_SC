"""Testes dos dados curados do dashboard e dos cálculos (sem Streamlit e sem acervo bruto)."""

import json
import re
import shutil

import pandas as pd
import pytest

from dashboard import calculos
from dashboard import dados_publicos as dp
from scripts.utils import project_path

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
ACUMULADO_VD = {  # (2023, 2024), valores aprovados na Etapa 14.1
    "Ameaça": (1957, 2085), "Calúnia": (109, 119), "Difamação": (190, 211), "Estupro": (22, 30), "Injúria": (541, 716),
    "Injúria real": (2, 6), "Lesão corporal grave ou gravíssima dolosa": (19, 10), "Lesão corporal leve dolosa": (989, 959), "Vias de fato": (229, 281),
}


@pytest.fixture(scope="module")
def sinesp():
    return dp.carregar_sinesp()


@pytest.fixture(scope="module")
def vd():
    return dp.carregar_violencia_domestica()


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


# ------------------------------------------------------------------ integridade dos arquivos mínimos
def test_arquivos_minimos_existem_e_batem_com_o_manifesto():
    integridade = dp.verificar_integridade()
    assert set(integridade["arquivo"]) == set(dp.ARQUIVOS_DE_DADOS)
    assert integridade["integro"].all(), integridade
    manifesto = dp.carregar_manifesto()
    for ficha in manifesto["arquivos"]:
        quadro = pd.read_csv(dp.DIRETORIO_DADOS / ficha["arquivo"], dtype=str, keep_default_na=False)
        assert (len(quadro), quadro.shape[1]) == (ficha["linhas"], ficha["colunas"])
        assert list(quadro.columns) == ficha["esquema"]
    assert {f["arquivo"]: f["linhas"] for f in manifesto["arquivos"]} == {
        dp.ARQ_SINESP: 900, dp.ARQ_SINESP_CATALOGO: 12, dp.ARQ_VD: 216, dp.ARQ_VD_RASTREIO: 216}


def test_manifesto_v2_registra_versao_datas_validacao_fontes_licencas_e_origem():
    manifesto = dp.carregar_manifesto()
    assert manifesto["schema_manifesto"] == 2 and re.fullmatch(r"\d{8}T\d{6}Z", manifesto["versao"])
    assert manifesto["situacao_validacao"]["status"] in ("validado", "aprovado")
    datas = manifesto["datas"]  # data de geração, de consulta, de publicação e competência são campos distintos
    assert datas["gerado_em_utc"].endswith("Z") and "competência estatística" in datas["nota"]
    assert manifesto["cobertura"]["sinesp"]["ultima_competencia"] == "2026-08" and manifesto["cobertura"]["sinesp"]["ano_parcial"] == 2026
    assert manifesto["cobertura"]["ssp_violencia_domestica"]["ultima_competencia"] == "2024-12"
    assert len(manifesto["fontes"]) == 2
    por_id = {f["id"]: f for f in manifesto["fontes"]}
    mj, sc = por_id["sinesp_vde"]["licenca"], por_id["ssp_sc_violencia_domestica"]["licenca"]
    assert mj["catalogo"]["confirmada_na_consulta"] is False and "NXDOMAIN" in mj["catalogo"]["observacao"]  # não declara licença não confirmada
    assert "CC BY-ND 3.0" in mj["site"]["licenca"] and mj["site"]["confirmada_na_consulta"] is True
    assert "other-open" in sc["catalogo"]["licenca"] and sc["catalogo"]["confirmada_na_consulta"] is True
    assert "Todos os Direitos Reservados" in sc["site"]["licenca"]
    for fonte in manifesto["fontes"]:
        assert fonte["url"].startswith("https://") and fonte["licenca"]["data_consulta"] == "2026-10-27" and fonte["recursos"]
        assert "condicoes_de_reutilizacao" in fonte and "consulta" in fonte and "publicacao" in fonte
    assert "Nenhuma proibição específica" in manifesto["avaliacao_de_reutilizacao"] and "NÃO há autorização específica" in manifesto["avaliacao_de_reutilizacao"]
    assert "MJSP" in manifesto["atribuicao"] and "SSP/SC" in manifesto["atribuicao"]
    origem = manifesto["origem_dos_dados"]
    assert set(origem["sinesp_xlsx_sha256"]) == {str(a) for a in range(2020, 2027)} == set(origem["sinesp_xlsx_bytes"])
    assert len(origem["ssp_pdf_sha256"]) == 3 == len(origem["ssp_pdf_bytes"])
    assert all(re.fullmatch(r"[0-9a-f]{64}", h) for h in origem["sinesp_xlsx_sha256"].values())


def test_carregador_aceita_competencia_nova_e_recusa_lacuna_na_serie(sinesp):
    nova = sinesp[sinesp["evento"] == "Suicídio"].iloc[[0]].assign(ano=2026, mes=9, valor=4)
    com_setembro = pd.concat([sinesp, nova], ignore_index=True).astype(str).replace("<NA>", "")
    assert dp.validar_sinesp(com_setembro)["mes"].max() == 12  # 2026-09 é aceita (sem limite fixo em 08/2026)
    com_lacuna = pd.concat([sinesp, nova.assign(mes=11)], ignore_index=True).astype(str).replace("<NA>", "")
    with pytest.raises(dp.ErroDados, match="lacuna"):
        dp.validar_sinesp(com_lacuna)


def test_cobertura_e_periodo_equivalente_por_serie_com_dados_de_setembro(sinesp):
    ate_agosto_prf = sinesp.copy()
    novas = sinesp.groupby(["evento", "abrangencia", "unidade"], as_index=False).size().drop(columns="size")
    novas = novas[novas["abrangencia"] != "Polícia Rodoviária Federal"].assign(ano=2026, mes=9, valor=1)
    dados = pd.concat([ate_agosto_prf, novas[ate_agosto_prf.columns]], ignore_index=True)
    anual = calculos.tabela_anual_sinesp(dados)
    cobertura = anual[anual["ano"] == 2026].set_index(["evento", "abrangencia"])["cobertura"]
    assert cobertura[("Suicídio", "Estadual")] == "parcial janeiro–setembro"
    assert cobertura[("Mortes no trânsito", "Polícia Rodoviária Federal")] == "parcial janeiro–agosto"  # série defasada: cobertura por série
    suicidio = calculos.serie_sinesp(dados, "Suicídio", "Estadual")
    assert calculos.ultima_competencia_da_serie(suicidio) == (2026, 9) and calculos.mes_final_da_serie(suicidio) == 9
    comparacao = calculos.comparacao_ultimo_periodo_sinesp(suicidio)
    esperado_2025 = int(sinesp[(sinesp["evento"] == "Suicídio") & (sinesp["ano"] == 2025) & (sinesp["mes"] <= 9)]["valor"].sum())
    assert comparacao["periodo"] == "janeiro–setembro" and int(comparacao["valor_anterior"]) == esperado_2025 and comparacao["ano_atual"] == 2026
    assert calculos.comparacao_ultimo_periodo_sinesp(calculos.serie_sinesp(sinesp, "Suicídio", "Estadual"))["periodo"] == "janeiro–agosto"
    completo = sinesp[(sinesp["evento"] == "Suicídio") & (sinesp["ano"] <= 2025)]
    assert calculos.comparacao_ultimo_periodo_sinesp(completo) is None  # último ano completo: nada a comparar como parcial


def test_arquivos_minimos_nao_contem_dados_brutos_nem_pessoais():
    for nome in dp.ARQUIVOS_DE_DADOS:
        texto = (dp.DIRETORIO_DADOS / nome).read_text(encoding="utf-8")
        assert not re.search(r"\d{3}\.\d{3}\.\d{3}-\d{2}", texto)  # sem CPF
        assert "@" not in texto
    permitidos = set(dp.ARQUIVOS_DE_DADOS) | {dp.ARQ_MANIFESTO, "LEIAME.md"}
    assert {p.name for p in dp.DIRETORIO_DADOS.iterdir() if p.is_file()} <= permitidos  # nenhum PDF, XLSX ou bruto extra


# --------------------------------------------------------------------------------------- Sinesp
def test_sinesp_cobertura_unidades_e_chaves(sinesp):
    assert sinesp.shape == (900, 6) and list(sinesp.columns) == dp.COLUNAS_SINESP
    assert not sinesp.duplicated(["evento", "abrangencia", "ano", "mes"]).any()
    assert sinesp["valor"].notna().all()  # nas séries publicadas não há ausência; se houver, deve permanecer <NA>
    assert (sinesp["ano"] * 100 + sinesp["mes"]).min() == 202001 and (sinesp["ano"] * 100 + sinesp["mes"]).max() == 202608
    assert sinesp.groupby(["evento", "abrangencia"]).ngroups == 12
    unidades = sinesp.groupby("evento")["unidade"].unique()
    assert set(unidades["Mandado de prisão cumprido"]) == {"mandados cumpridos (contagem publicada)"}
    assert all(set(u) == {"vítimas"} for evento, u in unidades.items() if evento != "Mandado de prisão cumprido")
    pf = sinesp[sinesp["abrangencia"].eq("Polícia Federal")]
    assert (pf["ano"] * 100 + pf["mes"]).min() == 202501 and len(pf) == 20  # sem linhas antes de 2025 (ausência de cobertura, não zero)


def test_sinesp_totais_anuais_iguais_ao_readme(sinesp):
    esperado = _tabela_readme("| Indicador / abrangência | 2020")
    assert len(esperado) == 12
    anual = calculos.tabela_anual_sinesp(sinesp)
    for rotulo, valores in esperado.items():
        evento, abrangencia = ROTULOS_README[rotulo]
        parte = anual[anual["evento"].eq(evento) & anual["abrangencia"].eq(abrangencia)].set_index("ano")["soma"]
        for ano, valor in zip(range(2020, 2027), valores):
            if valor is None:
                assert ano not in parte.index, f"{rotulo} {ano}: cobertura inexistente deve permanecer ausente"
            else:
                assert int(parte.loc[ano]) == valor, f"{rotulo} {ano}"


def test_sinesp_janeiro_agosto_iguais_ao_readme(sinesp):
    esperado = _tabela_readme("| Indicador / abrangência | 2020", )
    # a segunda tabela do README (janeiro–agosto) vem depois do título da seção
    linhas = README.read_text(encoding="utf-8").splitlines()
    inicio = next(i for i, l in enumerate(linhas) if l.startswith("### Comparações equivalentes: janeiro–agosto"))
    tabela = {}
    for linha in linhas[inicio:]:
        if linha.startswith("|") and not linha.startswith("|---") and "Indicador / abrangência" not in linha:
            celulas = [c.strip() for c in linha.strip("|").split("|")]
            tabela[celulas[0]] = [None if c == "—" else int(c) for c in celulas[1:]]
        elif tabela and not linha.startswith("|"):
            break
    assert len(tabela) == 12 and esperado
    periodo = calculos.comparacao_periodo_sinesp(sinesp, 8)
    for rotulo, valores in tabela.items():
        evento, abrangencia = ROTULOS_README[rotulo]
        parte = periodo[periodo["evento"].eq(evento) & periodo["abrangencia"].eq(abrangencia)].set_index("ano")["soma"]
        for ano, valor in zip(range(2020, 2027), valores):
            if valor is None:
                assert ano not in parte.index
            else:
                assert int(parte.loc[ano]) == valor, f"{rotulo} jan–ago {ano}"


def test_sinesp_homicidio_valores_conhecidos_e_2026_parcial(sinesp):
    anual = calculos.tabela_anual_sinesp(sinesp)
    h = anual[anual["evento"].eq("Homicídio doloso")].sort_values("ano")
    assert h["soma"].astype(int).tolist() == [62, 62, 49, 55, 36, 29, 22]
    assert h["cobertura"].tolist() == ["ano completo"] * 6 + ["parcial janeiro–agosto"]
    ja = calculos.comparacao_periodo_sinesp(sinesp, 8)
    assert ja[ja["evento"].eq("Homicídio doloso")].sort_values("ano")["soma"].astype(int).tolist() == [50, 40, 29, 40, 21, 18, 22]
    comp = calculos.comparacao_2026_2025_sinesp(sinesp)
    linha = comp[comp["evento"].eq("Homicídio doloso")].iloc[0]
    assert (int(linha["valor_2025"]), int(linha["valor_2026"]), int(linha["diferenca_absoluta"])) == (18, 22, 4)
    assert float(linha["variacao_percentual"]) == pytest.approx(22.22)
    zero = comp[comp["evento"].eq("Feminicídio")].iloc[0]  # base zero: percentual não aplicável, sem valor artificial
    assert pd.isna(zero["variacao_percentual"]) and int(zero["diferenca_absoluta"]) == 0


def test_sinesp_nao_ha_soma_entre_indicadores(sinesp):
    anual = calculos.tabela_anual_sinesp(sinesp)
    assert anual.groupby(["evento", "abrangencia", "ano"]).size().eq(1).all()
    assert "total" not in " ".join(map(str.lower, anual["evento"].unique()))


# ------------------------------------------------------------------------------ violência doméstica
def test_violencia_domestica_216_observacoes_validadas(vd):
    assert vd.shape == (216, 5) and list(vd.columns) == dp.COLUNAS_VD
    assert sorted(vd["categoria"].unique()) == sorted(dp.CATEGORIAS_VD)
    assert vd.groupby(["ano", "mes"]).size().eq(9).all() and vd.groupby(["ano", "mes"]).ngroups == 24
    assert not vd.duplicated(["municipio", "ano", "mes", "categoria"]).any()
    assert int(vd["fatos_comunicados"].eq(0).sum()) == 27 and vd["fatos_comunicados"].notna().all()
    assert vd.groupby("categoria").size().eq(24).all()


def test_violencia_domestica_totais_por_categoria_e_comparacao(vd):
    comparacao = calculos.comparacao_anual_vd(vd).set_index("categoria")
    for categoria, (a, b) in ACUMULADO_VD.items():
        assert (int(comparacao.loc[categoria, "acumulado_2023"]), int(comparacao.loc[categoria, "acumulado_2024"])) == (a, b)
        assert int(comparacao.loc[categoria, "diferenca_absoluta"]) == b - a
        assert float(comparacao.loc[categoria, "variacao_percentual"]) == pytest.approx(round((b - a) / a * 100, 2))
    assert len(comparacao) == 9 and "Total" not in comparacao.index
    # mesmo período nos dois anos e meses contados
    parcial = calculos.comparacao_anual_vd(vd, ["Ameaça"], 1, 6)
    assert (parcial["meses_2023"].iloc[0], parcial["meses_2024"].iloc[0]) == (6, 6)
    esperado = int(vd[(vd["categoria"] == "Ameaça") & (vd["ano"] == 2023) & (vd["mes"] <= 6)]["fatos_comunicados"].sum())
    assert int(parcial["acumulado_2023"].iloc[0]) == esperado


def test_variacao_percentual_nao_aplicavel_com_base_zero(vd):
    ajustado = vd.copy()
    mascara = (ajustado["categoria"] == "Injúria real") & (ajustado["ano"] == 2023)
    ajustado.loc[mascara, "fatos_comunicados"] = 0
    linha = calculos.comparacao_anual_vd(ajustado, ["Injúria real"]).iloc[0]
    assert int(linha["acumulado_2023"]) == 0 and pd.isna(linha["variacao_percentual"]) and "não aplicável" in linha["observacao_variacao"]


def test_estatisticas_e_extremos_vd(vd):
    est = calculos.estatisticas_vd(vd).set_index("categoria")
    assert int(est.loc["Ameaça", "soma_publicada"]) == 4042 and est.loc["Ameaça", "media_mensal"] == pytest.approx(168.4167)
    assert est.loc["Ameaça", "desvio_padrao_ddof0"] == pytest.approx(22.5683, abs=1e-4)
    assert int(est["meses_com_zero"].sum()) == 27 and est["meses_observados"].eq(24).all()
    ext = calculos.extremos_vd(vd, "Difamação")
    assert ext["maximo"] == 24 and ext["competencias_maximo"] == ["2023-01", "2024-02"]  # empates preservados
    assert calculos.extremos_vd(vd, "Ameaça")["maximo"] == 209


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


@pytest.mark.parametrize("arquivo, antigo, novo, trecho", [
    (dp.ARQ_SINESP, "2020,1,Feminicídio,Estadual,vítimas,0", "2020,1,Feminicídio,Estadual,vítimas,-3", "valor inválido"),
    (dp.ARQ_SINESP, "2020,1,Feminicídio,Estadual,vítimas,0", "2020,13,Feminicídio,Estadual,vítimas,0", "mês fora de 1–12"),
    (dp.ARQ_SINESP, "2020,1,Feminicídio,Estadual,vítimas,0", "2020,2,Feminicídio,Estadual,vítimas,0", "repetidas"),
    (dp.ARQ_SINESP, "2020,1,Feminicídio,Estadual,vítimas,0", "2020,1,Feminicídio,Estadual,mandados,0", "mais de uma unidade"),
    (dp.ARQ_VD, "JOINVILLE,2023,1,Ameaça,199", "JOINVILLE,2023,1,Ameaça,", "valor vazio"),
    (dp.ARQ_VD, "JOINVILLE,2023,1,Ameaça,199", "JOINVILLE,2023,1,Ameaça,19,9", "valor inválido|Esquema|malformado|ilegível"),
    (dp.ARQ_VD, "JOINVILLE,2023,1,Ameaça,199", "JOINVILLE,2025,1,Ameaça,199", "ano fora de 2023–2024"),
    (dp.ARQ_VD, "JOINVILLE,2023,1,Calúnia,17", "JOINVILLE,2023,1,Ameaça,17", "repetida"),
    (dp.ARQ_VD, "JOINVILLE,2023,1,Calúnia,17", "JOINVILLE,2023,1,Roubo,17", "categoria desconhecida"),
])
def test_valores_invalidos_geram_erro_explicito(tmp_path, arquivo, antigo, novo, trecho):
    destino = _copiar_dados(tmp_path)
    caminho = destino / arquivo
    texto = caminho.read_text(encoding="utf-8")
    assert antigo in texto
    caminho.write_text(texto.replace(antigo, novo, 1), encoding="utf-8", newline="\n")
    carregar = dp.carregar_sinesp if arquivo == dp.ARQ_SINESP else dp.carregar_violencia_domestica
    with pytest.raises((dp.ErroDados, pd.errors.ParserError), match=trecho):
        carregar(destino)


def test_integridade_detecta_arquivo_alterado(tmp_path):
    destino = _copiar_dados(tmp_path)
    caminho = destino / dp.ARQ_VD
    caminho.write_text(caminho.read_text(encoding="utf-8").replace("JOINVILLE,2023,1,Ameaça,199", "JOINVILLE,2023,1,Ameaça,198", 1), encoding="utf-8", newline="\n")
    resultado = dp.verificar_integridade(destino).set_index("arquivo")
    assert not resultado.loc[dp.ARQ_VD, "integro"] and resultado.drop(dp.ARQ_VD)["integro"].all()


def test_hash_normalizado_ignora_fim_de_linha_do_checkout():
    assert dp.sha256_normalizado(b"a,b\r\n1,2\r\n") == dp.sha256_normalizado(b"a,b\n1,2\n")
    manifesto = json.loads((dp.DIRETORIO_DADOS / dp.ARQ_MANIFESTO).read_text(encoding="utf-8"))
    conteudo = (dp.DIRETORIO_DADOS / dp.ARQ_VD).read_bytes().replace(b"\n", b"\r\n")
    assert dp.sha256_normalizado(conteudo) == next(f["sha256"] for f in manifesto["arquivos"] if f["arquivo"] == dp.ARQ_VD)


# ---------------------------------------------------------------------------- independência do acervo
def test_codigo_do_dashboard_nao_depende_do_acervo_nem_do_roteiro():
    codigos = list(project_path("dashboard").rglob("*.py")) + [project_path("scripts", "painel_streamlit.py")]
    for caminho in codigos:
        texto = caminho.read_text(encoding="utf-8")
        assert not re.search(r"\b[A-Za-z]:[\\/]", texto), caminho  # nenhum caminho absoluto de Windows
        assert "analise_seguranca_publica" not in texto, caminho
        assert "dados/processados" not in texto and "dados/brutos" not in texto, caminho
        assert "scripts.analysis" not in texto, caminho
