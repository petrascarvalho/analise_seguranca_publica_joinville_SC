"""Gera os arquivos mínimos do dashboard a partir das bases analíticas JÁ VALIDADAS do roteiro.

Procedimento (separado do roteiro e do Streamlit):

1. Extrai, por marcadores de texto, as células das etapas validadas de
   ``scripts/analise_seguranca_publica.py`` (Sinesp: etapas 1–2 e 5–9; SSP/SC: 13.1–13.3) e as
   executa em um espaço de nomes isolado. O roteiro NÃO é importado nem modificado.
2. Confere os valores conhecidos (900 observações Sinesp; 216 observações SSP/SC; totais
   anuais já documentados no README) antes de gravar qualquer arquivo.
3. Grava CSVs agregados e o manifesto (SHA-256) em ``dashboard/data_publica/``.

Requer os dados brutos locais (``dados/``); não os copia nem os redistribui. Ausência de
valor é preservada (campo vazio) e nunca convertida em zero. Nenhum valor é digitado.

Uso (a partir da raiz do projeto)::

    python -m scripts.gerar_dados_dashboard [--saida DIRETORIO] [--sobrescrever]
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

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from dashboard import dados_publicos as dp  # noqa: E402
from scripts import versionamento_dados as vv  # noqa: E402

ROTEIRO = RAIZ / "scripts" / "analise_seguranca_publica.py"

# Valores já documentados no README acadêmico (conferência; não são usados como dados).
HOMICIDIO_ANUAL_2020_2025 = [62, 62, 49, 55, 36, 29]
HOMICIDIO_JAN_AGO_2020_2026 = [50, 40, 29, 40, 21, 18, 22]
VD_ACUMULADO_2023 = {"Ameaça": 1957, "Lesão corporal leve dolosa": 989}
VD_ACUMULADO_2024 = {"Ameaça": 2085, "Lesão corporal leve dolosa": 959}

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
    """Executa as etapas validadas do roteiro e devolve os DataFrames de saída e as fichas de origem."""
    texto = ROTEIRO.read_text(encoding="utf-8")
    espaco_sinesp = {"__file__": str(ROTEIRO), "__name__": "gerador_sinesp"}
    for inicio, fim in (("1", "3"), ("5", "10")):  # etapas 1–2 e 5–9 (a 10 é só visualização)
        _executar(_bloco(texto, inicio, fim), espaco_sinesp, f"Sinesp {inicio}-{fim}")
    espaco_ssp = {"__file__": str(ROTEIRO), "__name__": "gerador_ssp"}
    _executar(_bloco(texto, "13.1", "13.3"), espaco_ssp, "SSP 13.1-13.2")
    _executar(_bloco(texto, "13.3", "14.1"), espaco_ssp, "SSP 13.3")

    # ---- Sinesp -------------------------------------------------------------------------------
    mensal = espaco_sinesp["tabela_mensal_sinesp"]
    _exigir(len(mensal) == 900, "tabela mensal Sinesp não tem 900 observações.")
    sinesp = pd.DataFrame({
        "ano": mensal["ano"].astype("int64"), "mes": mensal["mes"].astype("int64"), "evento": mensal["evento"],
        "abrangencia": mensal["abrangencia"], "unidade": mensal["unidade"], "valor": mensal["valor_publicado"].astype("Int64"),
    }).sort_values(["evento", "abrangencia", "ano", "mes"], kind="stable").reset_index(drop=True)
    anual = espaco_sinesp["tabela_anual_sinesp"]
    homicidio = anual.loc[anual["evento"].eq("Homicídio doloso") & anual["ano"].between(2020, 2025)].sort_values("ano")
    _exigir(homicidio["soma_medida_publicada"].astype(int).tolist() == HOMICIDIO_ANUAL_2020_2025, "homicídio doloso anual diverge do README.")
    jan_ago = espaco_sinesp["comparacao_jan_ago_sinesp"]
    homicidio_ja = jan_ago.loc[jan_ago["evento"].eq("Homicídio doloso")].sort_values("ano")
    _exigir(homicidio_ja["soma_medida_publicada"].astype(int).tolist() == HOMICIDIO_JAN_AGO_2020_2026, "homicídio janeiro–agosto diverge do README.")

    catalogo_base = espaco_sinesp["catalogo_indicadores_sinesp"].rename(columns={
        "evento_original": "evento", "medida_utilizada": "medida_origem", "unidade_medida": "unidade_catalogo"})
    linhas_catalogo = []
    for ficha in catalogo_base.itertuples(index=False):
        serie = sinesp.loc[sinesp["evento"].eq(ficha.evento) & sinesp["abrangencia"].eq(ficha.abrangencia)]
        _exigir(serie["unidade"].eq(ficha.unidade_catalogo).all(), f"unidade divergente em {ficha.evento}/{ficha.abrangencia}.")
        competencias = serie["ano"] * 100 + serie["mes"]
        linhas_catalogo.append({
            "evento": ficha.evento, "abrangencia": ficha.abrangencia, "unidade": ficha.unidade_catalogo, "natureza": ficha.natureza,
            "medida_origem": ficha.medida_origem,
            "inicio": f"{competencias.min() // 100}-{competencias.min() % 100:02d}", "fim": f"{competencias.max() // 100}-{competencias.max() % 100:02d}",
            "meses_observados": len(serie), "meses_com_valor": int(serie["valor"].notna().sum()),
            "meses_valor_zero": int(serie["valor"].eq(0).sum()), "meses_sem_valor": int(serie["valor"].isna().sum()), "limitacoes": ficha.limitacoes,
        })
    catalogo = pd.DataFrame(linhas_catalogo, columns=dp.COLUNAS_CATALOGO)
    _exigir(len(catalogo) == 12 and catalogo["meses_observados"].sum() == 900, "catálogo Sinesp inconsistente (esperado 12 séries, 900 meses).")

    # ---- SSP/SC -------------------------------------------------------------------------------
    resumo13 = espaco_ssp["resumo_validacoes_ssp133"]
    _exigir(len(resumo13) == 67 and bool(resumo13["ok"].all()), "validação da Etapa 13.3 não está integralmente aprovada (67 verificações).")
    base = espaco_ssp["df_violencia_domestica_joinville_ssp132"]
    rastreio = espaco_ssp["rastreabilidade_violencia_domestica_ssp132"]
    _exigir(base.shape == (216, 5) and rastreio.shape == (216, 23), "dimensões da base SSP/SC diferentes de 216×5 e 216×23.")
    vd = pd.DataFrame({
        "municipio": base["municipio"].astype(str), "ano": base["ano"].astype("int64"), "mes": base["mes"].astype("int64"),
        "categoria": base["categoria"].astype(str), "fatos_comunicados": base["fatos_comunicados"].astype("int64"),
    })
    soma = vd.groupby(["ano", "categoria"])["fatos_comunicados"].sum()
    for categoria, valor in VD_ACUMULADO_2023.items():
        _exigir(int(soma[(2023, categoria)]) == valor, f"acumulado 2023 de {categoria} diverge do README.")
    for categoria, valor in VD_ACUMULADO_2024.items():
        _exigir(int(soma[(2024, categoria)]) == valor, f"acumulado 2024 de {categoria} diverge do README.")
    _exigir(int(vd["fatos_comunicados"].eq(0).sum()) == 27, "esperados 27 zeros publicados.")
    rastro = pd.DataFrame({
        "municipio": rastreio["municipio"].astype(str), "ano": rastreio["ano"].astype("int64"), "mes": rastreio["mes"].astype("int64"),
        "categoria": rastreio["categoria"].astype(str), "arquivo_pdf": rastreio["arquivo_pdf"].astype(str),
        "pagina_pdf": rastreio["pagina_pdf"].astype(str), "tabela_pdf": rastreio["tabela_pdf"].astype(str),
        "linha_tabela": rastreio["linha_tabela"].astype(str), "coluna_csv": rastreio["coluna_csv"].astype(str),
        "rotulo_original_categoria": rastreio["rotulo_original_categoria"].astype(str),
        "cabecalho_mes_original": rastreio["cabecalho_mes_original"].astype(str),
        "valor_textual_original": rastreio["valor_textual_original"].astype(str),
    })
    pasta_pdf = espaco_ssp["pasta_pdf_ssp131"]
    origem = {
        "sinesp_xlsx_sha256": {str(ano): hash_ for ano, hash_ in espaco_sinesp["hashes_originais_etapa8"].items()},
        "sinesp_xlsx_bytes": {str(ano): int(caminho.stat().st_size) for ano, caminho in espaco_sinesp["arquivos_sinesp_por_ano"].items()},
        "ssp_pdf_sha256": dict(sorted(rastreio[["arquivo_pdf", "sha256_pdf"]].drop_duplicates().itertuples(index=False, name=None))),
        "ssp_pdf_bytes": {nome: int((pasta_pdf / nome).stat().st_size) for nome in sorted(rastreio["arquivo_pdf"].unique())},
    }
    saidas = {
        dp.ARQ_SINESP: sinesp, dp.ARQ_SINESP_CATALOGO: catalogo,
        dp.ARQ_VD: vd[dp.COLUNAS_VD], dp.ARQ_VD_RASTREIO: rastro[dp.COLUNAS_VD_RASTREIO],
    }
    return saidas, origem


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
    sinesp, vd = saidas[dp.ARQ_SINESP], saidas[dp.ARQ_VD]
    cobertura = vv.cobertura_padrao(sinesp, vd)
    manifesto = vv.montar_manifesto(
        versao=versao, versao_anterior=id_anterior, gerado_em=agora, gerador="scripts/gerar_dados_dashboard.py",
        roteiro_sha256=dp.sha256_normalizado(ROTEIRO.read_bytes()),
        validacao={"status": "validado", "descricao": "Gerado a partir das bases analíticas validadas do roteiro (Sinesp: Etapas 5–9; SSP/SC: Etapas 13.2–13.3 com 67 verificações aprovadas) e conferido contra valores conhecidos.",
                   "verificacoes": ["900 observações Sinesp e 12 séries", "homicídio doloso anual 2020–2025 e janeiro–agosto 2020–2026 iguais ao README",
                                    "216 observações SSP/SC; acumulados 2023/2024 de Ameaça e lesão leve; 27 zeros publicados"]},
        cobertura=cobertura,
        revisoes_historicas={
            "sinesp": "Primeira versão registrada: não há comparação com versão anterior." if anterior is None else "Versão regenerada a partir dos mesmos originais auditados; sem comparação adicional.",
            "ssp_violencia_domestica": "Sem revisão histórica comprovada documentalmente nos três relatórios auditados (Etapas 11–12).",
        },
        origem=origem, arquivos=fichas,
        criterios=[
            "Sinesp: 900 observações mensais da base analítica validada (Etapas 5–9); vítimas em total_vitima; mandados em total; ausência preservada como campo vazio, nunca como zero.",
            "SSP/SC: 216 observações da base analítica validada (Etapas 13.2–13.3); grafias '0 Dolosa' e '- Dolosa' unificadas por decisão metodológica do projeto, sem confirmação oficial.",
            "Não inclui homicídios SSP/SC (série histórica não resolvida), Prefeitura/SEPROT, PDFs, XLSX, CSVs brutos nem dados pessoais.",
        ],
        consulta=consulta)
    (destino / dp.ARQ_MANIFESTO).write_text(json.dumps(manifesto, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    return manifesto


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analisador.add_argument("--saida", type=Path, default=dp.DIRETORIO_DADOS, help="diretório de saída (padrão: dashboard/data_publica)")
    analisador.add_argument("--sobrescrever", action="store_true", help="substitui arquivos existentes que diferirem do gerado")
    analisador.add_argument("--relatorio-verificacao", type=Path, default=None,
                            help="JSON da operação 'verificar' (scripts.atualizacao_dados) a registrar no manifesto como consulta às fontes")
    argumentos = analisador.parse_args(argv)
    saidas, origem = construir_dados()
    consulta = json.loads(argumentos.relatorio_verificacao.read_text(encoding='utf-8')) if argumentos.relatorio_verificacao else None
    manifesto = gravar(saidas, origem, argumentos.saida, argumentos.sobrescrever, consulta)
    for ficha in manifesto["arquivos"]:
        print(f"{ficha['arquivo']}: {ficha['linhas']} linhas × {ficha['colunas']} colunas; sha256 {ficha['sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
