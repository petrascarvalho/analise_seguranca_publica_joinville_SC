"""Acervo SSP/SC de Joinville: inventário, extração validada, auditoria e bases tratadas (sem publicar no painel).

O que este módulo faz, em ordem:
    1. Inventaria os 45 PDFs oficiais da SSP/SC e os 45 CSVs extraídos deles (SHA-256, tamanho, tipo de documento).
    2. Executa, a partir desses arquivos, a extração já validada no roteiro histórico
       (``historico/scripts/analise_seguranca_publica.py``, etapas 11 a 14.1). Ela lê os PDFs e os CSVs, localiza
       Joinville, confere cabeçalhos de ano e mês e devolve as tabelas em memória. Nada é reescrito à mão aqui.
    3. Monta duas bases tratadas, separadas porque têm unidade e granularidade diferentes:
         • violência doméstica: 216 observações mensais (9 categorias × 24 meses, 2023–2024), unidade "Fato Comunicado";
         • homicídios dos boletins: 294 valores publicados (todas as edições), em "ano completo" ou "período acumulado".
    4. Anexa a cada valor de homicídio o seu grupo de republicação (JOIN muitos-para-um, com a cardinalidade conferida)
       e marca os grupos divergentes. Nenhuma versão é escolhida.
    5. Exporta tudo para ``dados/processados/ssp_sc/`` com nomes novos, sem sobrescrever os arquivos anteriores.

Situação de validação: "Fato Comunicado" não tem definição nos PDFs; por isso a violência doméstica fica
"em validação" e não é somada a vítimas nem a outras fontes. Os homicídios têm 41 grupos com versões divergentes.

Execução (a partir da raiz do projeto, com o acervo local em dados/brutos/ssp_sc/):
    python -m src.pipeline.ssp_sc
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
from pathlib import Path

import pandas as pd

from src.pipeline.utils import project_path

PASTA_BRUTOS = project_path("dados", "brutos", "ssp_sc")
PASTA_PROCESSADOS = project_path("dados", "processados", "ssp_sc")
ROTEIRO_HISTORICO = project_path("historico", "scripts", "analise_seguranca_publica.py")

FONTE = "SSP/SC"
UNIDADE_VD = "Fato Comunicado"
SITUACAO_VD = "em validação: unidade 'Fato Comunicado' sem definição oficial nos PDFs"
RELATORIOS_VD = {  # rótulo do relatório na extração -> arquivo PDF de origem
    "1º semestre de 2023": "2025_06_VIOLENCIA-DOMESTICA-1o-SEMESTRE-2023.pdf",
    "2º semestre de 2023": "2025_06_VIOLENCIA-DOMESTICA-2o-SEMESTRE-2023.pdf",
    "2024": "2025_06_VIOLENCIA-DOMESTICA-2024-SC.pdf",
}


def sha256_arquivo(caminho: Path) -> str:
    """SHA-256 do arquivo, lido em blocos de 1 MB (a "impressão digital" que mostra se ele mudou)."""
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def acervo_disponivel() -> bool:
    """True quando os 45 PDFs e os 45 CSVs extraídos estão no computador (eles não ficam no Git)."""
    return len(list((PASTA_BRUTOS / "pdfs").glob("*.pdf"))) == 45 and len(list((PASTA_BRUTOS / "csv_extraidos").glob("*.csv"))) == 45


# ------------------------------------------------------------------------------------------------ 1. inventário
def inventariar_acervo() -> pd.DataFrame:
    """Uma linha por PDF oficial, com o CSV extraído correspondente.

    Retorno: DataFrame com arquivo, tipo de documento, bytes, SHA-256 do PDF, nome e SHA-256 do CSV, linhas do CSV
    e se o par PDF/CSV está completo. O CSV é um derivado do PDF e não o substitui.
    """
    linhas = []
    for pdf in sorted((PASTA_BRUTOS / "pdfs").glob("*.pdf")):
        csv = PASTA_BRUTOS / "csv_extraidos" / (pdf.stem + ".csv")
        tipo = "relatório de violência doméstica (todos os municípios de SC)" if "VIOLENCIA-DOMESTICA" in pdf.name \
            else "boletim mensal Segurança em Números (indicadores estaduais e municipais)"
        linhas.append({
            "arquivo_pdf": pdf.name, "tipo_documento": tipo, "bytes_pdf": pdf.stat().st_size, "sha256_pdf": sha256_arquivo(pdf),
            "arquivo_csv": csv.name if csv.exists() else None, "sha256_csv": sha256_arquivo(csv) if csv.exists() else None,
            "linhas_csv": sum(1 for _ in csv.open(encoding="utf-8-sig")) - 1 if csv.exists() else None,
            "par_completo": csv.exists(),
        })
    inventario = pd.DataFrame(linhas)
    # Dois documentos diferentes nunca devem ter o mesmo conteúdo; se tiverem, é cópia duplicada.
    inventario["pdf_duplicado"] = inventario["sha256_pdf"].duplicated(keep=False)
    return inventario


# ------------------------------------------------------------------------------------------- 2. extração validada
def executar_extracao_validada() -> dict:
    """Executa as etapas 11 a 14.1 do roteiro histórico e devolve as tabelas produzidas (em memória).

    O roteiro lê os PDFs (pdfplumber/pypdf) e os CSVs extraídos, confere 68 verificações da violência doméstica e audita
    as republicações dos boletins. Ele não grava arquivos. Leva cerca de 1 a 2 minutos.
    Retorno: dicionário {nome da variável do roteiro: DataFrame}.
    """
    import matplotlib

    matplotlib.use("Agg")  # o roteiro importa o Matplotlib; sem janela gráfica
    texto = ROTEIRO_HISTORICO.read_text(encoding="utf-8")
    inicio = texto.index("# # ETAPA 11 — Inspeção dos dados brutos SSP/SC")
    fim = texto.index("# # ETAPA 14.2 — Visualizações")  # os gráficos não são necessários aqui
    espaco = {"__file__": str(ROTEIRO_HISTORICO), "__name__": "extracao_ssp_sc"}
    with contextlib.redirect_stdout(io.StringIO()):  # as tabelas impressas pelo roteiro ficam fora do terminal
        exec(compile(texto[inicio:fim], str(ROTEIRO_HISTORICO), "exec"), espaco)  # noqa: S102 — código do próprio projeto
    nomes = ("df_violencia_domestica_joinville_ssp132", "rastreabilidade_violencia_domestica_ssp132", "resumo_validacoes_ssp133",
             "evidencias_celulas_ssp", "matriz_republicacoes_ssp12", "edicoes_auditoria_ssp12")
    return {nome: espaco[nome] for nome in nomes}


# ------------------------------------------------------------------------------------- 3. violência doméstica
def tratar_violencia_domestica(extracao: dict) -> pd.DataFrame:
    """Base mensal de violência doméstica de Joinville no esquema comum do projeto (uma linha por categoria e mês).

    Nada é somado, preenchido ou excluído: são as 216 células publicadas (9 categorias × 24 meses).
    A unidade continua "Fato Comunicado" e a situação fica "em validação".
    """
    origem = extracao["rastreabilidade_violencia_domestica_ssp132"]  # onde está cada célula no PDF
    valores = extracao["df_violencia_domestica_joinville_ssp132"]  # a mesma ordem de linhas, com o valor já convertido
    # Conferência: as duas tabelas descrevem as mesmas células e o número convertido é o texto publicado.
    if not origem.index.equals(valores.index) or not (origem["valor_textual_original"].astype(int) == valores["fatos_comunicados"]).all():
        raise ValueError("Rastreabilidade e base de violência doméstica não correspondem célula a célula.")
    origem = origem.assign(fatos_comunicados=valores["fatos_comunicados"])
    base = pd.DataFrame({
        "fonte": FONTE,
        "municipio": "JOINVILLE",
        "uf": "SC",
        "serie_id": "ssp_vd|" + origem["categoria"],
        "indicador": "Violência doméstica — " + origem["categoria"],
        "indicador_original": origem["rotulo_original_categoria"],
        "abrangencia": "município do fato",
        "ano": origem["ano"].astype("Int64"),
        "mes": origem["mes"].astype("Int64"),
        "periodicidade": "mensal",
        "unidade": UNIDADE_VD,
        "valor": origem["fatos_comunicados"].astype("Int64"),
        "arquivo_origem": origem["arquivo_pdf"],
        "pagina_pdf": origem["pagina_pdf"].astype(str),
        "sha256_origem": origem["sha256_pdf"],
        "situacao_validacao": SITUACAO_VD,
    })
    base["periodo_inicio"] = pd.to_datetime(dict(year=base["ano"], month=base["mes"], day=1)).dt.strftime("%Y-%m-%d")
    base["periodo_fim"] = (pd.to_datetime(base["periodo_inicio"]) + pd.offsets.MonthEnd(0)).dt.strftime("%Y-%m-%d")
    return base.sort_values(["ano", "mes", "indicador"], ignore_index=True)


# ---------------------------------------------------------------------------------------------- 4. homicídios
def tratar_homicidios(extracao: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Todos os valores de homicídio publicados nos boletins, com o grupo de republicação de cada um.

    Cada boletim mensal republica totais de anos completos e o acumulado do ano até o mês; o mesmo número aparece em
    várias edições, às vezes com valores diferentes. Aqui cada valor publicado vira uma linha (294), e um JOIN
    muitos-para-um traz do quadro de grupos (58) se aquele grupo é concordante ou divergente. Nenhuma versão é escolhida.
    Retorno: (versões publicadas, grupos de republicação).
    """
    celulas = extracao["evidencias_celulas_ssp"]
    hom = celulas.loc[celulas["indicador_original"].str.startswith("Nº de vítimas de homicídio")].copy()
    grupos = extracao["matriz_republicacoes_ssp12"].copy()
    chave = ["periodo_tipo", "ano_referencia", "periodo_publicado"]
    hom["periodo_publicado"] = hom["periodo_referencia"]
    # validate="many_to_one" interrompe o processo se um grupo aparecer duas vezes (o JOIN multiplicaria linhas).
    unido = hom.merge(grupos[chave + ["grupo", "divergente", "situacao"]], on=chave, how="left", validate="many_to_one")
    if len(unido) != len(hom):
        raise ValueError("O JOIN com os grupos de republicação mudou a quantidade de linhas.")
    versoes = pd.DataFrame({
        "fonte": FONTE, "municipio": "JOINVILLE", "uf": "SC",
        "indicador": "Vítimas de homicídio", "indicador_original": unido["indicador_original"],
        "periodo_tipo": unido["periodo_tipo"], "ano_referencia": unido["ano_referencia"], "periodo_publicado": unido["periodo_publicado"],
        "unidade": "vítimas", "valor_publicado": unido["valor_publicado"], "edicao": unido["edicao"],
        "arquivo_origem": unido["arquivo_pdf"], "pagina_pdf": unido["pagina_pdf"].astype(str),
        "grupo_republicacao": unido["grupo"], "grupo_divergente": unido["divergente"],
        "situacao_validacao": unido["situacao"].fillna("publicado uma única vez, sem confirmação de versão definitiva"),
    })
    return versoes, grupos


# ------------------------------------------------------------------------------------------------ 5. exportação
def exportar(pasta: Path = PASTA_PROCESSADOS) -> dict:
    """Executa o fluxo completo e grava as bases tratadas em ``dados/processados/ssp_sc/`` (nomes novos; nada é sobrescrito).

    Retorno: resumo com as contagens usadas no README e nos testes.
    """
    if not acervo_disponivel():
        raise FileNotFoundError("Acervo SSP/SC incompleto: são esperados 45 PDFs e 45 CSVs em dados/brutos/ssp_sc/.")
    hashes_antes = {p: sha256_arquivo(p) for p in sorted(PASTA_BRUTOS.rglob("*")) if p.is_file()}
    inventario = inventariar_acervo()
    extracao = executar_extracao_validada()
    vd = tratar_violencia_domestica(extracao)
    versoes, grupos = tratar_homicidios(extracao)
    validacoes = extracao["resumo_validacoes_ssp133"]

    pasta.mkdir(parents=True, exist_ok=True)
    arquivos = {
        "inventario_acervo_ssp_sc.csv": inventario,
        "violencia_domestica_joinville_tratada.csv": vd,
        "homicidios_boletins_joinville_versoes.csv": versoes,
        "homicidios_republicacoes_grupos.csv": grupos.astype({c: str for c in grupos.columns if grupos[c].dtype == object}),
    }
    for nome, tabela in arquivos.items():
        tabela.to_csv(pasta / nome, index=False, encoding="utf-8", lineterminator="\n")

    # Os originais não podem ter mudado durante a leitura.
    if {p: sha256_arquivo(p) for p in hashes_antes} != hashes_antes:
        raise RuntimeError("Um arquivo bruto da SSP/SC mudou durante o processamento.")
    resumo = {
        "pdfs": int(len(inventario)), "csvs_extraidos": int(inventario["par_completo"].sum()),
        "pdfs_duplicados": int(inventario["pdf_duplicado"].sum()),
        "violencia_domestica": {"linhas": int(len(vd)), "categorias": int(vd["indicador"].nunique()),
                                "meses": int(vd[["ano", "mes"]].drop_duplicates().shape[0]),
                                "periodo": f"{vd['periodo_inicio'].min()} a {vd['periodo_fim'].max()}",
                                "zeros_publicados": int(vd["valor"].eq(0).sum()), "ausentes": int(vd["valor"].isna().sum()),
                                "verificacoes_aprovadas": f"{int(validacoes['ok'].sum())} de {len(validacoes)}",
                                "relatorios": {r: int(vd['arquivo_origem'].eq(a).sum()) for r, a in RELATORIOS_VD.items()}},
        "homicidios": {"valores_publicados": int(len(versoes)), "edicoes": int(versoes["edicao"].nunique()),
                       "grupos_republicados": int(len(grupos)), "grupos_divergentes": int(grupos["divergente"].sum()),
                       "grupos_concordantes": int((~grupos["divergente"]).sum())},
        "originais_inalterados": True,
        "arquivos_gerados": sorted(arquivos),
    }
    (pasta / "relatorio_auditoria_ssp_sc.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumo


if __name__ == "__main__":
    print(json.dumps(exportar(), ensure_ascii=False, indent=2))
