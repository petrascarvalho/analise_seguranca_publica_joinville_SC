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


def textos_visiveis(app) -> list:
    """Todo o texto que o visitante lê no estado atual do app: títulos, textos, avisos, legendas, rótulos, dicas, cards e tabelas."""
    textos = []
    for lista in (app.title, app.header, app.subheader, app.markdown, app.caption, app.info, app.warning, app.success, app.error):
        textos += [e.value for e in lista]
    textos += [e.label for e in app.expander] + [t.label for t in app.tabs]
    for w in list(app.selectbox) + list(app.select_slider) + list(app.toggle) + list(app.button) + list(app.radio) + list(app.multiselect):
        textos += [w.label, getattr(w, "help", None) or ""]
    textos += [f"{c.titulo} {c.detalhe} {c.valor} {c.delta} {c.base} {c.ajuda}" for c in cartoes(app)]
    for d in app.dataframe:
        tabela = d.value
        textos += [str(c) for c in tabela.columns]
        textos += [str(v) for v in tabela.to_numpy().ravel()]
    return [t for t in textos if t]
