"""Apoio comum dos testes do painel de página única.

Os cards do painel são HTML (``ui.cartoes_html``), não ``st.metric``. Aqui eles são lidos de volta como objetos simples, com os mesmos
nomes que os testes já usavam (``label``, ``value``, ``delta``) e mais ``detalhe``, ``base``, ``ajuda`` e ``direction``.
"""

import html
import re
from types import SimpleNamespace

ROTULO_DIRECAO = {"up": "UP", "down": "DOWN", "off": "NONE"}


def cartoes(app) -> list:
    """Todos os cards do app, na ordem em que aparecem na página."""
    lista = []
    for elemento in app.get("html"):
        corpo = elemento.proto.body
        for pedaco in corpo.split('<div class="cartao" ')[1:]:
            campos = {nome: html.unescape(texto) for nome, texto in re.findall(r'class="cartao-(\w+)">(.*?)</div>', pedaco)}
            direcao = re.search(r'data-direcao="(\w+)"', pedaco).group(1)
            ajuda = html.unescape(re.search(r'title="([^"]*)"', pedaco).group(1))
            variacao = campos.get("variacao", "").lstrip("▲▼ ")
            lista.append(SimpleNamespace(label=campos["titulo"], titulo=campos["titulo"], value=campos["valor"], valor=campos["valor"],
                                         detalhe=campos.get("detalhe", ""), delta=variacao, base=campos.get("base", ""), ajuda=ajuda,
                                         direction=ROTULO_DIRECAO[direcao]))
    return lista


def texto_dos_cartoes(app) -> str:
    """Texto de todos os cards (título, detalhe, valor, variação, base e dica), para buscas por trechos."""
    return " ".join(f"{c.titulo} {c.detalhe} {c.valor} {c.delta} {c.base} {c.ajuda}" for c in cartoes(app))


def escolher_serie(app, evento: str, abrangencia: str = "Estadual"):
    """Seleciona a série "Indicador — Abrangência" (o filtro de abrangência não existe mais) e executa o app de novo."""
    app.selectbox(key="serie").select(f"{evento} — {abrangencia}").run()
    return app
