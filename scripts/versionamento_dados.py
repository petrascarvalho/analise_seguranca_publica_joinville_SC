"""Manifesto versionado dos dados mínimos do dashboard — fonte única: Sinesp/MJSP (gerador e atualização).

O manifesto distingue, de forma verificável, quatro datas que NÃO devem ser confundidas:

* **data de consulta** — quando as fontes foram consultadas (verificação);
* **data de publicação** — informada pela própria fonte (p.ex. "Atualizado em" da página);
* **competência estatística** — período a que os dados se referem (p.ex. 2026-08);
* **data de geração** — quando esta versão derivada foi gerada.

Nenhum metadado ausente é inventado: o que a fonte não informa fica ``null``/"não informado".
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone

import pandas as pd

SCHEMA_MANIFESTO = 3  # 3: fonte única Sinesp/MJSP
EVENTO_MANDADO = "Mandado de prisão cumprido"
UNIDADE_VITIMAS = "vítimas"
UNIDADE_MANDADOS = "mandados cumpridos (contagem publicada)"

NATUREZAS = {
    "Feminicídio": "criminal", "Homicídio doloso": "criminal", "Lesão corporal seguida de morte": "criminal",
    EVENTO_MANDADO: "atividade policial",
    "Morte no trânsito ou em decorrência dele (exceto homicídio doloso)": "complementar: mortalidade no trânsito",
    "Mortes a esclarecer (sem indício de crime)": "complementar: mortes a esclarecer",
    "Mortes no trânsito": "complementar: mortalidade no trânsito",
    "Roubo seguido de morte (latrocínio)": "criminal", "Suicídio": "complementar: suicídio",
    "Tentativa de feminicídio": "criminal", "Tentativa de homicídio": "criminal",
}
# Notas metodológicas oficiais: nestes indicadores um mesmo mês pode ter duas linhas, a serem somadas.
EVENTOS_COM_LINHAS_MULTIPLAS = ("Tentativa de homicídio", "Estupro")


def limitacoes(mandado: bool) -> str:
    base = ("Não representa pessoas únicas; estadual e PF separados; exclusividade não demonstrada." if mandado else
            "Não somar às parcelas de sexo; manter categoria e abrangência; sobreposição entre indicadores/fontes requer definição.")
    return base + " 2026 parcial; linha tabular não equivale a ocorrência individual."


def agora_utc() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def id_versao(agora: datetime) -> str:
    return agora.strftime("%Y%m%dT%H%M%SZ")


def sha256_bytes_normalizado(conteudo: bytes) -> str:
    return hashlib.sha256(conteudo.replace(b"\r\n", b"\n")).hexdigest()


def competencia_texto(ano: int, mes: int) -> str:
    return f"{int(ano)}-{int(mes):02d}"


def primeira_e_ultima_competencia(quadro: pd.DataFrame) -> tuple[str, str]:
    chaves = quadro["ano"].astype(int) * 100 + quadro["mes"].astype(int)
    primeira, ultima = int(chaves.min()), int(chaves.max())
    return competencia_texto(primeira // 100, primeira % 100), competencia_texto(ultima // 100, ultima % 100)


# --------------------------------------------------------------------------------- fontes e licenças
FONTES_BASE = [
    {
        "id": "sinesp_vde",
        "nome": "MJSP / Sinesp VDE",
        "descricao": "Indicadores municipais de Joinville/SC extraídos dos XLSX anuais da base nacional (2020 a agosto/2026; 2026 parcial).",
        "url": "https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/dados-nacionais-1/base-de-dados-e-notas-metodologicas-dos-gestores-estaduais-sinesp-vde-2022-e-2023",
        "recursos": [{"identificador": f"bancovde-{ano}.xlsx",
                      "url": f"https://www.gov.br/mj/pt-br/assuntos/sua-seguranca/seguranca-publica/estatistica/download/dnsp-base-de-dados/bancovde-{ano}.xlsx/@@download/file",
                      "tipo": "xlsx"} for ano in range(2020, 2027)],
        "licenca": {
            "data_consulta": "2026-10-27",
            "catalogo": {
                "nome": "Sistema Nacional de Estatísticas de Segurança Pública (catálogo dados.mj.gov.br)",
                "url": "https://dados.mj.gov.br/dataset/sistema-nacional-de-estatisticas-de-seguranca-publica",
                "licenca": "Creative Commons Atribuição (informada pelo responsável do projeto)",
                "confirmada_na_consulta": False,
                "observacao": "O domínio dados.mj.gov.br não foi resolvido (NXDOMAIN; também falhou no WebFetch) nas consultas de 27/10/2026; o catálogo não pôde ser lido e a licença NÃO foi confirmada por esta verificação.",
            },
            "site": {
                "licenca": "Creative Commons Atribuição-SemDerivações 3.0 Não Adaptada (CC BY-ND 3.0)",
                "url": "https://creativecommons.org/licenses/by-nd/3.0/deed.pt_BR",
                "escopo": "Rodapé do portal gov.br: 'Todo o conteúdo deste site está publicado sob a licença...' (licença geral do site, não específica do conjunto de dados).",
                "confirmada_na_consulta": True,
            },
            "condicoes_especificas_do_recurso": "Nenhuma proibição, restrição de uso ou exigência de citação específica foi encontrada na página da base VDE nem no Termo de Uso do portal; a página traz notas metodológicas (p.ex. linhas múltiplas em 'Tentativa de Homicídio' e 'Estupro').",
        },
    },
]

AVALIACAO_DE_REUTILIZACAO = (
    "Os arquivos derivados contêm apenas contagens estatísticas municipais agregadas de Joinville/SC e metadados de cobertura. Os XLSX oficiais "
    "integrais, dados pessoais e informações protegidas NÃO são redistribuídos. Nenhuma proibição específica aplicável a esses arquivos derivados foi "
    "encontrada; também NÃO há autorização específica explícita: a licença do catálogo do MJSP não foi confirmada na consulta (domínio sem resolução) e o "
    "rodapé do portal gov.br declara CC BY-ND 3.0 (licença geral do site, de aplicação a bases de dados não esclarecida). A atribuição da fonte é "
    "obrigatória nas páginas do painel. Avaliação técnica, não parecer jurídico."
)
ATRIBUICAO = ("Fonte: MJSP / Sinesp VDE (Ministério da Justiça e Segurança Pública). Tabelas e gráficos são elaborações próprias do projeto "
              "a partir de valores estatísticos públicos.")
CRITERIOS = [
    "Fonte única: Sinesp/MJSP (base VDE); município de Joinville/SC; séries Estadual, Polícia Federal e PRF, quando presentes.",
    "Observações mensais da base analítica validada; vítimas em total_vitima; mandados em total; ausência preservada como campo vazio, nunca como zero.",
    "Não inclui outras fontes, XLSX nacionais, dados pessoais ou informações protegidas.",
]
METODO_DE_OBTENCAO = (
    "Download manual (ou assistido por `python -m scripts.atualizacao_dados preparar --baixar-sinesp`) dos XLSX anuais `bancovde-ANO.xlsx` da página oficial da "
    "base VDE do MJSP; filtro exato UF = SC e município = JOINVILLE; ETL em Python/Pandas com validações; os XLSX não são redistribuídos."
)
REGRAS_ETL = [
    "Recorte exato: uf = 'SC' e municipio = 'JOINVILLE' (sem correspondência parcial); as 14 colunas originais são conferidas.",
    "Competência: serial Excel (sistema 1900, origem 1899-12-30) convertido em ano/mês; deve ser dia 1 e do mesmo ano do arquivo; datas inválidas interrompem o ETL.",
    "Medida: vítimas em `total_vitima`; mandados cumpridos em `total` — conceitos distintos, nunca somados.",
    "Ausências são preservadas (campo vazio) e nunca convertidas em zero; zeros publicados são mantidos como zero.",
    "Valores devem ser inteiros não negativos; indicador novo, abrangência ausente ou esquema alterado interrompem o ETL.",
    "Sem deduplicação genérica: linhas repetidas na mesma competência só são somadas em 'Tentativa de homicídio' e 'Estupro', conforme nota metodológica oficial, com aviso.",
    "Cobertura contígua por série; competência histórica removida, unidade alterada ou série nova bloqueiam a promoção; revisão de valor histórico exige aprovação específica.",
    "Séries podem terminar em competências diferentes (p.ex. PRF); isso é informado, não corrigido nem preenchido.",
    "SHA-256 (fins de linha normalizados para LF) de cada arquivo derivado e dos XLSX de origem registrados no manifesto.",
]


def montar_fontes(consulta: dict | None = None) -> list[dict]:
    """Fontes com a licença verificada e, se houver, o resultado da última verificação registrada."""
    fontes = []
    for base in FONTES_BASE:
        ficha = {k: (list(v) if isinstance(v, list) else v) for k, v in base.items()}
        consulta_fonte = (consulta or {}).get("por_fonte", {}).get(base["id"], {})
        ficha["consulta"] = {
            "data_consulta_utc": (consulta or {}).get("consultado_em_utc"),
            "achados": consulta_fonte.get("achados", []),
            "observacao": None if consulta else "Nenhuma verificação das fontes foi registrada nesta versão.",
        }
        ficha["publicacao"] = consulta_fonte.get("publicacao") or {"informacao": "não informada/registrada"}
        ficha["condicoes_de_reutilizacao"] = (
            f"Catálogo: {base['licenca']['catalogo']['licenca']}"
            f"{'' if base['licenca']['catalogo']['confirmada_na_consulta'] else ' [NÃO confirmada na consulta]'}. "
            f"Site: {base['licenca']['site']['licenca']}. {base['licenca']['condicoes_especificas_do_recurso']}")
        fontes.append(ficha)
    return fontes


def montar_manifesto(*, versao: str, versao_anterior: str | None, gerado_em: datetime, gerador: str, roteiro_sha256: str | None,
                     validacao: dict, cobertura: dict, revisoes_historicas: dict, origem: dict, arquivos: list[dict],
                     criterios: list[str], consulta: dict | None = None, aprovacao: dict | None = None) -> dict:
    return {
        "schema_manifesto": SCHEMA_MANIFESTO,
        "versao": versao,
        "versao_anterior": versao_anterior,
        "descricao": "Arquivos mínimos do dashboard Segurança Pública de Joinville: contagens municipais agregadas do Sinesp/MJSP, derivadas de bases analíticas validadas.",
        "datas": {
            "gerado_em_utc": gerado_em.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ultima_consulta_as_fontes_utc": (consulta or {}).get("consultado_em_utc"),
            "nota": "Data de consulta à fonte, data de publicação (informada pela fonte), competência estatística (período dos dados) e data de geração são informações distintas.",
        },
        "gerador": gerador,
        "roteiro_sha256": roteiro_sha256,
        "situacao_validacao": validacao,
        "aprovacao": aprovacao,
        "cobertura": cobertura,
        "unidades": {UNIDADE_VITIMAS: "vítimas (total_vitima)", UNIDADE_MANDADOS: "mandados cumpridos (total) — Estadual e Polícia Federal"},
        "revisoes_historicas": revisoes_historicas,
        "criterios": criterios,
        "metodo_de_obtencao": METODO_DE_OBTENCAO,
        "regras_etl": REGRAS_ETL,
        "fontes": montar_fontes(consulta),
        "avaliacao_de_reutilizacao": AVALIACAO_DE_REUTILIZACAO,
        "atribuicao": ATRIBUICAO,
        "origem_dos_dados": origem,
        "normalizacao_hash": "SHA-256 do conteúdo com fins de linha normalizados para LF.",
        "arquivos": arquivos,
    }


def cobertura_padrao(sinesp: pd.DataFrame) -> dict:
    """Cobertura geral e INDIVIDUAL de cada série (início, fim, meses, zeros e ausências)."""
    ini, fim = primeira_e_ultima_competencia(sinesp)
    ano_fim = int(fim[:4])
    meses_ano_fim = sorted(int(m) for m in sinesp.loc[sinesp["ano"].astype(int).eq(ano_fim), "mes"].unique())
    parcial = ano_fim if meses_ano_fim != list(range(1, 13)) else None
    series = []
    for (evento, abrangencia), serie in sinesp.groupby(["evento", "abrangencia"], sort=True):
        s_ini, s_fim = primeira_e_ultima_competencia(serie)
        series.append({"evento": evento, "abrangencia": abrangencia, "unidade": serie["unidade"].iloc[0], "primeira_competencia": s_ini,
                       "ultima_competencia": s_fim, "meses_observados": int(len(serie)), "meses_com_valor": int(serie["valor"].notna().sum()),
                       "meses_valor_zero": int(serie["valor"].eq(0).sum()), "meses_sem_valor": int(serie["valor"].isna().sum())})
    return {
        "sinesp": {"primeira_competencia": ini, "ultima_competencia": fim, "ano_parcial": parcial,
                   "descricao": f"{ini} a {fim}; município de Joinville/SC; séries Estadual, PF e PRF" + (f"; {parcial} é parcial" if parcial else "")},
        "series": series,
    }
