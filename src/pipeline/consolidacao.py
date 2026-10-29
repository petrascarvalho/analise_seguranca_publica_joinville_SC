"""Esquema comum, UNION (pd.concat) auditável e matriz de compatibilidade entre as fontes de Joinville.

Regra do projeto: cada fonte é tratada e validada separadamente; só depois as linhas podem ser empilhadas (UNION,
pd.concat), e só quando cada linha mantém o seu significado (mesma granularidade, unidade identificada,
situação de validação explícita). Nada é somado entre fontes, e nenhum merge por município/mês/ano é usado para
"juntar" indicadores — isso multiplicaria linhas e misturaria conceitos.

Situação atual (Etapa 24):
    • Sinesp/MJSP: 911 observações mensais validadas (versão 20261027T114400Z).
    • SSP/SC, violência doméstica: 216 observações mensais com esquema compatível, mas unidade "Fato Comunicado" sem
      definição oficial → "em validação". A união é testada em memória e NÃO é gravada como consolidação definitiva.
    • SSP/SC, homicídios dos boletins: totais anuais e acumulados, publicados em várias edições, 41 grupos divergentes →
      granularidade incompatível; fora da união.

Execução: python -m src.pipeline.consolidacao grava a Sinesp no esquema comum e a matriz de compatibilidade.
"""

from __future__ import annotations

import pandas as pd

from dashboard import dados_publicos as dp
from src.pipeline.utils import project_path

ESQUEMA = [
    "fonte", "municipio", "uf", "serie_id", "indicador", "indicador_original", "abrangencia", "ano", "mes", "periodicidade",
    "periodo_inicio", "periodo_fim", "unidade", "valor", "arquivo_origem", "situacao_validacao",
]
PASTA_PROCESSADOS = project_path("dados", "processados")


def sinesp_no_esquema_comum(sinesp: pd.DataFrame | None = None, versao: str | None = None) -> pd.DataFrame:
    """A base publicada do Sinesp (911 linhas) reescrita no esquema comum, sem mudar nenhum valor.

    Parâmetros: sinesp — base mensal (por padrão, a publicada em dashboard/data_publica, só leitura); versao — rótulo da versão.
    Retorno: DataFrame com as colunas de ESQUEMA (uma linha por observação original).
    """
    # Usa a base publicada (só leitura) quando nenhuma tabela é passada.
    sinesp = dp.carregar_sinesp() if sinesp is None else sinesp
    versao = versao or dp.carregar_manifesto()["versao"]
    # Primeiro dia de cada mês; MonthEnd(0) leva ao último dia do mesmo mês.
    inicio = pd.to_datetime(dict(year=sinesp["ano"], month=sinesp["mes"], day=1))
    return pd.DataFrame({
        "fonte": "Sinesp/MJSP", "municipio": "JOINVILLE", "uf": "SC",
        "serie_id": "sinesp|" + sinesp["evento"] + "|" + sinesp["abrangencia"],
        "indicador": sinesp["evento"], "indicador_original": sinesp["evento"], "abrangencia": sinesp["abrangencia"],
        # astype("Int64") padroniza ano, mês e valor como inteiros que aceitam ausência, iguais aos da outra fonte.
        "ano": sinesp["ano"].astype("Int64"), "mes": sinesp["mes"].astype("Int64"), "periodicidade": "mensal",
        "periodo_inicio": inicio.dt.strftime("%Y-%m-%d"), "periodo_fim": (inicio + pd.offsets.MonthEnd(0)).dt.strftime("%Y-%m-%d"),
        "unidade": sinesp["unidade"], "valor": sinesp["valor"].astype("Int64"),
        "arquivo_origem": f"dashboard/data_publica/{dp.ARQ_SINESP}", "situacao_validacao": f"validado (versão {versao})",
    })[ESQUEMA]


def unir(*fontes: pd.DataFrame) -> pd.DataFrame:
    """UNION das fontes já tratadas (pd.concat), com conferências que interrompem o processo se algo estiver errado.

    Conferências: mesmas colunas em todas as fontes; nenhuma linha criada ou perdida; nenhuma chave repetida
    (fonte + série + período); cada série com uma única unidade. Os valores não são agregados.
    """
    for tabela in fontes:
        if list(tabela[ESQUEMA].columns) != ESQUEMA:
            raise ValueError("Fonte fora do esquema comum.")
    uniao = pd.concat([t[ESQUEMA] for t in fontes], ignore_index=True)  # empilha linhas; não cruza nem soma
    # Conferências da UNION: mesma quantidade de linhas, nenhuma chave repetida e uma unidade por série.
    if len(uniao) != sum(len(t) for t in fontes):
        raise ValueError("A união mudou a quantidade de linhas.")
    chave = ["fonte", "serie_id", "periodo_inicio", "periodo_fim"]
    # Conferências da UNION: nenhuma observação repetida (duplicated) e uma única unidade por série (nunique).
    if uniao.duplicated(subset=chave).any():
        raise ValueError("Chave repetida na união (a mesma observação aparece duas vezes).")
    if (uniao.groupby("serie_id")["unidade"].nunique() > 1).any():
        raise ValueError("Uma série com mais de uma unidade.")
    return uniao


def matriz_compatibilidade() -> pd.DataFrame:
    """Quais conjuntos podem entrar na UNION ou num JOIN, e por quê (decisão auditável, uma linha por conjunto)."""
    linhas = [
        ("Sinesp/MJSP — 12 séries mensais (vítimas e mandados)", "mensal", "vítimas; mandados cumpridos", "validado",
         "sim (base de referência)", "sim, com o catálogo: chave evento + abrangência, muitos-para-um (cardinalidade conferida)",
         "Produto ativo do painel. Vítimas e mandados nunca são somados."),
        ("SSP/SC — violência doméstica, 9 categorias", "mensal", "Fato Comunicado (sem definição oficial)", "em validação",
         "tecnicamente compatível (mesmo esquema e granularidade); não aprovada", "não: nenhuma chave equivalente no Sinesp",
         "Não equivale a vítimas nem a ocorrências; 'Estupro' e 'Lesão corporal' não existem no Sinesp de Joinville para comparar."),
        ("SSP/SC — vítimas de homicídio dos boletins mensais", "ano completo e acumulado do ano (várias edições)", "vítimas",
         "pendente: 41 de 58 grupos divergentes", "não: granularidade diferente e várias versões do mesmo número",
         "não: 'vítimas de homicídio' (SSP/SC) ≠ 'homicídio doloso' (Sinesp); comparar só lado a lado, sem somar",
         "Acumulado não vira mensal; nenhuma versão é escolhida automaticamente."),
        ("Prefeitura/SEPROT — furtos e roubos (notícias)", "anual", "não informada", "divergente entre publicações",
         "não", "não", "Acervo histórico preservado; valores conflitantes para o mesmo ano."),
    ]
    # Matriz de compatibilidade: uma linha por conjunto de dados, dizendo se pode entrar na UNION ou no JOIN.
    return pd.DataFrame(linhas, columns=["conjunto", "granularidade", "unidade", "situacao", "union_com_sinesp", "join", "observacao"])


def exportar() -> dict:
    """Grava a Sinesp no esquema comum e a matriz de compatibilidade. Não grava consolidação de duas fontes (pendente)."""
    sinesp = sinesp_no_esquema_comum()
    (PASTA_PROCESSADOS / "sinesp").mkdir(parents=True, exist_ok=True)
    # Grava a Sinesp no esquema comum e a matriz de compatibilidade; nenhuma consolidação entre fontes é gravada.
    sinesp.to_csv(PASTA_PROCESSADOS / "sinesp" / "sinesp_esquema_comum.csv", index=False, encoding="utf-8", lineterminator="\n")
    matriz_compatibilidade().to_csv(PASTA_PROCESSADOS / "matriz_compatibilidade_union.csv", index=False, encoding="utf-8", lineterminator="\n")
    return {"sinesp_esquema_comum": len(sinesp), "consolidado_duas_fontes": "não gerado: SSP/SC em validação"}


if __name__ == "__main__":
    print(exportar())
