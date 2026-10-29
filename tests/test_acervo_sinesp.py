"""Reprodutibilidade dos dados ativos a partir dos XLSX oficiais auditados (acervo local do Sinesp).

O acervo bruto não é versionado: sem ele, estes testes são pulados (por exemplo, em um clone limpo).
"""

import pytest

from dashboard import dados_publicos as dp
from src.pipeline import atualizacao_dados as au
from src.pipeline.utils import project_path

# Pasta (dentro de dados/brutos/sinesp) de cada XLSX auditado; vazio = fica na raiz da pasta.
ARQUIVOS_AUDITADOS = {
    2020: ("pendente_validacao_origem",), 2021: ("pendente_validacao_origem",), 2022: ("pendente_validacao_origem",),
    2023: (), 2024: (), 2025: (), 2026: (),
}


@pytest.fixture(scope="module")
def reconstrucao():
    # Sem os XLSX no computador, o teste é pulado; com eles, a base é reconstruída e comparada com a publicada.
    raiz = project_path("dados", "brutos", "sinesp")
    caminhos = {ano: raiz.joinpath(*sub, f"bancovde-{ano}.xlsx") for ano, sub in ARQUIVOS_AUDITADOS.items()}
    if not all(c.is_file() for c in caminhos.values()):
        pytest.skip("Acervo bruto do Sinesp ausente neste ambiente (esperado em clone limpo ou deploy).")
    mensal, catalogo, avisos = au.construir_sinesp({ano: au.ler_sinesp_xlsx(c) for ano, c in caminhos.items()})
    return mensal, catalogo, avisos


def _chaves(quadro):
    return quadro.set_index(["evento", "abrangencia", "ano", "mes"])


def test_valores_historicos_dos_originais_auditados_estao_preservados_nos_dados_ativos(reconstrucao):
    mensal, _, _ = reconstrucao
    ativo = dp.carregar_sinesp()
    assert len(mensal) == 900  # originais auditados: competências até 2026-08
    comum = _chaves(mensal).join(_chaves(ativo), how="left", lsuffix="_xlsx", rsuffix="_ativo")
    assert comum["unidade_ativo"].notna().all(), "competência histórica ausente nos dados ativos"
    assert comum["unidade_xlsx"].eq(comum["unidade_ativo"]).all()
    iguais = (comum["valor_xlsx"].eq(comum["valor_ativo"])) | (comum["valor_xlsx"].isna() & comum["valor_ativo"].isna())
    assert iguais.all(), comum.loc[~iguais].head()


def test_competencias_novas_dos_dados_ativos_sao_apenas_setembro_de_2026(reconstrucao):
    mensal, _, _ = reconstrucao
    ativo = dp.carregar_sinesp()
    novas = ativo.merge(mensal[["evento", "abrangencia", "ano", "mes"]], how="left", on=["evento", "abrangencia", "ano", "mes"], indicator=True)
    novas = novas[novas["_merge"] == "left_only"]
    assert len(novas) == len(ativo) - 900 == 11
    assert set(zip(novas["ano"], novas["mes"])) == {(2026, 9)}
    assert "Polícia Rodoviária Federal" not in set(novas["abrangencia"])  # a PRF ainda termina em 2026-08


def test_reconstrucao_dos_originais_reproduz_o_catalogo_nos_periodos_comuns(reconstrucao):
    mensal, catalogo, avisos = reconstrucao
    assert len(catalogo) == 12 and catalogo["meses_observados"].sum() == 900
    assert all("nota metodológica oficial" in a for a in avisos)  # só as duas séries com nota oficial somam linhas duplicadas
    ativo_catalogo = dp.carregar_catalogo_sinesp().set_index(["evento", "abrangencia"])
    for ficha in catalogo.itertuples():
        ativa = ativo_catalogo.loc[(ficha.evento, ficha.abrangencia)]
        assert ativa["unidade"] == ficha.unidade and int(ativa["meses_observados"]) - int(ficha.meses_observados) in (0, 1)
