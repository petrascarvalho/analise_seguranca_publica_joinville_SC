"""Cálculos descritivos do dashboard, sobre os dados curados (sem Streamlit).

Regras herdadas do roteiro acadêmico:
- soma com ``min_count=1``: sem valor publicado, o resultado é ``<NA>`` (nunca zero);
- desvio-padrão descritivo com ``ddof=0``;
- variação percentual só com base positiva; caso contrário ``<NA>`` (não aplicável);
- o último ano do Sinesp pode ser parcial (hoje 2026, até agosto): períodos só são comparados quando equivalentes;
- nenhum total geral é produzido pela soma de indicadores ou de categorias diferentes.
"""

from __future__ import annotations

import pandas as pd

from dashboard.dados_publicos import CATEGORIAS_VD

CHAVE_SERIE = ["evento", "abrangencia", "unidade"]


# --------------------------------------------------------------------------------------- Sinesp
def _cobertura(meses: tuple[int, ...], ano: int, ultimo_ano: int) -> str:
    """Cobertura de um ano de uma série: só o último ano da série pode ser parcial (janeiro até o último mês publicado)."""
    if meses == tuple(range(1, 13)):
        return "ano completo"
    if ano == ultimo_ano and meses == tuple(range(1, len(meses) + 1)):
        return f"parcial janeiro–{_nome_mes(len(meses))}"
    return "cobertura incompleta"


def tabela_anual_sinesp(sinesp: pd.DataFrame) -> pd.DataFrame:
    """Soma anual por série, com cobertura explícita (2026 = parcial)."""
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
    quadro = pd.DataFrame(linhas)
    quadro["soma"] = quadro["soma"].astype("Int64")
    return quadro


def _nome_mes(mes: int) -> str:
    from dashboard.formatacao import NOMES_MESES
    return NOMES_MESES[mes - 1]


def variacao(anterior, atual) -> tuple[object, object]:
    """(diferença absoluta, variação percentual); percentual só com base positiva."""
    if pd.isna(anterior) or pd.isna(atual):
        return pd.NA, pd.NA
    diferenca = int(atual) - int(anterior)
    if int(anterior) <= 0:
        return diferenca, pd.NA
    return diferenca, round(diferenca / int(anterior) * 100, 2)


def comparacao_2026_2025_sinesp(sinesp: pd.DataFrame) -> pd.DataFrame:
    """Janeiro–agosto de 2025 × 2026 (períodos equivalentes) por série."""
    periodo = comparacao_periodo_sinesp(sinesp, 8)
    linhas = []
    for chave, grupo in periodo.groupby(CHAVE_SERIE, sort=False):
        a, b = grupo.loc[grupo["ano"].eq(2025), "soma"], grupo.loc[grupo["ano"].eq(2026), "soma"]
        if a.empty or b.empty:
            continue
        dif, pct = variacao(a.iloc[0], b.iloc[0])
        linhas.append({**dict(zip(CHAVE_SERIE, chave)), "periodo": "janeiro–agosto", "valor_2025": a.iloc[0], "valor_2026": b.iloc[0],
                       "diferenca_absoluta": dif, "variacao_percentual": pct})
    quadro = pd.DataFrame(linhas)
    for coluna in ("valor_2025", "valor_2026", "diferenca_absoluta"):
        quadro[coluna] = quadro[coluna].astype("Int64")
    quadro["variacao_percentual"] = quadro["variacao_percentual"].astype("Float64")
    return quadro


def serie_sinesp(sinesp: pd.DataFrame, evento: str, abrangencia: str) -> pd.DataFrame:
    return sinesp.loc[sinesp["evento"].eq(evento) & sinesp["abrangencia"].eq(abrangencia)].sort_values(["ano", "mes"])


def mes_final_da_serie(serie: pd.DataFrame) -> int:
    """Último mês publicado no último ano da série (12 se o último ano está completo)."""
    ultimo_ano = int(serie["ano"].max())
    return int(serie.loc[serie["ano"].eq(ultimo_ano), "mes"].max())


def ultima_competencia_da_serie(serie: pd.DataFrame) -> tuple[int, int]:
    ultimo_ano = int(serie["ano"].max())
    return ultimo_ano, mes_final_da_serie(serie)


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
    return {"periodo": f"janeiro–{_nome_mes(mes_final)}", "ano_atual": ano, "ano_anterior": ano - 1, "valor_atual": atual.iloc[0],
            "valor_anterior": anterior.iloc[0], "diferenca_absoluta": dif, "variacao_percentual": pct}


def resumo_serie_sinesp(serie: pd.DataFrame) -> dict:
    """Descrição da série mensal observada (todo o período), por série única."""
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


# ------------------------------------------------------------------- Violência doméstica SSP/SC
def filtrar_vd(vd: pd.DataFrame, categorias=None, anos=None, mes_inicial: int = 1, mes_final: int = 12) -> pd.DataFrame:
    mascara = vd["mes"].between(mes_inicial, mes_final)
    if categorias is not None:
        mascara &= vd["categoria"].isin(list(categorias))
    if anos is not None:
        mascara &= vd["ano"].isin(list(anos))
    return vd.loc[mascara]


def acumulado_por_categoria_ano(vd: pd.DataFrame, mes_inicial: int = 1, mes_final: int = 12) -> pd.DataFrame:
    """Soma por categoria e ano no mesmo intervalo de meses (cada categoria isolada; sem total geral)."""
    recorte = filtrar_vd(vd, mes_inicial=mes_inicial, mes_final=mes_final)
    agrupado = recorte.groupby(["categoria", "ano"])["fatos_comunicados"].agg(soma="sum", meses="count").reset_index()
    return agrupado


def comparacao_anual_vd(vd: pd.DataFrame, categorias=None, mes_inicial: int = 1, mes_final: int = 12) -> pd.DataFrame:
    """2023 × 2024 por categoria, sobre os mesmos meses nos dois anos."""
    base = acumulado_por_categoria_ano(vd, mes_inicial, mes_final)
    ordem = [c for c in CATEGORIAS_VD if categorias is None or c in set(categorias)]
    linhas = []
    for categoria in ordem:
        a = base.loc[base["categoria"].eq(categoria) & base["ano"].eq(2023)].iloc[0]
        b = base.loc[base["categoria"].eq(categoria) & base["ano"].eq(2024)].iloc[0]
        dif, pct = variacao(a["soma"], b["soma"])
        linhas.append({
            "categoria": categoria, "meses_2023": int(a["meses"]), "acumulado_2023": int(a["soma"]),
            "meses_2024": int(b["meses"]), "acumulado_2024": int(b["soma"]), "diferenca_absoluta": dif, "variacao_percentual": pct,
            "observacao_variacao": "não aplicável (2023 = 0)" if int(a["soma"]) == 0 else "calculada sobre 2023",
        })
    quadro = pd.DataFrame(linhas)
    quadro["diferenca_absoluta"] = quadro["diferenca_absoluta"].astype("Int64")
    quadro["variacao_percentual"] = quadro["variacao_percentual"].astype("Float64")
    return quadro


def comparativo_mensal_vd(vd: pd.DataFrame, categoria: str) -> pd.DataFrame:
    parte = vd.loc[vd["categoria"].eq(categoria)]
    largo = parte.pivot(index="mes", columns="ano", values="fatos_comunicados").sort_index()
    saida = pd.DataFrame({"mes": largo.index.astype(int), "fatos_2023": largo[2023].astype(int).to_numpy(), "fatos_2024": largo[2024].astype(int).to_numpy()})
    saida["diferenca_2024_menos_2023"] = saida["fatos_2024"] - saida["fatos_2023"]
    return saida


def estatisticas_vd(vd: pd.DataFrame, categorias=None, anos=None, mes_inicial: int = 1, mes_final: int = 12) -> pd.DataFrame:
    """Estatísticas descritivas por categoria (desvio-padrão com ddof=0)."""
    recorte = filtrar_vd(vd, categorias, anos, mes_inicial, mes_final).copy()
    recorte["v"] = recorte["fatos_comunicados"].astype("float64")
    linhas = []
    for categoria in [c for c in CATEGORIAS_VD if categorias is None or c in set(categorias)]:
        v = recorte.loc[recorte["categoria"].eq(categoria), "v"]
        if v.empty:
            continue
        linhas.append({
            "categoria": categoria, "soma_publicada": int(v.sum()), "media_mensal": round(float(v.mean()), 4),
            "mediana_mensal": round(float(v.median()), 4), "minimo": int(v.min()), "maximo": int(v.max()),
            "desvio_padrao_ddof0": round(float(v.std(ddof=0)), 4), "meses_observados": int(v.count()), "meses_com_zero": int((v == 0).sum()),
        })
    return pd.DataFrame(linhas)


def extremos_vd(vd: pd.DataFrame, categoria: str, anos=None) -> dict:
    """Maior e menor valor mensal da categoria, preservando todos os meses empatados."""
    parte = filtrar_vd(vd, [categoria], anos)
    maximo, minimo = int(parte["fatos_comunicados"].max()), int(parte["fatos_comunicados"].min())
    rotulo = lambda linhas: [f"{int(l.ano)}-{int(l.mes):02d}" for l in linhas.itertuples()]  # noqa: E731
    return {"maximo": maximo, "competencias_maximo": rotulo(parte.loc[parte["fatos_comunicados"].eq(maximo)]),
            "minimo": minimo, "competencias_minimo": rotulo(parte.loc[parte["fatos_comunicados"].eq(minimo)])}
