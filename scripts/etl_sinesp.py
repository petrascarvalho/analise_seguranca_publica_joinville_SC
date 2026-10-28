"""ETL e análise dos indicadores do Sinesp/MJSP para Joinville/SC (2020–2026).

Este é o roteiro principal do projeto. Ele mostra, passo a passo, como os arquivos oficiais do Sinesp são lidos, tratados,
validados, analisados e transformados nas tabelas usadas pelo painel Streamlit.

Como executar (a partir da pasta do projeto, com o ambiente virtual criado):
    • No VS Code: abra este arquivo e use "Run Cell" em cada célula "# %%" (Python Interactive).
    • No terminal:  .\\.venv\\Scripts\\python.exe -m scripts.etl_sinesp

Fonte única: base nacional dos gestores estaduais (Sinesp VDE / MJSP), um arquivo XLSX por ano (bancovde-ANO.xlsx).
Os XLSX ficam em dados/brutos/sinesp/ (fora do Git). Sem eles, o roteiro roda em MODO DEMONSTRAÇÃO, usando a base já
publicada no painel, e avisa que isso não reproduz a extração.

O ETL grava somente em dados/processados/sinesp/. A base publicada no painel (dashboard/data_publica/) NUNCA é alterada
por este roteiro: ela só muda pelo fluxo controlado verificar → preparar → aprovar (src/pipeline/atualizacao_dados.py).

O trabalho anterior com SSP/SC e Prefeitura é histórico e fica em historico/scripts/analise_seguranca_publica.py (fora do escopo).
"""

# %% [markdown]
# # ETAPA 01 — Importação das bibliotecas
# **Objetivo:** carregar as ferramentas usadas no roteiro.
# - `pandas` organiza os dados em tabelas (DataFrames) e faz somas, agrupamentos e estatísticas.
# - `hashlib` calcula o SHA-256, uma "impressão digital" do arquivo que mostra se ele mudou.
# - `pathlib.Path` monta caminhos de pastas que funcionam em Windows e Linux.
# - Os módulos `dashboard.*` e `src.*` são do próprio projeto: as mesmas funções validadas que o painel usa.
#
# **Resultado esperado:** a versão do pandas impressa, sem erros de importação.

# %%
import hashlib
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from dashboard import calculos, graficos
from dashboard import dados_publicos as dp
from src.pipeline import atualizacao_dados as au
from src.pipeline import versionamento_dados as vv
from src.pipeline.utils import project_path

# Faz o terminal do Windows mostrar acentos corretamente.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Deixa as tabelas impressas mais largas, para caberem todas as colunas.
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

print(f"Pandas {pd.__version__}")


def mostrar(objeto):
    """Mostra uma tabela ou figura.

    Parâmetros: objeto — DataFrame, Series ou figura do Matplotlib.
    Retorno: nenhum. No VS Code Interactive aparece formatado; no terminal, é impresso como texto.
    """
    try:
        from IPython.display import display
        display(objeto)
    except ImportError:
        print(objeto)


# %% [markdown]
# # ETAPA 02 — Configuração dos diretórios e caminhos
# **Objetivo:** definir onde estão os dados brutos, onde o ETL grava os resultados e qual série será estudada.
# - `ANOS_SINESP`: anos dos arquivos oficiais (2020 a 2026).
# - `PASTA_BRUTOS`: XLSX originais (podem ser trocados pela variável de ambiente `SINESP_PASTA_XLSX`).
# - `PASTA_PROCESSADOS`: saídas do ETL (variável `SINESP_PASTA_PROCESSADOS`).
# - `INDICADOR_SELECIONADO` / `ABRANGENCIA_SELECIONADA`: série estudada nas etapas 14 a 16 (variáveis `SINESP_EVENTO_ESTUDO` e
#   `SINESP_ABRANGENCIA_ESTUDO`). Troque e execute de novo para estudar outra série.
#
# **Resultado esperado:** os caminhos impressos.

# %%
ANOS_SINESP = list(range(2020, 2027))
PASTA_BRUTOS = Path(os.environ.get("SINESP_PASTA_XLSX", project_path("dados", "brutos", "sinesp")))
PASTA_PROCESSADOS = Path(os.environ.get("SINESP_PASTA_PROCESSADOS", project_path("dados", "processados", "sinesp")))
INDICADOR_SELECIONADO = os.environ.get("SINESP_EVENTO_ESTUDO", "Homicídio doloso")
ABRANGENCIA_SELECIONADA = os.environ.get("SINESP_ABRANGENCIA_ESTUDO", "Estadual")

print(f"Dados brutos:       {PASTA_BRUTOS}")
print(f"Dados processados:  {PASTA_PROCESSADOS}")
print(f"Base publicada:     {dp.DIRETORIO_DADOS} (somente leitura neste roteiro)")
print(f"Série de estudo:    {INDICADOR_SELECIONADO} | {ABRANGENCIA_SELECIONADA}")

# %% [markdown]
# # ETAPA 03 — Localização dos arquivos originais
# **Objetivo:** encontrar um `bancovde-ANO.xlsx` para cada ano e conferir se é a mesma edição usada na base aprovada.
#
# O manifesto da base publicada guarda o SHA-256 de cada XLSX oficial. Se houver mais de uma edição do mesmo ano na pasta
# (por exemplo, a auditada em agosto/2026 e a republicada em outubro/2026), o roteiro escolhe a que tem o hash registrado.
#
# **Resultado esperado:** uma tabela com os sete anos e a situação de cada arquivo. Se faltar algum ano, o roteiro segue em
# MODO DEMONSTRAÇÃO.

# %%
manifesto = dp.carregar_manifesto()
hashes_aprovados = manifesto["origem_dos_dados"]["sinesp_xlsx_sha256"]


def sha256_arquivo(caminho: Path) -> str:
    """Calcula o SHA-256 de um arquivo, lendo-o em blocos de 1 MB (não carrega 24 MB de uma vez na memória).

    Parâmetros: caminho — arquivo a conferir.
    Retorno: o hash em texto hexadecimal (64 caracteres).
    """
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def localizar_xlsx(pasta: Path, ano: int) -> tuple[Path | None, str]:
    """Procura o arquivo oficial de um ano.

    Parâmetros: pasta — onde procurar (inclui subpastas); ano — ano do arquivo.
    Retorno: (caminho ou None, situação em texto). Com mais de um candidato, escolhe o de hash igual ao do manifesto.
    """
    candidatos = sorted(pasta.rglob(f"bancovde-{ano}.xlsx")) if pasta.is_dir() else []
    if not candidatos:
        return None, "arquivo não encontrado"
    for caminho in candidatos:
        if sha256_arquivo(caminho) == hashes_aprovados.get(str(ano)):
            return caminho, "hash igual ao da versão aprovada"
    if len(candidatos) == 1:
        return candidatos[0], "ATENÇÃO: hash diferente do registrado (outra edição do arquivo)"
    return None, f"{len(candidatos)} arquivos sem o hash aprovado: ambiguidade"


arquivos_localizados = {ano: localizar_xlsx(PASTA_BRUTOS, ano) for ano in ANOS_SINESP}
inventario_arquivos = pd.DataFrame([
    {"ano": ano, "arquivo": caminho.relative_to(PASTA_BRUTOS).as_posix() if caminho else "—",
     "tamanho_MB": round(caminho.stat().st_size / 1e6, 1) if caminho else None, "situação": situacao}
    for ano, (caminho, situacao) in arquivos_localizados.items()])
mostrar(inventario_arquivos)

# Se algum ano não foi encontrado, não há como reproduzir a extração: o roteiro usa a base publicada (dado derivado).
MODO_DEMONSTRACAO = any(caminho is None for caminho, _ in arquivos_localizados.values())
if MODO_DEMONSTRACAO:
    print("\nMODO DEMONSTRAÇÃO: os XLSX oficiais não estão completos neste ambiente. As etapas de leitura e ETL são puladas e a")
    print("análise usa a base JÁ PUBLICADA (dados derivados, não brutos). Isso NÃO reproduz a extração a partir dos originais.")

# %% [markdown]
# # ETAPA 04 — Leitura dos XLSX
# **Objetivo:** ler os arquivos oficiais e guardar, para cada ano, as linhas de Joinville/SC.
#
# Cada XLSX nacional tem cerca de 24 MB. Em vez de `pd.read_excel()` (que carregaria o país inteiro e levaria minutos), a função
# validada `ler_sinesp_xlsx` percorre o XML da planilha e mantém só as linhas com UF `SC` e município `JOINVILLE`. Ela também
# recusa o arquivo se as 14 colunas oficiais mudarem de nome ou de ordem.
#
# **Resultado esperado:** 911 linhas de Joinville/SC no total (132 por ano em 2020–2024, 144 em 2025 e 107 em 2026).

# %%
recortes_por_ano = {}
if not MODO_DEMONSTRACAO:
    for ano, (caminho, _) in arquivos_localizados.items():
        # Lê o XLSX do ano e devolve um DataFrame só com as linhas de Joinville/SC (14 colunas originais, sem alteração).
        recortes_por_ano[ano] = au.ler_sinesp_xlsx(caminho)
    linhas_por_ano = pd.DataFrame({"linhas Joinville": {ano: len(tabela) for ano, tabela in recortes_por_ano.items()}})
    mostrar(linhas_por_ano)
    print(f"Total de linhas originais de Joinville/SC lidas: {sum(len(t) for t in recortes_por_ano.values())}")

# %% [markdown]
# # ETAPA 05 — Inspeção dos dados brutos
# **Objetivo:** olhar os dados como vieram da fonte, antes de qualquer tratamento.
# - `pd.concat()` empilha as tabelas dos sete anos em uma só.
# - `head()` mostra as primeiras linhas; `info()` mostra colunas, tipos e quantidade de valores preenchidos.
#
# **Resultado esperado:** 911 linhas × 14 colunas; a data de referência aparece como número (serial do Excel).

# %%
if not MODO_DEMONSTRACAO:
    # Junta os sete anos em uma única tabela; ignore_index=True renumera as linhas de 0 a 910.
    dados_brutos = pd.concat(recortes_por_ano.values(), ignore_index=True)
    print(f"Dados brutos de Joinville: {dados_brutos.shape[0]} linhas × {dados_brutos.shape[1]} colunas")
    mostrar(dados_brutos.head())
    dados_brutos.info()

# %% [markdown]
# # ETAPA 06 — Identificação e descrição das colunas
# **Objetivo:** saber o que cada coluna significa e quais trazem informação.
# - `total_vitima` é a medida dos indicadores de vítimas; `total` é a medida dos mandados de prisão cumpridos.
# - Agente, arma, faixa etária e peso existem no arquivo, mas estão vazios em todo o recorte de Joinville.
#
# **Resultado esperado:** um dicionário de campos e a lista dos 11 eventos e 3 abrangências publicados para Joinville.

# %%
DICIONARIO_CAMPOS = pd.DataFrame([
    ("uf", "Unidade da federação (filtro: SC)"), ("municipio", "Município (filtro: JOINVILLE)"),
    ("evento", "Indicador publicado (ex.: Homicídio doloso)"), ("data_referencia", "Competência, em número serial do Excel (dia 1 do mês)"),
    ("agente", "Agente (vazio em todo o recorte)"), ("arma", "Arma (vazio em todo o recorte)"), ("faixa_etaria", "Faixa etária (vazio em todo o recorte)"),
    ("feminino", "Vítimas do sexo feminino"), ("masculino", "Vítimas do sexo masculino"), ("nao_informado", "Vítimas com sexo não informado"),
    ("total_vitima", "Total de vítimas (medida dos indicadores de vítimas)"), ("total", "Total de mandados cumpridos (medida dos mandados)"),
    ("total_peso", "Peso (vazio em todo o recorte)"), ("abrangencia", "Estadual, Polícia Federal ou Polícia Rodoviária Federal"),
], columns=["campo", "significado"])
mostrar(DICIONARIO_CAMPOS)

if not MODO_DEMONSTRACAO:
    # unique() lista os valores distintos de uma coluna; sorted() coloca em ordem alfabética.
    print("Eventos publicados para Joinville:", sorted(dados_brutos["evento"].unique()))
    print("Abrangências:", sorted(dados_brutos["abrangencia"].unique()))

# %% [markdown]
# # ETAPA 07 — Verificação de duplicidades
# **Objetivo:** descobrir se há linhas repetidas antes de qualquer agregação.
# - `duplicated()` marca as linhas idênticas a outra anterior (todas as colunas).
# - Também conferimos a chave da observação: evento + abrangência + competência.
#
# **Decisão:** nenhuma linha é apagada com `drop_duplicates()`. A nota metodológica oficial do Sinesp diz que *Tentativa de homicídio* e
# *Estupro* podem vir em mais de uma linha no mesmo mês como **parcelas** (que devem ser somadas, etapa 12). Em qualquer outro indicador,
# repetição interrompe o processo.
#
# **Resultado esperado:** zero linhas idênticas e zero repetições de chave na edição atual.

# %%
if not MODO_DEMONSTRACAO:
    linhas_identicas = int(dados_brutos.duplicated().sum())
    chave_observacao = ["evento", "abrangencia", "data_referencia"]
    repeticoes_de_chave = int(dados_brutos.duplicated(subset=chave_observacao, keep=False).sum())
    print(f"Linhas totalmente idênticas: {linhas_identicas}")
    print(f"Linhas que repetem evento + abrangência + competência: {repeticoes_de_chave}")

# %% [markdown]
# # ETAPA 08 — Tratamento e padronização dos dados
# **Objetivo:** transformar cada linha original em uma observação padronizada: `ano`, `mes`, `evento`, `abrangencia`, `unidade`, `valor`.
# 1. **Data:** o serial do Excel conta dias a partir de 30/12/1899. Ele precisa ser inteiro, cair no dia 1 e no ano do arquivo.
# 2. **Medida:** vítimas vêm de `total_vitima`; mandados, de `total`. São unidades diferentes e nunca são somadas.
# 3. **Valor:** inteiro não negativo, ou ausente (`<NA>`). Nada é preenchido.
#
# **Resultado esperado:** uma tabela de 911 observações com 6 colunas.

# %%
def serial_para_data(serial, ano_do_arquivo: int) -> pd.Timestamp:
    """Converte o número serial do Excel em data e confere se é o 1º dia de um mês do ano do arquivo.

    Parâmetros: serial — número da célula data_referencia; ano_do_arquivo — ano do XLSX lido.
    Retorno: a data (pd.Timestamp). Levanta erro se o serial não for inteiro ou cair fora do ano/dia esperado.
    """
    if isinstance(serial, bool) or not isinstance(serial, (int, float)) or float(serial) != int(serial):
        raise ValueError(f"Serial de data inválido: {serial!r}")
    data = pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(serial))
    if data.day != 1 or data.year != ano_do_arquivo:
        raise ValueError(f"Competência inesperada ({data.date()}) no arquivo de {ano_do_arquivo}")
    return data


def valor_inteiro(valor):
    """Confere a contagem publicada.

    Parâmetros: valor — número lido da planilha (ou vazio).
    Retorno: inteiro não negativo, ou pd.NA se a célula estiver vazia (ausência NÃO vira zero).
    """
    if pd.isna(valor):
        return pd.NA
    if float(valor) != int(valor) or valor < 0:
        raise ValueError(f"Valor inválido (esperado inteiro não negativo): {valor!r}")
    return int(valor)


def transformar_recorte(recorte: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Transforma as linhas originais de um ano em observações padronizadas.

    Parâmetros: recorte — linhas de Joinville de um XLSX; ano — ano do arquivo.
    Retorno: DataFrame com ano, mes, evento, abrangencia, unidade e valor.
    """
    observacoes = []
    for linha in recorte.itertuples(index=False):
        # Um evento fora da lista oficial exige decisão metodológica antes de entrar na base.
        if linha.evento not in vv.NATUREZAS:
            raise ValueError(f"Indicador não previsto: {linha.evento!r}")
        if pd.isna(linha.abrangencia):
            raise ValueError("Abrangência ausente")
        data = serial_para_data(linha.data_referencia, ano)
        eh_mandado = linha.evento == vv.EVENTO_MANDADO
        observacoes.append({
            "ano": data.year, "mes": data.month, "evento": linha.evento, "abrangencia": str(linha.abrangencia),
            "unidade": vv.UNIDADE_MANDADOS if eh_mandado else vv.UNIDADE_VITIMAS,
            "valor": valor_inteiro(linha.total if eh_mandado else linha.total_vitima)})
    return pd.DataFrame(observacoes)


if not MODO_DEMONSTRACAO:
    dados_tratados = pd.concat([transformar_recorte(recortes_por_ano[ano], ano) for ano in ANOS_SINESP], ignore_index=True)
    print(f"Observações padronizadas: {len(dados_tratados)}")
    mostrar(dados_tratados.head(8))

# %% [markdown]
# # ETAPA 09 — Identificação de valores ausentes e zeros
# **Objetivo:** separar duas coisas que parecem iguais, mas não são:
# - **zero publicado** — a fonte informou 0 vítimas no mês (é uma observação válida);
# - **valor ausente** — a fonte não informou nada (`<NA>`); nunca é trocado por zero.
# - `isna()` marca os ausentes; `eq(0)` marca os zeros.
#
# **Resultado esperado:** 0 ausentes e 401 zeros publicados na base atual. Na camada original, os campos vazios de `total_vitima` e
# `total` refletem só a divisão entre vítimas e mandados (cada linha usa uma das duas medidas).

# %%
if not MODO_DEMONSTRACAO:
    ausencias_por_campo = dados_brutos.isna().sum().rename("ausências").to_frame()
    ausencias_por_campo["%"] = (ausencias_por_campo["ausências"] / len(dados_brutos) * 100).round(2)
    print("Campos vazios na camada original:")
    mostrar(ausencias_por_campo)
    print(f"Valores ausentes após o tratamento: {int(dados_tratados['valor'].isna().sum())}")
    print(f"Zeros publicados após o tratamento: {int(dados_tratados['valor'].eq(0).sum())}")

# %% [markdown]
# # ETAPA 10 — Seleção de Joinville/SC
# **Objetivo:** garantir que a base tem somente o município estudado.
#
# O filtro foi aplicado na leitura (etapa 04) para economizar memória: o arquivo nacional tem milhões de linhas. Aqui conferimos o
# resultado com `loc[]` e `eq()`: todas as linhas precisam ter UF `SC` e município `JOINVILLE`. Nenhum dado estadual é usado como se
# fosse de Joinville.
#
# **Resultado esperado:** "True" para as duas conferências.

# %%
if not MODO_DEMONSTRACAO:
    so_santa_catarina = bool(dados_brutos["uf"].eq("SC").all())
    so_joinville = bool(dados_brutos["municipio"].eq("JOINVILLE").all())
    print(f"Todas as linhas são de SC: {so_santa_catarina} | todas são de JOINVILLE: {so_joinville}")
    linhas_fora = dados_brutos.loc[~dados_brutos["municipio"].eq("JOINVILLE")]
    print(f"Linhas de outros municípios: {len(linhas_fora)}")

# %% [markdown]
# # ETAPA 11 — Ajustes dos tipos de dados
# **Objetivo:** usar o tipo certo em cada coluna.
# - `ano` e `mes`: inteiros (`int64`).
# - `valor`: `Int64` (com "I" maiúsculo), o inteiro do pandas que aceita ausência (`<NA>`). O `int64` comum não aceita ausência e
#   forçaria trocar vazio por algum número — o que seria inventar dado.
#
# **Resultado esperado:** a lista de tipos com `Int64` em `valor`.

# %%
if not MODO_DEMONSTRACAO:
    dados_tratados[["ano", "mes"]] = dados_tratados[["ano", "mes"]].astype("int64")
    dados_tratados["valor"] = dados_tratados["valor"].astype("Int64")
    mostrar(dados_tratados.dtypes.rename("tipo").to_frame())

# %% [markdown]
# # ETAPA 12 — Consolidação das observações mensais
# **Objetivo:** ter exatamente uma linha por série (evento × abrangência) e mês.
# - `groupby()` junta as linhas com a mesma chave e `agg()` soma os valores — **somente** em *Tentativa de homicídio* e *Estupro*,
#   como manda a nota oficial; em outro indicador, repetição é erro.
# - `sum(min_count=1)` faz a soma devolver `<NA>` quando todas as parcelas estão vazias (em vez de 0).
# - `sort_values()` ordena por evento, abrangência, ano e mês, a mesma ordem da base publicada.
#
# **Resultado esperado:** 911 observações (nenhuma linha repetida a somar na edição atual).

# %%
def somar_linhas_com_nota_oficial(observacoes: pd.DataFrame) -> pd.DataFrame:
    """Soma linhas repetidas na mesma competência apenas onde a nota oficial do Sinesp permite.

    Parâmetros: observacoes — tabela padronizada (etapa 08).
    Retorno: tabela com uma linha por evento, abrangência, ano e mês, nas colunas oficiais.
    """
    chave = ["evento", "abrangencia", "ano", "mes"]
    repetidas = observacoes[observacoes.duplicated(chave, keep=False)]
    nao_permitidos = set(repetidas["evento"]) - set(vv.EVENTOS_COM_LINHAS_MULTIPLAS)
    if nao_permitidos:
        raise ValueError(f"Repetição sem nota oficial em {sorted(nao_permitidos)}")
    print(f"Linhas repetidas somadas conforme a nota oficial: {len(repetidas)} (indicadores: {sorted(set(repetidas['evento']))})")
    somadas = observacoes.groupby(chave + ["unidade"], as_index=False, sort=False)["valor"].agg(lambda parcelas: parcelas.sum(min_count=1))
    return somadas[dp.COLUNAS_SINESP]  # o groupby muda a ordem das colunas; aqui ela volta à oficial


if not MODO_DEMONSTRACAO:
    dados_processados = somar_linhas_com_nota_oficial(dados_tratados)
    dados_processados = dados_processados.sort_values(["evento", "abrangencia", "ano", "mes"], kind="stable").reset_index(drop=True)
    dados_processados["valor"] = dados_processados["valor"].astype("Int64")
    dados_processados[["ano", "mes"]] = dados_processados[["ano", "mes"]].astype("int64")
    print(f"Base reconstruída: {dados_processados.shape[0]} observações × {dados_processados.shape[1]} colunas")

# %% [markdown]
# # ETAPA 13 — Validação e rastreabilidade
# **Objetivo:** provar que a base reconstruída é a mesma que foi aprovada e está publicada no painel.
# 1. Regras: colunas na ordem certa, sem competência repetida, meses consecutivos em cada série, uma unidade por série, valores válidos.
# 2. Igualdade com a base publicada (valores, tipos e ordem).
# 3. Rastreabilidade: o SHA-256 do CSV gerado **em memória** é o mesmo registrado no manifesto.
#
# **Resultado esperado:** todas as verificações "True". Em modo demonstração, valida-se a própria base publicada.

# %%
base_publicada = dp.carregar_sinesp()
catalogo_publicado = dp.carregar_catalogo_sinesp()
CHAVE = ["evento", "abrangencia", "ano", "mes"]


def validar_base(base: pd.DataFrame) -> pd.DataFrame:
    """Aplica as regras de qualidade à base mensal.

    Parâmetros: base — DataFrame com as 6 colunas oficiais.
    Retorno: tabela com cada verificação e se foi aprovada.
    """
    # Índice contínuo de meses (ano × 12 + mês) para conferir se cada série não pula meses.
    indice_mes = base["ano"] * 12 + base["mes"] - 1
    sem_lacuna = all(
        (indices.sort_values().diff().dropna() == 1).all()
        for _, indices in indice_mes.groupby([base["evento"], base["abrangencia"]]))
    verificacoes = {
        "colunas na ordem esperada": list(base.columns) == dp.COLUNAS_SINESP,
        "sem competência repetida": not base.duplicated(CHAVE).any(),
        "séries com meses consecutivos": sem_lacuna,
        "uma unidade por série": base.groupby(["evento", "abrangencia"])["unidade"].nunique().eq(1).all(),
        "valores inteiros não negativos (ou ausentes)": bool((base["valor"].dropna() >= 0).all()),
        "nenhum valor ausente convertido em zero (ausências preservadas)": int(base["valor"].isna().sum()) == int(base_publicada["valor"].isna().sum()),
    }
    return pd.DataFrame({"verificação": list(verificacoes), "aprovada": list(verificacoes.values())})


if MODO_DEMONSTRACAO:
    print("MODO DEMONSTRAÇÃO: validando a base publicada (não há reconstrução a conferir).")
    mostrar(validar_base(base_publicada))
    base_analitica = base_publicada.copy()
else:
    mostrar(validar_base(dados_processados))
    # to_csv sem caminho devolve o texto do CSV (nada é gravado); assim o hash é comparável ao do manifesto.
    csv_em_memoria = dados_processados.to_csv(index=False, lineterminator="\n", na_rep="").encode("utf-8")
    hash_gerado = dp.sha256_normalizado(csv_em_memoria)
    hash_aprovado = next(f["sha256"] for f in manifesto["arquivos"] if f["arquivo"] == dp.ARQ_SINESP)
    bases_iguais = dados_processados.astype(base_publicada.dtypes.to_dict()).equals(base_publicada)
    print(f"Base reconstruída igual à publicada (valores, tipos e ordem): {bases_iguais}")
    print(f"SHA-256 do CSV reconstruído = SHA-256 do manifesto: {hash_gerado == hash_aprovado}")
    assert bases_iguais and hash_gerado == hash_aprovado, "A reconstrução diverge dos dados aprovados: revisar antes de continuar."
    base_analitica = dados_processados


def montar_catalogo(base: pd.DataFrame) -> pd.DataFrame:
    """Resume cada série: início, fim, meses, meses com valor, zeros e ausências.

    Parâmetros: base — base mensal validada.
    Retorno: uma linha por evento × abrangência × unidade.
    """
    base = base.assign(competencia=base["ano"].astype(str) + "-" + base["mes"].astype(str).str.zfill(2))
    grupos = base.groupby(["evento", "abrangencia", "unidade"])
    catalogo = grupos.agg(inicio=("competencia", "min"), fim=("competencia", "max"), meses=("valor", "size"),
                          com_valor=("valor", "count"), zeros=("valor", lambda valores: int((valores == 0).sum()))).reset_index()
    catalogo["sem_valor"] = catalogo["meses"] - catalogo["com_valor"]
    return catalogo


catalogo = montar_catalogo(base_analitica)
mostrar(catalogo)
catalogo_confere = (catalogo[["evento", "abrangencia"]].reset_index(drop=True).equals(catalogo_publicado[["evento", "abrangencia"]].reset_index(drop=True))
                    and catalogo["meses"].tolist() == catalogo_publicado["meses_observados"].astype(int).tolist()
                    and catalogo["fim"].tolist() == catalogo_publicado["fim"].tolist())
print(f"Séries: {len(catalogo)} | observações: {len(base_analitica)} | catálogo confere com o publicado: {catalogo_confere}")
assert len(base_analitica) == len(base_publicada) and len(catalogo) == len(catalogo_publicado)

# %% [markdown]
# # ETAPA 14 — Estatísticas descritivas
# **Objetivo:** descrever os valores **mensais** de cada série.
# - `agg()` calcula de uma vez: quantidade de meses, soma, média (`mean`), mediana (`median`), mínimo, máximo e desvio-padrão (`std`).
# - O desvio-padrão usa `ddof=0` porque descreve os meses observados (não é uma amostra para inferência).
# - Quartis (`quantile`) e IQR ficam na função validada `calculos.quartis_iqr`.
#
# **Resultado esperado:** uma tabela por série; homicídio doloso (Estadual) com 81 meses, soma 318 e mediana 3.

# %%
estatisticas = (base_analitica.groupby(["evento", "abrangencia"])["valor"]
                .agg(meses="count", soma="sum", media="mean", mediana="median", minimo="min", maximo="max",
                     desvio_padrao=lambda valores: valores.astype("float64").std(ddof=0)).round(2))
mostrar(estatisticas)

serie_estudo = calculos.serie_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA)
unidade_estudo = serie_estudo["unidade"].iloc[0]
print(f"Série de estudo: {INDICADOR_SELECIONADO} | {ABRANGENCIA_SELECIONADA} | unidade: {unidade_estudo} | {len(serie_estudo)} meses")
quartis = calculos.quartis_iqr(serie_estudo["valor"])
print(f"Quartis da série de estudo: Q1 = {quartis['q1']}, mediana = {quartis['mediana']}, Q3 = {quartis['q3']}, IQR = {quartis['iqr']}")

# %% [markdown]
# # ETAPA 15 — Análise exploratória
# **Objetivo:** responder perguntas sobre a evolução dos indicadores, sem misturar períodos de tamanhos diferentes.
# 1. **Anos completos (2020–2025):** soma dos 12 meses de cada ano.
# 2. **Períodos equivalentes:** janeiro até o mesmo mês em todos os anos (jan–ago vale para todas as séries; jan–set, exceto a PRF).
#    2026 é parcial e só é comparado com o mesmo período dos anos anteriores.
# 3. **Grade ano × mês** e **distribuição** dos valores mensais (zero publicado como faixa própria).
# 4. **Pontos fora dos limites (IQR)**: só quando o método é informativo para a série.
# 5. **Perfil por mês do ano**: mediana de cada mês, usando somente anos completos.
#
# **Resultado esperado:** homicídio doloso 62 (2020) e 29 (2025) em anos completos; 21 (2025) e 25 (2026) em janeiro–setembro.

# %%
ultima_competencia = catalogo.set_index(["evento", "abrangencia"])["fim"]
print("Séries que terminam antes das demais:")
mostrar(ultima_competencia[ultima_competencia != ultima_competencia.max()].to_frame("termina em"))
print(f"Competência mais recente da base: {ultima_competencia.max()} | zeros publicados: {int((base_analitica['valor'] == 0).sum())} | "
      f"valores ausentes: {int(base_analitica['valor'].isna().sum())}")

anos_completos = base_analitica[base_analitica["ano"] <= 2025]  # 2020–2025: todas as séries têm 12 meses (a PF, só desde 2025)
totais_anuais = anos_completos.groupby(["evento", "abrangencia", "ano"])["valor"].sum().unstack("ano")
# Onde a série não existe no ano (PF antes de 2025), a soma daria 0; where() devolve <NA> para não confundir ausência com zero.
totais_anuais = totais_anuais.where(anos_completos.groupby(["evento", "abrangencia", "ano"])["valor"].count().unstack("ano").notna())
print("\nTotais por ano completo (vítimas; mandados em contagem publicada). '<NA>' = série sem cobertura no ano, não zero:")
mostrar(totais_anuais)


def periodo_equivalente(base: pd.DataFrame, mes_final: int) -> pd.DataFrame:
    """Soma janeiro até ``mes_final`` em cada ano, só nos anos que têm todos esses meses.

    Parâmetros: base — base mensal; mes_final — último mês do período (1 a 12).
    Retorno: tabela série × ano (vazia onde o período não está completo).
    """
    recorte = base[base["mes"] <= mes_final]
    meses_por_ano = recorte.groupby(["evento", "abrangencia", "ano"])["mes"].nunique().unstack("ano")
    somas = recorte.groupby(["evento", "abrangencia", "ano"])["valor"].sum().unstack("ano")
    return somas.where(meses_por_ano == mes_final)


janeiro_agosto = periodo_equivalente(base_analitica, 8)
janeiro_setembro = periodo_equivalente(base_analitica, 9)
print("Janeiro–agosto (oito meses em todos os anos):")
mostrar(janeiro_agosto)
print("Janeiro–setembro (nove meses; a PRF ainda não publicou setembro/2026):")
mostrar(janeiro_setembro)

print("\nGrade ano × mês da série de estudo (<NA> = mês ainda sem valor publicado, não zero) — é a tabela do mapa de calor:")
mostrar(calculos.quadro_ano_mes(serie_estudo))
distribuicao = calculos.distribuicao_frequencias(serie_estudo)
print("Distribuição dos valores mensais em faixas (zero publicado = faixa própria; regra de Sturges para as demais):")
mostrar(distribuicao)
assert int(distribuicao["n_meses"].sum()) == int(serie_estudo["valor"].count())

# %%
# Pontos fora dos limites de Tukey (Q1 − 1,5·IQR e Q3 + 1,5·IQR). Em contagens com muitos zeros ou IQR = 0 o método não é informativo.
print("Diagnóstico do método IQR em cada série (período completo):")
mostrar(calculos.diagnostico_outliers_todas_as_series(base_analitica))
diagnostico = calculos.diagnostico_outliers_iqr(serie_estudo)
print(f"\nSérie de estudo — {diagnostico['rotulo']}.")
print(diagnostico["mensagem"])
if diagnostico["interpretavel"]:
    print("Pontos fora dos limites (atípicos estatísticos, não anomalias comprovadas):")
    mostrar(diagnostico["fora"])
else:
    print("Nenhum ponto é apresentado como atípico: o método não é informativo para esta série.")

perfil_mensal = calculos.perfil_sazonal(serie_estudo)
print(f"\nPerfil por mês — anos completos usados: {perfil_mensal.attrs['anos_usados']} (n = {len(perfil_mensal.attrs['anos_usados'])})")
mostrar(perfil_mensal.round(2))


def variacao_entre_periodos(tabela: pd.DataFrame, ano_anterior: int, ano_atual: int) -> pd.DataFrame:
    """Diferença absoluta e percentual entre dois anos de uma tabela de períodos equivalentes.

    Parâmetros: tabela — saída de periodo_equivalente; ano_anterior, ano_atual — anos comparados.
    Retorno: tabela com os dois valores, a diferença e a variação % (só quando a base é positiva).
    """
    quadro = pd.DataFrame({ano_anterior: tabela[ano_anterior], ano_atual: tabela[ano_atual]}).dropna()
    quadro["diferença"] = quadro[ano_atual] - quadro[ano_anterior]
    quadro["variação %"] = (quadro["diferença"] / quadro[ano_anterior].where(quadro[ano_anterior] > 0) * 100).round(1)
    return quadro


print("Janeiro–setembro de 2026 × 2025 (percentual indefinido quando a base é zero; contagens pequenas variam muito):")
mostrar(variacao_entre_periodos(janeiro_setembro, 2025, 2026))

# %% [markdown]
# # ETAPA 16 — Construção dos gráficos
# **Objetivo:** visualizar os resultados com as mesmas funções do painel (`dashboard/graficos.py`), que usam Matplotlib
# (`bar()` para barras, `plot()` para linhas). Cada figura desenha exatamente a tabela calculada antes.
# - Visão geral: mapa de calor, períodos equivalentes e ranking.
# - Evolução temporal: barras anuais, barras mensais, média móvel e acumulado.
# - Estatística descritiva: boxplot, distribuição e perfil mensal (mediana).
# - Outliers: série mensal com os limites de Tukey.
#
# **Resultado esperado:** as figuras exibidas e duas conferências "True" (o desenhado é o que está na tabela).

# %%
mapa_calor = graficos.figura_mapa_calor_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA, ANOS_SINESP)
mostrar(mapa_calor)
mes_final_serie = calculos.mes_final_da_serie(serie_estudo)
mostrar(graficos.figura_periodo_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA, ANOS_SINESP, mes_final_serie))
ranking = calculos.ranking_por_unidade(base_analitica, 2025, unidade_estudo)  # séries da mesma unidade, ano completo 2025
mostrar(graficos.figura_ranking_sinesp(ranking, 2025, destaque=(INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA)))

mostrar(graficos.figura_serie_anual_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA, ANOS_SINESP))
mostrar(graficos.figura_mensal_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA, [2025, 2026]))
mostrar(graficos.figura_media_movel_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA, ANOS_SINESP))
mostrar(graficos.figura_acumulado_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA, ANOS_SINESP))

mostrar(graficos.figura_boxplot_anual_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA, ANOS_SINESP))
mostrar(graficos.figura_distribuicao_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA, ANOS_SINESP))
figura_perfil = graficos.figura_sazonalidade_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA, ANOS_SINESP)
if figura_perfil is None:
    print("Sazonalidade não apresentada: menos de 2 anos completos nesta série.")
else:
    mostrar(figura_perfil)

mostrar(graficos.figura_outliers_iqr_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA, ANOS_SINESP))
mostrar(graficos.figura_outliers_iqr_sinesp(base_analitica, "Roubo seguido de morte (latrocínio)", "Estadual", ANOS_SINESP))  # exemplo com IQR = 0

# %%
# Conferência: os números desenhados são os da tabela.
def numeros_do_mapa_de_calor(figura) -> list:
    """Lê os valores das células do mapa de calor (None = mês sem valor publicado).

    Parâmetros: figura — figura criada por figura_mapa_calor_sinesp.
    Retorno: lista de linhas (anos) com os valores de cada mês.
    """
    matriz = figura.axes[0].images[0].get_array()
    return [[None if matriz[i, j] is np.ma.masked else int(matriz[i, j]) for j in range(matriz.shape[1])] for i in range(matriz.shape[0])]


tabela_mapa = calculos.quadro_ano_mes(serie_estudo)
esperado_mapa = [[None if pd.isna(v) else int(v) for v in linha] for linha in tabela_mapa.to_numpy()]
print("Mapa de calor = tabela ano × mês:", numeros_do_mapa_de_calor(mapa_calor) == esperado_mapa)

linhas_media_movel = {linha.get_gid(): linha for linha in graficos.figura_media_movel_sinesp(base_analitica, INDICADOR_SELECIONADO, ABRANGENCIA_SELECIONADA, ANOS_SINESP).axes[0].lines}
tabela_media_movel = calculos.media_movel(serie_estudo)
desenhado = np.array(linhas_media_movel["media_movel"].get_ydata(), dtype="float64")
print("Média móvel desenhada = tabela:", bool(np.allclose(desenhado, tabela_media_movel["media_movel"].astype("float64").to_numpy(), equal_nan=True)))

# %% [markdown]
# # ETAPA 17 — Exportação controlada
# **Objetivo:** gravar os resultados do ETL para conferência e auditoria, **sem tocar na base publicada**.
# - `to_csv()` grava as tabelas em `dados/processados/sinesp/` (pasta local, fora do Git).
# - `etl_recorte_joinville_bruto.csv`: as linhas originais de Joinville (14 colunas, sem tratamento).
# - `etl_sinesp_joinville_mensal.csv`: a base analítica reconstruída (igual, byte a byte, à publicada).
# - `etl_catalogo_series.csv` e `etl_relatorio.json`: resumo das séries, hashes e resultado das conferências.
#
# A base do painel (`dashboard/data_publica/`) só muda pelo fluxo controlado de atualização, nunca por este roteiro.
#
# **Resultado esperado:** quatro arquivos gravados (ou aviso de que nada foi exportado em modo demonstração).

# %%
if MODO_DEMONSTRACAO:
    print("MODO DEMONSTRAÇÃO: nada é exportado (não houve extração a partir dos XLSX oficiais).")
else:
    PASTA_PROCESSADOS.mkdir(parents=True, exist_ok=True)
    assert PASTA_PROCESSADOS.resolve() != dp.DIRETORIO_DADOS.resolve(), "O ETL não pode gravar sobre a base publicada."
    dados_brutos.to_csv(PASTA_PROCESSADOS / "etl_recorte_joinville_bruto.csv", index=False, encoding="utf-8")
    (PASTA_PROCESSADOS / "etl_sinesp_joinville_mensal.csv").write_bytes(csv_em_memoria)  # mesmo conteúdo conferido na etapa 13
    catalogo.to_csv(PASTA_PROCESSADOS / "etl_catalogo_series.csv", index=False, encoding="utf-8")
    relatorio = {
        "observacoes": int(len(dados_processados)), "series": int(len(catalogo)), "zeros_publicados": int(dados_processados["valor"].eq(0).sum()),
        "valores_ausentes": int(dados_processados["valor"].isna().sum()), "competencia_final": str(ultima_competencia.max()),
        "sha256_base_mensal": hash_gerado, "igual_a_base_publicada": bool(bases_iguais), "versao_publicada": manifesto["versao"],
        "xlsx": {str(ano): {"arquivo": caminho.name, "sha256": sha256_arquivo(caminho)} for ano, (caminho, _) in arquivos_localizados.items()},
    }
    (PASTA_PROCESSADOS / "etl_relatorio.json").write_text(json.dumps(relatorio, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Arquivos exportados em {PASTA_PROCESSADOS}: etl_recorte_joinville_bruto.csv, etl_sinesp_joinville_mensal.csv, "
          "etl_catalogo_series.csv, etl_relatorio.json")

# %% [markdown]
# # ETAPA 18 — Conclusões e limitações
# **Objetivo:** resumir o que os dados mostram e o que eles NÃO permitem afirmar. Os números são calculados a partir das tabelas acima.

# %%
homicidio_anual = totais_anuais.loc[("Homicídio doloso", "Estadual")]
homicidio_jan_set = janeiro_setembro.loc[("Homicídio doloso", "Estadual")]
tentativa_jan_set = janeiro_setembro.loc[("Tentativa de homicídio", "Estadual")]
print("CONCLUSÕES (descritivas, sobre contagens publicadas):")
print(f"- Homicídio doloso em anos completos: {int(homicidio_anual[2020])} vítimas em 2020 e {int(homicidio_anual[2025])} em 2025.")
print(f"- Janeiro–setembro: homicídio doloso {int(homicidio_jan_set[2025])} (2025) e {int(homicidio_jan_set[2026])} (2026); "
      f"tentativa de homicídio {int(tentativa_jan_set[2025])} e {int(tentativa_jan_set[2026])}.")
print(f"- A base tem {len(base_analitica)} observações em {len(catalogo)} séries, de {base_analitica['ano'].min()}-01 até {ultima_competencia.max()}.")
diagnosticos = calculos.diagnostico_outliers_todas_as_series(base_analitica)
series_informativas = int(diagnosticos["classificacao"].eq("método informativo").sum())
print(f"- Critério IQR (Tukey): informativo em {series_informativas} das {len(diagnosticos)} séries; nas demais (IQR = 0, maioria de zeros, contagens muito baixas "
      "ou distribuição degenerada) nenhum ponto é apontado como atípico. Pontos fora dos limites são atípicos estatísticos, não anomalias comprovadas.")
anos_usados = perfil_mensal.attrs["anos_usados"]
if anos_usados:
    print(f"- Sazonalidade: calculada só com anos completos ({anos_usados[0]}–{anos_usados[-1]}, n = {len(anos_usados)}); "
          "2026 é parcial e fica de fora. Com tão poucos anos, o perfil mensal é exploratório e não demonstra sazonalidade.")
else:
    print("- Sazonalidade: a série de estudo não tem ano completo; perfil mensal não calculado.")
print("\nLIMITAÇÕES:")
print("- Registros administrativos agregados: não medem toda a criminalidade, não estimam subnotificação e não indicam causa.")
print("- Sem taxas populacionais, sem dados por bairro, rua, horário ou corporação; sem total geral entre indicadores ou abrangências.")
print("- 2026 é parcial; a PRF termina antes das demais séries; zeros publicados não provam ausência do fenômeno.")
print("- Contagens pequenas (feminicídio, latrocínio) geram percentuais instáveis: observe a diferença absoluta.")
print("- Furto, roubo, estupro e tráfico não existem no Sinesp de Joinville; fontes municipais divergem e não entram na base.")
print("- A fonte pode revisar valores históricos; a atualização controlada do painel detecta e bloqueia revisões não aprovadas.")
if MODO_DEMONSTRACAO:
    print("- ESTA EXECUÇÃO FOI EM MODO DEMONSTRAÇÃO: a base usada é a publicada, não a reconstruída a partir dos XLSX oficiais.")
