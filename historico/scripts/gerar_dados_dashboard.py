"""Gera os arquivos mínimos do dashboard (fonte única Sinesp/MJSP) a partir da base analítica JÁ VALIDADA do roteiro.

Procedimento (separado do roteiro e do Streamlit):

1. Extrai, por marcadores de texto, as células das etapas validadas de ``historico/scripts/analise_seguranca_publica.py``
   (Sinesp: etapas 1–2 e 5–9) e as executa em um espaço de nomes isolado. O roteiro NÃO é importado nem modificado,
   e as etapas históricas de outras fontes (SSP/SC, Prefeitura) NÃO são executadas.
2. Confere valores conhecidos (900 observações; homicídio doloso anual e janeiro–agosto, conforme o README) antes de gravar.
3. Grava CSVs agregados e o manifesto (SHA-256) em ``dashboard/data_publica/``.

Requer os XLSX oficiais do Sinesp em ``dados/brutos/sinesp/`` (que não são copiados nem redistribuídos). Ausência de valor é
preservada (campo vazio) e nunca convertida em zero. Nenhum valor é digitado.

Este gerador reproduz a versão inicial (competências até 2026-08, auditada). Para novas publicações oficiais use o fluxo
controlado ``python -m src.pipeline.atualizacao_dados`` (verificar → preparar → aprovar), que não depende do roteiro.

Uso (a partir da raiz do projeto)::

    python -m historico.scripts.gerar_dados_dashboard [--saida DIRETORIO] [--sobrescrever]
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import re
import shutil
import sys
from pathlib import Path

import pandas as pd

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from dashboard import dados_publicos as dp  # noqa: E402
from src.pipeline import versionamento_dados as vv  # noqa: E402

ROTEIRO = RAIZ / "historico" / "scripts" / "analise_seguranca_publica.py"

# Valores já documentados no README acadêmico (conferência; não são usados como dados).
HOMICIDIO_ANUAL_2020_2025 = [62, 62, 49, 55, 36, 29]
HOMICIDIO_JAN_AGO_2020_2026 = [50, 40, 29, 40, 21, 18, 22]


def _bloco(texto: str, inicio: str, fim: str) -> str:
    """Trecho do roteiro entre os cabeçalhos '# # ETAPA <inicio> ' e '# # ETAPA <fim> '."""
    marcador_inicio = re.search(rf"^# # ETAPA {re.escape(inicio)} ", texto, re.MULTILINE)
    marcador_fim = re.search(rf"^# # ETAPA {re.escape(fim)} ", texto, re.MULTILINE)
    if marcador_inicio is None or marcador_fim is None or marcador_fim.start() <= marcador_inicio.start():
        raise RuntimeError(f"Marcadores de etapa não encontrados no roteiro: {inicio} → {fim}.")
    return texto[marcador_inicio.start():marcador_fim.start()]


def _executar(codigo: str, espaco: dict, rotulo: str) -> None:
    with contextlib.redirect_stdout(io.StringIO()):
        exec(compile(codigo, f"{ROTEIRO} [{rotulo}]", "exec"), espaco)  # noqa: S102 — código do próprio projeto


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise RuntimeError(f"Geração interrompida: {mensagem}")


def construir_dados() -> tuple[dict[str, pd.DataFrame], dict]:
    """Executa as etapas Sinesp validadas do roteiro e devolve os DataFrames de saída e as fichas de origem."""
    texto = ROTEIRO.read_text(encoding="utf-8")
    espaco = {"__file__": str(ROTEIRO), "__name__": "gerador_sinesp"}
    for inicio, fim in (("1", "3"), ("5", "10")):  # etapas 1–2 e 5–9 (a 10 é só visualização)
        _executar(_bloco(texto, inicio, fim), espaco, f"Sinesp {inicio}-{fim}")
    mensal = espaco["tabela_mensal_sinesp"]
    _exigir(len(mensal) == 900, "tabela mensal Sinesp não tem 900 observações.")
    sinesp = pd.DataFrame({
        "ano": mensal["ano"].astype("int64"), "mes": mensal["mes"].astype("int64"), "evento": mensal["evento"],
        "abrangencia": mensal["abrangencia"], "unidade": mensal["unidade"], "valor": mensal["valor_publicado"].astype("Int64"),
    }).sort_values(["evento", "abrangencia", "ano", "mes"], kind="stable").reset_index(drop=True)
    anual = espaco["tabela_anual_sinesp"]
    homicidio = anual.loc[anual["evento"].eq("Homicídio doloso") & anual["ano"].between(2020, 2025)].sort_values("ano")
    _exigir(homicidio["soma_medida_publicada"].astype(int).tolist() == HOMICIDIO_ANUAL_2020_2025, "homicídio doloso anual diverge do README.")
    jan_ago = espaco["comparacao_jan_ago_sinesp"]
    homicidio_ja = jan_ago.loc[jan_ago["evento"].eq("Homicídio doloso")].sort_values("ano")
    _exigir(homicidio_ja["soma_medida_publicada"].astype(int).tolist() == HOMICIDIO_JAN_AGO_2020_2026, "homicídio janeiro–agosto diverge do README.")

    catalogo_base = espaco["catalogo_indicadores_sinesp"].rename(columns={
        "evento_original": "evento", "medida_utilizada": "medida_origem", "unidade_medida": "unidade_catalogo"})
    linhas_catalogo = []
    for ficha in catalogo_base.itertuples(index=False):
        serie = sinesp.loc[sinesp["evento"].eq(ficha.evento) & sinesp["abrangencia"].eq(ficha.abrangencia)]
        _exigir(serie["unidade"].eq(ficha.unidade_catalogo).all(), f"unidade divergente em {ficha.evento}/{ficha.abrangencia}.")
        inicio, fim = vv.primeira_e_ultima_competencia(serie)
        linhas_catalogo.append({
            "evento": ficha.evento, "abrangencia": ficha.abrangencia, "unidade": ficha.unidade_catalogo, "natureza": ficha.natureza,
            "medida_origem": ficha.medida_origem, "inicio": inicio, "fim": fim, "meses_observados": len(serie),
            "meses_com_valor": int(serie["valor"].notna().sum()), "meses_valor_zero": int(serie["valor"].eq(0).sum()),
            "meses_sem_valor": int(serie["valor"].isna().sum()), "limitacoes": ficha.limitacoes,
        })
    catalogo = pd.DataFrame(linhas_catalogo, columns=dp.COLUNAS_CATALOGO).sort_values(["evento", "abrangencia"], kind="stable").reset_index(drop=True)
    _exigir(len(catalogo) == 12 and catalogo["meses_observados"].sum() == 900, "catálogo Sinesp inconsistente (esperado 12 séries, 900 meses).")
    dp.validar_consistencia(sinesp, catalogo.astype(str))
    origem = {
        "sinesp_xlsx_sha256": {str(ano): hash_ for ano, hash_ in espaco["hashes_originais_etapa8"].items()},
        "sinesp_xlsx_bytes": {str(ano): int(caminho.stat().st_size) for ano, caminho in espaco["arquivos_sinesp_por_ano"].items()},
    }
    return {dp.ARQ_SINESP: sinesp, dp.ARQ_SINESP_CATALOGO: catalogo}, origem


def _csv_bytes(quadro: pd.DataFrame) -> bytes:
    return quadro.to_csv(index=False, lineterminator="\n", na_rep="").encode("utf-8")


def _ler_manifesto_existente(destino: Path) -> dict | None:
    caminho = destino / dp.ARQ_MANIFESTO
    if not caminho.is_file():
        return None
    try:
        return json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def gravar(saidas: dict[str, pd.DataFrame], origem: dict, destino: Path, sobrescrever: bool, consulta: dict | None = None,
           raiz_versoes: Path | None = None) -> dict:
    destino.mkdir(parents=True, exist_ok=True)
    conteudos = {nome: _csv_bytes(quadro) for nome, quadro in saidas.items()}
    for nome, conteudo in conteudos.items():
        caminho = destino / nome
        if caminho.exists() and caminho.read_bytes() != conteudo and not sobrescrever:
            raise FileExistsError(f"{caminho} existe e difere do gerado; use --sobrescrever para substituir.")
    anterior = _ler_manifesto_existente(destino)
    agora = vv.agora_utc()
    versao = vv.id_versao(agora)
    id_anterior = None
    if anterior is not None:  # preserva a versão anterior antes de qualquer substituição
        raiz = raiz_versoes or (RAIZ / "atualizacao" / "versoes")
        id_anterior = anterior.get("versao") or "sem_versao_" + versao
        backup = raiz / id_anterior
        if not backup.exists():
            shutil.copytree(destino, backup)
    fichas = []
    for nome, conteudo in conteudos.items():
        (destino / nome).write_bytes(conteudo)
        quadro = saidas[nome]
        fichas.append({"arquivo": nome, "linhas": int(len(quadro)), "colunas": int(quadro.shape[1]), "esquema": list(quadro.columns),
                       "bytes": len(conteudo), "sha256": dp.sha256_normalizado(conteudo)})
    manifesto = vv.montar_manifesto(
        versao=versao, versao_anterior=id_anterior, gerado_em=agora, gerador="historico/scripts/gerar_dados_dashboard.py",
        roteiro_sha256=dp.sha256_normalizado(ROTEIRO.read_bytes()),
        validacao={"status": "validado", "descricao": "Gerado a partir da base analítica Sinesp validada do roteiro (Etapas 5–9) e conferido contra valores conhecidos.",
                   "verificacoes": ["900 observações Sinesp e 12 séries", "homicídio doloso anual 2020–2025 e janeiro–agosto 2020–2026 iguais ao README"]},
        cobertura=vv.cobertura_padrao(saidas[dp.ARQ_SINESP]),
        revisoes_historicas={"sinesp": "Primeira versão registrada: sem comparação com versão anterior." if anterior is None
                             else "Versão regenerada a partir dos mesmos originais auditados; sem comparação adicional."},
        origem=origem, arquivos=fichas,
        criterios=vv.CRITERIOS,
        consulta=consulta)
    (destino / dp.ARQ_MANIFESTO).write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifesto


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analisador.add_argument("--saida", type=Path, default=dp.DIRETORIO_DADOS, help="diretório de saída (padrão: dashboard/data_publica)")
    analisador.add_argument("--sobrescrever", action="store_true", help="substitui arquivos existentes que diferirem do gerado")
    analisador.add_argument("--relatorio-verificacao", type=Path, default=None,
                            help="JSON da operação 'verificar' (src.pipeline.atualizacao_dados) a registrar no manifesto como consulta à fonte")
    argumentos = analisador.parse_args(argv)
    saidas, origem = construir_dados()
    consulta = json.loads(argumentos.relatorio_verificacao.read_text(encoding="utf-8")) if argumentos.relatorio_verificacao else None
    manifesto = gravar(saidas, origem, argumentos.saida, argumentos.sobrescrever, consulta)
    for ficha in manifesto["arquivos"]:
        print(f"{ficha['arquivo']}: {ficha['linhas']} linhas × {ficha['colunas']} colunas; sha256 {ficha['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
