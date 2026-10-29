"""Formatação numérica brasileira (milhar com ponto, decimal com vírgula)."""

from __future__ import annotations

import pandas as pd

# Traço mostrado no lugar de um número ausente (o painel nunca troca ausência por zero).
TRACO = "—"


def _ausente(valor) -> bool:
    """Diz se o valor é vazio (None ou NaN); texto nunca conta como ausente."""
    # pd.isna reconhece os vazios do pandas (NaN e <NA>); isinstance evita testar textos.
    return valor is None or (not isinstance(valor, str) and bool(pd.isna(valor)))


def fmt_int(valor) -> str:
    """1957 → '1.957'; ausente → '—' (nunca '0')."""
    if _ausente(valor):
        return TRACO
    # O Python escreve 1,957 (padrão americano); replace troca a vírgula pelo ponto: 1.957.
    return f"{int(valor):,}".replace(",", ".")


def fmt_dec(valor, casas: int = 2) -> str:
    """168.4167 → '168,42'; ausente → '—'."""
    if _ausente(valor):
        return TRACO
    # Troca os separadores em três passos (com § como marcador temporário): 1,234.56 vira 1.234,56.
    return f"{float(valor):,.{casas}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def fmt_pct(valor, casas: int = 2, *, sinal: bool = True) -> str:
    """6.54 → '+6,54%'; ausente → 'n/a' (variação não aplicável, p.ex. base zero)."""
    if _ausente(valor):
        return "n/a"
    texto = fmt_dec(abs(float(valor)), casas)
    prefixo = ("+" if float(valor) > 0 else "−" if float(valor) < 0 else "") if sinal else ("−" if float(valor) < 0 else "")
    return f"{prefixo}{texto}%"


def fmt_dif(valor) -> str:
    """Diferença absoluta com sinal: 128 → '+128'; -9 → '−9'."""
    if _ausente(valor):
        return TRACO
    numero = int(valor)
    return f"+{fmt_int(numero)}" if numero > 0 else (f"−{fmt_int(abs(numero))}" if numero < 0 else "0")


# Nomes dos meses (índice 0 = janeiro), usados em textos e rótulos.
NOMES_MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
ABREV_MESES = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")


def fmt_mes_extenso(competencia: str) -> str:
    """Competência no formato do arquivo ('2026-09') em frase de texto corrido: 'setembro de 2026'."""
    try:
        ano, mes = str(competencia).split("-")[:2]
        return f"{NOMES_MESES[int(mes) - 1]} de {ano}"
    except (ValueError, IndexError):
        return str(competencia)


def fmt_competencia(competencia: str, *, curto: bool = False) -> str:
    """Competência no formato do arquivo ('2026-09') em texto para o público: 'setembro/2026' (ou 'set/2026' se curto=True)."""
    try:
        ano, mes = str(competencia).split("-")[:2]
        nome = ABREV_MESES[int(mes) - 1].lower() if curto else NOMES_MESES[int(mes) - 1]
        return f"{nome}/{ano}"
    except (ValueError, IndexError):
        return str(competencia)
