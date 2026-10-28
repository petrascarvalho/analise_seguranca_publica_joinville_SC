"""Acervo SSP/SC (inventário, violência doméstica, homicídios dos boletins) e UNION auditável com o Sinesp.

Os testes que leem os PDFs são pulados quando o acervo local (dados/brutos/ssp_sc/, fora do Git) não existe.
"""

import pandas as pd
import pytest

from dashboard import dados_publicos as dp
from src.pipeline import consolidacao, ssp_sc
from src.pipeline.utils import project_path

precisa_acervo = pytest.mark.skipif(not ssp_sc.acervo_disponivel(), reason="acervo SSP/SC local ausente (fora do Git)")


@pytest.fixture(scope="module")
def processado(tmp_path_factory):
    """Executa o fluxo completo uma vez (cerca de 30 s) e grava numa pasta temporária (tabelas e gráfico)."""
    pasta = tmp_path_factory.mktemp("ssp_sc")
    resumo = ssp_sc.exportar(pasta, pasta_graficos=pasta)
    leitura = {"dtype": {"ano": "Int64", "mes": "Int64", "valor": "Int64"}}
    return {
        "resumo": resumo,
        "inventario": pd.read_csv(pasta / "inventario_acervo_ssp_sc.csv"),
        "vd": pd.read_csv(pasta / "violencia_domestica_joinville_tratada.csv", **leitura),
        "versoes": pd.read_csv(pasta / "homicidios_boletins_joinville_versoes.csv"),
        "grupos": pd.read_csv(pasta / "homicidios_republicacoes_grupos.csv"),
        "verificacoes": pd.read_csv(pasta / "verificacoes_extracao_ssp_sc.csv"),
        "rastreabilidade": pd.read_csv(pasta / "rastreabilidade_celulas_ssp_sc.csv", dtype=str, keep_default_na=False),
        "grafico": pasta / "07-sspsc_violencia_domestica_2023_2024.png",
    }


# ------------------------------------------------------------------------------------------------ acervo
@precisa_acervo
def test_acervo_tem_45_pdfs_oficiais_cada_um_com_o_seu_csv_derivado_e_sem_copias(processado):
    inv = processado["inventario"]
    assert len(inv) == 45 and inv["par_completo"].all() and not inv["pdf_duplicado"].any()
    assert inv["tipo_documento"].str.startswith("relatório de violência doméstica").sum() == 3
    assert inv["tipo_documento"].str.startswith("boletim mensal").sum() == 42
    assert processado["resumo"]["originais_inalterados"] is True  # hashes dos brutos iguais antes e depois


# ------------------------------------------------------------------------------------- violência doméstica
@precisa_acervo
def test_violencia_domestica_preserva_as_216_celulas_publicadas_sem_preencher_nem_somar(processado):
    vd = processado["vd"]
    assert len(vd) == 216 and vd["indicador"].nunique() == 9
    assert vd[["ano", "mes"]].drop_duplicates().shape[0] == 24 and sorted(vd["ano"].unique()) == [2023, 2024]
    assert not vd.duplicated(subset=["serie_id", "ano", "mes"]).any()  # uma célula por categoria e mês
    assert vd["valor"].notna().all() and int(vd["valor"].eq(0).sum()) == 27  # zeros publicados mantidos; nenhum ausente
    assert set(vd["unidade"]) == {"Fato Comunicado"} and vd["situacao_validacao"].str.startswith("em validação").all()
    # cada mês vem de um único relatório: não há republicação a somar
    assert vd.groupby(["ano", "mes"])["arquivo_origem"].nunique().eq(1).all()
    verificacoes = processado["verificacoes"]
    assert len(verificacoes) >= 150 and verificacoes["ok"].all()  # CSV = PDF em cada linha usada, cabeçalhos, meses e alinhamento
    assert processado["resumo"]["verificacoes_aprovadas"] == f"{len(verificacoes)} de {len(verificacoes)}"
    # rótulos originais preservados (as duas grafias das lesões corporais)
    assert {"Lesão corporal leve 0 Dolosa", "Lesão corporal leve - Dolosa"} <= set(vd["indicador_original"])
    ameaca = vd.loc[vd["indicador"].eq("Violência doméstica — Ameaça")]
    assert int(ameaca.loc[ameaca["ano"].eq(2023), "valor"].sum()) == 1957 and int(ameaca.loc[ameaca["ano"].eq(2024), "valor"].sum()) == 2085


# ---------------------------------------------------------------------------------------------- homicídios
@precisa_acervo
def test_homicidios_dos_boletins_mantem_todas_as_versoes_e_os_58_grupos_sem_escolher_uma(processado):
    versoes, grupos = processado["versoes"], processado["grupos"]
    assert len(versoes) == 294 and versoes["edicao"].nunique() == 42
    assert len(grupos) == 58 and int(grupos["divergente"].sum()) == 41 and int((~grupos["divergente"]).sum()) == 17
    assert grupos["classificacao"].value_counts().to_dict() == {
        "Inconsistência ainda não explicada": 37, "Sem divergência de valor": 17, "Possível problema de cabeçalho": 4}
    assert versoes["grupo_republicacao"].notna().sum() == grupos["quantidade_edicoes"].sum() == 264  # o JOIN não multiplicou linhas
    assert set(versoes["periodo_tipo"]) == {"ano completo", "período acumulado"} and set(versoes["unidade"]) == {"vítimas"}
    sem_grupo = versoes["grupo_republicacao"].isna()
    assert sem_grupo.sum() == 30 and versoes.loc[sem_grupo, "grupo_divergente"].isna().all()
    assert grupos["explicacao_documental"].notna().all()


@precisa_acervo
def test_cada_celula_exportada_tem_coordenadas_valor_e_hash_do_pdf(processado):
    rastros = processado["rastreabilidade"]
    assert len(rastros) == 510 and rastros.groupby("conjunto").size().to_dict() == {"homicídios": 294, "violência doméstica": 216}
    coordenadas = ["arquivo_pdf", "pagina_pdf", "tabela_pdf", "linha_tabela", "coluna_csv"]
    assert not rastros.duplicated(coordenadas).any()
    inventario = processado["inventario"].set_index("arquivo_pdf")
    for r in rastros.itertuples(index=False):
        linha = ssp_sc.linha_da_tabela_no_pdf(r.arquivo_pdf, int(r.pagina_pdf), int(r.tabela_pdf), int(r.linha_tabela))
        assert linha[int(r.coluna_csv.removeprefix("celula_")) - 1] == r.valor_publicado
        assert r.sha256_pdf == inventario.loc[r.arquivo_pdf, "sha256_pdf"]


@precisa_acervo
def test_inventario_atual_corresponde_aos_hashes_versionados(processado):
    fixado = pd.read_csv(project_path("documentacao", "auditoria", "ssp_sc_acervo_sha256.csv"))
    colunas = list(fixado.columns)
    pd.testing.assert_frame_equal(fixado.sort_values("arquivo_pdf").reset_index(drop=True),
                                  processado["inventario"][colunas].sort_values("arquivo_pdf").reset_index(drop=True))


@precisa_acervo
def test_saida_compativel_com_as_tabelas_preservadas_da_etapa24(processado):
    tabelas = {"vd": "violencia_domestica_joinville_tratada.csv", "versoes": "homicidios_boletins_joinville_versoes.csv",
               "grupos": "homicidios_republicacoes_grupos.csv", "inventario": "inventario_acervo_ssp_sc.csv"}
    if not all((ssp_sc.PASTA_PROCESSADOS / nome).is_file() for nome in tabelas.values()):
        pytest.skip("saídas locais da Etapa 24 ausentes; comparação de regressão não executada")
    for chave, nome in tabelas.items():
        antiga = pd.read_csv(ssp_sc.PASTA_PROCESSADOS / nome).astype("string")
        nova = processado[chave].astype("string")
        colunas = list(antiga.columns)
        pd.testing.assert_frame_equal(antiga.sort_values(colunas).reset_index(drop=True),
                                      nova[colunas].sort_values(colunas).reset_index(drop=True))


# ------------------------------------------------------------------------------------------------ UNION
def test_sinesp_no_esquema_comum_mantem_as_911_observacoes_e_os_valores():
    comum = consolidacao.sinesp_no_esquema_comum()
    publicada = dp.carregar_sinesp()
    assert list(comum.columns) == consolidacao.ESQUEMA and len(comum) == 911
    assert comum["serie_id"].nunique() == 12 and int(comum["valor"].eq(0).sum()) == 401 and comum["valor"].notna().all()
    assert comum["valor"].astype(int).tolist() == publicada["valor"].astype(int).tolist()  # nenhum valor alterado
    assert set(comum["unidade"]) == set(publicada["unidade"]) and set(comum["periodicidade"]) == {"mensal"}


@precisa_acervo
def test_uniao_empilha_as_fontes_sem_multiplicar_somar_ou_misturar_unidades(processado):
    sinesp = consolidacao.sinesp_no_esquema_comum()
    uniao = consolidacao.unir(sinesp, processado["vd"])
    assert len(uniao) == 911 + 216
    assert uniao.groupby("fonte").size().to_dict() == {"SSP/SC": 216, "Sinesp/MJSP": 911}
    assert (uniao.groupby("serie_id")["unidade"].nunique() == 1).all()  # nenhuma série com duas unidades
    assert set(uniao["periodicidade"]) == {"mensal"}  # homicídios anuais/acumulados ficaram fora
    assert set(uniao.columns) == set(consolidacao.ESQUEMA)  # só agregados municipais: nenhum dado pessoal
    with pytest.raises(ValueError):
        consolidacao.unir(sinesp, sinesp)  # a mesma observação duas vezes é recusada


def test_consolidado_de_duas_fontes_nao_e_gravado_enquanto_a_ssp_estiver_em_validacao():
    matriz = consolidacao.matriz_compatibilidade()
    assert len(matriz) == 4 and matriz.loc[matriz["conjunto"].str.startswith("SSP/SC — violência"), "situacao"].item() == "em validação"
    assert not project_path("dados", "processados", "joinville_indicadores_consolidados.csv").exists()


@precisa_acervo
def test_grafico_de_violencia_domestica_identifica_fonte_unidade_em_validacao_e_nao_soma_categorias(processado):
    from PIL import Image

    assert processado["grafico"].is_file() and Image.open(processado["grafico"]).size[0] >= 1000
    vd = ssp_sc.extrair_violencia_domestica()
    figura = ssp_sc.figura_violencia_domestica(vd)
    textos = " ".join(t.get_text() for t in figura.texts) + figura.get_suptitle()
    for trecho in ("SSP/SC", "Fato Comunicado — definição em validação", "2023 e 2024", "categorias não são somadas", "não integra o painel"):
        assert trecho in textos, trecho
    barras = {b.get_label(): [int(r.get_width()) for r in b] for b in figura.axes[0].containers}
    totais = vd.groupby(["ano", "categoria"])["fatos_comunicados"].sum()
    assert sorted(barras["2023"]) == sorted(totais[2023].tolist()) and sorted(barras["2024"]) == sorted(totais[2024].tolist())


def test_extracao_ssp_nao_depende_do_roteiro_antigo():
    codigo = project_path("src", "pipeline", "ssp_sc.py").read_text(encoding="utf-8")
    assert "exec(" not in codigo and "historico" not in codigo and "analise_seguranca_publica" not in codigo
