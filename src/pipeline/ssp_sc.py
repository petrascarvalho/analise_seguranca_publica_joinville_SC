"""Acervo SSP/SC de Joinville: inventário, extração, auditoria e bases tratadas (investigação; não entra no painel).

Fonte: SSP/SC, "Segurança em Números" — 42 boletins mensais e 3 relatórios de violência doméstica, em PDF, com todos os
municípios de SC. Cada PDF tem um CSV extraído (``dados/brutos/ssp_sc/csv_extraidos/``) com a posição de cada célula:
página, tabela e linha. O CSV localiza os valores; o PDF continua sendo o documento oficial.

O que este módulo faz, em ordem:
    1. Inventaria os 45 PDFs e os 45 CSVs (SHA-256, tamanho, tipo de documento).
    2. Violência doméstica: em cada relatório, lê o bloco de JOINVILLE (9 categorias) e junta as duas metades da tabela
       (os primeiros meses ficam numa página e os demais na página pareada). Ano e meses vêm do cabeçalho impresso no PDF.
       Resultado: 216 células mensais (9 categorias × 24 meses), unidade "Fato Comunicado".
    3. Homicídios: em cada boletim, lê a linha de JOINVILLE da tabela municipal de vítimas de homicídio (3 anos completos e
       4 acumulados do ano). Resultado: 294 valores publicados, um por edição.
    4. Republicações: agrupa o mesmo número publicado em várias edições e marca os grupos com versões diferentes.
       Nenhuma versão é escolhida.
    5. Confere cada célula usada contra a tabela do próprio PDF e exporta para ``dados/processados/ssp_sc/``.

Situação: "Fato Comunicado" não tem definição nos PDFs, por isso a violência doméstica fica "em validação" e não é somada a
vítimas nem a outras fontes. Os homicídios têm grupos com versões divergentes.

Execução (na raiz do projeto, com o acervo local em dados/brutos/ssp_sc/):
    python -m src.pipeline.ssp_sc
"""

from __future__ import annotations

import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

import pandas as pd

from src.pipeline.utils import project_path

PASTA_BRUTOS = project_path("dados", "brutos", "ssp_sc")
PASTA_PROCESSADOS = project_path("dados", "processados", "ssp_sc")
PASTA_GRAFICOS = project_path("documentacao", "graficos", "analises")

FONTE = "SSP/SC"
UNIDADE_VD = "Fato Comunicado"
SITUACAO_VD = "em validação: unidade 'Fato Comunicado' sem definição oficial nos PDFs"
MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")
# Rótulo publicado → categoria. As duas grafias das lesões ("0 Dolosa" no 1º semestre de 2023, "- Dolosa" depois) são a mesma
# categoria (decisão documentada no README); nenhuma categoria é somada a outra.
CATEGORIAS_VD = {
    "Ameaça": "Ameaça", "Calúnia": "Calúnia", "Difamação": "Difamação", "Estupro": "Estupro", "Injúria": "Injúria",
    "Injúria real": "Injúria real", "Vias de fato": "Vias de fato",
    "Lesão corporal grave ou gravíssima 0 Dolosa": "Lesão corporal grave ou gravíssima dolosa",
    "Lesão corporal grave ou gravíssima - Dolosa": "Lesão corporal grave ou gravíssima dolosa",
    "Lesão corporal leve 0 Dolosa": "Lesão corporal leve dolosa",
    "Lesão corporal leve - Dolosa": "Lesão corporal leve dolosa",
}


# ------------------------------------------------------------------------------------------------ leitura básica
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


def ler_csv_extraido(nome_pdf: str) -> pd.DataFrame:
    """CSV extraído de um PDF, tudo como texto: zeros, vazios e grafias ficam exatamente como foram extraídos."""
    caminho = PASTA_BRUTOS / "csv_extraidos" / (Path(nome_pdf).stem + ".csv")
    return pd.read_csv(caminho, sep=";", encoding="utf-8-sig", dtype=str, keep_default_na=False, na_filter=False)


@lru_cache(maxsize=None)
def texto_pagina(nome_pdf: str, pagina: int) -> str:
    """Texto impresso numa página do PDF (pypdf), usado para ler ano, meses e período dos cabeçalhos."""
    from pypdf import PdfReader

    return PdfReader(PASTA_BRUTOS / "pdfs" / nome_pdf).pages[pagina - 1].extract_text() or ""


@lru_cache(maxsize=None)
def paginas_pdf(nome_pdf: str) -> int:
    from pypdf import PdfReader

    return len(PdfReader(PASTA_BRUTOS / "pdfs" / nome_pdf).pages)


@lru_cache(maxsize=None)
def _tabelas_da_pagina(nome_pdf: str, pagina: int) -> tuple:
    import pdfplumber

    with pdfplumber.open(PASTA_BRUTOS / "pdfs" / nome_pdf) as pdf:
        return tuple(pdf.pages[pagina - 1].extract_tables())


def linha_da_tabela_no_pdf(nome_pdf: str, pagina: int, tabela: int, linha: int) -> list[str]:
    """Células de uma linha de tabela lidas diretamente do PDF (pdfplumber), para conferir o CSV extraído."""
    return ["" if c is None else c for c in _tabelas_da_pagina(nome_pdf, pagina)[tabela - 1][linha - 1]]


def _celulas(linha: pd.Series) -> list[str]:
    return [linha[c] for c in linha.index if c.startswith("celula_")]


# ------------------------------------------------------------------------------------------------- 1. inventário
def inventariar_acervo() -> pd.DataFrame:
    """Uma linha por PDF oficial, com o CSV extraído correspondente (o CSV é derivado do PDF e não o substitui)."""
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
    inventario["pdf_duplicado"] = inventario["sha256_pdf"].duplicated(keep=False)  # dois documentos com o mesmo conteúdo
    return inventario


# ------------------------------------------------------------------------------------------ 2. violência doméstica
def extrair_violencia_domestica(verificacoes: list | None = None) -> pd.DataFrame:
    """As 216 células mensais de violência doméstica de Joinville, com a localização de cada uma no PDF.

    Em cada relatório (N páginas), a tabela é larga demais e foi impressa em duas metades: páginas 1 a N/2 com município,
    categoria e os primeiros meses; páginas N/2+1 a N com os meses restantes, na mesma linha. Os meses de cada metade estão no
    cabeçalho da primeira página da metade; o ano, no topo dessas páginas. Nada é preenchido: valor não numérico interrompe.
    """
    verificacoes = [] if verificacoes is None else verificacoes
    registros = []
    for pdf in sorted((PASTA_BRUTOS / "pdfs").glob("*VIOLENCIA-DOMESTICA*.pdf")):
        nome, bruto = pdf.name, ler_csv_extraido(pdf.name)
        metade = paginas_pdf(nome) // 2
        topo_esq, topo_dir = texto_pagina(nome, 1), texto_pagina(nome, metade + 1)
        ano = re.search(r"\b20\d{2}\b", topo_esq).group()
        meses_esq = re.findall(r"\b(?:" + "|".join(MESES) + r")\b", topo_esq[:120])
        meses_dir = re.findall(r"\b(?:" + "|".join(MESES) + r")\b", topo_dir[:80])
        numeros = [MESES.index(m) + 1 for m in meses_esq + meses_dir]
        verificacoes += [
            (nome, "páginas em número par (duas metades)", paginas_pdf(nome) % 2 == 0),
            (nome, "mesmo ano no topo das duas metades", re.search(r"\b20\d{2}\b", topo_dir).group() == ano),
            (nome, "meses consecutivos no cabeçalho", numeros == list(range(numeros[0], numeros[0] + len(numeros)))),
        ]
        inicio = bruto.loc[bruto["celula_01"].eq("JOINVILLE")].iloc[0]
        pagina_esq = int(inicio["pagina_pdf"])
        pagina_dir = pagina_esq + metade
        esquerda = bruto.loc[bruto["pagina_pdf"].eq(str(pagina_esq)) & bruto["tabela_pdf"].eq(inicio["tabela_pdf"])]
        direita = bruto.loc[bruto["pagina_pdf"].eq(str(pagina_dir)) & bruto["tabela_pdf"].eq(inicio["tabela_pdf"])]
        verificacoes.append((nome, "metades alinhadas linha a linha", esquerda["linha_tabela"].tolist() == direita["linha_tabela"].tolist()))
        # Bloco de Joinville: da linha "JOINVILLE" até a próxima linha com outro município.
        bloco = []
        for _, linha in esquerda.loc[inicio.name:].iterrows():
            if linha.name != inicio.name and linha["celula_01"] != "":
                break
            bloco.append(linha)
        verificacoes.append((nome, "9 categorias no bloco de Joinville", len(bloco) == 9 and all(l["celula_02"] in CATEGORIAS_VD for l in bloco)))
        for linha_esq in bloco:
            linha_dir = direita.loc[direita["linha_tabela"].eq(linha_esq["linha_tabela"])].iloc[0]
            for pagina, linha, meses, primeira in ((pagina_esq, linha_esq, meses_esq, 3), (pagina_dir, linha_dir, meses_dir, 1)):
                # Conferência: a linha do CSV é igual à linha da tabela do PDF.
                no_pdf = linha_da_tabela_no_pdf(nome, pagina, int(linha["tabela_pdf"]), int(linha["linha_tabela"]))
                verificacoes.append((nome, f"CSV = PDF na p.{pagina}, linha {linha['linha_tabela']}", _celulas(linha)[:len(no_pdf)] == no_pdf))
                for posicao, mes in enumerate(meses):
                    coluna = f"celula_{posicao + primeira:02d}"
                    texto = linha[coluna]
                    if not (texto.isascii() and texto.isdigit()):
                        raise ValueError(f"{nome}: valor não numérico na p.{pagina}, {coluna}: {texto!r}")
                    registros.append({
                        "ano": int(ano), "mes": MESES.index(mes) + 1, "categoria": CATEGORIAS_VD[linha_esq["celula_02"]],
                        "rotulo_original": linha_esq["celula_02"], "fatos_comunicados": int(texto), "arquivo_pdf": nome,
                        "pagina_pdf": str(pagina), "tabela_pdf": linha["tabela_pdf"],
                        "linha_tabela": linha["linha_tabela"], "coluna_csv": coluna,
                    })
    vd = pd.DataFrame(registros)
    meses_por_ano = vd.groupby("ano")["mes"].apply(lambda m: sorted(set(m)))
    verificacoes += [
        ("violência doméstica", "216 células (9 categorias × 24 meses)", len(vd) == 216 and vd["categoria"].nunique() == 9),
        ("violência doméstica", "12 meses em cada ano", all(m == list(range(1, 13)) for m in meses_por_ano)),
        ("violência doméstica", "nenhuma célula repetida", not vd.duplicated(subset=["ano", "mes", "categoria"]).any()),
    ]
    return vd


def tratar_violencia_domestica(vd: pd.DataFrame) -> pd.DataFrame:
    """A extração no esquema comum do projeto (uma linha por categoria e mês), com a rastreabilidade de cada célula."""
    hashes = {nome: sha256_arquivo(PASTA_BRUTOS / "pdfs" / nome) for nome in vd["arquivo_pdf"].unique()}
    base = pd.DataFrame({
        "fonte": FONTE, "municipio": "JOINVILLE", "uf": "SC",
        "serie_id": "ssp_vd|" + vd["categoria"], "indicador": "Violência doméstica — " + vd["categoria"],
        "indicador_original": vd["rotulo_original"], "abrangencia": "município do fato",
        "ano": vd["ano"].astype("Int64"), "mes": vd["mes"].astype("Int64"), "periodicidade": "mensal",
        "unidade": UNIDADE_VD, "valor": vd["fatos_comunicados"].astype("Int64"),
        "arquivo_origem": vd["arquivo_pdf"], "pagina_pdf": vd["pagina_pdf"], "sha256_origem": vd["arquivo_pdf"].map(hashes),
        "situacao_validacao": SITUACAO_VD,
    })
    base["periodo_inicio"] = pd.to_datetime(dict(year=base["ano"], month=base["mes"], day=1)).dt.strftime("%Y-%m-%d")
    base["periodo_fim"] = (pd.to_datetime(base["periodo_inicio"]) + pd.offsets.MonthEnd(0)).dt.strftime("%Y-%m-%d")
    return base.sort_values(["ano", "mes", "indicador"], ignore_index=True)


# --------------------------------------------------------------------------------------------------- 3. homicídios
def edicao_do_boletim(nome_pdf: str) -> dict:
    """Ano e período da edição, lidos na página 1 do boletim (ex.: '2024: 01/01 - 31/01'), nunca no nome do arquivo."""
    texto = texto_pagina(nome_pdf, 1)
    ano = re.search(r"\b20\d{2}\b", texto).group()
    limite = re.search(r"PERÍODO\s*\((01/01\s*-\s*\d{2}/\d{2})\)", texto)
    return {"ano_edicao": ano, "edicao": f"{ano}: {limite.group(1) if limite else 'pendente'}"}


def extrair_homicidios(verificacoes: list | None = None) -> pd.DataFrame:
    """Todos os valores de vítimas de homicídio de Joinville publicados nos 42 boletins (um por coluna e edição).

    A tabela municipal tem 7 colunas de ano: as 3 primeiras são totais de anos completos e as 4 últimas, o acumulado do ano
    até a data indicada no texto da página ("NO PERÍODO (01/01 - dd/mm)"). Os anos são os publicados no cabeçalho; se não
    acompanharem a edição, a linha é marcada como "cabeçalho suspeito" (não é corrigida).
    """
    verificacoes = [] if verificacoes is None else verificacoes
    registros = []
    for pdf in sorted((PASTA_BRUTOS / "pdfs").glob("*.pdf")):
        if "VIOLENCIA-DOMESTICA" in pdf.name:
            continue
        nome, bruto = pdf.name, ler_csv_extraido(pdf.name)
        edicao = edicao_do_boletim(nome)
        celulas = [c for c in bruto.columns if c.startswith("celula_")]
        tem_titulo = bruto[celulas].apply(lambda c: c.str.contains("VÍTIMAS DE HOMICÍDIO NOS MUNICÍPIOS", regex=False)).any(axis=1).any()
        for _, linha in bruto.loc[bruto["celula_01"].eq("JOINVILLE")].iterrows():
            pagina = int(linha["pagina_pdf"])
            tabela = bruto.loc[bruto["pagina_pdf"].eq(linha["pagina_pdf"]) & bruto["tabela_pdf"].eq(linha["tabela_pdf"])]
            cabecalho = tabela.loc[tabela["celula_01"].str.contains("MUNICÍPIO", regex=False)]
            texto = texto_pagina(nome, pagina)
            if not tem_titulo or cabecalho.empty or "VÍTIMAS POR ANO" not in texto:
                continue  # outra tabela que cita Joinville (por exemplo, um ranking): não é a contagem municipal
            cabecalho = cabecalho.iloc[0]
            colunas_ano = [c for c in celulas if re.fullmatch(r"20\d{2}", cabecalho[c])]
            limite = re.search(r"NO PERÍODO\s*\(([^)]+)\)", texto)
            verificacoes.append((nome, "7 colunas de ano e período acumulado no texto", len(colunas_ano) == 7 and limite is not None))
            anos = [cabecalho[c] for c in colunas_ano]
            ano_ed = int(edicao["ano_edicao"])
            esperados = [str(a) for a in range(ano_ed - 3, ano_ed)] + [str(a) for a in range(ano_ed - 3, ano_ed + 1)]
            no_pdf = linha_da_tabela_no_pdf(nome, pagina, int(linha["tabela_pdf"]), int(linha["linha_tabela"]))
            verificacoes.append((nome, f"CSV = PDF na p.{pagina}, linha {linha['linha_tabela']}", _celulas(linha)[:len(no_pdf)] == no_pdf))
            for posicao, coluna in enumerate(colunas_ano):
                anual = posicao < 3
                registros.append({
                    "indicador_original": "Nº de vítimas de homicídio", "periodo_tipo": "ano completo" if anual else "período acumulado",
                    "ano_referencia": anos[posicao], "periodo_publicado": anos[posicao] if anual else limite.group(1),
                    "valor_publicado": linha[coluna], "edicao": edicao["edicao"], "arquivo_pdf": nome, "pagina_pdf": str(pagina),
                    "tabela_pdf": linha["tabela_pdf"], "linha_tabela": linha["linha_tabela"], "coluna_csv": coluna,
                    "cabecalho_suspeito": anos != esperados,
                })
    hom = pd.DataFrame(registros)
    verificacoes += [
        ("homicídios", "valores inteiros literais", hom["valor_publicado"].str.fullmatch(r"\d+").all()),
        ("homicídios", "uma edição por boletim (42)", hom["arquivo_pdf"].nunique() == 42),
        ("homicídios", "294 células únicas (7 por boletim)", len(hom) == 294
         and hom.groupby("arquivo_pdf").size().eq(7).all()
         and not hom.duplicated(["arquivo_pdf", "pagina_pdf", "tabela_pdf", "linha_tabela", "coluna_csv"]).any()),
    ]
    return hom


def agrupar_republicacoes(hom: pd.DataFrame) -> pd.DataFrame:
    """Grupos do mesmo número (tipo de período + ano + período) publicado em 2 ou mais edições, sem escolher uma versão.

    Classificação: "Sem divergência de valor" quando todas as edições concordam; "Possível problema de cabeçalho" quando só a
    edição com cabeçalho suspeito difere das demais; caso contrário, "Inconsistência ainda não explicada".
    """
    chave = ["periodo_tipo", "ano_referencia", "periodo_publicado"]
    grupos = []
    for valores_chave, grupo in hom.groupby(chave, sort=True):
        if len(grupo) < 2:
            continue
        divergente = grupo["valor_publicado"].nunique() > 1
        suspeita = grupo["cabecalho_suspeito"].any()
        if not divergente:
            classe = "Sem divergência de valor"
        elif suspeita and grupo.loc[~grupo["cabecalho_suspeito"], "valor_publicado"].nunique() == 1:
            classe = "Possível problema de cabeçalho"
        else:
            classe = "Inconsistência ainda não explicada"
        explicacoes = {
            "Sem divergência de valor": "Republicações literais concordantes; não representam observações independentes.",
            "Possível problema de cabeçalho": "Diferença restrita à edição jan/2025, cujo cabeçalho municipal não acompanha a edição; causa definitiva pendente.",
            "Inconsistência ainda não explicada": "Não localizada nota documental que explique a mudança desta observação; não presumir revisão, erro ou mudança de cobertura.",
        }
        valores = [int(v) for v in grupo["valor_publicado"]]
        grupos.append({
            "grupo": f"G{len(grupos) + 1:02d}", "indicador": "Nº de vítimas de homicídio", "municipio": "JOINVILLE", "unidade": "vítimas",
            **dict(zip(chave, valores_chave)), "quantidade_edicoes": len(grupo), "divergente": divergente,
            "valores_publicados_distintos": tuple(sorted(set(grupo["valor_publicado"]), key=int)),
            "amplitude_entre_versoes": max(valores) - min(valores), "classificacao": classe,
            "inclui_edicao_com_cabecalho_suspeito": bool(suspeita),
            "situacao": "pendente de validação" if divergente else "concordante, sem escolha definitiva",
            "explicacao_documental": explicacoes[classe],
        })
    return pd.DataFrame(grupos)


def tratar_homicidios(hom: pd.DataFrame, grupos: pd.DataFrame) -> pd.DataFrame:
    """Uma linha por valor publicado (294), com o grupo de republicação anexado por JOIN muitos-para-um (cardinalidade conferida)."""
    chave = ["periodo_tipo", "ano_referencia", "periodo_publicado"]
    unido = hom.merge(grupos[chave + ["grupo", "divergente", "situacao"]], on=chave, how="left", validate="many_to_one")
    if len(unido) != len(hom):
        raise ValueError("O JOIN com os grupos de republicação mudou a quantidade de linhas.")
    return pd.DataFrame({
        "fonte": FONTE, "municipio": "JOINVILLE", "uf": "SC", "indicador": "Vítimas de homicídio",
        "indicador_original": unido["indicador_original"], "periodo_tipo": unido["periodo_tipo"], "ano_referencia": unido["ano_referencia"],
        "periodo_publicado": unido["periodo_publicado"], "unidade": "vítimas", "valor_publicado": unido["valor_publicado"],
        "edicao": unido["edicao"], "arquivo_origem": unido["arquivo_pdf"], "pagina_pdf": unido["pagina_pdf"],
        "grupo_republicacao": unido["grupo"], "grupo_divergente": unido["divergente"],
        "situacao_validacao": unido["situacao"].fillna("publicado uma única vez, sem confirmação de versão definitiva"),
    })


# ---------------------------------------------------------------------------------------------------- 4. gráfico
def figura_violencia_domestica(vd: pd.DataFrame):
    """Fatos comunicados por categoria, 2023 × 2024 (barras horizontais lado a lado; cada categoria comparada só consigo mesma).

    A soma é feita dentro de cada categoria e ano (12 meses publicados). Categorias não são somadas entre si.
    """
    from matplotlib.figure import Figure

    tabela = vd.groupby(["categoria", "ano"])["fatos_comunicados"].sum().unstack("ano").sort_values(2024)
    figura = Figure(figsize=(10, 6.4), dpi=120)
    figura.subplots_adjust(left=0.34, right=0.95, top=0.80, bottom=0.17)
    eixo = figura.add_subplot(111)
    posicoes = range(len(tabela))
    for deslocamento, ano, cor in ((-0.2, 2023, "#9FB7D3"), (0.2, 2024, "#2563A6")):
        barras = eixo.barh([p + deslocamento for p in posicoes], tabela[ano], height=0.38, color=cor, label=str(ano))
        eixo.bar_label(barras, labels=[f"{int(v):,}".replace(",", ".") for v in tabela[ano]], padding=3, fontsize=9)
    eixo.set_yticks(list(posicoes), tabela.index)
    eixo.set_xlabel("Fatos comunicados no ano (soma dos 12 meses publicados)", fontsize=10)
    eixo.spines[["top", "right"]].set_visible(False)
    eixo.grid(axis="x", color="#E3E8EF", linewidth=0.8)
    eixo.set_axisbelow(True)
    eixo.set_xlim(0, tabela.max().max() * 1.15)
    eixo.legend(loc="lower right", frameon=False, fontsize=10)
    figura.suptitle("Violência doméstica em Joinville/SC — fatos comunicados por categoria", x=0.04, y=0.97, ha="left", fontsize=14, fontweight="semibold")
    figura.text(0.04, 0.905, "Anos completos de 2023 e 2024 · cada categoria é comparada só consigo mesma; categorias não são somadas", fontsize=10, color="#444444")
    figura.text(0.04, 0.865, "Unidade: Fato Comunicado — definição em validação (não equivale a vítimas, pessoas ou ocorrências únicas)",
                fontsize=10, color="#9A3412")
    figura.text(0.04, 0.035, "Fonte: SSP/SC — Segurança em Números, relatórios de violência doméstica (1º e 2º semestres de 2023; 2024).\n"
                "Análise exploratória; não integra o painel.", fontsize=8.5, color="#555555")
    return figura


# ------------------------------------------------------------------------------------------------ 5. exportação
def processar() -> dict:
    """Executa o fluxo completo em memória e devolve as tabelas e o resumo (nada é gravado)."""
    if not acervo_disponivel():
        raise FileNotFoundError("Acervo SSP/SC incompleto: são esperados 45 PDFs e 45 CSVs em dados/brutos/ssp_sc/.")
    verificacoes: list = []
    inventario = inventariar_acervo()
    vd_extraida = extrair_violencia_domestica(verificacoes)
    hom = extrair_homicidios(verificacoes)
    grupos = agrupar_republicacoes(hom)
    vd, versoes = tratar_violencia_domestica(vd_extraida), tratar_homicidios(hom, grupos)
    tabela_verificacoes = pd.DataFrame(verificacoes, columns=["documento", "verificacao", "ok"])
    if not tabela_verificacoes["ok"].all():
        falhas = tabela_verificacoes.loc[~tabela_verificacoes["ok"]]
        raise ValueError(f"Verificações da extração SSP/SC falharam:\n{falhas.to_string(index=False)}")
    resumo = {
        "pdfs": int(len(inventario)), "csvs_extraidos": int(inventario["par_completo"].sum()), "pdfs_duplicados": int(inventario["pdf_duplicado"].sum()),
        "violencia_domestica": {"linhas": int(len(vd)), "categorias": int(vd["indicador"].nunique()),
                                "meses": int(vd[["ano", "mes"]].drop_duplicates().shape[0]),
                                "periodo": f"{vd['periodo_inicio'].min()} a {vd['periodo_fim'].max()}",
                                "zeros_publicados": int(vd["valor"].eq(0).sum()), "ausentes": int(vd["valor"].isna().sum())},
        "homicidios": {"valores_publicados": int(len(versoes)), "edicoes": int(versoes["edicao"].nunique()),
                       "grupos_republicados": int(len(grupos)), "grupos_divergentes": int(grupos["divergente"].sum()),
                       "grupos_concordantes": int((~grupos["divergente"]).sum()),
                       "classificacao": grupos["classificacao"].value_counts().to_dict()},
        "verificacoes_aprovadas": f"{int(tabela_verificacoes['ok'].sum())} de {len(tabela_verificacoes)}",
    }
    coordenadas = ["arquivo_pdf", "pagina_pdf", "tabela_pdf", "linha_tabela", "coluna_csv"]
    rastreabilidade = pd.concat([
        vd_extraida[coordenadas].assign(conjunto="violência doméstica", valor_publicado=vd_extraida["fatos_comunicados"].astype(str)),
        hom[coordenadas].assign(conjunto="homicídios", valor_publicado=hom["valor_publicado"]),
    ], ignore_index=True)
    rastreabilidade["sha256_pdf"] = rastreabilidade["arquivo_pdf"].map(inventario.set_index("arquivo_pdf")["sha256_pdf"])
    return {"inventario": inventario, "vd_extraida": vd_extraida, "vd": vd, "versoes": versoes, "grupos": grupos,
            "rastreabilidade": rastreabilidade,
            "verificacoes": tabela_verificacoes, "resumo": resumo}


def exportar(pasta: Path = PASTA_PROCESSADOS, pasta_graficos: Path | None = PASTA_GRAFICOS) -> dict:
    """Grava as bases tratadas em ``dados/processados/ssp_sc/`` e o gráfico em ``documentacao/graficos/analises/``.

    Os arquivos brutos são conferidos por SHA-256 antes e depois. Retorno: o resumo usado no README e nos testes.
    """
    hashes_antes = {p: sha256_arquivo(p) for p in sorted(PASTA_BRUTOS.rglob("*")) if p.is_file()}
    resultado = processar()
    pasta.mkdir(parents=True, exist_ok=True)
    grupos = resultado["grupos"].astype({"valores_publicados_distintos": str})
    arquivos = {
        "inventario_acervo_ssp_sc.csv": resultado["inventario"],
        "violencia_domestica_joinville_tratada.csv": resultado["vd"],
        "homicidios_boletins_joinville_versoes.csv": resultado["versoes"],
        "homicidios_republicacoes_grupos.csv": grupos,
        "verificacoes_extracao_ssp_sc.csv": resultado["verificacoes"],
        "rastreabilidade_celulas_ssp_sc.csv": resultado["rastreabilidade"],
    }
    for nome, tabela in arquivos.items():
        tabela.to_csv(pasta / nome, index=False, encoding="utf-8", lineterminator="\n")
    if pasta_graficos is not None:
        pasta_graficos.mkdir(parents=True, exist_ok=True)
        figura_violencia_domestica(resultado["vd_extraida"]).savefig(pasta_graficos / "07-sspsc_violencia_domestica_2023_2024.png")
    if {p: sha256_arquivo(p) for p in hashes_antes} != hashes_antes:
        raise RuntimeError("Um arquivo bruto da SSP/SC mudou durante o processamento.")
    resumo = {**resultado["resumo"], "originais_inalterados": True, "arquivos_gerados": sorted(arquivos)}
    (pasta / "relatorio_auditoria_ssp_sc.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumo


if __name__ == "__main__":
    print(json.dumps(exportar(), ensure_ascii=False, indent=2))
