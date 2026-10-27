"""Manifesto versionado dos dados mínimos do dashboard (compartilhado pelo gerador e pela atualização).

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

SCHEMA_MANIFESTO = 2
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
    {
        "id": "ssp_sc_violencia_domestica",
        "nome": "SSP/SC — Segurança em Números (relatórios de violência doméstica 2023–2024)",
        "descricao": "Contagens mensais de 'Fato Comunicado' de Joinville/SC por categoria, extraídas de três relatórios PDF (216 observações).",
        "url": "https://ssp.sc.gov.br/segurancaemnumeros/",
        "recursos": [
            {"identificador": "VIOLENCIA-DOMESTICA-1o-SEMESTRE-2023.pdf", "url": "https://ssp.sc.gov.br/wp-content/uploads/2025/06/VIOLENCIA-DOMESTICA-1o-SEMESTRE-2023.pdf", "tipo": "pdf"},
            {"identificador": "VIOLENCIA-DOMESTICA-2o-SEMESTRE-2023.pdf", "url": "https://ssp.sc.gov.br/wp-content/uploads/2025/06/VIOLENCIA-DOMESTICA-2o-SEMESTRE-2023.pdf", "tipo": "pdf"},
            {"identificador": "VIOLENCIA-DOMESTICA-2024-SC.pdf", "url": "https://ssp.sc.gov.br/wp-content/uploads/2025/06/VIOLENCIA-DOMESTICA-2024-SC.pdf", "tipo": "pdf"},
        ],
        "licenca": {
            "data_consulta": "2026-10-27",
            "catalogo": {
                "nome": "Segurança em Números (catálogo dados.sc.gov.br)",
                "url": "https://www.dados.sc.gov.br/dataset/https-ssp-sc-gov-br-segurancaemnumeros",
                "licenca": "Outra (Aberta) — license_id 'other-open'; a página indica que satisfaz a Definição de Aberto (Open Definition)",
                "confirmada_na_consulta": True,
                "observacao": "Confirmada pela API CKAN e pela página. O único recurso do conjunto é um link HTML para ssp.sc.gov.br/segurancaemnumeros; não há texto integral de licença nem licença específica por documento.",
            },
            "site": {
                "licenca": "Copyright © 2023 Todos os Direitos Reservados SC - Governo de Santa Catarina",
                "url": "https://ssp.sc.gov.br/segurancaemnumeros/",
                "escopo": "Rodapé do site da SSP/SC; não declara licença de reutilização nem exigência de citação.",
                "confirmada_na_consulta": True,
            },
            "condicoes_especificas_do_recurso": "Nenhuma condição específica foi encontrada nos relatórios consultados além do que a página informa. O aviso de direitos reservados do site e a classificação aberta do catálogo coexistem; a divergência não foi esclarecida com a SSP/SC.",
        },
    },
]

AVALIACAO_DE_REUTILIZACAO = (
    "Os arquivos derivados contêm apenas contagens estatísticas municipais agregadas e metadados de rastreabilidade (nomes de arquivos, "
    "páginas, linhas e colunas). Os documentos oficiais integrais (XLSX e PDF), dados pessoais e informações protegidas NÃO são redistribuídos. "
    "Nenhuma proibição específica aplicável a esses arquivos derivados foi encontrada; também NÃO há autorização específica explícita: a "
    "licença do catálogo do MJSP não foi confirmada nesta consulta e o rodapé do portal gov.br declara CC BY-ND 3.0, e o site da SSP/SC "
    "declara direitos reservados enquanto o catálogo catarinense a classifica como aberta. A atribuição das fontes é obrigatória nas páginas do painel."
)
ATRIBUICAO = ("Fontes: MJSP / Sinesp VDE (Ministério da Justiça e Segurança Pública) e SSP/SC — Segurança em Números (Secretaria de Estado da Segurança "
              "Pública de Santa Catarina). Tabelas e gráficos são elaborações próprias do projeto a partir de valores estatísticos públicos.")


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
        "descricao": "Arquivos mínimos do dashboard Segurança Pública de Joinville: contagens municipais agregadas, derivadas de bases analíticas validadas.",
        "datas": {
            "gerado_em_utc": gerado_em.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "ultima_consulta_as_fontes_utc": (consulta or {}).get("consultado_em_utc"),
            "nota": "Data de consulta às fontes, data de publicação (informada pela fonte), competência estatística (período dos dados) e data de geração são informações distintas.",
        },
        "gerador": gerador,
        "roteiro_sha256": roteiro_sha256,
        "situacao_validacao": validacao,
        "aprovacao": aprovacao,
        "cobertura": cobertura,
        "revisoes_historicas": revisoes_historicas,
        "criterios": criterios,
        "fontes": montar_fontes(consulta),
        "avaliacao_de_reutilizacao": AVALIACAO_DE_REUTILIZACAO,
        "atribuicao": ATRIBUICAO,
        "origem_dos_dados": origem,
        "normalizacao_hash": "SHA-256 do conteúdo com fins de linha normalizados para LF.",
        "arquivos": arquivos,
    }


def cobertura_padrao(sinesp: pd.DataFrame, vd: pd.DataFrame) -> dict:
    s_ini, s_fim = primeira_e_ultima_competencia(sinesp)
    v_ini, v_fim = primeira_e_ultima_competencia(vd)
    ano_fim = int(s_fim[:4])
    meses_ano_fim = sorted(int(m) for m in sinesp.loc[sinesp["ano"].astype(int).eq(ano_fim), "mes"].unique())
    parcial = ano_fim if meses_ano_fim != list(range(1, 13)) else None
    return {
        "sinesp": {"primeira_competencia": s_ini, "ultima_competencia": s_fim, "ano_parcial": parcial,
                   "descricao": f"{s_ini} a {s_fim}; município de Joinville/SC; séries Estadual, PF e PRF"
                                + (f"; {parcial} é parcial" if parcial else "")},
        "ssp_violencia_domestica": {"primeira_competencia": v_ini, "ultima_competencia": v_fim,
                                    "descricao": f"{v_ini} a {v_fim}; Joinville/SC; nove categorias; unidade 'Fato Comunicado'"},
    }
