"""Formatação numérica brasileira (milhar com ponto, decimal com vírgula)."""

from __future__ import annotations

import pandas as pd

TRACO = "—"


def _ausente(valor) -> bool:
    return valor is None or (not isinstance(valor, str) and bool(pd.isna(valor)))


def fmt_int(valor) -> str:
    """1957 → '1.957'; ausente → '—' (nunca '0')."""
    if _ausente(valor):
        return TRACO
    return f"{int(valor):,}".replace(",", ".")


def fmt_dec(valor, casas: int = 2) -> str:
    """168.4167 → '168,42'; ausente → '—'."""
    if _ausente(valor):
        return TRACO
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


NOMES_MESES = ("janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro")
ABREV_MESES = ("Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez")


def fmt_competencia(competencia: str, *, curto: bool = False) -> str:
    """Competência no formato do arquivo ('2026-09') em texto para o público: 'setembro/2026' (ou 'set/2026' se curto=True)."""
    try:
        ano, mes = str(competencia).split("-")[:2]
        nome = ABREV_MESES[int(mes) - 1].lower() if curto else NOMES_MESES[int(mes) - 1]
        return f"{nome}/{ano}"
    except (ValueError, IndexError):
        return str(competencia)
