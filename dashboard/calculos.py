"""Cálculos descritivos do dashboard sobre os dados Sinesp/MJSP curados (sem Streamlit).

Regras herdadas do roteiro acadêmico (Etapa 9) e do fluxo de atualização:
- soma só existe quando TODOS os meses presentes têm valor publicado (soma incompleta nunca é apresentada como total);
- desvio-padrão descritivo com ddof=0;
- variação percentual só com base positiva; caso contrário <NA> (não aplicável);
- o último ano de cada série pode ser parcial (hoje 2026, até setembro; a PRF pode terminar antes): períodos só são
  comparados quando equivalentes (mesmos meses nos dois anos);
- nenhum total geral é produzido pela soma de indicadores, abrangências ou unidades diferentes (vítimas × mandados).
"""

from __future__ import annotations

# math: logaritmo e arredondamento para cima (regra de Sturges); pandas: tabelas, agrupamentos e estatísticas.
import math

import pandas as pd

from dashboard.formatacao import NOMES_MESES, fmt_int, fmt_pct

# Colunas que identificam uma série: indicador + classificação institucional + unidade.
CHAVE_SERIE = ["evento", "abrangencia", "unidade"]


def _nome_mes(mes: int) -> str:
    """Nome do mês (1 = janeiro)."""
    return NOMES_MESES[mes - 1]


def _cobertura(meses: tuple[int, ...], ano: int, ultimo_ano: int) -> str:
    """Cobertura de um ano de uma série: só o último ano da série pode ser parcial (janeiro até o último mês publicado)."""
    # Os 12 meses presentes = ano completo; só os primeiros meses do último ano = ano parcial.
    if meses == tuple(range(1, 13)):
        return "ano completo"
    if ano == ultimo_ano and meses == tuple(range(1, len(meses) + 1)):
        return f"parcial janeiro–{_nome_mes(len(meses))}"
    return "cobertura incompleta"


def tabela_anual_sinesp(sinesp: pd.DataFrame) -> pd.DataFrame:
    """Soma anual por série, com cobertura explícita (o último ano, se incompleto, é parcial)."""
    linhas = []
    # Último ano de cada série: groupby separa as séries e max() pega o maior ano de cada uma.
    ultimo_ano_serie = sinesp.groupby(CHAVE_SERIE)["ano"].max()
    # Percorre cada grupo série + ano: chave traz (indicador, classificação, unidade, ano) e grupo traz as linhas desse ano.
    for chave, grupo in sinesp.groupby(CHAVE_SERIE + ["ano"], sort=False):
        meses = tuple(sorted(int(m) for m in grupo["mes"].unique()))
        # notna() marca os meses com valor e sum() conta quantos são.
        com_valor = int(grupo["valor"].notna().sum())
        linhas.append({
            **dict(zip(CHAVE_SERIE + ["ano"], chave)), "cobertura": _cobertura(meses, int(chave[-1]), int(ultimo_ano_serie[chave[:-1]])),
            "meses_presentes": len(meses), "meses_com_valor": com_valor,
            # Soma só quando todos os meses presentes têm valor: soma incompleta nunca é apresentada como total.
            "soma": grupo["valor"].sum(min_count=1) if com_valor == len(grupo) else pd.NA,
        })
    # Transforma a lista de dicionários em tabela; a soma vira Int64 (inteiro que aceita ausência <NA>).
    quadro = pd.DataFrame(linhas)
    quadro["soma"] = quadro["soma"].astype("Int64")
    return quadro


def comparacao_periodo_sinesp(sinesp: pd.DataFrame, mes_final: int = 8) -> pd.DataFrame:
    """Soma de janeiro até mes_final em cada ano; só anos com todos esses meses publicados."""
    linhas = []
    # Mesmo laço por série e ano, agora para somar só de janeiro até o mês final.
    for chave, grupo in sinesp.groupby(CHAVE_SERIE + ["ano"], sort=False):
        # Mantém só janeiro até o mês final (le = menor ou igual): o mesmo período em todos os anos.
        recorte = grupo.loc[grupo["mes"].le(mes_final)]
        meses = tuple(sorted(int(m) for m in recorte["mes"].unique()))
        if meses != tuple(range(1, mes_final + 1)):
            continue  # período não equivalente: não é comparado
        linhas.append({
            **dict(zip(CHAVE_SERIE + ["ano"], chave)), "periodo": f"janeiro–{_nome_mes(mes_final)}",
            "meses_com_valor": int(recorte["valor"].notna().sum()),
            # Soma só se todos os meses do período têm valor; sum(min_count=1) devolve vazio (e não 0) quando não há nenhum valor.
            "soma": recorte["valor"].sum(min_count=1) if recorte["valor"].notna().all() else pd.NA,
        })
    # columns= fixa as colunas: mesmo sem nenhum ano válido, a tabela sai vazia, mas com as colunas certas.
    quadro = pd.DataFrame(linhas, columns=CHAVE_SERIE + ["ano", "periodo", "meses_com_valor", "soma"])
    quadro["soma"] = quadro["soma"].astype("Int64")
    return quadro


def variacao(anterior, atual) -> tuple[object, object]:
    """(diferença absoluta, variação percentual); percentual só com base positiva."""
    # Se faltar um dos dois valores, não há como comparar: devolve ausente nas duas medidas (nunca zero).
    if pd.isna(anterior) or pd.isna(atual):
        return pd.NA, pd.NA
    # Diferença absoluta; a variação percentual só existe quando o valor anterior é maior que zero.
    diferenca = int(atual) - int(anterior)
    if int(anterior) <= 0:
        return diferenca, pd.NA
    return diferenca, round(diferenca / int(anterior) * 100, 2)


def serie_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str) -> pd.DataFrame:
    """Linhas de uma única série (indicador + classificação institucional), em ordem de ano e mês."""
    # Filtro com duas condições: eq() compara cada linha com o texto e & exige as duas ao mesmo tempo.
    return sinesp.loc[sinesp["evento"].eq(evento) & sinesp["abrangencia"].eq(abrangencia)].sort_values(["ano", "mes"])


def mes_final_da_serie(serie: pd.DataFrame) -> int:
    """Último mês publicado no último ano da série (12 se o último ano está completo)."""
    ultimo_ano = int(serie["ano"].max())
    # Maior mês publicado no último ano da série (ex.: 9 = setembro).
    return int(serie.loc[serie["ano"].eq(ultimo_ano), "mes"].max())


def ultima_competencia_da_serie(serie: pd.DataFrame) -> tuple[int, int]:
    """Ano e mês do último valor publicado da série."""
    return int(serie["ano"].max()), mes_final_da_serie(serie)


def comparacao_ultimo_periodo_sinesp(serie: pd.DataFrame) -> dict | None:
    """Último ano parcial da série × ano anterior no MESMO período (janeiro até o último mês publicado), ou None."""
    ano, mes_final = ultima_competencia_da_serie(serie)
    if mes_final == 12:
        return None
    periodo = comparacao_periodo_sinesp(serie, mes_final)
    # Soma do mesmo período no ano atual e no ano anterior.
    atual, anterior = periodo.loc[periodo["ano"].eq(ano), "soma"], periodo.loc[periodo["ano"].eq(ano - 1), "soma"]
    if atual.empty or anterior.empty:
        return None
    # iloc[0] pega o primeiro (e único) valor de cada seleção.
    dif, pct = variacao(anterior.iloc[0], atual.iloc[0])
    return {"periodo": f"janeiro–{_nome_mes(mes_final)}", "mes_final": mes_final, "ano_atual": ano, "ano_anterior": ano - 1,
            "valor_atual": atual.iloc[0], "valor_anterior": anterior.iloc[0], "diferenca_absoluta": dif, "variacao_percentual": pct}


def comparacao_ultimo_periodo_todas_as_series(sinesp: pd.DataFrame) -> pd.DataFrame:
    """Comparação do último período parcial × mesmo período do ano anterior para cada série (cada uma com seu mês final)."""
    linhas = []
    # groupby por série devolve, a cada volta, a chave (indicador, classificação, unidade) e as linhas dessa série.
    for (evento, abrangencia, unidade), serie in sinesp.groupby(CHAVE_SERIE, sort=True):
        resultado = comparacao_ultimo_periodo_sinesp(serie.sort_values(["ano", "mes"]))
        if resultado is not None:
            linhas.append({"evento": evento, "abrangencia": abrangencia, "unidade": unidade, **resultado})
    return pd.DataFrame(linhas)


def resumo_serie_sinesp(serie: pd.DataFrame) -> dict:
    """Descrição da série mensal observada (todo o período informado)."""
    valores = serie["valor"]
    # count() conta só os valores preenchidos (ignora os ausentes).
    n = int(valores.count())
    return {
        "meses_observados": int(len(serie)), "meses_com_valor": n, "meses_sem_valor": int(valores.isna().sum()),
        "meses_valor_zero": int(valores.eq(0).sum()), "soma": valores.sum(min_count=1),
        # mean = média, median = mediana; astype("float64") converte para número decimal antes do cálculo.
        "media_mensal": valores.astype("float64").mean() if n else pd.NA,
        "mediana_mensal": valores.astype("float64").median() if n else pd.NA,
        "minimo": valores.min() if n else pd.NA, "maximo": valores.max() if n else pd.NA,
        # Desvio-padrão com ddof=0: descreve os meses observados (não é estimativa de amostra).
        "desvio_padrao_ddof0": valores.astype("float64").std(ddof=0) if n >= 2 else pd.NA,
    }


def estatisticas_por_ano(serie: pd.DataFrame) -> pd.DataFrame:
    """Estatísticas descritivas MENSAIS por ano de uma série (média, mediana, mínimo, máximo, desvio-padrão com ddof=0)."""
    linhas = []
    ultimo_ano = int(serie["ano"].max())
    for ano, grupo in serie.groupby("ano", sort=True):
        # groupby("ano") separa a série em um grupo por ano; para cada um, calcula as estatísticas mensais.
        resumo = resumo_serie_sinesp(grupo)
        meses = tuple(sorted(int(m) for m in grupo["mes"].unique()))
        linhas.append({"ano": int(ano), "cobertura": _cobertura(meses, int(ano), ultimo_ano), **resumo})
    return pd.DataFrame(linhas)


def variacoes_anuais(serie: pd.DataFrame) -> pd.DataFrame:
    """Variação entre anos COMPLETOS consecutivos (soma de 12 meses); anos parciais ou sem soma ficam de fora."""
    anual = tabela_anual_sinesp(serie)
    # Mantém só os anos completos com total conhecido (.loc com duas condições) e os ordena por ano.
    completos = anual.loc[anual["cobertura"].eq("ano completo") & anual["soma"].notna()].sort_values("ano")
    linhas = []
    # Dicionário ano -> total, só com anos completos; compara cada ano com o anterior, se existir.
    anteriores = {int(a): s for a, s in zip(completos["ano"], completos["soma"])}
    for ano, soma in anteriores.items():
        if ano - 1 in anteriores:
            dif, pct = variacao(anteriores[ano - 1], soma)
            linhas.append({"ano_anterior": ano - 1, "ano": ano, "valor_anterior": anteriores[ano - 1], "valor": soma,
                           "diferenca_absoluta": dif, "variacao_percentual": pct})
    # Tabela das variações; astype define os tipos: Int64 para contagens e Float64 para o percentual (os dois aceitam ausência).
    quadro = pd.DataFrame(linhas, columns=["ano_anterior", "ano", "valor_anterior", "valor", "diferenca_absoluta", "variacao_percentual"])
    for coluna in ("valor_anterior", "valor", "diferenca_absoluta"):
        quadro[coluna] = quadro[coluna].astype("Int64")
    quadro["variacao_percentual"] = quadro["variacao_percentual"].astype("Float64")
    return quadro


def comparar_anos_completos(serie: pd.DataFrame, ano_a: int, ano_b: int) -> dict | None:
    """Comparação entre dois anos COMPLETOS quaisquer da série (None se algum não for completo ou não tiver soma)."""
    # set_index("ano") deixa o ano como índice: anual.loc[2025, "soma"] lê o total de 2025.
    anual = tabela_anual_sinesp(serie).set_index("ano")
    for ano in (ano_a, ano_b):
        if ano not in anual.index or anual.loc[ano, "cobertura"] != "ano completo" or pd.isna(anual.loc[ano, "soma"]):
            return None
    # anual.loc[ano, "soma"] lê o total do ano (linha = ano, coluna = soma).
    dif, pct = variacao(anual.loc[ano_a, "soma"], anual.loc[ano_b, "soma"])
    return {"ano_a": ano_a, "ano_b": ano_b, "valor_a": anual.loc[ano_a, "soma"], "valor_b": anual.loc[ano_b, "soma"],
            "diferenca_absoluta": dif, "variacao_percentual": pct}


def ranking_por_unidade(sinesp: pd.DataFrame, ano: int, unidade: str) -> pd.DataFrame:
    """Séries (indicador × abrangência) ordenadas pela soma do ANO COMPLETO ano, SOMENTE dentro de uma mesma unidade.

    É uma ordenação, não um total: nada é somado entre séries. Séries sem o ano completo ficam fora.
    """
    anual = tabela_anual_sinesp(sinesp)
    # Séries do ano escolhido, na mesma unidade, com o ano completo e total conhecido.
    parte = anual.loc[anual["ano"].eq(ano) & anual["unidade"].eq(unidade) & anual["cobertura"].eq("ano completo") & anual["soma"].notna()]
    # Ordena do maior para o menor total (empate: ordem alfabética) e mantém só quatro colunas.
    return parte.sort_values(["soma", "evento"], ascending=[False, True])[["evento", "abrangencia", "unidade", "soma"]].reset_index(drop=True)


def anos_completos_comuns(sinesp: pd.DataFrame) -> list[int]:
    """Anos em que TODAS as séries presentes nesse ano estão completas (12 meses)."""
    anual = tabela_anual_sinesp(sinesp)
    # Anos em que TODAS as séries estão completas (all() exige que a condição valha para todas as linhas).
    return sorted(int(a) for a, g in anual.groupby("ano") if g["cobertura"].eq("ano completo").all())


def achados_principais(sinesp: pd.DataFrame) -> list[dict]:
    """Achados DESCRITIVOS calculados dos dados (observações, não causas). Cada item: titulo e texto."""
    achados = []
    serie = serie_sinesp(sinesp, "Homicídio doloso", "Estadual")
    if not serie.empty:
        variacoes = variacoes_anuais(serie)
        anual = tabela_anual_sinesp(serie)
        completos = anual.loc[anual["cobertura"].eq("ano completo") & anual["soma"].notna()].sort_values("ano")
        if len(completos) >= 2:
            # iloc[0] é o primeiro ano completo e iloc[-1] é o último.
            primeiro, ultimo = completos.iloc[0], completos.iloc[-1]
            _, pct = variacao(primeiro["soma"], ultimo["soma"])
            achados.append({"titulo": "Homicídio doloso — anos completos", "texto":
                            f"O total publicado passou de {fmt_int(primeiro['soma'])} vítimas em {int(primeiro['ano'])} para {fmt_int(ultimo['soma'])} em "
                            f"{int(ultimo['ano'])} ({fmt_pct(pct)}), com oscilações intermediárias. Série descritiva, sem causas identificadas."})
        comparacao = comparacao_ultimo_periodo_sinesp(serie)
        if comparacao is not None:
            achados.append({"titulo": f"Homicídio doloso — {comparacao['periodo']}", "texto":
                            f"{fmt_int(comparacao['valor_anterior'])} vítimas em {comparacao['ano_anterior']} e {fmt_int(comparacao['valor_atual'])} em "
                            f"{comparacao['ano_atual']} no mesmo período ({comparacao['periodo']}; {fmt_pct(comparacao['variacao_percentual'])})."})
    tentativa = serie_sinesp(sinesp, "Tentativa de homicídio", "Estadual")
    if not tentativa.empty:
        comparacao = comparacao_ultimo_periodo_sinesp(tentativa)
        if comparacao is not None:
            achados.append({"titulo": f"Tentativa de homicídio — {comparacao['periodo']}", "texto":
                            f"{fmt_int(comparacao['valor_anterior'])} vítimas em {comparacao['ano_anterior']} e {fmt_int(comparacao['valor_atual'])} em "
                            f"{comparacao['ano_atual']} no mesmo período ({fmt_pct(comparacao['variacao_percentual'])}). Tentativas e homicídios são séries distintas e não se somam."})
    comuns = anos_completos_comuns(sinesp)
    if comuns:
        ano = comuns[-1]
        ranking = ranking_por_unidade(sinesp, ano, "vítimas")
        # head(3) pega as três primeiras linhas (as maiores contagens).
        topo = ranking.head(3)
        if len(topo):
            itens = "; ".join(f"{r.evento} ({r.abrangencia}): {fmt_int(r.soma)}" for r in topo.itertuples())
            achados.append({"titulo": f"Maiores contagens de vítimas em {ano} (ano completo)", "texto":
                            f"{itens}. Ordenação dentro da mesma unidade (vítimas), sem total entre indicadores; mandados cumpridos têm outra unidade e são apresentados à parte."})
    return achados


# ===================================================================================================================
# Etapa 20 — distribuição, outliers (IQR), sazonalidade, médias móveis e acumulados.
# Todas as funções recebem a série de UM indicador × UMA abrangência (uma única unidade) e devolvem tabelas numéricas;
# as figuras de graficos.py desenham exatamente essas tabelas.
# ===================================================================================================================
# Parâmetros do critério estatístico de Tukey e das situações em que ele não é usado.
FATOR_TUKEY = 1.5
MESES_MINIMOS_IQR = 12          # menos meses com valor: o método IQR não é aplicado
PROPORCAO_ZEROS_MAXIMA = 0.5    # a partir daí, a maioria dos meses é zero publicado: Tukey não é informativo
LIMITE_CONTAGENS_BAIXAS = 1     # Q3 ≤ 1: três quartos dos meses têm no máximo 1 evento
ANOS_MINIMOS_SAZONALIDADE = 3   # abaixo disso, o perfil mensal é apenas ilustrativo
_ROTULOS_DIAGNOSTICO = {
    "informativo": "método informativo",
    "dados_insuficientes": "dados insuficientes",
    "distribuicao_degenerada": "distribuição degenerada",
    "iqr_zero": "IQR igual a zero",
    "maioria_zeros": "maioria de zeros publicados",
    "contagens_baixas": "contagens muito baixas",
}


def _exigir_uma_serie(serie: pd.DataFrame) -> None:
    """Interrompe o cálculo se a tabela misturar séries ou unidades diferentes."""
    if serie[["evento", "abrangencia", "unidade"]].drop_duplicates().shape[0] > 1:
        raise ValueError("Cálculo exige uma única série (indicador × abrangência × unidade): não se misturam séries nem unidades.")


def quartis_iqr(valores) -> dict:
    """Quartis (interpolação linear, método 7: padrão do pandas/NumPy), IQR e limites de Tukey (Q1 − 1,5·IQR; Q3 + 1,5·IQR).

    Valores ausentes são ignorados (nunca viram zero). Sem valores, tudo é <NA> e n = 0.
    """
    # dropna() descarta os ausentes (eles não viram zero).
    v = pd.Series(valores).dropna().astype("float64")
    if v.empty:
        return {"n": 0, "minimo": pd.NA, "q1": pd.NA, "mediana": pd.NA, "q3": pd.NA, "maximo": pd.NA, "iqr": pd.NA,
                "limite_inferior": pd.NA, "limite_superior": pd.NA}
    # quantile calcula os quartis: 25% (Q1), 50% (mediana) e 75% (Q3); IQR = Q3 - Q1.
    q1, mediana, q3 = (float(x) for x in v.quantile([0.25, 0.5, 0.75]))
    iqr = q3 - q1
    return {"n": int(len(v)), "minimo": float(v.min()), "q1": q1, "mediana": mediana, "q3": q3, "maximo": float(v.max()), "iqr": iqr,
            "limite_inferior": q1 - FATOR_TUKEY * iqr, "limite_superior": q3 + FATOR_TUKEY * iqr}


def _fora_dos_limites(serie: pd.DataFrame, inferior: float, superior: float) -> pd.DataFrame:
    """Meses com valor abaixo do limite inferior ou acima do superior, com a direção de cada um."""
    # Converte para decimal (Float64 aceita ausência) para comparar com os limites, que podem ter casas decimais.
    valor = serie["valor"].astype("Float64")
    # Marca os meses abaixo do limite inferior e acima do superior; | (ou) junta as duas marcações.
    abaixo, acima = valor.notna() & (valor < inferior), valor.notna() & (valor > superior)
    selecao = (abaixo | acima).to_numpy(dtype=bool)
    fora = serie.loc[selecao, ["ano", "mes", "valor"]].copy()
    fora["direcao"] = ["abaixo" if a else "acima" for a in abaixo.to_numpy(dtype=bool)[selecao]]
    return fora.reset_index(drop=True)


def diagnostico_outliers_iqr(serie: pd.DataFrame) -> dict:
    """Aplica o critério de Tukey aos valores MENSAIS da série e diz se o método é informativo.

    Classificações: informativo; dados_insuficientes (< 12 meses com valor); distribuicao_degenerada (todos os valores
    iguais); iqr_zero (Q1 = Q3: qualquer valor diferente seria "atípico"); maioria_zeros (≥ 50% de zeros publicados);
    contagens_baixas (Q3 ≤ 1: oscilações de 0 a 3 eventos são comuns e não são anomalias).
    Fora do caso informativo nenhum ponto deve ser apresentado como anomalia (interpretavel é falso).
    """
    _exigir_uma_serie(serie)
    # Coloca os meses em ordem cronológica antes dos cálculos.
    serie = serie.sort_values(["ano", "mes"])
    q = quartis_iqr(serie["valor"])
    n = q["n"]
    # Quantos meses têm zero publicado e quantos valores diferentes existem (nunique).
    zeros = int(serie["valor"].eq(0).sum())
    proporcao = zeros / n if n else pd.NA
    distintos = int(serie["valor"].nunique())
    # Sequência de testes: o critério só é "informativo" se a série passar por todos (meses suficientes, IQR > 0, poucos zeros...).
    if n < MESES_MINIMOS_IQR:
        classificacao = "dados_insuficientes"
        mensagem = f"Há apenas {n} mês(es) com valor (mínimo de {MESES_MINIMOS_IQR}): o método IQR não é aplicado."
    elif distintos <= 1:
        classificacao = "distribuicao_degenerada"
        mensagem = "Todos os meses têm o mesmo valor (distribuição degenerada): não há variação a avaliar e nenhum ponto atípico é apontado."
    elif q["iqr"] == 0:
        classificacao = "iqr_zero"
        mensagem = (f"Q1 e Q3 coincidem ({q['q1']:.0f}; IQR = 0): pelo critério de Tukey qualquer valor diferente seria considerado atípico. "
                    "O método não é informativo para esta série e não se conclui anomalia.")
    elif proporcao >= PROPORCAO_ZEROS_MAXIMA:
        classificacao = "maioria_zeros"
        mensagem = (f"{proporcao * 100:.0f}% dos meses ({zeros} de {n}) têm zero publicado: em contagens de eventos raros a distribuição é muito assimétrica "
                    "e os limites de Tukey não são informativos. Valores acima do limite não indicam anomalia.")
    elif q["q3"] <= LIMITE_CONTAGENS_BAIXAS:
        classificacao = "contagens_baixas"
        mensagem = (f"Três quartos dos meses têm no máximo {q['q3']:.0f} evento(s): com contagens tão baixas, valores como 2 ou 3 são oscilações comuns "
                    "e o critério de Tukey os marcaria como atípicos sem significado. O método não é informativo.")
    else:
        classificacao = "informativo"
        mensagem = ("Os limites de Tukey são informativos para esta série. Pontos fora deles são atípicos estatísticos em relação ao conjunto dos meses "
                    "observados — não são prova de erro, de anomalia ou de mudança real; séries com tendência podem ter limites pouco representativos.")
    # Os meses fora dos limites só são procurados quando há meses suficientes e valores diferentes; senão, a tabela fica vazia.
    fora = (_fora_dos_limites(serie, q["limite_inferior"], q["limite_superior"]) if n >= MESES_MINIMOS_IQR and distintos > 1
            else pd.DataFrame(columns=["ano", "mes", "valor", "direcao"]))
    return {**q, "zeros": zeros, "proporcao_zeros": proporcao, "valores_distintos": distintos, "classificacao": classificacao,
            "rotulo": _ROTULOS_DIAGNOSTICO[classificacao], "interpretavel": classificacao == "informativo", "mensagem": mensagem,
            "fora": fora, "n_fora": int(len(fora))}


def diagnostico_outliers_todas_as_series(sinesp: pd.DataFrame) -> pd.DataFrame:
    """Quadro com o diagnóstico IQR de cada série (cada uma tratada separadamente, na sua própria unidade)."""
    linhas = []
    # Aplica o diagnóstico a cada uma das 12 séries, separadamente (cada uma na sua unidade).
    for (evento, abrangencia, unidade), serie in sinesp.groupby(CHAVE_SERIE, sort=True):
        d = diagnostico_outliers_iqr(serie)
        linhas.append({"evento": evento, "abrangencia": abrangencia, "unidade": unidade, "meses": d["n"], "q1": d["q1"], "q3": d["q3"],
                       "iqr": d["iqr"], "zeros": d["zeros"], "classificacao": d["rotulo"], "pontos_fora": d["n_fora"] if d["interpretavel"] else pd.NA})
    return pd.DataFrame(linhas)


def quartis_por_ano(serie: pd.DataFrame) -> pd.DataFrame:
    """Resumo de cinco números por ano (valores mensais), com limites de Tukey, bigodes e pontos fora, para o boxplot.

    Bigodes: menor e maior valor DENTRO dos limites. Em anos com IQR = 0 o boxplot é degenerado (iqr_zero verdadeiro) e os
    pontos fora não são interpretados.
    """
    _exigir_uma_serie(serie)
    ultimo_ano = int(serie["ano"].max())
    linhas = []
    # Um grupo por ano: quartis e limites calculados só com os meses daquele ano.
    for ano, grupo in serie.sort_values(["ano", "mes"]).groupby("ano", sort=True):
        q = quartis_iqr(grupo["valor"])
        if q["n"] == 0:
            continue
        valores = grupo["valor"].dropna().astype("float64")
        # Valores dentro e fora dos limites do ano (os de dentro definem as pontas do gráfico de caixa).
        dentro = valores[(valores >= q["limite_inferior"]) & (valores <= q["limite_superior"])]
        fora = valores[(valores < q["limite_inferior"]) | (valores > q["limite_superior"])]
        meses = tuple(sorted(int(m) for m in grupo["mes"].unique()))
        linhas.append({"ano": int(ano), "cobertura": _cobertura(meses, int(ano), ultimo_ano), **q, "bigode_inferior": float(dentro.min()),
                       "bigode_superior": float(dentro.max()), "n_fora": int(len(fora)), "valores_fora": sorted(float(x) for x in fora),
                       "iqr_zero": q["iqr"] == 0})
    return pd.DataFrame(linhas)


def quadro_ano_mes(serie: pd.DataFrame) -> pd.DataFrame:
    """Valores publicados em grade ano × mês (<NA> onde não há valor observado; nunca zero)."""
    _exigir_uma_serie(serie)
    # pivot cria a tabela ano x mês; reindex garante as 12 colunas de mês, mesmo que algum falte (fica vazio, não zero).
    quadro = serie.pivot(index="ano", columns="mes", values="valor").reindex(columns=range(1, 13)).sort_index()
    return quadro.astype("Int64")


def anos_completos_da_serie(serie: pd.DataFrame) -> list[int]:
    """Anos com os 12 meses publicados e com valor (um ano parcial, como 2026, nunca entra)."""
    anual = tabela_anual_sinesp(serie)
    completos = anual.loc[anual["cobertura"].eq("ano completo") & anual["soma"].notna() & anual["meses_com_valor"].eq(12)]
    return sorted(int(a) for a in completos["ano"])


def perfil_sazonal(serie: pd.DataFrame, anos: list[int] | None = None) -> pd.DataFrame:
    """Perfil por mês-calendário usando SOMENTE anos completos (e, se informados, apenas entre anos).

    Colunas: mes, n_anos, media, mediana, minimo, maximo, indice (média do mês ÷ média de todos os meses usados; <NA> se a média geral
    for zero). Os anos usados ficam em perfil.attrs["anos_usados"]. Poucos anos completos tornam o perfil descritivo, sem poder de
    provar sazonalidade.
    """
    _exigir_uma_serie(serie)
    usados = [a for a in anos_completos_da_serie(serie) if anos is None or a in anos]
    colunas = ["mes", "n_anos", "media", "mediana", "minimo", "maximo", "indice"]
    if not usados:
        # Sem anos completos: devolve uma tabela vazia com as colunas certas (nada é inventado).
        vazio = pd.DataFrame(columns=colunas)
        vazio.attrs["anos_usados"] = []
        return vazio
    # Só os anos completos entram no perfil por mês do ano.
    base = serie.loc[serie["ano"].isin(usados)]
    # groupby("mes") junta os janeiros, os fevereiros...; agg calcula várias estatísticas de uma vez.
    # As duas lambdas convertem para decimal antes da média e da mediana (mínimo e máximo continuam inteiros).
    perfil = base.groupby("mes")["valor"].agg(n_anos="count", media=lambda s: s.astype("float64").mean(), mediana=lambda s: s.astype("float64").median(),
                                              minimo="min", maximo="max").reset_index()
    geral = float(base["valor"].astype("float64").mean())
    perfil["indice"] = perfil["media"] / geral if geral > 0 else pd.NA
    perfil = perfil[colunas]
    perfil.attrs["anos_usados"] = usados
    return perfil


def media_movel(serie: pd.DataFrame, janela: int = 12) -> pd.DataFrame:
    """Média móvel (janela de janela meses consecutivos, alinhada ao último mês da janela).

    Só existe quando TODOS os meses da janela têm valor; meses ausentes ou lacunas geram <NA> (nada é interpolado).
    """
    _exigir_uma_serie(serie)
    # Número sequencial do mês (ano x 12 + mês): meses seguidos viram números seguidos.
    indice = serie["ano"].astype(int) * 12 + serie["mes"].astype(int) - 1
    # Série de valores decimais indexada pelo número do mês; a ausência vira NaN (vazio), nunca zero.
    valores = pd.Series(serie["valor"].astype("Float64").to_numpy(dtype="float64", na_value=float("nan")), index=indice.to_numpy())
    # reindex inclui os meses que faltarem (como vazios) para a janela não pular meses.
    completo = valores.reindex(range(int(indice.min()), int(indice.max()) + 1))
    # rolling(12).mean(): média de cada mês com os 11 anteriores; min_periods=12 deixa vazio se faltar algum mês.
    movel = completo.rolling(janela, min_periods=janela).mean()
    # Volta do número sequencial para ano e mês: // é a divisão inteira e % é o resto da divisão.
    quadro = pd.DataFrame({"ano": completo.index // 12, "mes": completo.index % 12 + 1, "valor": completo.to_numpy(), "media_movel": movel.to_numpy()})
    quadro["valor"] = quadro["valor"].astype("Int64")
    return quadro.reset_index(drop=True)


def acumulado_no_ano(serie: pd.DataFrame) -> pd.DataFrame:
    """Soma acumulada de janeiro até cada mês, por ano; <NA> depois de um mês sem valor (nunca soma parcial como total)."""
    _exigir_uma_serie(serie)
    linhas = []
    # Um grupo por ano; os meses precisam começar em janeiro e não pular nenhum.
    for ano, grupo in serie.sort_values(["ano", "mes"]).groupby("ano", sort=True):
        meses = grupo["mes"].astype(int).tolist()
        if meses != list(range(1, len(meses) + 1)):
            raise ValueError(f"Meses não consecutivos a partir de janeiro em {ano}: acumulado não é calculado.")
        # cumsum soma acumulando (jan, jan+fev, ...); skipna=False: depois de um mês sem valor, o acumulado fica vazio.
        acumulado = grupo["valor"].astype("Float64").cumsum(skipna=False)
        for mes, valor, soma in zip(meses, grupo["valor"], acumulado):
            linhas.append({"ano": int(ano), "mes": mes, "valor": valor, "acumulado": soma})
    # Tabela final do acumulado; valor e acumulado ficam Int64 (inteiros que aceitam ausência).
    quadro = pd.DataFrame(linhas)
    quadro["valor"], quadro["acumulado"] = quadro["valor"].astype("Int64"), quadro["acumulado"].astype("Int64")
    return quadro


def numero_de_faixas(n: int) -> int:
    """Número de faixas pela regra de Sturges: ⌈1 + log₂ n⌉ (81 meses → 8 faixas; 21 meses → 6)."""
    # Regra de Sturges: número de faixas = 1 + log2(n), arredondado para cima.
    return int(math.ceil(1 + math.log2(n))) if n > 0 else 0


def distribuicao_frequencias(serie: pd.DataFrame) -> pd.DataFrame:
    """Frequência dos valores mensais em faixas de contagem (barras categóricas), com regra simples e documentada.

    Regra: (1) o zero publicado é sempre uma faixa própria (0), nunca misturado a outros valores; (2) os valores positivos
    (ou todos, se não houver zero) são agrupados em faixas de largura inteira igual w = ⌈amplitude / k⌉, onde a amplitude vai do
    menor ao maior valor positivo observado e k vem da regra de Sturges (numero_de_faixas; uma faixa a menos quando há faixa de
    zero). Assim não surge uma faixa vazia entre o zero e o menor valor positivo (que pode estar longe de 1, como nos mandados).
    Se w = 1, cada inteiro é uma faixa. O valor extremo nunca é removido: ele cai na última faixa, que termina no máximo observado.

    Colunas: rotulo, inicio, fim (inclusivos), n_meses, percentual. A soma de n_meses é o número de meses com valor; ausências
    ficam de fora (e são contadas na página/roteiro). tabela.attrs["largura"] guarda w.
    """
    _exigir_uma_serie(serie)
    # Só os meses com valor (dropna), como inteiros: ausências não entram na distribuição.
    v = serie["valor"].dropna().astype("int64")
    colunas = ["rotulo", "inicio", "fim", "n_meses", "percentual"]
    if v.empty:
        # Sem valores: tabela vazia com as colunas certas.
        vazio = pd.DataFrame(columns=colunas)
        vazio.attrs["largura"] = 1
        return vazio
    n = len(v)
    linhas = []

    def faixa(inicio: int, fim: int) -> dict:
        """Conta os meses com valor entre início e fim e calcula o percentual sobre o total de meses."""
        # between(inicio, fim) marca os valores dentro da faixa (inclusive as pontas); sum() conta quantos são.
        quantos = int(v.between(inicio, fim).sum())
        return {"rotulo": str(inicio) if inicio == fim else f"{inicio}–{fim}", "inicio": inicio, "fim": fim, "n_meses": quantos,
                "percentual": round(quantos / n * 100, 2)}

    # O zero publicado vira uma faixa própria; os demais valores são divididos em faixas de mesma largura.
    tem_zero = bool((v == 0).any())
    if tem_zero:
        linhas.append(faixa(0, 0))
    positivos = v[v > 0] if tem_zero else v
    largura = 1
    if not positivos.empty:
        inicio, maximo = int(positivos.min()), int(positivos.max())
        faixas_positivas = max(numero_de_faixas(n) - (1 if tem_zero else 0), 1)
        # Largura de cada faixa: divisão arredondada para cima (o truque -(-a // b) faz isso só com inteiros).
        largura = max(1, -(-(maximo - inicio + 1) // faixas_positivas))
        # Cria as faixas uma a uma até chegar ao maior valor; a última termina exatamente no máximo.
        while inicio <= maximo:
            linhas.append(faixa(inicio, min(inicio + largura - 1, maximo)))
            inicio += largura
    # Tabela de frequências; attrs guarda a largura das faixas junto com a tabela (usada no texto explicativo).
    quadro = pd.DataFrame(linhas, columns=colunas)
    quadro.attrs["largura"] = largura
    return quadro


def soma_no_periodo(serie: pd.DataFrame, mes_inicial: int, mes_final: int) -> pd.DataFrame:
    """Soma, por ano, dos meses mes_inicial–mes_final. Só entra o ano em que TODOS esses meses foram publicados e têm valor
    (nunca soma parcial como total). Colunas: ano, soma (Int64), meses_com_valor."""
    _exigir_uma_serie(serie)
    esperado = mes_final - mes_inicial + 1
    linhas = []
    # Para cada ano, soma só os meses escolhidos no filtro.
    for ano, grupo in serie.groupby("ano", sort=True):
        # Só os meses escolhidos no filtro, dentro de cada ano.
        recorte = grupo.loc[grupo["mes"].between(mes_inicial, mes_final)]
        # O ano só entra se tiver todos os meses escolhidos e todos com valor.
        completo = len(recorte) == esperado and recorte["valor"].notna().all()
        linhas.append({"ano": int(ano), "soma": int(recorte["valor"].sum()) if completo else pd.NA, "meses_com_valor": int(recorte["valor"].notna().sum())})
    # Tabela por ano; a soma vira Int64 para aceitar ausência nos anos incompletos.
    quadro = pd.DataFrame(linhas, columns=["ano", "soma", "meses_com_valor"])
    quadro["soma"] = quadro["soma"].astype("Int64")
    return quadro
