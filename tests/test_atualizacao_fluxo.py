"""Testes das operações B (preparar) e C (aprovar/reverter) com fixtures sintéticas.

Os XLSX do Sinesp são GERADOS a partir dos dados ativos (formato dos arquivos oficiais: 14 colunas, serial Excel,
linhas de outros municípios), em diretórios temporários. Nenhum dado real, nenhum acervo bruto e nenhuma rede.
"""

import hashlib
import json
import shutil

import pandas as pd
import pytest
from openpyxl import Workbook

from dashboard import dados_publicos as dp
from src.pipeline import atualizacao_dados as au
from src.pipeline import transform
from src.pipeline import versionamento_dados as vv


# ---------------------------------------------------------------------------------------- fixtures
@pytest.fixture()
def ambiente(tmp_path):
    ativa = tmp_path / "dashboard" / "data_publica"
    shutil.copytree(dp.DIRETORIO_DADOS, ativa)
    base = tmp_path / "atualizacao"
    return {"ativa": ativa, "staging": base / "staging", "versoes": base / "versoes", "entradas": tmp_path / "entradas", "base": base, "tmp": tmp_path}


def _hash_pasta(pasta):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(pasta.iterdir()) if p.is_file()}


def _linhas_xlsx(mensal, ano):
    linhas = []
    for r in mensal[mensal["ano"] == ano].itertuples():
        mandado = r.evento == vv.EVENTO_MANDADO
        serial = (pd.Timestamp(int(ano), int(r.mes), 1) - pd.Timestamp("1899-12-30")).days
        valor = None if pd.isna(r.valor) else int(r.valor)
        linhas.append(["SC", "JOINVILLE", r.evento, serial, None, None, None, None, None, None,
                       None if mandado else valor, valor if mandado else None, None, r.abrangencia])
    return linhas


def _escrever_xlsx(caminho, linhas, cabecalho=None, extras=True):
    livro = Workbook()
    planilha = livro.active
    planilha.append(cabecalho or transform.HEADERS)
    for linha in linhas:
        planilha.append(linha)
    if extras:  # linhas de outros municípios/UF, que o filtro deve ignorar
        serial = (pd.Timestamp(2023, 1, 1) - pd.Timestamp("1899-12-30")).days
        planilha.append(["SC", "BLUMENAU", "Homicídio doloso", serial, None, None, None, None, None, None, 99, None, None, "Estadual"])
        planilha.append(["PR", "JOINVILLE", "Homicídio doloso", serial, None, None, None, None, None, None, 77, None, None, "Estadual"])
    livro.save(caminho)


def _entradas(pasta, mensal, anos=range(2020, 2027)):
    pasta.mkdir(parents=True, exist_ok=True)
    for ano in anos:
        _escrever_xlsx(pasta / f"bancovde-{ano}.xlsx", _linhas_xlsx(mensal, ano))
    return pasta


def _com_proxima_competencia(mensal, valor=1, ignorar=()):
    """Acrescenta, a cada série, a competência seguinte à sua última (a PRF, que termina em 2026-08, ganha 2026-09; as demais, 2026-10)."""
    mensal = mensal.assign(indice=mensal["ano"] * 12 + mensal["mes"] - 1)
    ultimas = mensal.groupby(["evento", "abrangencia", "unidade"], as_index=False)["indice"].max()
    ultimas = ultimas[~ultimas["evento"].isin(ignorar)]
    proximo = ultimas["indice"] + 1
    novas = ultimas.assign(ano=proximo // 12, mes=proximo % 12 + 1, valor=valor)
    return pd.concat([mensal.drop(columns="indice"), novas[mensal.drop(columns="indice").columns]], ignore_index=True)


def _preparar(amb, mensal=None, **extra):
    mensal = dp.carregar_sinesp(amb["ativa"]) if mensal is None else mensal
    pasta = _entradas(amb["entradas"] / f"e{len(list(amb['entradas'].glob('e*'))) if amb['entradas'].exists() else 0}", mensal)
    return au.preparar(ativa=amb["ativa"], staging_root=amb["staging"], entradas_sinesp=pasta, **extra)


def _agora(segundos):
    return pd.Timestamp("2026-10-27 12:00:00", tz="UTC").to_pydatetime().replace(second=segundos)


# --------------------------------------------------------------------------- leitura do XLSX oficial
def test_leitura_xlsx_filtra_joinville_e_preserva_valores(ambiente):
    mensal = dp.carregar_sinesp(ambiente["ativa"])
    caminho = ambiente["tmp"] / "bancovde-2023.xlsx"
    _escrever_xlsx(caminho, _linhas_xlsx(mensal, 2023))
    quadro = au.ler_sinesp_xlsx(caminho)
    assert list(quadro.columns) == transform.HEADERS
    assert len(quadro) == int((mensal["ano"] == 2023).sum())  # as 2 linhas extras de outros municípios/UF ficaram de fora
    assert quadro["uf"].eq("SC").all() and quadro["municipio"].eq("JOINVILLE").all()
    assert sorted(quadro["total_vitima"].dropna().astype(int)) == sorted(
        mensal[(mensal["ano"] == 2023) & (mensal["evento"] != vv.EVENTO_MANDADO)]["valor"].astype(int))


@pytest.mark.parametrize("cabecalho", [
    [c if c != "total_vitima" else "vitimas" for c in transform.HEADERS],  # coluna renomeada
    transform.HEADERS[:-1],                                              # coluna removida
    transform.HEADERS + ["nova_coluna"],                                  # coluna adicional
])
def test_alteracao_de_esquema_do_xlsx_e_recusada(ambiente, cabecalho):
    caminho = ambiente["tmp"] / "bancovde-2023.xlsx"
    _escrever_xlsx(caminho, [], cabecalho=cabecalho)
    with pytest.raises(au.ErroAtualizacao, match="esquema|Esquema|Nenhuma linha"):
        au.ler_sinesp_xlsx(caminho)


# ------------------------------------------------------------------------------------ construir
def _recorte(linhas):
    return pd.DataFrame(linhas, columns=transform.HEADERS)


def _linha(evento="Homicídio doloso", ano=2026, mes=1, vitimas=3, total=None, abrangencia="Estadual", serial=None):
    serial = serial if serial is not None else (pd.Timestamp(ano, mes, 1) - pd.Timestamp("1899-12-30")).days
    return ["SC", "JOINVILLE", evento, serial, None, None, None, None, None, None, vitimas, total, None, abrangencia]


def test_construir_preserva_zero_e_ausencia_e_unidades_separadas():
    recorte = _recorte([_linha(vitimas=0), _linha(mes=2, vitimas=None), _linha(evento=vv.EVENTO_MANDADO, vitimas=None, total=7, abrangencia="Polícia Federal")])
    mensal, catalogo, avisos = au.construir_sinesp({2026: recorte})
    assert avisos == []
    homicidio = mensal[mensal["evento"] == "Homicídio doloso"].sort_values("mes")
    assert homicidio["valor"].iloc[0] == 0 and pd.isna(homicidio["valor"].iloc[1])  # zero publicado ≠ ausência
    mandados = mensal[mensal["evento"] == vv.EVENTO_MANDADO]
    assert mandados["unidade"].iloc[0] == vv.UNIDADE_MANDADOS and int(mandados["valor"].iloc[0]) == 7
    assert set(mensal[mensal["evento"] == "Homicídio doloso"]["unidade"]) == {vv.UNIDADE_VITIMAS}
    cat = catalogo.set_index(["evento", "abrangencia"])
    assert cat.loc[("Homicídio doloso", "Estadual"), "meses_valor_zero"] == 1 and cat.loc[("Homicídio doloso", "Estadual"), "meses_sem_valor"] == 1
    assert _csv_vazio_para_ausente(mensal)


def _csv_vazio_para_ausente(mensal):
    linhas = au._csv_bytes(mensal).decode("utf-8").splitlines()
    return any(l.endswith(",") for l in linhas) and any(l.endswith(",0") for l in linhas)


@pytest.mark.parametrize("linha, trecho", [
    (_linha(evento="Roubo de veículo"), "Indicador novo"),
    (_linha(vitimas=-1), "Valor inválido"),
    (_linha(vitimas=2.5), "Valor inválido"),
    (_linha(vitimas="três"), "Valor inválido"),
    (_linha(abrangencia=None), "Abrangência ausente"),
    (_linha(serial=46000.5), "Data de referência inválida"),
    (_linha(serial=(pd.Timestamp(2026, 1, 15) - pd.Timestamp("1899-12-30")).days), "primeiro dia"),
    (_linha(ano=2025), "outro ano"),
])
def test_valores_e_estruturas_invalidos_interrompem_a_construcao(linha, trecho):
    with pytest.raises(au.ErroAtualizacao, match=trecho):
        au.construir_sinesp({2026: _recorte([linha])})


def test_linhas_multiplas_so_sao_somadas_onde_ha_nota_oficial():
    mensal, _, avisos = au.construir_sinesp({2026: _recorte([_linha(evento="Tentativa de homicídio", vitimas=2), _linha(evento="Tentativa de homicídio", vitimas=3)])})
    assert int(mensal["valor"].iloc[0]) == 5 and len(mensal) == 1 and "nota metodológica oficial" in avisos[0]
    with pytest.raises(au.ErroAtualizacao, match="[Ss]em deduplicação genérica"):
        au.construir_sinesp({2026: _recorte([_linha(vitimas=2), _linha(vitimas=2)])})  # Homicídio doloso repetido: sem nota oficial


# -------------------------------------------------------------------------------------- preparar
def test_preparar_com_originais_identicos_reproduz_os_dados_ativos_sem_alterar_a_ativa(ambiente):
    antes = _hash_pasta(ambiente["ativa"])
    candidato = _preparar(ambiente)
    assert _hash_pasta(ambiente["ativa"]) == antes  # a versão ativa não é tocada
    assert candidato.validacao.status == "validado" and candidato.validacao.erros == [] and candidato.comparacao.empty
    for nome in dp.ARQUIVOS_DE_DADOS:
        assert (candidato.diretorio / "dados" / nome).read_bytes() == (ambiente["ativa"] / nome).read_bytes()
    manifesto = json.loads((candidato.diretorio / "dados" / dp.ARQ_MANIFESTO).read_text(encoding="utf-8"))
    assert manifesto["versao"] == candidato.id and manifesto["versao_anterior"] == dp.carregar_manifesto(ambiente["ativa"])["versao"]
    assert manifesto["situacao_validacao"]["status"] == "validado" and manifesto["aprovacao"] is None
    assert set(manifesto["origem_dos_dados"]["sinesp_xlsx_sha256"]) == {str(a) for a in range(2020, 2027)}
    assert dp.verificar_integridade(candidato.diretorio / "dados")["integro"].all()
    assert (ambiente["base"] / "historico.jsonl").is_file()


def test_nova_competencia_e_detectada_sem_ser_promovida(ambiente):
    mensal = _com_proxima_competencia(dp.carregar_sinesp(ambiente["ativa"]))
    antes = _hash_pasta(ambiente["ativa"])
    candidato = _preparar(ambiente, mensal)
    assert candidato.validacao.status == "validado" and candidato.validacao.informacoes["novas_competencias"] == 12
    assert set(candidato.comparacao["situacao"]) == {"novo"} and set(zip(candidato.comparacao["ano"], candidato.comparacao["mes"])) == {(2026, 9), (2026, 10)}
    prf = candidato.comparacao[candidato.comparacao["abrangencia"] == "Polícia Rodoviária Federal"]
    assert set(zip(prf["ano"], prf["mes"])) == {(2026, 9)}  # a PRF avança de agosto para setembro; as demais, de setembro para outubro
    assert candidato.validacao.informacoes["ultima_competencia"] == "2026-10"
    manifesto = json.loads((candidato.diretorio / "dados" / dp.ARQ_MANIFESTO).read_text(encoding="utf-8"))
    assert manifesto["cobertura"]["sinesp"]["ultima_competencia"] == "2026-10" and manifesto["cobertura"]["sinesp"]["ano_parcial"] == 2026
    assert _hash_pasta(ambiente["ativa"]) == antes  # nada foi substituído durante a preparação
    assert dp.carregar_manifesto(ambiente["ativa"])["cobertura"]["sinesp"]["ultima_competencia"] == "2026-09"


def test_series_com_competencias_desalinhadas_sao_informadas_sem_bloquear(ambiente):
    mensal = _com_proxima_competencia(dp.carregar_sinesp(ambiente["ativa"]), ignorar=["Mortes no trânsito"])
    candidato = _preparar(ambiente, mensal)
    assert candidato.validacao.status == "validado" and candidato.validacao.erros == []
    atrasadas = candidato.validacao.informacoes["series_com_ultima_competencia_diferente"]
    assert atrasadas["Mortes no trânsito/Polícia Rodoviária Federal"] == 202608 and all(v < 202610 for v in atrasadas.values())


def test_nova_competencia_fora_de_sequencia_e_erro(ambiente):
    mensal = dp.carregar_sinesp(ambiente["ativa"])
    nova = mensal[(mensal["evento"] == "Suicídio")].iloc[[0]].assign(ano=2026, mes=11, valor=1)  # pula outubro (última publicada: setembro)
    candidato = _preparar(ambiente, pd.concat([mensal, nova], ignore_index=True))
    assert candidato.validacao.status == "bloqueado" and any("lacuna" in e.lower() for e in candidato.validacao.erros)


def test_revisao_de_competencia_historica_e_detectada_e_exige_aceite(ambiente):
    mensal = dp.carregar_sinesp(ambiente["ativa"])
    mascara = (mensal["evento"] == "Homicídio doloso") & (mensal["ano"] == 2023) & (mensal["mes"] == 5)
    original = int(mensal.loc[mascara, "valor"].iloc[0])
    mensal.loc[mascara, "valor"] = original + 4
    candidato = _preparar(ambiente, mensal)
    assert candidato.validacao.status == "requer_revisao"
    linha = candidato.comparacao[candidato.comparacao["situacao"] == "alterado"].iloc[0]
    assert (linha["evento"], linha["ano"], linha["mes"], int(linha["valor_ativo"]), int(linha["valor_candidato"])) == ("Homicídio doloso", 2023, 5, original, original + 4)
    assert any("REVISÃO HISTÓRICA" in a for a in candidato.validacao.avisos)
    antes = _hash_pasta(ambiente["ativa"])
    with pytest.raises(au.ErroAtualizacao, match="--aceitar-revisoes"):
        au.aprovar(candidato.id, confirmacao=candidato.id, ativa=ambiente["ativa"], staging_root=ambiente["staging"], versoes_root=ambiente["versoes"])
    assert _hash_pasta(ambiente["ativa"]) == antes


def test_competencia_historica_removida_bloqueia_a_promocao(ambiente):
    mensal = dp.carregar_sinesp(ambiente["ativa"])
    removida = mensal[~((mensal["evento"] == "Suicídio") & (mensal["ano"] == 2026) & (mensal["mes"] == 9))]  # some a última competência da série
    candidato = _preparar(ambiente, removida)
    assert candidato.validacao.status == "bloqueado" and any("removida" in e for e in candidato.validacao.erros)
    with pytest.raises(au.ErroAtualizacao, match="erros de validação"):
        au.aprovar(candidato.id, confirmacao=candidato.id, aceitar_revisoes=True, ativa=ambiente["ativa"], staging_root=ambiente["staging"], versoes_root=ambiente["versoes"])


def test_serie_nova_ou_ausente_bloqueia(ambiente):
    mensal = dp.carregar_sinesp(ambiente["ativa"])
    sem_pf = mensal[mensal["abrangencia"] != "Polícia Federal"]
    candidato = _preparar(ambiente, sem_pf)
    assert candidato.validacao.status == "bloqueado" and any("ausente(s) na candidata" in e for e in candidato.validacao.erros)


def test_arquivo_de_ano_anterior_ausente_nao_e_assumido_como_inalterado(ambiente):
    mensal = dp.carregar_sinesp(ambiente["ativa"])
    pasta = _entradas(ambiente["entradas"] / "parcial", mensal, anos=range(2021, 2027))  # falta 2020
    with pytest.raises(au.ErroAtualizacao, match="NÃO são assumidos como inalterados"):
        au.preparar(ativa=ambiente["ativa"], staging_root=ambiente["staging"], entradas_sinesp=pasta)
    assert not ambiente["staging"].exists() or not any(ambiente["staging"].iterdir())  # candidata parcial removida


def test_falha_de_preparacao_nao_deixa_candidata_parcial_nem_altera_a_ativa(ambiente):
    mensal = dp.carregar_sinesp(ambiente["ativa"])
    pasta = _entradas(ambiente["entradas"] / "ruim", mensal)
    _escrever_xlsx(pasta / "bancovde-2024.xlsx", [_linha(evento="Evento inventado", ano=2024)])
    antes = _hash_pasta(ambiente["ativa"])
    with pytest.raises(au.ErroAtualizacao, match="Indicador novo"):
        au.preparar(ativa=ambiente["ativa"], staging_root=ambiente["staging"], entradas_sinesp=pasta)
    assert _hash_pasta(ambiente["ativa"]) == antes
    assert not ambiente["staging"].exists() or not any(ambiente["staging"].iterdir())


def test_relatorio_de_verificacao_e_registrado_como_consulta_sem_alterar_os_dados(ambiente):
    relatorio = {"consultado_em_utc": "2026-10-27T12:00:00Z", "por_fonte": {"sinesp_vde": {"achados": [], "publicacao": {"pagina_atualizada_em": "26/10/2026 17h07"}}}}
    candidato = _preparar(ambiente, relatorio_verificacao=relatorio)
    manifesto = json.loads((candidato.diretorio / "dados" / dp.ARQ_MANIFESTO).read_text(encoding="utf-8"))
    assert manifesto["datas"]["ultima_consulta_as_fontes_utc"] == "2026-10-27T12:00:00Z"
    assert [f["id"] for f in manifesto["fontes"]] == ["sinesp_vde"] and manifesto["fontes"][0]["publicacao"]["pagina_atualizada_em"] == "26/10/2026 17h07"
    for nome in dp.ARQUIVOS_DE_DADOS:
        assert (candidato.diretorio / "dados" / nome).read_bytes() == (ambiente["ativa"] / nome).read_bytes()


def test_candidata_so_contem_arquivos_sinesp(ambiente):
    candidato = _preparar(ambiente)
    assert sorted(p.name for p in (candidato.diretorio / "dados").iterdir()) == sorted([dp.ARQ_SINESP, dp.ARQ_SINESP_CATALOGO, dp.ARQ_MANIFESTO])


# ------------------------------------------------------------------------------------ download oficial
class _ClienteDownload:
    def __init__(self, respostas):
        self.respostas = list(respostas)
        self.chamadas = []

    def obter(self, url, cabecalhos=None, timeout=30.0):
        self.chamadas.append(url)
        item = self.respostas.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def _xlsx_bytes(tmp_path):
    caminho = tmp_path / "modelo.xlsx"
    _escrever_xlsx(caminho, [_linha()])
    return caminho.read_bytes()


def test_download_repete_apenas_queda_de_conexao(tmp_path):
    cliente = _ClienteDownload([au.fo.ErroConsulta("IncompleteRead"), au.fo.ErroConsulta("IncompleteRead"), au.fo.Resposta(200, {}, _xlsx_bytes(tmp_path))])
    caminhos = au.baixar_sinesp([2026], tmp_path / "baixados", cliente)
    assert len(cliente.chamadas) == 3 and caminhos[2026].read_bytes()[:2] == b"PK"
    cliente = _ClienteDownload([au.fo.ErroConsulta("queda")] * 3)
    with pytest.raises(au.ErroAtualizacao, match="3 tentativas"):
        au.baixar_sinesp([2026], tmp_path / "outros", cliente)
    assert len(cliente.chamadas) == 3 and not list((tmp_path / "outros").glob("*.xlsx"))


def test_download_bloqueado_403_nao_e_repetido_nem_contornado(tmp_path):
    cliente = _ClienteDownload([au.fo.Resposta(403, {}, b"Forbidden"), au.fo.Resposta(200, {}, _xlsx_bytes(tmp_path))])
    with pytest.raises(au.ErroAtualizacao, match="não contornado|não contornado"):
        au.baixar_sinesp([2026], tmp_path / "baixados", cliente)
    assert len(cliente.chamadas) == 1 and not list((tmp_path / "baixados").glob("*.xlsx"))


def test_download_que_nao_e_xlsx_e_recusado(tmp_path):
    cliente = _ClienteDownload([au.fo.Resposta(200, {}, b"<html>pagina de erro</html>")])
    with pytest.raises(au.ErroAtualizacao, match="não é um XLSX"):
        au.baixar_sinesp([2026], tmp_path / "baixados", cliente)
    assert not list((tmp_path / "baixados").glob("*.xlsx"))


# ----------------------------------------------------------------------- aprovar, versões e reverter
def _promover(amb, candidato, **extra):
    return au.aprovar(candidato.id, confirmacao=candidato.id, ativa=amb["ativa"], staging_root=amb["staging"], versoes_root=amb["versoes"], **extra)


def test_promocao_exige_confirmacao_explicita(ambiente):
    candidato = _preparar(ambiente, _com_proxima_competencia(dp.carregar_sinesp(ambiente["ativa"])))
    antes = _hash_pasta(ambiente["ativa"])
    for confirmacao in (None, "", "outro-id"):
        with pytest.raises(au.ErroAtualizacao, match="não confirmada"):
            au.aprovar(candidato.id, confirmacao=confirmacao, ativa=ambiente["ativa"], staging_root=ambiente["staging"], versoes_root=ambiente["versoes"])
    with pytest.raises(au.ErroAtualizacao, match="inexistente"):
        au.aprovar("20990101T000000Z", confirmacao="20990101T000000Z", ativa=ambiente["ativa"], staging_root=ambiente["staging"], versoes_root=ambiente["versoes"])
    assert _hash_pasta(ambiente["ativa"]) == antes and not ambiente["versoes"].exists()


def test_promocao_preserva_a_versao_anterior_e_registra_a_aprovacao(ambiente):
    manifesto_antes = dp.carregar_manifesto(ambiente["ativa"])
    hashes_antes = _hash_pasta(ambiente["ativa"])
    candidato = _preparar(ambiente, _com_proxima_competencia(dp.carregar_sinesp(ambiente["ativa"])))
    anterior = _promover(ambiente, candidato, aprovado_por="teste")
    assert anterior == manifesto_antes["versao"]
    assert _hash_pasta(ambiente["versoes"] / anterior) == hashes_antes  # versão anterior preservada, intacta
    ativo = dp.carregar_manifesto(ambiente["ativa"])
    assert ativo["versao"] == candidato.id and ativo["versao_anterior"] == anterior and ativo["situacao_validacao"]["status"] == "aprovado"
    assert ativo["aprovacao"]["aprovado_por"] == "teste" and ativo["aprovacao"]["candidata"] == candidato.id
    assert ativo["cobertura"]["sinesp"]["ultima_competencia"] == "2026-10"
    assert dp.verificar_integridade(ambiente["ativa"])["integro"].all() and len(dp.carregar_sinesp(ambiente["ativa"])) == 923
    assert sorted(p.name for p in ambiente["ativa"].iterdir()) == sorted([dp.ARQ_SINESP, dp.ARQ_SINESP_CATALOGO, dp.ARQ_MANIFESTO])
    assert not ambiente["ativa"].with_name("data_publica.antigo").exists() and not ambiente["ativa"].with_name("data_publica.novo").exists()
    assert (candidato.diretorio / "promovida.json").is_file()
    with pytest.raises(au.ErroAtualizacao, match="já foi promovida"):
        _promover(ambiente, candidato)
    assert [v["versao"] for v in au.listar_versoes(ambiente["versoes"])] == [anterior]


def test_reversao_restaura_a_versao_anterior_e_preserva_a_substituida(ambiente):
    hashes_originais = _hash_pasta(ambiente["ativa"])
    candidato = _preparar(ambiente, _com_proxima_competencia(dp.carregar_sinesp(ambiente["ativa"])))
    anterior = _promover(ambiente, candidato)
    with pytest.raises(au.ErroAtualizacao, match="não confirmada"):
        au.reverter(anterior, confirmacao=None, ativa=ambiente["ativa"], versoes_root=ambiente["versoes"])
    substituida = au.reverter(anterior, confirmacao=anterior, ativa=ambiente["ativa"], versoes_root=ambiente["versoes"])
    assert substituida == candidato.id
    assert _hash_pasta(ambiente["ativa"]) == hashes_originais and dp.carregar_manifesto(ambiente["ativa"])["versao"] == anterior
    assert (ambiente["versoes"] / candidato.id).is_dir()  # a versão revertida também fica preservada
    with pytest.raises(au.ErroAtualizacao, match="não encontrada"):
        au.reverter("inexistente", confirmacao="inexistente", ativa=ambiente["ativa"], versoes_root=ambiente["versoes"])


def test_falha_na_troca_mantem_a_versao_ativa_integra(ambiente, monkeypatch):
    candidato = _preparar(ambiente, _com_proxima_competencia(dp.carregar_sinesp(ambiente["ativa"])))
    antes = _hash_pasta(ambiente["ativa"])
    chamadas = []
    original = au._renomear

    def renomear_com_falha(origem, destino):
        chamadas.append((str(origem), str(destino)))
        if len(chamadas) == 2:  # a segunda renomeação (novo → ativa) falha
            raise OSError("falha simulada na troca")
        return original(origem, destino)

    monkeypatch.setattr(au, "_renomear", renomear_com_falha)
    with pytest.raises(OSError, match="falha simulada"):
        _promover(ambiente, candidato)
    monkeypatch.setattr(au, "_renomear", original)
    assert _hash_pasta(ambiente["ativa"]) == antes and dp.verificar_integridade(ambiente["ativa"])["integro"].all()  # sem arquivos parciais
    assert dp.carregar_manifesto(ambiente["ativa"])["cobertura"]["sinesp"]["ultima_competencia"] == "2026-09"
    assert not ambiente["ativa"].with_name("data_publica.antigo").exists() and not ambiente["ativa"].with_name("data_publica.novo").exists()
    assert not (candidato.diretorio / "promovida.json").exists()
    _promover(ambiente, candidato)  # sem a falha, a mesma candidata ainda pode ser promovida
    assert dp.carregar_manifesto(ambiente["ativa"])["versao"] == candidato.id


def test_candidata_adulterada_depois_da_preparacao_nao_e_promovida(ambiente):
    candidato = _preparar(ambiente, _com_proxima_competencia(dp.carregar_sinesp(ambiente["ativa"])))
    csv = candidato.diretorio / "dados" / dp.ARQ_SINESP
    csv.write_text(csv.read_text(encoding="utf-8").replace("2026,10,Suicídio,Estadual,vítimas,1", "2026,10,Suicídio,Estadual,vítimas,2", 1), encoding="utf-8", newline="\n")
    antes = _hash_pasta(ambiente["ativa"])
    with pytest.raises(dp.ErroDados, match="integridade"):
        _promover(ambiente, candidato)
    assert _hash_pasta(ambiente["ativa"]) == antes and not ambiente["ativa"].with_name("data_publica.novo").exists()


def test_relatorio_de_validacao_forjado_nao_libera_dados_invalidos(ambiente):
    candidato = _preparar(ambiente, _com_proxima_competencia(dp.carregar_sinesp(ambiente["ativa"])))
    csv = candidato.diretorio / "dados" / dp.ARQ_SINESP
    csv.write_text(csv.read_text(encoding="utf-8").replace("2026,10,Suicídio,Estadual,vítimas,1", "2026,10,Suicídio,Estadual,vítimas,-1", 1), encoding="utf-8", newline="\n")
    antes = _hash_pasta(ambiente["ativa"])
    with pytest.raises(dp.ErroDados):  # mesmo com status "validado" no relatório, a promoção revalida os arquivos
        _promover(ambiente, candidato)
    assert _hash_pasta(ambiente["ativa"]) == antes


def test_versao_ativa_mudou_desde_a_preparacao_exige_nova_preparacao(ambiente):
    mensal = dp.carregar_sinesp(ambiente["ativa"])
    primeira = _preparar(ambiente, _com_proxima_competencia(mensal))
    segunda = au.preparar(ativa=ambiente["ativa"], staging_root=ambiente["staging"], entradas_sinesp=_entradas(ambiente["entradas"] / "x2", mensal), agora=_agora(30))
    _promover(ambiente, primeira)
    with pytest.raises(au.ErroAtualizacao, match="versão ativa mudou"):
        _promover(ambiente, segunda)


def test_historico_registra_as_operacoes(ambiente):
    candidato = _preparar(ambiente, _com_proxima_competencia(dp.carregar_sinesp(ambiente["ativa"])))
    _promover(ambiente, candidato)
    eventos = [json.loads(l) for l in (ambiente["base"] / "historico.jsonl").read_text(encoding="utf-8").splitlines()]
    assert [e["operacao"] for e in eventos] == ["preparar", "aprovar"] and eventos[1]["id"] == candidato.id


def test_comparar_sinesp_classifica_novo_removido_alterado_e_unidade():
    base = pd.DataFrame({"ano": [2026] * 3, "mes": [1, 2, 3], "evento": ["Suicídio"] * 3, "abrangencia": ["Estadual"] * 3, "unidade": ["vítimas"] * 3,
                         "valor": pd.array([1, 2, 3], dtype="Int64")})
    cand = pd.DataFrame({"ano": [2026] * 3, "mes": [2, 3, 4], "evento": ["Suicídio"] * 3, "abrangencia": ["Estadual"] * 3, "unidade": ["vítimas", "mandados", "vítimas"],
                         "valor": pd.array([2, 3, 9], dtype="Int64")})
    resultado = au.comparar_sinesp(base, cand).set_index("mes")["situacao"].to_dict()
    assert resultado == {1: "removido", 3: "unidade_alterada", 4: "novo"}
    cand2 = cand.assign(unidade="vítimas").assign(valor=pd.array([5, 3, 9], dtype="Int64"))
    assert au.comparar_sinesp(base, cand2).set_index("mes")["situacao"].to_dict() == {1: "removido", 2: "alterado", 4: "novo"}


def test_listar_versoes_le_manifestos_antigos_e_ilegiveis(tmp_path):
    raiz = tmp_path / "versoes"
    (raiz / "v1_antigo").mkdir(parents=True)
    (raiz / "v1_antigo" / dp.ARQ_MANIFESTO).write_text(json.dumps({"gerado_em_utc": "2026-10-16T00:00:00Z", "cobertura": {"sinesp": "texto antigo"}}), encoding="utf-8")
    (raiz / "ilegivel").mkdir()
    (raiz / "ilegivel" / dp.ARQ_MANIFESTO).write_text("{nao e json", encoding="utf-8")
    (raiz / "v2").mkdir()
    (raiz / "v2" / dp.ARQ_MANIFESTO).write_text(json.dumps({"schema_manifesto": 2, "datas": {"gerado_em_utc": "2026-10-27T01:00:00Z"},
                                                           "cobertura": {"sinesp": {"ultima_competencia": "2026-08"}}}), encoding="utf-8")
    fichas = {f["versao"]: f for f in au.listar_versoes(raiz)}
    assert fichas["v1_antigo"]["schema"] == 1 and fichas["v1_antigo"]["gerada_em"] == "2026-10-16T00:00:00Z" and fichas["v1_antigo"]["ultima_competencia_sinesp"] is None
    assert fichas["ilegivel"]["gerada_em"] is None
    assert fichas["v2"]["ultima_competencia_sinesp"] == "2026-08" and fichas["v2"]["schema"] == 2
