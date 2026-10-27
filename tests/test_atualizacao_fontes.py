"""Testes da operação A (verificar fontes oficiais) com cliente HTTP falso: nenhuma rede, nenhum dado real alterado."""

import hashlib
import json
from datetime import datetime, timezone

import pytest

from dashboard import dados_publicos as dp
from scripts import fontes_oficiais as fo

AGORA = datetime(2026, 10, 27, 12, 0, 0, tzinfo=timezone.utc)


def _pasta_hash(diretorio):
    return {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(diretorio.iterdir()) if p.is_file()}


class ClienteFalso:
    """Responde por URL (prefixo). Registra todas as chamadas para provar que não há tentativa de contornar bloqueios."""

    def __init__(self, respostas):
        self.respostas = respostas
        self.chamadas = []

    def obter(self, url, cabecalhos=None, timeout=30.0):
        self.chamadas.append((url, dict(cabecalhos or {})))
        for prefixo, valor in self.respostas.items():
            if url.startswith(prefixo):
                if isinstance(valor, Exception):
                    raise valor
                return valor(url) if callable(valor) else valor
        return fo.Resposta(404, {})


def _pagina(atualizado="26/10/2026 17h07", anos=range(2015, 2027), licenca=True):
    links = " ".join(f'<a href="x/bancovde-{a}.xlsx/@@download/file">{a}</a>' for a in anos)
    rodape = '<a rel="license" href="https://creativecommons.org/licenses/by-nd/3.0/deed.pt_BR">CC</a>' if licenca else ""
    data, hora = atualizado.split()
    return fo.Resposta(200, {}, f"<html><span>Publicado em <!-- x --> 27/12/2023 10h57 Atualizado em {data} {hora.replace('h', 'h')}</span>{links}{rodape}</html>".encode())


def _faixa(total):
    return fo.Resposta(206, {"content-range": f"bytes 0-0/{total}"}, b"x")


def _manifesto():
    return dp.carregar_manifesto()


def _tamanhos_sinesp(manifesto, **mudancas):
    base = {int(a): int(b) for a, b in manifesto["origem_dos_dados"]["sinesp_xlsx_bytes"].items()}
    base.update({int(k[1:]): v for k, v in mudancas.items()})
    return base


def _cliente(manifesto, *, tamanhos=None, pagina=None, ckan_mj=None, ckan_sc=None, midia=None, proximo_ano=404):
    tamanhos = tamanhos or _tamanhos_sinesp(manifesto)
    respostas = {fo.URL_SINESP_PAGINA: pagina or _pagina()}
    for ano, total in tamanhos.items():
        respostas[fo.URL_SINESP_ARQUIVO.format(ano=ano)] = _faixa(total)
    proximo = max(tamanhos) + 1
    respostas[fo.URL_SINESP_ARQUIVO.format(ano=proximo)] = fo.Resposta(proximo_ano, {"content-range": "bytes 0-0/10"} if proximo_ano == 206 else {})
    respostas[fo.URL_CKAN_MJ] = ckan_mj or fo.Resposta(200, {}, json.dumps({"result": {"license_id": "cc-by", "license_title": "Creative Commons Atribuição",
                                                                                      "metadata_modified": "2026-01-01", "resources": []}}).encode())
    respostas[fo.URL_CKAN_SC] = ckan_sc or fo.Resposta(200, {}, json.dumps({"result": {"license_id": "other-open", "license_title": "Outra (Aberta)",
                                                                                      "metadata_modified": "2026-03-20", "resources": [{"id": "r", "format": "HTML"}]}}).encode())
    pdfs = {n.split("_", 2)[2]: b for n, b in manifesto["origem_dos_dados"]["ssp_pdf_bytes"].items()}
    itens = [{"source_url": f"https://ssp.sc.gov.br/wp-content/uploads/2025/06/{nome}", "mime_type": "application/pdf", "date": "2025-06-13T17:59:04", "modified": "2025-06-13T17:59:04"} for nome in pdfs]
    respostas[fo.URL_SSP_MIDIA] = midia or fo.Resposta(200, {}, json.dumps(itens).encode())
    for nome, total in pdfs.items():
        respostas[f"https://ssp.sc.gov.br/wp-content/uploads/2025/06/{nome}"] = _faixa(total)
    return ClienteFalso(respostas), pdfs


def _por_recurso(relatorio):
    saida = {}
    for a in relatorio.achados:
        saida.setdefault(a.recurso, []).append(a)
    return saida


def _classificacoes(relatorio, recurso):
    return {a.classificacao for a in _por_recurso(relatorio)[recurso]}


# ----------------------------------------------------------------------------------------- cenários
def test_sem_novidade_e_pagina_atualizada_sozinha_nao_prova_alteracao():
    manifesto = _manifesto()
    cliente, _ = _cliente(manifesto)
    relatorio = fo.verificar_fontes(manifesto, cliente, AGORA)
    assert {a.classificacao for a in relatorio.achados} == {fo.Classificacao.NENHUMA_NOVIDADE}
    pagina = _por_recurso(relatorio)["pagina_sinesp_vde"][0]
    assert pagina.evidencia["pagina_atualizada_em"] == "26/10/2026 17h07" and pagina.evidencia["pagina_publicada_em"] == "27/12/2023 10h57"
    registrada = next(f for f in manifesto["fontes"] if f["id"] == fo.ID_SINESP)["publicacao"].get("pagina_atualizada_em")
    assert pagina.requer_verificacao_manual == (registrada != "26/10/2026 17h07")  # data igual à registrada: sem alerta; diferente/ausente: conferência manual
    # data de página posterior à registrada: continua "nenhuma novidade" (não prova nada), mas pede conferência manual
    posterior = fo.verificar_fontes(manifesto, _cliente(manifesto, pagina=_pagina(atualizado="28/10/2026 09h00"))[0], AGORA)
    achado = _por_recurso(posterior)["pagina_sinesp_vde"][0]
    assert achado.classificacao == fo.Classificacao.NENHUMA_NOVIDADE and achado.requer_verificacao_manual and "NÃO prova" in achado.detalhe
    sem_registro = json.loads(json.dumps(manifesto))
    next(f for f in sem_registro["fontes"] if f["id"] == fo.ID_SINESP)["publicacao"] = {}
    assert _por_recurso(fo.verificar_fontes(sem_registro, _cliente(manifesto)[0], AGORA))["pagina_sinesp_vde"][0].requer_verificacao_manual
    assert fo.Classificacao.NOVA_COMPETENCIA not in {a.classificacao for a in relatorio.achados}  # nenhuma competência inventada pela data
    assert relatorio.resumo()[fo.Classificacao.NENHUMA_NOVIDADE.value] == len(relatorio.achados)


def test_deteccao_de_nova_competencia_no_ultimo_ano():
    manifesto = _manifesto()
    tamanhos = _tamanhos_sinesp(manifesto)
    cliente, _ = _cliente(manifesto, tamanhos={**tamanhos, 2026: tamanhos[2026] + 2_000_000})
    relatorio = fo.verificar_fontes(manifesto, cliente, AGORA)
    arquivo_2026 = next(a for a in relatorio.achados if a.identificador == "bancovde-2026.xlsx")
    assert arquivo_2026.classificacao == fo.Classificacao.NOVA_COMPETENCIA and arquivo_2026.requer_verificacao_manual
    assert "indício" in arquivo_2026.detalhe and "PREPARAR" in arquivo_2026.detalhe
    assert "PREPARAR" in relatorio.acao_recomendada()


def test_deteccao_de_ano_novo_e_de_revisao_historica():
    manifesto = _manifesto()
    tamanhos = _tamanhos_sinesp(manifesto)
    cliente, _ = _cliente(manifesto, tamanhos={**tamanhos, 2024: tamanhos[2024] + 12}, proximo_ano=206)
    relatorio = fo.verificar_fontes(manifesto, cliente, AGORA)
    por_arquivo = {a.identificador: a.classificacao for a in relatorio.achados if a.recurso == "arquivo_sinesp"}
    assert por_arquivo["bancovde-2024.xlsx"] == fo.Classificacao.POSSIVEL_REVISAO
    assert por_arquivo["bancovde-2027.xlsx"] == fo.Classificacao.NOVA_COMPETENCIA
    assert por_arquivo["bancovde-2025.xlsx"] == fo.Classificacao.NENHUMA_NOVIDADE
    assert fo.Classificacao.POSSIVEL_REVISAO.value in relatorio.resumo()


def test_arquivo_menor_no_ultimo_ano_e_revisao_e_nao_nova_competencia():
    manifesto = _manifesto()
    tamanhos = _tamanhos_sinesp(manifesto)
    cliente, _ = _cliente(manifesto, tamanhos={**tamanhos, 2026: tamanhos[2026] - 5})
    relatorio = fo.verificar_fontes(manifesto, cliente, AGORA)
    assert next(a for a in relatorio.achados if a.identificador == "bancovde-2026.xlsx").classificacao == fo.Classificacao.POSSIVEL_REVISAO


def test_pagina_com_anos_antigos_fora_do_escopo_nao_e_novidade():
    manifesto = _manifesto()
    cliente, _ = _cliente(manifesto, pagina=_pagina(anos=range(2010, 2027)))  # 2010–2019 nunca fizeram parte do escopo
    pagina = _por_recurso(fo.verificar_fontes(manifesto, cliente, AGORA))["pagina_sinesp_vde"][0]
    assert pagina.classificacao == fo.Classificacao.NENHUMA_NOVIDADE


def test_pagina_com_ano_posterior_listado_indica_nova_competencia():
    manifesto = _manifesto()
    cliente, _ = _cliente(manifesto, pagina=_pagina(anos=range(2015, 2028)))
    assert _classificacoes(fo.verificar_fontes(manifesto, cliente, AGORA), "pagina_sinesp_vde") == {fo.Classificacao.NOVA_COMPETENCIA}


def test_alteracao_de_esquema_da_pagina():
    manifesto = _manifesto()
    cliente, _ = _cliente(manifesto, pagina=fo.Resposta(200, {}, b"<html>pagina reformulada sem datas nem links</html>"))
    pagina = _por_recurso(fo.verificar_fontes(manifesto, cliente, AGORA))["pagina_sinesp_vde"][0]
    assert pagina.classificacao == fo.Classificacao.ALTERACAO_ESQUEMA_OU_FONTE and pagina.requer_verificacao_manual


def test_bloqueio_403_e_falha_de_rede_viram_falha_sem_tentativa_de_contornar():
    manifesto = _manifesto()
    cliente, _ = _cliente(manifesto)
    cliente.respostas[fo.URL_SINESP_ARQUIVO.format(ano=2025)] = fo.Resposta(403, {}, b"Forbidden")
    cliente.respostas[fo.URL_CKAN_MJ] = fo.ErroConsulta("URLError: getaddrinfo failed")
    relatorio = fo.verificar_fontes(manifesto, cliente, AGORA)
    assert next(a for a in relatorio.achados if a.identificador == "bancovde-2025.xlsx").classificacao == fo.Classificacao.FALHA_CONSULTA
    assert _classificacoes(relatorio, "catalogo_mj") == {fo.Classificacao.FALHA_CONSULTA}
    assert "não contornado" in next(a for a in relatorio.achados if a.identificador == "bancovde-2025.xlsx").detalhe
    # O arquivo bloqueado (403) foi pedido uma única vez: nada de nova tentativa com outra identidade ou cabeçalho.
    urls = [u for u, _ in cliente.chamadas]
    assert urls.count(fo.URL_SINESP_ARQUIVO.format(ano=2025)) == 1 and urls.count(fo.URL_CKAN_MJ) == 1


def test_cliente_padrao_se_identifica_honestamente():
    assert "analise-seguranca-publica-joinville" in fo.USER_AGENT and "Mozilla" not in fo.USER_AGENT


def test_licenca_do_catalogo_alterada_exige_revisao_das_condicoes():
    manifesto = _manifesto()
    mudou = fo.Resposta(200, {}, json.dumps({"result": {"license_id": "cc-by-nd", "license_title": "x", "metadata_modified": "2026-10-01", "resources": []}}).encode())
    cliente, _ = _cliente(manifesto, ckan_sc=mudou)
    achado = _por_recurso(fo.verificar_fontes(manifesto, cliente, AGORA))["catalogo_sc"][0]
    assert achado.classificacao == fo.Classificacao.ALTERACAO_ESQUEMA_OU_FONTE and "Licença do catálogo mudou" in achado.detalhe


def test_catalogo_com_formato_inesperado():
    manifesto = _manifesto()
    cliente, _ = _cliente(manifesto, ckan_sc=fo.Resposta(200, {}, b"<html>nao e json</html>"))
    assert _classificacoes(fo.verificar_fontes(manifesto, cliente, AGORA), "catalogo_sc") == {fo.Classificacao.ALTERACAO_ESQUEMA_OU_FONTE}


def _midia(pdfs, extras=(), omitir=()):
    itens = [{"source_url": f"https://ssp.sc.gov.br/wp-content/uploads/2025/06/{n}", "mime_type": "application/pdf", "date": "2025-06-13T17:59:04", "modified": "2025-06-13T17:59:04"}
             for n in pdfs if n not in omitir]
    itens += list(extras)
    return fo.Resposta(200, {}, json.dumps(itens).encode())


def test_ssp_novo_relatorio_pdf_xlsx_revisao_e_remocao():
    manifesto = _manifesto()
    _, pdfs = _cliente(manifesto)
    extras = [
        {"source_url": "https://ssp.sc.gov.br/wp-content/uploads/2026/10/VIOLENCIA-DOMESTICA-SC-1o-SEMESTRE-2025.xlsx",
         "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", "date": "2026-10-19T19:02:34", "modified": "2026-10-19T19:02:34"},
        {"source_url": "https://ssp.sc.gov.br/wp-content/uploads/2026/10/VIOLENCIA-DOMESTICA-2025-SC.pdf", "mime_type": "application/pdf", "date": "2026-10-19", "modified": "2026-10-19"},
    ]
    nome_removido, nome_revisado = sorted(pdfs)[0], sorted(pdfs)[1]
    cliente, _ = _cliente(manifesto, midia=_midia(pdfs, extras, omitir=[nome_removido]))
    cliente.respostas[f"https://ssp.sc.gov.br/wp-content/uploads/2025/06/{nome_revisado}"] = _faixa(pdfs[nome_revisado] + 100)
    cliente.respostas["https://ssp.sc.gov.br/wp-content/uploads/2026/10/VIOLENCIA-DOMESTICA-2025-SC.pdf"] = _faixa(1234)
    relatorio = fo.verificar_fontes(manifesto, cliente, AGORA)
    por_id = {a.identificador: a for a in relatorio.achados if a.fonte == fo.ID_SSP}
    assert por_id["VIOLENCIA-DOMESTICA-SC-1o-SEMESTRE-2025.xlsx"].classificacao == fo.Classificacao.ALTERACAO_ESQUEMA_OU_FONTE
    assert "NÃO incorporado automaticamente" in por_id["VIOLENCIA-DOMESTICA-SC-1o-SEMESTRE-2025.xlsx"].detalhe
    assert por_id["VIOLENCIA-DOMESTICA-2025-SC.pdf"].classificacao == fo.Classificacao.NOVA_COMPETENCIA
    assert por_id[nome_revisado].classificacao == fo.Classificacao.POSSIVEL_REVISAO
    assert por_id[nome_removido].classificacao == fo.Classificacao.ALTERACAO_ESQUEMA_OU_FONTE
    assert "auditoria" in por_id["VIOLENCIA-DOMESTICA-2025-SC.pdf"].detalhe


def test_ssp_resposta_de_midia_malformada():
    manifesto = _manifesto()
    cliente, _ = _cliente(manifesto, midia=fo.Resposta(200, {}, b'{"nao": "e lista"}'))
    assert _classificacoes(fo.verificar_fontes(manifesto, cliente, AGORA), "midia_ssp_violencia_domestica") == {fo.Classificacao.ALTERACAO_ESQUEMA_OU_FONTE}


def test_referencia_ausente_no_manifesto_e_erro_explicito():
    manifesto = _manifesto()
    sem_bytes = json.loads(json.dumps(manifesto))
    del sem_bytes["origem_dos_dados"]["sinesp_xlsx_bytes"]
    cliente, _ = _cliente(manifesto)
    with pytest.raises(fo.ErroReferencia, match="sinesp_xlsx_bytes"):
        fo.verificar_fontes(sem_bytes, cliente, AGORA)


def test_verificacao_nao_altera_os_dados_e_so_grava_o_relatorio_no_diretorio_indicado(tmp_path):
    manifesto = _manifesto()
    antes = _pasta_hash(dp.DIRETORIO_DADOS)
    cliente, _ = _cliente(manifesto)
    relatorio = fo.verificar_fontes(manifesto, cliente, AGORA)
    caminho = fo.salvar_relatorio(relatorio, tmp_path / "verificacoes")
    assert _pasta_hash(dp.DIRETORIO_DADOS) == antes
    conteudo = json.loads(caminho.read_text(encoding="utf-8"))
    assert conteudo["consultado_em_utc"] == "2026-10-27T12:00:00Z" and conteudo["manifesto_versao_comparada"] == manifesto["versao"]
    assert conteudo["limitacoes"] and conteudo["por_fonte"][fo.ID_SINESP]["publicacao"]["pagina_atualizada_em"] == "26/10/2026 17h07"
    assert all(set(a) >= {"fonte", "recurso", "url", "identificador", "consultado_em_utc", "classificacao", "evidencia"} for a in conteudo["achados"])


def test_falha_total_de_consulta_nao_levanta_nem_altera_dados():
    manifesto = _manifesto()
    antes = _pasta_hash(dp.DIRETORIO_DADOS)
    cliente = ClienteFalso({"https://": fo.ErroConsulta("sem rede")})
    relatorio = fo.verificar_fontes(manifesto, cliente, AGORA)
    assert {a.classificacao for a in relatorio.achados} == {fo.Classificacao.FALHA_CONSULTA}
    assert "Alguma consulta falhou" in relatorio.acao_recomendada()
    assert _pasta_hash(dp.DIRETORIO_DADOS) == antes
