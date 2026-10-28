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
    """Executa o fluxo completo uma vez (cerca de 1 a 2 minutos) e grava numa pasta temporária."""
    pasta = tmp_path_factory.mktemp("ssp_sc")
    resumo = ssp_sc.exportar(pasta)
    leitura = {"dtype": {"ano": "Int64", "mes": "Int64", "valor": "Int64"}}
    return {
        "resumo": resumo,
        "inventario": pd.read_csv(pasta / "inventario_acervo_ssp_sc.csv"),
        "vd": pd.read_csv(pasta / "violencia_domestica_joinville_tratada.csv", **leitura),
        "versoes": pd.read_csv(pasta / "homicidios_boletins_joinville_versoes.csv"),
        "grupos": pd.read_csv(pasta / "homicidios_republicacoes_grupos.csv"),
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
    assert processado["resumo"]["violencia_domestica"]["verificacoes_aprovadas"] == "68 de 68"
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
    assert versoes["grupo_republicacao"].notna().sum() == grupos["quantidade_edicoes"].sum() == 264  # o JOIN não multiplicou linhas
    assert set(versoes["periodo_tipo"]) == {"ano completo", "período acumulado"} and set(versoes["unidade"]) == {"vítimas"}


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
