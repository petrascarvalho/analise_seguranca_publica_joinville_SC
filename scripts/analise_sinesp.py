"""Roteiro acadêmico do projeto: indicadores de segurança pública do Sinesp/MJSP em Joinville/SC (2020–2026).

Como usar no VS Code (abrir a PASTA do projeto):
    1. Abra este arquivo e execute cada célula com "Run Cell" (ou "Run All Cells") no Python Interactive.
    2. Ou execute tudo no terminal:  python -m scripts.analise_sinesp

Fonte única: base de dados nacional dos gestores estaduais (Sinesp VDE / MJSP), um XLSX por ano (``bancovde-ANO.xlsx``).
O roteiro lê os XLSX do acervo local (``dados/``, fora do Git), reconstrói a base analítica e confere o resultado com os dois
CSVs publicados no dashboard. Se os XLSX não estiverem disponíveis, entra em MODO DEMONSTRAÇÃO: usa a base publicada
(já derivada e aprovada) apenas para as etapas de análise, e avisa que isso NÃO reproduz a extração.

Nada é gravado em disco. O trabalho anterior com SSP/SC e Prefeitura é histórico e fica em
``scripts/analise_seguranca_publica.py`` (fora do escopo da entrega).
"""

# %% [markdown]
# # 1. Objetivo e bibliotecas
# **Pergunta analítica:** como evoluíram, desde janeiro/2020, os indicadores oficiais de segurança pública do
# Sinesp/MJSP para Joinville/SC, e o que a comparação entre períodos equivalentes permite — e não permite — afirmar?
#
# Etapas: leitura → campos → ETL → validação → base analítica → exploração → estatísticas → gráficos → conclusões.

# %%
import hashlib
import os
import sys
from pathlib import Path

import pandas as pd

from dashboard import calculos, graficos
from dashboard import dados_publicos as dp
from scripts import atualizacao_dados as au
from scripts import versionamento_dados as vv
from scripts.utils import project_path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")  # acentos legíveis também no terminal do Windows
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

ANOS = list(range(2020, 2027))
ACERVO_SINESP = Path(os.environ.get("SINESP_PASTA_XLSX", project_path("dados", "brutos", "sinesp")))
MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"]


def mostrar(objeto):
    """Mostra tabelas e figuras no Interactive Window; no terminal, imprime."""
    try:
        from IPython.display import display
        display(objeto)
    except ImportError:
        print(objeto)


print(f"Pandas {pd.__version__} | acervo procurado em: {ACERVO_SINESP}")

# %% [markdown]
# # 2. Leitura e inspeção dos dados originais
# Cada XLSX nacional tem ~24 MB. Para não carregar o país inteiro, a leitura percorre o XML da planilha e extrai apenas as
# linhas com UF `SC` e município `JOINVILLE` (função `ler_sinesp_xlsx`, que também recusa mudanças no esquema de 14 colunas).
# O SHA-256 de cada arquivo é comparado com o registrado no manifesto da versão aprovada.

# %%
manifesto = dp.carregar_manifesto()
hashes_aprovados = manifesto["origem_dos_dados"]["sinesp_xlsx_sha256"]


def sha256_arquivo(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def localizar_xlsx(pasta: Path, ano: int) -> tuple[Path | None, str]:
    """Procura bancovde-ANO.xlsx; havendo mais de um, escolhe o que tem o hash da versão aprovada."""
    candidatos = sorted(pasta.rglob(f"bancovde-{ano}.xlsx")) if pasta.is_dir() else []
    if not candidatos:
        return None, "arquivo não encontrado"
    for caminho in candidatos:
        if sha256_arquivo(caminho) == hashes_aprovados.get(str(ano)):
            return caminho, "hash igual ao da versão aprovada"
    if len(candidatos) == 1:
        return candidatos[0], "ATENÇÃO: hash diferente do registrado (outra edição do arquivo)"
    return None, f"{len(candidatos)} arquivos sem o hash aprovado: ambiguidade"


localizados = {ano: localizar_xlsx(ACERVO_SINESP, ano) for ano in ANOS}
inventario = pd.DataFrame([
    {"ano": ano, "arquivo": caminho.name if caminho else "—", "tamanho_MB": round(caminho.stat().st_size / 1e6, 1) if caminho else None, "situação": situacao}
    for ano, (caminho, situacao) in localizados.items()])
mostrar(inventario)

MODO_DEMONSTRACAO = any(caminho is None for caminho, _ in localizados.values())
if MODO_DEMONSTRACAO:
    print("\nMODO DEMONSTRAÇÃO: os XLSX oficiais não estão completos neste ambiente. As etapas de leitura e ETL são puladas e a")
    print("análise usa a base JÁ PUBLICADA (dados derivados, não brutos). Isso NÃO reproduz a extração a partir dos originais.")
else:
    recortes = {ano: au.ler_sinesp_xlsx(caminho) for ano, (caminho, _) in localizados.items()}
    resumo_leitura = pd.DataFrame({"linhas Joinville": {ano: len(q) for ano, q in recortes.items()}})
    mostrar(resumo_leitura)
    print(f"Total de linhas originais de Joinville/SC lidas: {sum(len(q) for q in recortes.values())}")
    mostrar(recortes[2026].head())

# %% [markdown]
# # 3. Identificação dos campos e do conteúdo original
# Os campos abaixo vêm do cabeçalho do XLSX. `total_vitima` conta vítimas; `total` é usado nos mandados cumpridos.
# Campos totalmente vazios (agente, arma, faixa etária, peso) existem no arquivo, mas não trazem informação.

# %%
DICIONARIO = pd.DataFrame([
    ("uf", "Unidade da federação (filtro: SC)"), ("municipio", "Município (filtro: JOINVILLE)"),
    ("evento", "Indicador publicado (ex.: Homicídio doloso)"), ("data_referencia", "Competência, em número serial do Excel (dia 1 do mês)"),
    ("agente", "Agente (vazio em todo o recorte)"), ("arma", "Arma (vazio em todo o recorte)"), ("faixa_etaria", "Faixa etária (vazio em todo o recorte)"),
    ("feminino", "Vítimas do sexo feminino"), ("masculino", "Vítimas do sexo masculino"), ("nao_informado", "Vítimas com sexo não informado"),
    ("total_vitima", "Total de vítimas (medida dos indicadores de vítimas)"), ("total", "Total de mandados cumpridos (medida dos mandados)"),
    ("total_peso", "Peso (vazio em todo o recorte)"), ("abrangencia", "Estadual, Polícia Federal ou Polícia Rodoviária Federal"),
], columns=["campo", "significado"])
mostrar(DICIONARIO)

if not MODO_DEMONSTRACAO:
    original = pd.concat(recortes.values(), ignore_index=True)
    ausencias = original.isna().sum().rename("ausências").to_frame()
    ausencias["%"] = (ausencias["ausências"] / len(original) * 100).round(2)
    print(f"Recorte original: {len(original)} linhas × {original.shape[1]} colunas")
    mostrar(ausencias)
    print("Eventos publicados para Joinville:", sorted(original["evento"].unique()))
    print("Abrangências:", sorted(original["abrangencia"].unique()))

# %% [markdown]
# # 4. ETL: seleção, tratamento e transformação
# Regras (as mesmas do fluxo de atualização do dashboard):
# 1. Seleção exata de `SC` / `JOINVILLE` (já feita na leitura).
# 2. **Data:** o serial do Excel é convertido com origem `1899-12-30`; deve ser um inteiro, cair no dia 1 e no ano do arquivo.
# 3. **Medida:** vítimas em `total_vitima`; mandados em `total`. Unidades distintas, nunca somadas.
# 4. **Ausência** é preservada (`<NA>`, nunca zero); **zero publicado** é uma observação e é mantido.
# 5. **Linhas repetidas** na mesma competência só são somadas em *Tentativa de homicídio* e *Estupro* (nota metodológica oficial);
#    em qualquer outro indicador a repetição interrompe o processo (sem deduplicação genérica).

# %%
def serial_para_data(serial, ano_do_arquivo: int) -> pd.Timestamp:
    """Converte o serial do Excel em data, validando inteiro, dia 1 e ano do arquivo."""
    if isinstance(serial, bool) or not isinstance(serial, (int, float)) or float(serial) != int(serial):
        raise ValueError(f"Serial de data inválido: {serial!r}")
    data = pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(serial))
    if data.day != 1 or data.year != ano_do_arquivo:
        raise ValueError(f"Competência inesperada ({data.date()}) no arquivo de {ano_do_arquivo}")
    return data


def valor_inteiro(valor):
    """Inteiro não negativo, ou <NA> se ausente; qualquer outra coisa é erro."""
    if pd.isna(valor):
        return pd.NA
    if float(valor) != int(valor) or valor < 0:
        raise ValueError(f"Valor inválido (esperado inteiro não negativo): {valor!r}")
    return int(valor)


def transformar_recorte(recorte: pd.DataFrame, ano: int) -> pd.DataFrame:
    """Uma linha do recorte original → uma observação (ano, mes, evento, abrangencia, unidade, valor)."""
    observacoes = []
    for linha in recorte.itertuples(index=False):
        if linha.evento not in vv.NATUREZAS:
            raise ValueError(f"Indicador não previsto: {linha.evento!r}")
        if pd.isna(linha.abrangencia):
            raise ValueError("Abrangência ausente")
        data = serial_para_data(linha.data_referencia, ano)
        mandado = linha.evento == vv.EVENTO_MANDADO
        observacoes.append({
            "ano": data.year, "mes": data.month, "evento": linha.evento, "abrangencia": str(linha.abrangencia),
            "unidade": vv.UNIDADE_MANDADOS if mandado else vv.UNIDADE_VITIMAS,
            "valor": valor_inteiro(linha.total if mandado else linha.total_vitima)})
    return pd.DataFrame(observacoes)


def somar_linhas_com_nota_oficial(observacoes: pd.DataFrame) -> pd.DataFrame:
    """Soma linhas repetidas na mesma competência apenas onde a nota oficial permite."""
    chave = ["evento", "abrangencia", "ano", "mes"]
    repetidas = observacoes[observacoes.duplicated(chave, keep=False)]
    nao_permitidos = set(repetidas["evento"]) - set(vv.EVENTOS_COM_LINHAS_MULTIPLAS)
    if nao_permitidos:
        raise ValueError(f"Repetição sem nota oficial em {sorted(nao_permitidos)}")
    print(f"Linhas repetidas somadas conforme a nota oficial: {len(repetidas)} (indicadores: {sorted(set(repetidas['evento']))})")
    somadas = observacoes.groupby(chave + ["unidade"], as_index=False, sort=False)["valor"].agg(lambda s: s.sum(min_count=1))
    return somadas[dp.COLUNAS_SINESP]  # o groupby reordena as colunas; restaura a ordem oficial


if not MODO_DEMONSTRACAO:
    observacoes = pd.concat([transformar_recorte(recortes[ano], ano) for ano in ANOS], ignore_index=True)
    observacoes = somar_linhas_com_nota_oficial(observacoes)
    base_etl = observacoes.sort_values(["evento", "abrangencia", "ano", "mes"], kind="stable").reset_index(drop=True)
    base_etl["valor"] = base_etl["valor"].astype("Int64")
    base_etl[["ano", "mes"]] = base_etl[["ano", "mes"]].astype("int64")
    print(f"Base reconstruída: {base_etl.shape[0]} observações × {base_etl.shape[1]} colunas")
    mostrar(base_etl.dtypes.rename("tipo").to_frame())
    mostrar(base_etl.head(8))

# %% [markdown]
# # 5. Validação das informações
# Verificações sobre a base reconstruída: (a) colunas e tipos; (b) sem competência repetida; (c) cada série tem meses consecutivos
# (sem lacunas) e uma única unidade; (d) valores inteiros não negativos; (e) ausências e zeros contados, não alterados;
# (f) a base é **idêntica byte a byte** aos dados aprovados — o SHA-256 do CSV gerado em memória é o registrado no manifesto.

# %%
publicada = dp.carregar_sinesp()
catalogo_publicado = dp.carregar_catalogo_sinesp()
CHAVE = ["evento", "abrangencia", "ano", "mes"]


def validar_base(base: pd.DataFrame) -> pd.DataFrame:
    """Devolve um quadro de verificações (descrição, aprovado)."""
    indice = base["ano"] * 12 + base["mes"] - 1
    sem_lacuna = all(
        (g.sort_values().diff().dropna() == 1).all()
        for _, g in indice.groupby([base["evento"], base["abrangencia"]]))
    verificacoes = {
        "colunas na ordem esperada": list(base.columns) == dp.COLUNAS_SINESP,
        "sem competência repetida": not base.duplicated(CHAVE).any(),
        "séries com meses consecutivos": sem_lacuna,
        "uma unidade por série": base.groupby(["evento", "abrangencia"])["unidade"].nunique().eq(1).all(),
        "valores inteiros não negativos (ou ausentes)": bool((base["valor"].dropna() >= 0).all()),
        "nenhum valor ausente convertido em zero (ausências preservadas)": int(base["valor"].isna().sum()) == int(publicada["valor"].isna().sum()),
    }
    return pd.DataFrame({"verificação": list(verificacoes), "aprovada": list(verificacoes.values())})


if MODO_DEMONSTRACAO:
    print("MODO DEMONSTRAÇÃO: validando a base publicada (não há reconstrução a conferir).")
    mostrar(validar_base(publicada))
    base_analitica = publicada.copy()
else:
    mostrar(validar_base(base_etl))
    csv_gerado = base_etl.to_csv(index=False, lineterminator="\n", na_rep="").encode("utf-8")  # somente em memória
    hash_gerado = dp.sha256_normalizado(csv_gerado)
    hash_aprovado = next(f["sha256"] for f in manifesto["arquivos"] if f["arquivo"] == dp.ARQ_SINESP)
    iguais = base_etl.astype(publicada.dtypes.to_dict()).equals(publicada)  # mesmos valores, ordem e tipos de leitura do dashboard
    print(f"Base reconstruída igual à publicada (valores, tipos e ordem): {iguais}")
    print(f"SHA-256 do CSV reconstruído = SHA-256 do manifesto: {hash_gerado == hash_aprovado}")
    assert iguais and hash_gerado == hash_aprovado, "A reconstrução diverge dos dados aprovados: revisar antes de continuar."
    base_analitica = base_etl

# %% [markdown]
# # 6. Construção da base analítica
# A base analítica tem uma linha por **série × mês**: `ano, mes, evento, abrangencia, unidade, valor`.
# Abaixo, o catálogo das 12 séries (indicador × abrangência) com cobertura, zeros e ausências.

# %%
def montar_catalogo(base: pd.DataFrame) -> pd.DataFrame:
    base = base.assign(competencia=base["ano"].astype(str) + "-" + base["mes"].astype(str).str.zfill(2))
    grupos = base.groupby(["evento", "abrangencia", "unidade"])
    return grupos.agg(inicio=("competencia", "min"), fim=("competencia", "max"), meses=("valor", "size"),
                      com_valor=("valor", "count"), zeros=("valor", lambda s: int((s == 0).sum()))).reset_index().assign(
        sem_valor=lambda t: t["meses"] - t["com_valor"])


catalogo = montar_catalogo(base_analitica)
mostrar(catalogo)
ok = (catalogo[["evento", "abrangencia"]].reset_index(drop=True).equals(catalogo_publicado[["evento", "abrangencia"]].reset_index(drop=True))
      and catalogo["meses"].tolist() == catalogo_publicado["meses_observados"].astype(int).tolist()
      and catalogo["fim"].tolist() == catalogo_publicado["fim"].tolist())
print(f"Séries: {len(catalogo)} | observações: {len(base_analitica)} | catálogo confere com o publicado: {ok}")
assert len(base_analitica) == len(publicada) and len(catalogo) == len(catalogo_publicado)

# %% [markdown]
# # 7. Análise exploratória
# Perguntas: qual a cobertura de cada série? Quais anos estão completos? Há zeros e ausências? Como se comparam períodos equivalentes?
# **Regra:** o último ano pode ser parcial e nunca é comparado com anos completos; a série da PRF pode terminar antes das demais.

# %%
ultima = catalogo.set_index(["evento", "abrangencia"])["fim"]
print("Última competência por série (a PRF termina antes das demais):")
mostrar(ultima[ultima != ultima.max()].to_frame("termina em"))
print(f"Competência mais recente da base: {ultima.max()} | zeros publicados: {int((base_analitica['valor'] == 0).sum())} | "
      f"valores ausentes: {int(base_analitica['valor'].isna().sum())}")

completos = base_analitica[base_analitica["ano"] <= 2025]  # 2020–2025: todas as séries com 12 meses (a PF, só desde 2025)
anual = (completos.groupby(["evento", "abrangencia", "ano"])["valor"].sum().unstack("ano"))
anual = anual.where(completos.groupby(["evento", "abrangencia", "ano"])["valor"].count().unstack("ano").notna())
print("\nTotais por ano completo (vítimas; mandados em contagem publicada). '<NA>' = série sem cobertura no ano, não zero:")
mostrar(anual)

# %%
# Períodos equivalentes: janeiro até o mesmo mês em todos os anos. Janeiro–agosto vale para todas as séries; janeiro–setembro, exceto a PRF.
def periodo_equivalente(base: pd.DataFrame, mes_final: int) -> pd.DataFrame:
    recorte = base[base["mes"] <= mes_final]
    meses_por_ano = recorte.groupby(["evento", "abrangencia", "ano"])["mes"].nunique().unstack("ano")
    somas = recorte.groupby(["evento", "abrangencia", "ano"])["valor"].sum().unstack("ano")
    return somas.where(meses_por_ano == mes_final)  # ano sem todos os meses do período não entra


jan_ago = periodo_equivalente(base_analitica, 8)
jan_set = periodo_equivalente(base_analitica, 9)
print("Janeiro–agosto (oito meses em todos os anos):")
mostrar(jan_ago)
print("Janeiro–setembro (nove meses; a PRF ainda não publicou setembro/2026):")
mostrar(jan_set)

# %% [markdown]
# # 8. Estatísticas descritivas
# Sobre os valores **mensais** de cada série: soma, média, mediana, mínimo, máximo e desvio-padrão descritivo (`ddof=0`, pois descreve
# os meses observados, sem inferência). Variações entre períodos: diferença absoluta sempre; percentual só com base positiva.

# %%
estatisticas = (base_analitica.groupby(["evento", "abrangencia"])["valor"]
                .agg(meses="count", soma="sum", media="mean", mediana="median", minimo="min", maximo="max",
                     desvio_padrao=lambda s: s.astype("float64").std(ddof=0)).round(2))
mostrar(estatisticas)


def variacao_entre_periodos(tabela: pd.DataFrame, ano_anterior: int, ano_atual: int) -> pd.DataFrame:
    """Diferença absoluta e percentual (só com base positiva) entre dois anos de uma tabela de períodos equivalentes."""
    quadro = pd.DataFrame({ano_anterior: tabela[ano_anterior], ano_atual: tabela[ano_atual]}).dropna()
    quadro["diferença"] = quadro[ano_atual] - quadro[ano_anterior]
    quadro["variação %"] = (quadro["diferença"] / quadro[ano_anterior].where(quadro[ano_anterior] > 0) * 100).round(1)
    return quadro


print("Janeiro–setembro de 2026 × 2025 (percentual indefinido quando a base é zero; contagens pequenas variam muito):")
mostrar(variacao_entre_periodos(jan_set, 2025, 2026))

# %% [markdown]
# # 9. Visualizações
# As figuras reutilizam as funções já validadas do dashboard (`dashboard/graficos.py`); aqui elas são apenas exibidas.
# O aperfeiçoamento visual dos gráficos é uma etapa posterior e não é feito neste roteiro.

# %%
figuras = graficos.figuras_sinesp_etapa10(base_analitica)
for nome, figura in figuras.items():
    print(nome)
    mostrar(figura)

figura_suicidio = graficos.figura_serie_anual_sinesp(base_analitica, "Suicídio", "Estadual", ANOS)
mostrar(figura_suicidio)

# %% [markdown]
# # 10. Conclusões e limitações

# %%
homicidio = anual.loc[("Homicídio doloso", "Estadual")]
homicidio_ja = jan_set.loc[("Homicídio doloso", "Estadual")]
tentativa_ja = jan_set.loc[("Tentativa de homicídio", "Estadual")]
print("CONCLUSÕES (descritivas, sobre contagens publicadas):")
print(f"- Homicídio doloso em anos completos: {int(homicidio[2020])} vítimas em 2020 e {int(homicidio[2025])} em 2025.")
print(f"- Janeiro–setembro: homicídio doloso {int(homicidio_ja[2025])} (2025) e {int(homicidio_ja[2026])} (2026); "
      f"tentativa de homicídio {int(tentativa_ja[2025])} e {int(tentativa_ja[2026])}.")
print(f"- A base tem {len(base_analitica)} observações em {len(catalogo)} séries, de {base_analitica['ano'].min()}-01 até {ultima.max()}.")
print("\nLIMITAÇÕES:")
print("- Registros administrativos agregados: não medem toda a criminalidade, não estimam subnotificação e não indicam causa.")
print("- Sem taxas populacionais, sem dados por bairro, rua, horário ou corporação; sem total geral entre indicadores ou abrangências.")
print("- 2026 é parcial; a PRF termina antes das demais séries; zeros publicados não provam ausência do fenômeno.")
print("- Contagens pequenas (feminicídio, latrocínio) geram percentuais instáveis: observe a diferença absoluta.")
print("- A fonte pode revisar valores históricos; a atualização controlada do dashboard detecta e bloqueia revisões não aprovadas.")
if MODO_DEMONSTRACAO:
    print("- ESTA EXECUÇÃO FOI EM MODO DEMONSTRAÇÃO: a base usada é a publicada, não a reconstruída a partir dos XLSX oficiais.")
