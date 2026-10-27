"""Operação A — VERIFICAR: identifica possíveis novas publicações oficiais do Sinesp/MJSP (somente leitura).

Este módulo NÃO baixa arquivos de dados, NÃO executa ETL e NÃO altera nenhum arquivo usado pelo dashboard.
Ele só consulta metadados e registra evidências, com classificação prudente:

* ``nenhuma_novidade_identificada``
* ``possivel_nova_competencia``
* ``possivel_revisao_de_competencia_historica``
* ``alteracao_de_esquema_ou_fonte``
* ``falha_de_consulta``

Princípios:

* Mudança na página (data "Atualizado em") ou no tamanho de um arquivo é **indício**, nunca prova de que
  valores mudaram. Só a operação B (preparar), com o conteúdo do arquivo, confirma nova competência ou revisão.
* Nenhuma competência é inventada a partir de datas do site.
* Preferem-se APIs documentadas (CKAN do catálogo; ``Range`` HTTP para obter o tamanho). Onde não há consulta automática confiável (datas dos arquivos do Sinesp no
  gov.br), a limitação é registrada e a verificação manual assistida é recomendada.
* Bloqueios de acesso (HTTP 403 etc.) NÃO são contornados: viram ``falha_de_consulta``. O cliente se
  identifica honestamente (User-Agent do projeto).
"""

from __future__ import annotations

import http.client
import json
import re
import urllib.error
import urllib.request
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Protocol

from scripts import versionamento_dados as vv

USER_AGENT = "analise-seguranca-publica-joinville/1.0 (projeto academico SENAI/LAB365; verificacao de metadados)"
URL_SINESP_PAGINA = vv.FONTES_BASE[0]["url"]
URL_SINESP_ARQUIVO = ("https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/"
                      "bancovde-{ano}.xlsx/@@download/file")
URL_CKAN_MJ = "https://dados.mj.gov.br/api/3/action/package_show?id=sistema-nacional-de-estatisticas-de-seguranca-publica"
ID_SINESP = "sinesp_vde"


class Classificacao(str, Enum):
    NENHUMA_NOVIDADE = "nenhuma_novidade_identificada"
    NOVA_COMPETENCIA = "possivel_nova_competencia"
    POSSIVEL_REVISAO = "possivel_revisao_de_competencia_historica"
    ALTERACAO_ESQUEMA_OU_FONTE = "alteracao_de_esquema_ou_fonte"
    FALHA_CONSULTA = "falha_de_consulta"


class ErroConsulta(Exception):
    """Falha de rede (DNS, tempo esgotado, conexão)."""


class ErroReferencia(ValueError):
    """O manifesto local não tem a referência necessária para comparar."""


@dataclass
class Resposta:
    status: int
    cabecalhos: dict[str, str]
    corpo: bytes = b""

    def texto(self) -> str:
        return self.corpo.decode("utf-8", errors="replace")


class Cliente(Protocol):
    def obter(self, url: str, cabecalhos: dict[str, str] | None = None, timeout: float = 30.0) -> Resposta: ...


class ClienteHTTP:
    """Cliente padrão (``urllib``), com identificação honesta e sem tentativa de contornar bloqueios."""

    def obter(self, url: str, cabecalhos: dict[str, str] | None = None, timeout: float = 30.0) -> Resposta:
        pedido = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(cabecalhos or {})}, method="GET")
        try:
            with urllib.request.urlopen(pedido, timeout=timeout) as resposta:  # noqa: S310 — URLs fixas e https
                return Resposta(resposta.status, {k.lower(): v for k, v in resposta.headers.items()}, resposta.read())
        except urllib.error.HTTPError as erro:
            return Resposta(erro.code, {k.lower(): v for k, v in (erro.headers or {}).items()}, erro.read() if hasattr(erro, "read") else b"")
        except (urllib.error.URLError, TimeoutError, OSError, http.client.HTTPException) as erro:  # inclui IncompleteRead (conexão interrompida)
            raise ErroConsulta(f"{type(erro).__name__}: {erro}") from erro


@dataclass
class Achado:
    fonte: str
    recurso: str
    url: str
    identificador: str
    consultado_em_utc: str
    classificacao: Classificacao
    detalhe: str
    evidencia: dict = field(default_factory=dict)
    requer_verificacao_manual: bool = False

    def para_dict(self) -> dict:
        dados = asdict(self)
        dados["classificacao"] = self.classificacao.value
        return dados


@dataclass
class Relatorio:
    consultado_em_utc: str
    achados: list[Achado]
    manifesto_versao: str | None

    def resumo(self) -> dict[str, int]:
        contagem = {c.value: 0 for c in Classificacao}
        for achado in self.achados:
            contagem[achado.classificacao.value] += 1
        return contagem

    def acao_recomendada(self) -> str:
        r = self.resumo()
        if r[Classificacao.ALTERACAO_ESQUEMA_OU_FONTE.value]:
            return "Há alteração de esquema, formato ou fonte: auditar manualmente antes de qualquer incorporação (não automatizável)."
        if r[Classificacao.POSSIVEL_REVISAO.value] or r[Classificacao.NOVA_COMPETENCIA.value]:
            return "Indícios de nova competência ou de revisão: baixar os originais oficiais e executar a operação PREPARAR; nada foi alterado."
        if r[Classificacao.FALHA_CONSULTA.value]:
            return "Alguma consulta falhou: repetir mais tarde ou usar a verificação manual assistida; nada foi alterado."
        if any(a.requer_verificacao_manual for a in self.achados):
            return "Nenhuma novidade comprovada, mas há indícios de atualização de página: conferir manualmente."
        return "Nenhuma novidade identificada nas consultas realizadas (limitada ao que cada fonte expõe)."

    def para_dict(self) -> dict:
        por_fonte: dict[str, dict] = {}
        for achado in self.achados:
            ficha = por_fonte.setdefault(achado.fonte, {"achados": [], "publicacao": None})
            ficha["achados"].append({"recurso": achado.recurso, "classificacao": achado.classificacao.value, "detalhe": achado.detalhe,
                                     "requer_verificacao_manual": achado.requer_verificacao_manual})
            if achado.recurso == "pagina_sinesp_vde" and achado.evidencia.get("pagina_atualizada_em"):
                ficha["publicacao"] = {"pagina_publicada_em": achado.evidencia.get("pagina_publicada_em"),
                                       "pagina_atualizada_em": achado.evidencia["pagina_atualizada_em"],
                                       "observacao": "Datas informadas pela página; não provam alteração de valores."}
        return {"consultado_em_utc": self.consultado_em_utc, "manifesto_versao_comparada": self.manifesto_versao,
                "resumo": self.resumo(), "acao_recomendada": self.acao_recomendada(),
                "limitacoes": LIMITACOES, "por_fonte": por_fonte, "achados": [a.para_dict() for a in self.achados]}


LIMITACOES = [
    "Sinesp/gov.br: não há API pública documentada (a API REST do portal responde 401) e o método HEAD é bloqueado (403). O tamanho do arquivo é obtido "
    "por GET com 'Range: bytes=0-0'; não há data de modificação dos arquivos. A data 'Atualizado em' é da página, não de cada arquivo.",
    "Tamanho igual não prova conteúdo idêntico, e tamanho diferente não prova mudança de valores: apenas a operação PREPARAR, com o conteúdo, confirma.",
    "dados.mj.gov.br (CKAN do MJSP) não resolvia (NXDOMAIN) nas consultas de 27/10/2026; sem catálogo, a licença do MJSP não é monitorada.",
]


# --------------------------------------------------------------------------------------- utilidades
def _agora_texto(agora: datetime) -> str:
    return agora.strftime("%Y-%m-%dT%H:%M:%SZ")


def _tamanho_remoto(cliente: Cliente, url: str) -> tuple[int | None, Resposta]:
    """Tamanho total via GET 'Range: bytes=0-0' (sem baixar o arquivo)."""
    resposta = cliente.obter(url, {"Range": "bytes=0-0"}, 60.0)
    intervalo = resposta.cabecalhos.get("content-range", "")
    encontrado = re.fullmatch(r"bytes\s+\d+-\d+/(\d+)", intervalo.strip())
    if resposta.status == 206 and encontrado:
        return int(encontrado.group(1)), resposta
    if resposta.status == 200 and resposta.cabecalhos.get("content-length", "").isdigit():
        return int(resposta.cabecalhos["content-length"]), resposta
    return None, resposta


def _referencia(manifesto: dict, chave: str) -> dict:
    origem = manifesto.get("origem_dos_dados", {})
    if chave not in origem or not origem[chave]:
        raise ErroReferencia(f"O manifesto não registra '{chave}'; gere o manifesto atual (scripts.gerar_dados_dashboard) antes de verificar.")
    return origem[chave]


def _falha(fonte, recurso, url, identificador, instante, erro) -> Achado:
    return Achado(fonte, recurso, url, identificador, instante, Classificacao.FALHA_CONSULTA, f"Consulta não concluída: {erro}",
                  {"erro": str(erro)}, requer_verificacao_manual=True)


def _data_pagina(texto: str, rotulo_regex: str) -> str | None:
    encontrado = re.search(rotulo_regex, texto)
    return f"{encontrado.group(1)} {encontrado.group(2)}h{encontrado.group(3)}" if encontrado else None


# ------------------------------------------------------------------------------------------ Sinesp
def verificar_sinesp_pagina(cliente: Cliente, manifesto: dict, instante: str) -> list[Achado]:
    """Página da base VDE: datas informadas, links dos arquivos anuais e licença do rodapé (evidências)."""
    recurso, url = "pagina_sinesp_vde", URL_SINESP_PAGINA
    try:
        resposta = cliente.obter(url, None, 60.0)
    except ErroConsulta as erro:
        return [_falha(ID_SINESP, recurso, url, "pagina", instante, erro)]
    if resposta.status != 200:
        return [_falha(ID_SINESP, recurso, url, "pagina", instante, f"HTTP {resposta.status}")]
    html = resposta.texto()
    texto = re.sub(r"\s+", " ", re.sub(r"<!--.*?-->", " ", re.sub(r"<[^>]+>", " ", html), flags=re.S))
    atualizado = _data_pagina(texto, r"Atualizado em\s*(\d{2}/\d{2}/\d{4})\s*(\d{2})h(\d{2})")
    publicado = _data_pagina(texto, r"(\d{2}/\d{2}/\d{4})\s*(\d{2})h(\d{2})\s*Atualizado em")
    anos_remotos = sorted({int(a) for a in re.findall(r"bancovde-(\d{4})\.xlsx", html)})
    licenca = re.search(r'rel="license"\s+href="([^"]+)"', html) or re.search(r'href="([^"]+)"[^>]*rel="license"', html)
    evidencia = {"pagina_atualizada_em": atualizado, "pagina_publicada_em": publicado, "anos_listados": anos_remotos,
                 "licenca_do_rodape": licenca.group(1) if licenca else None}
    if not atualizado or not anos_remotos:
        return [Achado(ID_SINESP, recurso, url, "pagina", instante, Classificacao.ALTERACAO_ESQUEMA_OU_FONTE,
                       "Estrutura da página não reconhecida (datas ou links dos arquivos anuais ausentes): a fonte pode ter mudado.", evidencia, True)]
    cobertos = {int(a) for a in _referencia(manifesto, "sinesp_xlsx_bytes")}
    registrada = next((f.get("publicacao", {}) or {} for f in manifesto.get("fontes", []) if f.get("id") == ID_SINESP), {}).get("pagina_atualizada_em")
    # Anos anteriores ao primeiro/fora do escopo (p.ex. 2015–2019) nunca foram incorporados e não são "novidade":
    # só contam anos POSTERIORES ao último já coberto.
    novos = sorted(a for a in set(anos_remotos) - cobertos if a > max(cobertos))
    if novos:
        return [Achado(ID_SINESP, recurso, url, "pagina", instante, Classificacao.NOVA_COMPETENCIA,
                       f"A página lista arquivo(s) de ano(s) ainda não incorporado(s): {novos}. Confirmar no PREPARAR.", evidencia, True)]
    mudou = bool(registrada) and registrada != atualizado
    detalhe = (f"Página 'Atualizado em {atualizado}' (registrado anteriormente: {registrada or 'não registrado'}). "
               "A data da página, isoladamente, NÃO prova alteração de valores; veja a verificação dos arquivos.")
    return [Achado(ID_SINESP, recurso, url, "pagina", instante, Classificacao.NENHUMA_NOVIDADE, detalhe, evidencia, requer_verificacao_manual=mudou or not registrada)]


def verificar_sinesp_arquivos(cliente: Cliente, manifesto: dict, instante: str) -> list[Achado]:
    """Tamanho de cada arquivo anual (e do ano seguinte ao último coberto) comparado ao dos originais auditados."""
    tamanhos = {int(a): int(b) for a, b in _referencia(manifesto, "sinesp_xlsx_bytes").items()}
    ultimo = max(tamanhos)
    achados = []
    for ano in list(sorted(tamanhos)) + [ultimo + 1]:
        url = URL_SINESP_ARQUIVO.format(ano=ano)
        identificador = f"bancovde-{ano}.xlsx"
        try:
            remoto, resposta = _tamanho_remoto(cliente, url)
        except ErroConsulta as erro:
            achados.append(_falha(ID_SINESP, "arquivo_sinesp", url, identificador, instante, erro))
            continue
        evidencia = {"http_status": resposta.status, "bytes_remoto": remoto, "bytes_local_auditado": tamanhos.get(ano)}
        if ano not in tamanhos:  # ano seguinte
            if resposta.status in (200, 206):
                achados.append(Achado(ID_SINESP, "arquivo_sinesp", url, identificador, instante, Classificacao.NOVA_COMPETENCIA,
                                      f"Existe arquivo de {ano}, ainda não incorporado. Confirmar no PREPARAR.", evidencia, True))
            elif resposta.status == 404:
                achados.append(Achado(ID_SINESP, "arquivo_sinesp", url, identificador, instante, Classificacao.NENHUMA_NOVIDADE,
                                      f"Arquivo de {ano} ainda não publicado (HTTP 404).", evidencia))
            else:
                achados.append(_falha(ID_SINESP, "arquivo_sinesp", url, identificador, instante, f"HTTP {resposta.status} (acesso não contornado)"))
            continue
        if remoto is None:
            achados.append(_falha(ID_SINESP, "arquivo_sinesp", url, identificador, instante, f"HTTP {resposta.status}; tamanho indisponível (acesso não contornado)"))
        elif remoto == tamanhos[ano]:
            achados.append(Achado(ID_SINESP, "arquivo_sinesp", url, identificador, instante, Classificacao.NENHUMA_NOVIDADE,
                                  "Tamanho igual ao do original auditado (não prova conteúdo idêntico).", evidencia))
        elif ano == ultimo and remoto > tamanhos[ano]:
            achados.append(Achado(ID_SINESP, "arquivo_sinesp", url, identificador, instante, Classificacao.NOVA_COMPETENCIA,
                                  f"Arquivo do último ano coberto ({ano}) maior que o auditado ({remoto} > {tamanhos[ano]} bytes): indício de nova(s) competência(s) "
                                  "ou de revisão; confirmar no PREPARAR.", evidencia, True))
        else:
            achados.append(Achado(ID_SINESP, "arquivo_sinesp", url, identificador, instante, Classificacao.POSSIVEL_REVISAO,
                                  f"Tamanho diferente do auditado ({remoto} ≠ {tamanhos[ano]} bytes) em arquivo de ano já coberto: indício de revisão; confirmar no PREPARAR.",
                                  evidencia, True))
    return achados


# ----------------------------------------------------------------------------------------- catálogos
def verificar_catalogo_ckan(cliente: Cliente, url: str, fonte: str, recurso: str, licenca_esperada: str | None, instante: str) -> list[Achado]:
    try:
        resposta = cliente.obter(url, {"Accept": "application/json"}, 30.0)
    except ErroConsulta as erro:
        return [_falha(fonte, recurso, url, "catalogo_ckan", instante, erro)]
    if resposta.status != 200:
        return [_falha(fonte, recurso, url, "catalogo_ckan", instante, f"HTTP {resposta.status}")]
    try:
        resultado = json.loads(resposta.texto())["result"]
        evidencia = {"license_id": resultado.get("license_id"), "license_title": resultado.get("license_title"),
                     "metadata_modified": resultado.get("metadata_modified"),
                     "recursos": [{"id": r.get("id"), "formato": r.get("format"), "url": r.get("url"), "last_modified": r.get("last_modified")} for r in resultado.get("resources", [])]}
    except (ValueError, KeyError, TypeError) as erro:
        return [Achado(fonte, recurso, url, "catalogo_ckan", instante, Classificacao.ALTERACAO_ESQUEMA_OU_FONTE,
                       f"Resposta do catálogo fora do formato CKAN esperado ({erro}).", {}, True)]
    if licenca_esperada and evidencia["license_id"] != licenca_esperada:
        return [Achado(fonte, recurso, url, "catalogo_ckan", instante, Classificacao.ALTERACAO_ESQUEMA_OU_FONTE,
                       f"Licença do catálogo mudou: esperada '{licenca_esperada}', encontrada '{evidencia['license_id']}'. Rever as condições de reutilização.", evidencia, True)]
    return [Achado(fonte, recurso, url, "catalogo_ckan", instante, Classificacao.NENHUMA_NOVIDADE,
                   f"Catálogo consultado (licença '{evidencia['license_id']}'; metadados modificados em {evidencia['metadata_modified']}). Data dos metadados do catálogo não prova nova competência.",
                   evidencia)]


# ---------------------------------------------------------------------------------------- orquestração
def verificar_fontes(manifesto: dict, cliente: Cliente | None = None, agora: datetime | None = None) -> Relatorio:
    """Executa todas as verificações. Nunca lança por falha de rede e nunca altera dados."""
    cliente = cliente or ClienteHTTP()
    instante = _agora_texto(agora or vv.agora_utc())
    achados: list[Achado] = []
    achados += verificar_sinesp_pagina(cliente, manifesto, instante)
    achados += verificar_sinesp_arquivos(cliente, manifesto, instante)
    achados += verificar_catalogo_ckan(cliente, URL_CKAN_MJ, ID_SINESP, "catalogo_mj", None, instante)
    return Relatorio(instante, achados, manifesto.get("versao"))


def salvar_relatorio(relatorio: Relatorio, diretorio: Path) -> Path:
    diretorio.mkdir(parents=True, exist_ok=True)
    caminho = diretorio / f"verificacao_{relatorio.consultado_em_utc.replace(':', '').replace('-', '')}.json"
    caminho.write_text(json.dumps(relatorio.para_dict(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return caminho
