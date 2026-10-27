"""Cálculos descritivos do dashboard sobre os dados Sinesp/MJSP curados (sem Streamlit).

Regras herdadas do roteiro acadêmico (Etapa 9) e do fluxo de atualização:
- soma só existe quando TODOS os meses presentes têm valor publicado (soma incompleta nunca é apresentada como total);
- desvio-padrão descritivo com ``ddof=0``;
- variação percentual só com base positiva; caso contrário ``<NA>`` (não aplicável);
- o último ano de cada série pode ser parcial (hoje 2026, até setembro; a PRF pode terminar antes): períodos só são
  comparados quando equivalentes (mesmos meses nos dois anos);
- nenhum total geral é produzido pela soma de indicadores, abrangências ou unidades diferentes (vítimas × mandados).
"""

from __future__ import annotations

import pandas as pd

from dashboard.formatacao import NOMES_MESES, fmt_int, fmt_pct

CHAVE_SERIE = ["evento", "abrangencia", "unidade"]


def _nome_mes(mes: int) -> str:
    return NOMES_MESES[mes - 1]


def _cobertura(meses: tuple[int, ...], ano: int, ultimo_ano: int) -> str:
    """Cobertura de um ano de uma série: só o último ano da série pode ser parcial (janeiro até o último mês publicado)."""
    if meses == tuple(range(1, 13)):
        return "ano completo"
    if ano == ultimo_ano and meses == tuple(range(1, len(meses) + 1)):
        return f"parcial janeiro–{_nome_mes(len(meses))}"
    return "cobertura incompleta"


def tabela_anual_sinesp(sinesp: pd.DataFrame) -> pd.DataFrame:
    """Soma anual por série, com cobertura explícita (o último ano, se incompleto, é parcial)."""
    linhas = []
    ultimo_ano_serie = sinesp.groupby(CHAVE_SERIE)["ano"].max()
    for chave, grupo in sinesp.groupby(CHAVE_SERIE + ["ano"], sort=False):
        meses = tuple(sorted(int(m) for m in grupo["mes"].unique()))
        com_valor = int(grupo["valor"].notna().sum())
        linhas.append({
            **dict(zip(CHAVE_SERIE + ["ano"], chave)), "cobertura": _cobertura(meses, int(chave[-1]), int(ultimo_ano_serie[chave[:-1]])),
            "meses_presentes": len(meses), "meses_com_valor": com_valor,
            # Soma só quando todos os meses presentes têm valor: soma incompleta nunca é apresentada como total.
            "soma": grupo["valor"].sum(min_count=1) if com_valor == len(grupo) else pd.NA,
        })
    quadro = pd.DataFrame(linhas)
    quadro["soma"] = quadro["soma"].astype("Int64")
    return quadro


def comparacao_periodo_sinesp(sinesp: pd.DataFrame, mes_final: int = 8) -> pd.DataFrame:
    """Soma de janeiro até ``mes_final`` em cada ano; só anos com todos esses meses publicados."""
    linhas = []
    for chave, grupo in sinesp.groupby(CHAVE_SERIE + ["ano"], sort=False):
        recorte = grupo.loc[grupo["mes"].le(mes_final)]
        meses = tuple(sorted(int(m) for m in recorte["mes"].unique()))
        if meses != tuple(range(1, mes_final + 1)):
            continue  # período não equivalente: não é comparado
        linhas.append({
            **dict(zip(CHAVE_SERIE + ["ano"], chave)), "periodo": f"janeiro–{_nome_mes(mes_final)}",
            "meses_com_valor": int(recorte["valor"].notna().sum()),
            "soma": recorte["valor"].sum(min_count=1) if recorte["valor"].notna().all() else pd.NA,
        })
    quadro = pd.DataFrame(linhas, columns=CHAVE_SERIE + ["ano", "periodo", "meses_com_valor", "soma"])
    quadro["soma"] = quadro["soma"].astype("Int64")
    return quadro


def variacao(anterior, atual) -> tuple[object, object]:
    """(diferença absoluta, variação percentual); percentual só com base positiva."""
    if pd.isna(anterior) or pd.isna(atual):
        return pd.NA, pd.NA
    diferenca = int(atual) - int(anterior)
    if int(anterior) <= 0:
        return diferenca, pd.NA
    return diferenca, round(diferenca / int(anterior) * 100, 2)


def serie_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str) -> pd.DataFrame:
    return sinesp.loc[sinesp["evento"].eq(evento) & sinesp["abrangencia"].eq(abrangencia)].sort_values(["ano", "mes"])


def mes_final_da_serie(serie: pd.DataFrame) -> int:
    """Último mês publicado no último ano da série (12 se o último ano está completo)."""
    ultimo_ano = int(serie["ano"].max())
    return int(serie.loc[serie["ano"].eq(ultimo_ano), "mes"].max())


def ultima_competencia_da_serie(serie: pd.DataFrame) -> tuple[int, int]:
    return int(serie["ano"].max()), mes_final_da_serie(serie)


def comparacao_ultimo_periodo_sinesp(serie: pd.DataFrame) -> dict | None:
    """Último ano parcial da série × ano anterior no MESMO período (janeiro até o último mês publicado), ou ``None``."""
    ano, mes_final = ultima_competencia_da_serie(serie)
    if mes_final == 12:
        return None
    periodo = comparacao_periodo_sinesp(serie, mes_final)
    atual, anterior = periodo.loc[periodo["ano"].eq(ano), "soma"], periodo.loc[periodo["ano"].eq(ano - 1), "soma"]
    if atual.empty or anterior.empty:
        return None
    dif, pct = variacao(anterior.iloc[0], atual.iloc[0])
    return {"periodo": f"janeiro–{_nome_mes(mes_final)}", "mes_final": mes_final, "ano_atual": ano, "ano_anterior": ano - 1,
            "valor_atual": atual.iloc[0], "valor_anterior": anterior.iloc[0], "diferenca_absoluta": dif, "variacao_percentual": pct}


def comparacao_ultimo_periodo_todas_as_series(sinesp: pd.DataFrame) -> pd.DataFrame:
    """Comparação do último período parcial × mesmo período do ano anterior para cada série (cada uma com seu mês final)."""
    linhas = []
    for (evento, abrangencia, unidade), serie in sinesp.groupby(CHAVE_SERIE, sort=True):
        resultado = comparacao_ultimo_periodo_sinesp(serie.sort_values(["ano", "mes"]))
        if resultado is not None:
            linhas.append({"evento": evento, "abrangencia": abrangencia, "unidade": unidade, **resultado})
    return pd.DataFrame(linhas)


def resumo_serie_sinesp(serie: pd.DataFrame) -> dict:
    """Descrição da série mensal observada (todo o período informado)."""
    valores = serie["valor"]
    n = int(valores.count())
    return {
        "meses_observados": int(len(serie)), "meses_com_valor": n, "meses_sem_valor": int(valores.isna().sum()),
        "meses_valor_zero": int(valores.eq(0).sum()), "soma": valores.sum(min_count=1),
        "media_mensal": valores.astype("float64").mean() if n else pd.NA,
        "mediana_mensal": valores.astype("float64").median() if n else pd.NA,
        "minimo": valores.min() if n else pd.NA, "maximo": valores.max() if n else pd.NA,
        "desvio_padrao_ddof0": valores.astype("float64").std(ddof=0) if n >= 2 else pd.NA,
    }


def estatisticas_por_ano(serie: pd.DataFrame) -> pd.DataFrame:
    """Estatísticas descritivas MENSAIS por ano de uma série (média, mediana, mínimo, máximo, desvio-padrão com ddof=0)."""
    linhas = []
    ultimo_ano = int(serie["ano"].max())
    for ano, grupo in serie.groupby("ano", sort=True):
        resumo = resumo_serie_sinesp(grupo)
        meses = tuple(sorted(int(m) for m in grupo["mes"].unique()))
        linhas.append({"ano": int(ano), "cobertura": _cobertura(meses, int(ano), ultimo_ano), **resumo})
    return pd.DataFrame(linhas)


def variacoes_anuais(serie: pd.DataFrame) -> pd.DataFrame:
    """Variação entre anos COMPLETOS consecutivos (soma de 12 meses); anos parciais ou sem soma ficam de fora."""
    anual = tabela_anual_sinesp(serie)
    completos = anual.loc[anual["cobertura"].eq("ano completo") & anual["soma"].notna()].sort_values("ano")
    linhas = []
    anteriores = {int(a): s for a, s in zip(completos["ano"], completos["soma"])}
    for ano, soma in anteriores.items():
        if ano - 1 in anteriores:
            dif, pct = variacao(anteriores[ano - 1], soma)
            linhas.append({"ano_anterior": ano - 1, "ano": ano, "valor_anterior": anteriores[ano - 1], "valor": soma,
                           "diferenca_absoluta": dif, "variacao_percentual": pct})
    quadro = pd.DataFrame(linhas, columns=["ano_anterior", "ano", "valor_anterior", "valor", "diferenca_absoluta", "variacao_percentual"])
    for coluna in ("valor_anterior", "valor", "diferenca_absoluta"):
        quadro[coluna] = quadro[coluna].astype("Int64")
    quadro["variacao_percentual"] = quadro["variacao_percentual"].astype("Float64")
    return quadro


def comparar_anos_completos(serie: pd.DataFrame, ano_a: int, ano_b: int) -> dict | None:
    """Comparação entre dois anos COMPLETOS quaisquer da série (``None`` se algum não for completo ou não tiver soma)."""
    anual = tabela_anual_sinesp(serie).set_index("ano")
    for ano in (ano_a, ano_b):
        if ano not in anual.index or anual.loc[ano, "cobertura"] != "ano completo" or pd.isna(anual.loc[ano, "soma"]):
            return None
    dif, pct = variacao(anual.loc[ano_a, "soma"], anual.loc[ano_b, "soma"])
    return {"ano_a": ano_a, "ano_b": ano_b, "valor_a": anual.loc[ano_a, "soma"], "valor_b": anual.loc[ano_b, "soma"],
            "diferenca_absoluta": dif, "variacao_percentual": pct}


def ranking_por_unidade(sinesp: pd.DataFrame, ano: int, unidade: str) -> pd.DataFrame:
    """Séries (indicador × abrangência) ordenadas pela soma do ANO COMPLETO ``ano``, SOMENTE dentro de uma mesma unidade.

    É uma ordenação, não um total: nada é somado entre séries. Séries sem o ano completo ficam fora.
    """
    anual = tabela_anual_sinesp(sinesp)
    parte = anual.loc[anual["ano"].eq(ano) & anual["unidade"].eq(unidade) & anual["cobertura"].eq("ano completo") & anual["soma"].notna()]
    return parte.sort_values(["soma", "evento"], ascending=[False, True])[["evento", "abrangencia", "unidade", "soma"]].reset_index(drop=True)


def anos_completos_comuns(sinesp: pd.DataFrame) -> list[int]:
    """Anos em que TODAS as séries presentes nesse ano estão completas (12 meses)."""
    anual = tabela_anual_sinesp(sinesp)
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
        topo = ranking.head(3)
        if len(topo):
            itens = "; ".join(f"{r.evento} ({r.abrangencia}): {fmt_int(r.soma)}" for r in topo.itertuples())
            achados.append({"titulo": f"Maiores contagens de vítimas em {ano} (ano completo)", "texto":
                            f"{itens}. Ordenação dentro da mesma unidade (vítimas), sem total entre indicadores; mandados cumpridos têm outra unidade e são apresentados à parte."})
    return achados
