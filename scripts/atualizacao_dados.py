"""Atualização controlada dos dados mínimos do dashboard, em três operações separadas.

A — VERIFICAR   consulta as fontes e relata possíveis novidades (``scripts.fontes_oficiais``); NÃO altera dados.
B — PREPARAR    monta uma versão CANDIDATA isolada em ``atualizacao/staging/<id>/`` a partir dos originais oficiais
                baixados/colocados manualmente, executa o ETL e valida; NÃO altera os dados ativos.
C — APROVAR     promove a candidata à versão ativa somente com aprovação explícita (``--confirmo <id>``), depois de
                preservar a versão anterior e com troca segura de diretório (com reversão automática em caso de falha).
    REVERTER    restaura uma versão anterior preservada, também com confirmação explícita.

Nada aqui desativa validações. Uma atualização inválida (erros de validação) jamais pode ser promovida; revisões de
valores históricos exigem ``--aceitar-revisoes``. Os dados do SSP/SC (violência doméstica) não são recalculados: novos
relatórios têm formato/definições não auditados e exigem auditoria manual antes de qualquer incorporação.

Uso (a partir da raiz do projeto)::

    python -m scripts.atualizacao_dados verificar
    python -m scripts.atualizacao_dados preparar --entradas-sinesp dados/brutos/sinesp
    python -m scripts.atualizacao_dados comparar <id>
    python -m scripts.atualizacao_dados aprovar <id> --confirmo <id> [--aceitar-revisoes]
    python -m scripts.atualizacao_dados versoes
    python -m scripts.atualizacao_dados reverter <versao> --confirmo <versao>
"""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import os
import re
import shutil
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile

import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from dashboard import dados_publicos as dp  # noqa: E402
from scripts import fontes_oficiais as fo  # noqa: E402
from scripts import transform  # noqa: E402
from scripts import versionamento_dados as vv  # noqa: E402

BASE_ATUALIZACAO = RAIZ / "atualizacao"
ATIVA_PADRAO = dp.DIRETORIO_DADOS
ARQ_LEIAME = "LEIAME.md"
_renomear = os.replace  # indireção para testes (simulação de falha na troca)


class ErroAtualizacao(Exception):
    """Falha impeditiva no fluxo de atualização (nunca deixa a versão ativa parcialmente substituída)."""


@dataclass
class Validacao:
    erros: list[str] = field(default_factory=list)
    avisos: list[str] = field(default_factory=list)
    informacoes: dict = field(default_factory=dict)

    @property
    def status(self) -> str:
        return "bloqueado" if self.erros else ("requer_revisao" if self.avisos else "validado")

    def para_dict(self) -> dict:
        return {"status": self.status, "erros": self.erros, "avisos": self.avisos, "informacoes": self.informacoes}


@dataclass
class Candidato:
    id: str
    diretorio: Path
    validacao: Validacao
    comparacao: pd.DataFrame


# ---------------------------------------------------------------------------------------- utilidades
def _csv_bytes(quadro: pd.DataFrame) -> bytes:
    return quadro.to_csv(index=False, lineterminator="\n", na_rep="").encode("utf-8")


def _sha256_arquivo(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as fluxo:
        for bloco in iter(lambda: fluxo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def _ler_csv_bytes(conteudo: bytes) -> pd.DataFrame:
    return pd.read_csv(io.BytesIO(conteudo), dtype=str, keep_default_na=False, na_filter=False, encoding="utf-8")


def _registrar_historico(base: Path, evento: dict) -> None:
    base.mkdir(parents=True, exist_ok=True)
    with (base / "historico.jsonl").open("a", encoding="utf-8", newline="\n") as fluxo:
        fluxo.write(json.dumps({"em_utc": vv.agora_utc().strftime("%Y-%m-%dT%H:%M:%SZ"), **evento}, ensure_ascii=False) + "\n")


# --------------------------------------------------------------------------------- leitura do Sinesp
def _cabecalho_xlsx(caminho: Path) -> tuple[list, bool]:
    with ZipFile(caminho) as pacote:
        textos = transform._shared_strings(pacote)
        xml = pacote.read("xl/worksheets/sheet1.xml")
    linha = re.search(rb'<row\b[^>]*\br="1"[^>]*>.*?</row>', xml, re.DOTALL)
    if linha is None:
        raise ErroAtualizacao(f"Cabeçalho ausente em {caminho.name}: alteração de esquema.")
    elemento = transform._parse_sheet_row(linha.group())
    celulas = {c.get("r").rstrip("0123456789"): transform._cell_value(c, textos) for c in elemento.findall(transform.NS + "c")}
    colunas_extras = re.search(rb'<c\b[^>]*\br="(?:[O-Z]|[A-Z]{2,})\d+"', xml) is not None
    return [celulas.get(chr(65 + i)) for i in range(len(transform.HEADERS))], colunas_extras


def ler_sinesp_xlsx(caminho: Path) -> pd.DataFrame:
    """Linhas SC/JOINVILLE (14 colunas originais, sem alteração) de um XLSX anual do Sinesp VDE."""
    cabecalho, extras = _cabecalho_xlsx(caminho)
    if cabecalho != transform.HEADERS or extras:
        raise ErroAtualizacao(f"Alteração de esquema em {caminho.name}: colunas esperadas {transform.HEADERS}; encontradas {cabecalho}"
                              f"{' (há colunas adicionais)' if extras else ''}.")
    linhas = transform._joinville_rows(caminho)
    if not linhas:
        raise ErroAtualizacao(f"Nenhuma linha SC/JOINVILLE em {caminho.name}.")
    return pd.DataFrame.from_records(linhas, columns=transform.HEADERS)


def _inteiro_nao_negativo(valor, descricao: str):
    if pd.isna(valor):
        return pd.NA
    if isinstance(valor, bool) or not isinstance(valor, (int, float)) or float(valor) != int(valor) or valor < 0:
        raise ErroAtualizacao(f"Valor inválido (esperado inteiro não negativo) em {descricao}: {valor!r}.")
    return int(valor)


def construir_sinesp(quadros: dict[int, pd.DataFrame]) -> tuple[pd.DataFrame, pd.DataFrame, list[str]]:
    """Séries mensais (ano, mes, evento, abrangencia, unidade, valor) e catálogo, a partir dos recortes de Joinville.

    Regras (as mesmas das Etapas 5–9 do roteiro): vítimas em ``total_vitima``; mandados em ``total``; ausência é preservada;
    evento desconhecido, abrangência ausente, data inválida ou ano diferente do arquivo interrompem a preparação.
    Linhas múltiplas na mesma competência só são aceitas (somadas) nos indicadores com nota metodológica oficial.
    """
    avisos: list[str] = []
    registros = []
    for ano_arquivo, quadro in sorted(quadros.items()):
        if list(quadro.columns) != transform.HEADERS:
            raise ErroAtualizacao(f"Esquema incompatível no recorte de {ano_arquivo}.")
        if not (quadro["uf"].eq("SC").all() and quadro["municipio"].eq("JOINVILLE").all()):
            raise ErroAtualizacao(f"Recorte de {ano_arquivo} contém linhas fora de SC/JOINVILLE.")
        for posicao, linha in enumerate(quadro.itertuples(index=False)):
            descricao = f"{ano_arquivo}, linha {posicao + 1} do recorte"
            if linha.evento not in vv.NATUREZAS:
                raise ErroAtualizacao(f"Indicador novo ou renomeado em {descricao}: {linha.evento!r}. Exige decisão metodológica; não incorporado.")
            if pd.isna(linha.abrangencia) or str(linha.abrangencia).strip() == "":
                raise ErroAtualizacao(f"Abrangência ausente em {descricao}.")
            serial = linha.data_referencia
            if isinstance(serial, bool) or not isinstance(serial, (int, float)) or float(serial) != int(serial) or not 0 < serial < 100000:
                raise ErroAtualizacao(f"Data de referência inválida em {descricao}: {serial!r}.")
            data = pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(serial))
            if data.day != 1 or data.year != ano_arquivo:
                raise ErroAtualizacao(f"Competência fora do primeiro dia do mês ou de outro ano em {descricao}: {data.date()}.")
            mandado = linha.evento == vv.EVENTO_MANDADO
            valor = _inteiro_nao_negativo(linha.total if mandado else linha.total_vitima, descricao)
            registros.append({"ano": data.year, "mes": data.month, "evento": linha.evento, "abrangencia": str(linha.abrangencia),
                              "unidade": vv.UNIDADE_MANDADOS if mandado else vv.UNIDADE_VITIMAS, "valor": valor})
    bruto = pd.DataFrame(registros)
    chave = ["evento", "abrangencia", "ano", "mes"]
    repetidas = bruto[bruto.duplicated(chave, keep=False)]
    if len(repetidas):
        eventos_repetidos = set(repetidas["evento"])
        proibidos = eventos_repetidos - set(vv.EVENTOS_COM_LINHAS_MULTIPLAS)
        if proibidos:
            raise ErroAtualizacao(f"Linhas repetidas na mesma competência em indicador sem nota oficial de soma: {sorted(proibidos)}. Sem deduplicação genérica.")
        avisos.append(f"Linhas múltiplas na mesma competência somadas conforme nota metodológica oficial em: {sorted(eventos_repetidos)} "
                      f"({len(repetidas)} linhas; requer conferência).")
        agrupado = bruto.groupby(chave + ["unidade"], as_index=False, sort=False)["valor"].agg(lambda s: s.sum(min_count=1))
        bruto = agrupado
    mensal = bruto.sort_values(["evento", "abrangencia", "ano", "mes"], kind="stable").reset_index(drop=True)
    mensal["valor"] = mensal["valor"].astype("Int64")
    mensal["ano"], mensal["mes"] = mensal["ano"].astype("int64"), mensal["mes"].astype("int64")
    mensal = mensal[dp.COLUNAS_SINESP]
    linhas_catalogo = []
    for (evento, abrangencia), serie in mensal.groupby(["evento", "abrangencia"], sort=True):
        mandado = evento == vv.EVENTO_MANDADO
        ini, fim = vv.primeira_e_ultima_competencia(serie)
        linhas_catalogo.append({
            "evento": evento, "abrangencia": abrangencia, "unidade": serie["unidade"].iloc[0], "natureza": vv.NATUREZAS[evento],
            "medida_origem": "total" if mandado else "total_vitima", "inicio": ini, "fim": fim, "meses_observados": len(serie),
            "meses_com_valor": int(serie["valor"].notna().sum()), "meses_valor_zero": int(serie["valor"].eq(0).sum()),
            "meses_sem_valor": int(serie["valor"].isna().sum()), "limitacoes": vv.limitacoes(mandado)})
    return mensal, pd.DataFrame(linhas_catalogo, columns=dp.COLUNAS_CATALOGO), avisos


# ----------------------------------------------------------------------- comparação e validação
def comparar_sinesp(ativa: pd.DataFrame, candidata: pd.DataFrame) -> pd.DataFrame:
    """Diferenças por chave (evento, abrangência, ano, mês): novo, removido ou alterado."""
    chave = ["evento", "abrangencia", "ano", "mes"]
    a = ativa.assign(ano=ativa["ano"].astype("int64"), mes=ativa["mes"].astype("int64")).rename(columns={"valor": "valor_ativo", "unidade": "unidade_ativa"})
    c = candidata.assign(ano=candidata["ano"].astype("int64"), mes=candidata["mes"].astype("int64")).rename(columns={"valor": "valor_candidato", "unidade": "unidade_candidata"})
    junto = a.merge(c, on=chave, how="outer", indicator="origem")
    linhas = []
    for linha in junto.itertuples(index=False):
        if linha.origem == "left_only":
            situacao = "removido"
        elif linha.origem == "right_only":
            situacao = "novo"
        elif linha.unidade_ativa != linha.unidade_candidata:
            situacao = "unidade_alterada"
        elif pd.isna(linha.valor_ativo) and pd.isna(linha.valor_candidato):
            continue
        elif pd.isna(linha.valor_ativo) != pd.isna(linha.valor_candidato) or int(linha.valor_ativo) != int(linha.valor_candidato):
            situacao = "alterado"
        else:
            continue
        linhas.append({"evento": linha.evento, "abrangencia": linha.abrangencia, "ano": int(linha.ano), "mes": int(linha.mes), "situacao": situacao,
                       "valor_ativo": linha.valor_ativo, "valor_candidato": linha.valor_candidato})
    return pd.DataFrame(linhas, columns=["evento", "abrangencia", "ano", "mes", "situacao", "valor_ativo", "valor_candidato"])


def validar_sinesp_candidato(candidata: pd.DataFrame, catalogo: pd.DataFrame, ativa: pd.DataFrame | None, comparacao: pd.DataFrame | None) -> Validacao:
    validacao = Validacao()
    series_cand = set(zip(candidata["evento"], candidata["abrangencia"]))
    if ativa is not None:
        series_ativas = set(zip(ativa["evento"], ativa["abrangencia"]))
        if series_cand - series_ativas:
            validacao.erros.append(f"Série(s) nova(s) (indicador/abrangência): {sorted(series_cand - series_ativas)}; exigem decisão metodológica.")
        if series_ativas - series_cand:
            validacao.erros.append(f"Série(s) ausente(s) na candidata: {sorted(series_ativas - series_cand)}.")
    for (evento, abrangencia), serie in candidata.groupby(["evento", "abrangencia"]):
        indices = (serie["ano"].astype(int) * 12 + serie["mes"].astype(int) - 1).sort_values().tolist()
        if indices != list(range(indices[0], indices[0] + len(indices))):
            validacao.erros.append(f"Lacuna de competências em {evento}/{abrangencia}.")
    ultimas = candidata.groupby(["evento", "abrangencia"]).apply(lambda s: (s["ano"].astype(int) * 100 + s["mes"].astype(int)).max(), include_groups=False)
    if ultimas.nunique() > 1:
        validacao.avisos.append("Séries com última competência diferente entre si: " + ", ".join(f"{k[0]}/{k[1]}={v}" for k, v in ultimas.items()))
    ini, fim = vv.primeira_e_ultima_competencia(candidata)
    validacao.informacoes.update({"observacoes": int(len(candidata)), "series": int(len(series_cand)), "primeira_competencia": ini, "ultima_competencia": fim,
                                  "valores_ausentes": int(candidata["valor"].isna().sum()), "zeros_publicados": int(candidata["valor"].eq(0).sum())})
    if comparacao is not None:
        contagem = comparacao["situacao"].value_counts().to_dict()
        validacao.informacoes["comparacao"] = {k: int(v) for k, v in contagem.items()}
        if contagem.get("removido"):
            validacao.erros.append(f"{contagem['removido']} competência(s) histórica(s) removida(s) na candidata.")
        if contagem.get("unidade_alterada"):
            validacao.erros.append(f"{contagem['unidade_alterada']} série(s)/competência(s) com unidade alterada.")
        if contagem.get("alterado"):
            validacao.avisos.append(f"REVISÃO HISTÓRICA: {contagem['alterado']} valor(es) de competências já publicadas foram alterados; revisar `comparacao_sinesp.csv`.")
        novos = comparacao[comparacao["situacao"].eq("novo")]
        if len(novos) and ativa is not None:
            fim_ativo = ativa.groupby(["evento", "abrangencia"]).apply(lambda s: (s["ano"].astype(int) * 12 + s["mes"].astype(int)).max(), include_groups=False)
            for (evento, abrangencia), grupo in novos.groupby(["evento", "abrangencia"]):
                esperado_inicio = int(fim_ativo[(evento, abrangencia)]) + 1
                inicio = int((grupo["ano"] * 12 + grupo["mes"]).min())
                if inicio != esperado_inicio:
                    validacao.erros.append(f"Nova(s) competência(s) de {evento}/{abrangencia} não seguem a última já publicada (lacuna).")
            validacao.informacoes["novas_competencias"] = int(len(novos))
    return validacao


# --------------------------------------------------------------------------------- operação B: PREPARAR
def localizar_entradas_sinesp(pasta: Path, anos: list[int]) -> dict[int, Path]:
    encontrados = {}
    for ano in anos:
        candidatos = sorted(Path(pasta).rglob(f"bancovde-{ano}.xlsx"))
        if len(candidatos) != 1:
            raise ErroAtualizacao(f"Esperado exatamente um 'bancovde-{ano}.xlsx' em {pasta}; encontrados: {len(candidatos)}. "
                                  "Arquivos de anos anteriores NÃO são assumidos como inalterados: todos devem ser fornecidos.")
        encontrados[ano] = candidatos[0]
    return encontrados


def preparar(*, ativa: Path = ATIVA_PADRAO, staging_root: Path | None = None, entradas_sinesp: Path | None = None,
             relatorio_verificacao: dict | None = None, agora: datetime | None = None, anos_adicionais: list[int] | None = None) -> Candidato:
    """Operação B: gera a versão candidata isolada. Não altera ``ativa``; em caso de falha remove a candidata parcial."""
    staging_alvo = Path(staging_root) if staging_root else BASE_ATUALIZACAO / "staging"
    antes = set(staging_alvo.iterdir()) if staging_alvo.is_dir() else set()
    try:
        return _preparar(ativa=ativa, staging_root=staging_root, entradas_sinesp=entradas_sinesp, relatorio_verificacao=relatorio_verificacao,
                         agora=agora, anos_adicionais=anos_adicionais)
    except BaseException:
        if staging_alvo.is_dir():
            for pasta in set(staging_alvo.iterdir()) - antes:
                shutil.rmtree(pasta, ignore_errors=True)
        raise


def _preparar(*, ativa: Path, staging_root: Path | None, entradas_sinesp: Path | None, relatorio_verificacao: dict | None,
              agora: datetime | None, anos_adicionais: list[int] | None) -> Candidato:
    staging_root = Path(staging_root) if staging_root else BASE_ATUALIZACAO / "staging"
    agora = agora or vv.agora_utc()
    id_candidata = vv.id_versao(agora)
    manifesto_ativo = dp.carregar_manifesto(ativa)
    ativa_sinesp, ativa_vd = dp.carregar_sinesp(ativa), dp.carregar_violencia_domestica(ativa)
    raiz_candidata = staging_root / id_candidata
    if raiz_candidata.exists():
        raise ErroAtualizacao(f"Candidata {id_candidata} já existe.")
    destino = raiz_candidata / "dados"
    destino.mkdir(parents=True)

    origem = json.loads(json.dumps(manifesto_ativo.get("origem_dos_dados", {})))
    comparacao = pd.DataFrame(columns=["evento", "abrangencia", "ano", "mes", "situacao", "valor_ativo", "valor_candidato"])
    if entradas_sinesp is not None:
        anos = sorted({int(a) for a in origem.get("sinesp_xlsx_bytes", {})} | set(anos_adicionais or []))
        arquivos = localizar_entradas_sinesp(Path(entradas_sinesp), anos)
        quadros, hashes, tamanhos = {}, {}, {}
        for ano, caminho in arquivos.items():
            quadros[ano] = ler_sinesp_xlsx(caminho)
            hashes[str(ano)], tamanhos[str(ano)] = _sha256_arquivo(caminho), int(caminho.stat().st_size)
        mensal, catalogo, avisos_construcao = construir_sinesp(quadros)
        origem["sinesp_xlsx_sha256"], origem["sinesp_xlsx_bytes"] = hashes, tamanhos
        comparacao = comparar_sinesp(ativa_sinesp, mensal)
        validacao = validar_sinesp_candidato(mensal, catalogo, ativa_sinesp, comparacao)
        validacao.avisos.extend(avisos_construcao)
        alterados = [a for a, h in hashes.items() if origem_ativa_hash(manifesto_ativo, a) not in (None, h)]
        validacao.informacoes["arquivos_de_origem_com_hash_diferente_do_auditado"] = alterados
        sinesp_bytes, catalogo_bytes = _csv_bytes(mensal), _csv_bytes(catalogo)
    else:
        validacao = Validacao()
        validacao.informacoes["sinesp"] = "sem novos originais: dados Sinesp inalterados (cópia da versão ativa)"
        mensal, catalogo = ativa_sinesp, dp.carregar_catalogo_sinesp(ativa)
        sinesp_bytes, catalogo_bytes = (ativa / dp.ARQ_SINESP).read_bytes(), (ativa / dp.ARQ_SINESP_CATALOGO).read_bytes()

    (destino / dp.ARQ_SINESP).write_bytes(sinesp_bytes)
    (destino / dp.ARQ_SINESP_CATALOGO).write_bytes(catalogo_bytes)
    for nome in (dp.ARQ_VD, dp.ARQ_VD_RASTREIO):  # SSP/SC: inalterados (novos relatórios exigem auditoria manual)
        shutil.copy2(ativa / nome, destino / nome)
    if (ativa / ARQ_LEIAME).is_file():
        shutil.copy2(ativa / ARQ_LEIAME, destino / ARQ_LEIAME)
    pendencias_ssp = [a for a in (relatorio_verificacao or {}).get("achados", []) if a.get("fonte") == fo.ID_SSP and a.get("classificacao") != fo.Classificacao.NENHUMA_NOVIDADE.value]
    if pendencias_ssp:
        validacao.avisos.append(f"SSP/SC: {len(pendencias_ssp)} indício(s) de novo/alterado relatório de violência doméstica; NÃO incorporados (exigem auditoria manual).")
    validacao.informacoes["ssp_violencia_domestica"] = "inalterada (216 observações auditadas; novos relatórios não incorporados automaticamente)"

    fichas = []
    for nome in dp.ARQUIVOS_DE_DADOS:
        conteudo = (destino / nome).read_bytes()
        quadro = _ler_csv_bytes(conteudo)
        fichas.append({"arquivo": nome, "linhas": int(len(quadro)), "colunas": int(quadro.shape[1]), "esquema": list(quadro.columns), "bytes": len(conteudo),
                       "sha256": dp.sha256_normalizado(conteudo)})
    cobertura = vv.cobertura_padrao(mensal, ativa_vd)
    revisoes = {
        "sinesp": (f"Comparação com a versão {manifesto_ativo.get('versao')}: " + json.dumps(validacao.informacoes.get("comparacao", {}), ensure_ascii=False)
                   if entradas_sinesp is not None else "Sem novos originais: sem alterações."),
        "ssp_violencia_domestica": "Inalterada; relatórios novos ou diferentes não foram incorporados.",
    }
    manifesto = vv.montar_manifesto(
        versao=id_candidata, versao_anterior=manifesto_ativo.get("versao"), gerado_em=agora, gerador="scripts/atualizacao_dados.py (preparar)",
        roteiro_sha256=manifesto_ativo.get("roteiro_sha256"), validacao={"status": validacao.status, "erros": validacao.erros, "avisos": validacao.avisos,
                                                                         "descricao": "Candidata preparada; pendente de aprovação explícita."},
        cobertura=cobertura, revisoes_historicas=revisoes, origem=origem, arquivos=fichas, criterios=manifesto_ativo.get("criterios", []), consulta=relatorio_verificacao)
    (destino / dp.ARQ_MANIFESTO).write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    # Validação estrutural final do que foi gravado (mesmos validadores do dashboard).
    try:
        dp.carregar_sinesp(destino), dp.carregar_catalogo_sinesp(destino), dp.carregar_violencia_domestica(destino), dp.carregar_rastreio_vd(destino)
        integridade = dp.verificar_integridade(destino)
        if not integridade["integro"].all():
            validacao.erros.append("Integridade (SHA-256) da candidata não confere com o seu manifesto.")
    except dp.ErroDados as erro:
        validacao.erros.append(f"Validação estrutural reprovada: {erro}")
    comparacao.to_csv(raiz_candidata / "comparacao_sinesp.csv", index=False, lineterminator="\n")
    (raiz_candidata / "relatorio_validacao.json").write_text(json.dumps({"id": id_candidata, "versao_ativa_comparada": manifesto_ativo.get("versao"),
                                                                       **validacao.para_dict()}, ensure_ascii=False, indent=2, default=str) + "\n", encoding="utf-8", newline="\n")
    _registrar_historico(staging_root.parent, {"operacao": "preparar", "id": id_candidata, "status": validacao.status})
    return Candidato(id_candidata, raiz_candidata, validacao, comparacao)


def origem_ativa_hash(manifesto: dict, ano: str):
    return (manifesto.get("origem_dos_dados", {}).get("sinesp_xlsx_sha256", {}) or {}).get(str(ano))


# ------------------------------------------------------------------- operação C: APROVAR / REVERTER
def _trocar_diretorio(novo: Path, ativa: Path) -> Path:
    """Troca ``ativa`` por ``novo`` (renomeações), com reversão se a segunda renomeação falhar. Devolve o diretório antigo."""
    antigo = ativa.with_name(ativa.name + ".antigo")
    if antigo.exists():
        shutil.rmtree(antigo)
    _renomear(ativa, antigo)
    try:
        _renomear(novo, ativa)
    except BaseException:
        _renomear(antigo, ativa)
        raise
    return antigo


def _validar_diretorio(diretorio: Path) -> None:
    dp.carregar_sinesp(diretorio), dp.carregar_catalogo_sinesp(diretorio), dp.carregar_violencia_domestica(diretorio), dp.carregar_rastreio_vd(diretorio)
    integridade = dp.verificar_integridade(diretorio)
    if not integridade["integro"].all():
        raise dp.ErroDados("integridade (SHA-256) divergente: " + ", ".join(integridade.loc[~integridade["integro"], "arquivo"]))


def _promover_diretorio(origem: Path, ativa: Path, versoes_root: Path, *, aprovacao: dict | None = None) -> str:
    """Preserva a versão ativa em ``versoes_root`` e promove ``origem`` com troca segura. Devolve o id da versão preservada."""
    manifesto_ativo = dp.carregar_manifesto(ativa)
    id_anterior = manifesto_ativo.get("versao") or "sem_versao_" + vv.id_versao(vv.agora_utc())
    backup = versoes_root / id_anterior
    if not backup.exists():
        versoes_root.mkdir(parents=True, exist_ok=True)
        shutil.copytree(ativa, backup)
    novo = ativa.with_name(ativa.name + ".novo")
    if novo.exists():
        shutil.rmtree(novo)
    shutil.copytree(origem, novo)
    try:
        if aprovacao is not None:
            manifesto = json.loads((novo / dp.ARQ_MANIFESTO).read_text(encoding="utf-8"))
            manifesto["aprovacao"] = aprovacao
            manifesto["situacao_validacao"] = {**manifesto.get("situacao_validacao", {}), "status": "aprovado", "descricao": "Aprovada explicitamente pelo responsável."}
            (novo / dp.ARQ_MANIFESTO).write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
        _validar_diretorio(novo)
        antigo = _trocar_diretorio(novo, ativa)
    except BaseException:
        shutil.rmtree(novo, ignore_errors=True)
        raise
    try:
        _validar_diretorio(ativa)  # verificação após a troca: reverte se algo estiver inconsistente
    except BaseException:
        _renomear(ativa, novo)
        _renomear(antigo, ativa)
        shutil.rmtree(novo, ignore_errors=True)
        raise
    shutil.rmtree(antigo, ignore_errors=True)
    return id_anterior


def aprovar(id_candidata: str, *, confirmacao: str | None, aceitar_revisoes: bool = False, ativa: Path = ATIVA_PADRAO,
            staging_root: Path | None = None, versoes_root: Path | None = None, aprovado_por: str = "responsável (confirmação explícita)",
            agora: datetime | None = None) -> str:
    """Operação C: promove a candidata aprovada. Exige confirmação explícita igual ao id e validação sem erros."""
    staging_root = Path(staging_root) if staging_root else BASE_ATUALIZACAO / "staging"
    versoes_root = Path(versoes_root) if versoes_root else BASE_ATUALIZACAO / "versoes"
    raiz = staging_root / id_candidata
    if confirmacao != id_candidata:
        raise ErroAtualizacao(f"Aprovação não confirmada: informe --confirmo {id_candidata}. Nenhum dado foi alterado.")
    if not (raiz / "dados").is_dir() or not (raiz / "relatorio_validacao.json").is_file():
        raise ErroAtualizacao(f"Candidata {id_candidata} inexistente ou sem relatório de validação. Nenhum dado foi alterado.")
    if (raiz / "promovida.json").exists():
        raise ErroAtualizacao(f"Candidata {id_candidata} já foi promovida.")
    relatorio = json.loads((raiz / "relatorio_validacao.json").read_text(encoding="utf-8"))
    if relatorio["status"] == "bloqueado" or relatorio["erros"]:
        raise ErroAtualizacao("Candidata com erros de validação: promoção impossível. " + "; ".join(relatorio["erros"]))
    if relatorio["status"] == "requer_revisao" and not aceitar_revisoes:
        raise ErroAtualizacao("Candidata com avisos (revisões históricas/linhas múltiplas/pendências): revise `comparacao_sinesp.csv` e confirme com --aceitar-revisoes. "
                              "Nenhum dado foi alterado.")
    manifesto_ativo = dp.carregar_manifesto(ativa)
    if relatorio.get("versao_ativa_comparada") != manifesto_ativo.get("versao"):
        raise ErroAtualizacao("A versão ativa mudou desde a preparação da candidata: prepare novamente. Nenhum dado foi alterado.")
    agora = agora or vv.agora_utc()
    anterior = _promover_diretorio(raiz / "dados", ativa, versoes_root, aprovacao={
        "aprovado_em_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"), "aprovado_por": aprovado_por, "aceitou_revisoes": bool(aceitar_revisoes), "candidata": id_candidata})
    (raiz / "promovida.json").write_text(json.dumps({"promovida_em_utc": agora.strftime("%Y-%m-%dT%H:%M:%SZ"), "versao_anterior": anterior}) + "\n", encoding="utf-8")
    _registrar_historico(staging_root.parent, {"operacao": "aprovar", "id": id_candidata, "versao_anterior": anterior})
    return anterior


def listar_versoes(versoes_root: Path | None = None) -> list[dict]:
    versoes_root = Path(versoes_root) if versoes_root else BASE_ATUALIZACAO / "versoes"
    saida = []
    for pasta in sorted(p for p in versoes_root.iterdir() if p.is_dir()) if versoes_root.is_dir() else []:
        try:
            manifesto = json.loads((pasta / dp.ARQ_MANIFESTO).read_text(encoding="utf-8"))
            # Manifestos antigos (schema 1) guardavam 'cobertura' como texto e a data na raiz: leitura tolerante.
            cobertura = manifesto.get("cobertura", {}).get("sinesp", {}) if isinstance(manifesto.get("cobertura"), dict) else {}
            datas = manifesto.get("datas") if isinstance(manifesto.get("datas"), dict) else {}
            saida.append({"versao": pasta.name, "schema": manifesto.get("schema_manifesto", 1),
                          "gerada_em": datas.get("gerado_em_utc") or manifesto.get("gerado_em_utc"),
                          "ultima_competencia_sinesp": cobertura.get("ultima_competencia") if isinstance(cobertura, dict) else None})
        except (OSError, ValueError):
            saida.append({"versao": pasta.name, "schema": None, "gerada_em": None, "ultima_competencia_sinesp": None})
    return saida


def reverter(versao: str, *, confirmacao: str | None, ativa: Path = ATIVA_PADRAO, versoes_root: Path | None = None) -> str:
    """Restaura uma versão preservada (preservando antes a ativa atual). Exige confirmação explícita."""
    versoes_root = Path(versoes_root) if versoes_root else BASE_ATUALIZACAO / "versoes"
    if confirmacao != versao:
        raise ErroAtualizacao(f"Reversão não confirmada: informe --confirmo {versao}. Nenhum dado foi alterado.")
    origem = versoes_root / versao
    if not origem.is_dir():
        raise ErroAtualizacao(f"Versão {versao} não encontrada em {versoes_root}.")
    try:
        _validar_diretorio(origem)
    except dp.ErroDados as erro:
        raise ErroAtualizacao(f"A versão {versao} preservada está inválida ({erro}); reversão cancelada.") from erro
    anterior = _promover_diretorio(origem, ativa, versoes_root)
    _registrar_historico(versoes_root.parent, {"operacao": "reverter", "para": versao, "versao_substituida": anterior})
    return anterior


# ---------------------------------------------------------------------------------------------- CLI
def baixar_sinesp(anos: list[int], destino: Path, cliente: fo.Cliente | None = None) -> dict[int, Path]:
    """Baixa os XLSX oficiais (GET integral) para ``destino``. Bloqueios (403 etc.) NÃO são contornados."""
    cliente = cliente or fo.ClienteHTTP()
    destino.mkdir(parents=True, exist_ok=True)
    caminhos = {}
    for ano in anos:
        resposta = cliente.obter(fo.URL_SINESP_ARQUIVO.format(ano=ano), None, 600.0)
        if resposta.status != 200 or not resposta.corpo:
            raise ErroAtualizacao(f"Download de bancovde-{ano}.xlsx não concluído (HTTP {resposta.status}); acesso não contornado. Baixe manualmente do site oficial.")
        caminho = destino / f"bancovde-{ano}.xlsx"
        caminho.write_bytes(resposta.corpo)
        caminhos[ano] = caminho
    return caminhos


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = analisador.add_subparsers(dest="comando", required=True)
    p = sub.add_parser("verificar", help="A: consulta as fontes (não altera dados)")
    p.add_argument("--ativa", type=Path, default=ATIVA_PADRAO)
    p = sub.add_parser("preparar", help="B: prepara uma versão candidata isolada")
    p.add_argument("--ativa", type=Path, default=ATIVA_PADRAO)
    p.add_argument("--entradas-sinesp", type=Path, default=None, help="pasta com TODOS os bancovde-ANO.xlsx (colocados manualmente)")
    p.add_argument("--baixar-sinesp", action="store_true", help="baixa os XLSX oficiais para atualizacao/entradas/ (pode falhar por bloqueio; não é contornado)")
    p.add_argument("--ano-adicional", type=int, action="append", default=[], help="ano novo a incluir (ex.: 2027)")
    p.add_argument("--relatorio-verificacao", type=Path, default=None)
    p = sub.add_parser("comparar", help="mostra o relatório de validação e a comparação de uma candidata")
    p.add_argument("id")
    p = sub.add_parser("aprovar", help="C: promove uma candidata (exige --confirmo <id>)")
    p.add_argument("id")
    p.add_argument("--confirmo", default=None)
    p.add_argument("--aceitar-revisoes", action="store_true")
    sub.add_parser("versoes", help="lista versões preservadas")
    p = sub.add_parser("reverter", help="restaura uma versão preservada (exige --confirmo <versao>)")
    p.add_argument("versao")
    p.add_argument("--confirmo", default=None)
    argumentos = analisador.parse_args(argv)
    try:
        if argumentos.comando == "verificar":
            manifesto = dp.carregar_manifesto(argumentos.ativa)
            relatorio = fo.verificar_fontes(manifesto)
            caminho = fo.salvar_relatorio(relatorio, BASE_ATUALIZACAO / "verificacoes")
            _registrar_historico(BASE_ATUALIZACAO, {"operacao": "verificar", "resumo": relatorio.resumo()})
            print(json.dumps({"resumo": relatorio.resumo(), "acao_recomendada": relatorio.acao_recomendada(), "relatorio": str(caminho)}, ensure_ascii=False, indent=2))
            for a in relatorio.achados:
                print(f"[{a.classificacao.value}] {a.fonte}/{a.recurso} {a.identificador}: {a.detalhe}")
        elif argumentos.comando == "preparar":
            entradas = argumentos.entradas_sinesp
            manifesto = dp.carregar_manifesto(ATIVA_PADRAO)
            if argumentos.baixar_sinesp:
                anos = sorted({int(a) for a in manifesto["origem_dos_dados"]["sinesp_xlsx_bytes"]} | set(argumentos.ano_adicional))
                entradas = BASE_ATUALIZACAO / "entradas" / vv.id_versao(vv.agora_utc())
                baixar_sinesp(anos, entradas)
            relatorio = json.loads(argumentos.relatorio_verificacao.read_text(encoding="utf-8")) if argumentos.relatorio_verificacao else None
            candidato = preparar(ativa=argumentos.ativa, entradas_sinesp=entradas, relatorio_verificacao=relatorio, anos_adicionais=argumentos.ano_adicional)
            print(f"Candidata {candidato.id} em {candidato.diretorio}: status {candidato.validacao.status}")
            print(json.dumps(candidato.validacao.para_dict(), ensure_ascii=False, indent=2, default=str))
        elif argumentos.comando == "comparar":
            raiz = BASE_ATUALIZACAO / "staging" / argumentos.id
            print((raiz / "relatorio_validacao.json").read_text(encoding="utf-8"))
            print((raiz / "comparacao_sinesp.csv").read_text(encoding="utf-8"))
        elif argumentos.comando == "aprovar":
            anterior = aprovar(argumentos.id, confirmacao=argumentos.confirmo, aceitar_revisoes=argumentos.aceitar_revisoes)
            print(f"Candidata {argumentos.id} promovida. Versão anterior preservada em atualizacao/versoes/{anterior}.")
        elif argumentos.comando == "versoes":
            for ficha in listar_versoes():
                print(ficha)
        elif argumentos.comando == "reverter":
            substituida = reverter(argumentos.versao, confirmacao=argumentos.confirmo)
            print(f"Versão {argumentos.versao} restaurada. A versão substituída ({substituida}) foi preservada.")
    except (ErroAtualizacao, dp.ErroDados, fo.ErroReferencia) as erro:
        print(f"ERRO: {erro}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
