"""Gera, a partir dos dados publicados (sem dados fictícios), as imagens para a revisão visual dos gráficos do dashboard.

Saída em ``revisao_visual/`` (pasta local, ignorada pelo Git), com um índice ``INDICE.md``:

* ``telas/desktop_1366/``, ``telas/celular_390/`` e ``telas/celular_350/`` — cada gráfico "montado em uma tela" com a largura do dispositivo,
  como o Streamlit o exibiria: figura ajustada à largura útil, os textos explicativos como texto nativo abaixo dela (só no modo compacto) e a
  indicação do expander com a tabela. O desktop usa a figura completa; os celulares usam a figura do **modo compacto**;
* ``selecao_aprovacao/`` — 16 imagens escolhidas (desktop × celular do mesmo gráfico, casos difíceis, séries com zeros, outliers e o "antes"
  = figura completa reduzida à largura do celular).

É uma SIMULAÇÃO por imagens: ela mostra tamanhos, cortes e legibilidade, mas **não substitui o teste em um navegador ou em um celular real**.

Uso (a partir da raiz do projeto)::

    python -m ferramentas.gerar_revisao_visual [--saida revisao_visual]
"""

from __future__ import annotations

import argparse
import io
import sys
import textwrap
from pathlib import Path

import matplotlib
from PIL import Image, ImageDraw, ImageFont

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

from dashboard import calculos, graficos  # noqa: E402
from dashboard import dados_publicos as dp  # noqa: E402

ANOS = list(range(2020, 2027))
# nome da tela: (largura da tela, largura útil da figura, modo compacto?)
TELAS = {"desktop_1366": (1366, 1000, False), "celular_390": (390, 358, True), "celular_350": (350, 318, True)}
SERIES = [
    ("homicidio_doloso", "Homicídio doloso", "Estadual"),
    ("mandados_estadual", "Mandado de prisão cumprido", "Estadual"),
    ("mortes_transito_prf", "Mortes no trânsito", "Polícia Rodoviária Federal"),
    ("feminicidio", "Feminicídio", "Estadual"),
    ("latrocinio", "Roubo seguido de morte (latrocínio)", "Estadual"),
    ("todos_zero_mortes_a_esclarecer", "Mortes a esclarecer (sem indício de crime)", "Estadual"),
]
GRAFICOS = {
    "mensal": ("Evolução mensal", lambda s, e, a, anos: graficos.figura_mensal_sinesp(s, e, a, anos)),
    "acumulado": ("Acumulado anual", lambda s, e, a, anos: graficos.figura_acumulado_sinesp(s, e, a, anos)),
    "histograma": ("Distribuição em faixas de contagem", lambda s, e, a, anos: graficos.figura_distribuicao_sinesp(s, e, a, anos)),
    "mapa_calor": ("Mapa de calor ano × mês", lambda s, e, a, anos: graficos.figura_mapa_calor_sinesp(s, e, a, anos)),
    "boxplot": ("Boxplot por ano", lambda s, e, a, anos: graficos.figura_boxplot_anual_sinesp(s, e, a, anos)),
    "outliers": ("Outliers (IQR)", lambda s, e, a, anos: graficos.figura_outliers_iqr_sinesp(s, e, a, anos)),
    "periodos": ("Períodos equivalentes", lambda s, e, a, anos: graficos.figura_periodo_sinesp(s, e, a, anos, calculos.mes_final_da_serie(calculos.serie_sinesp(s, e, a)))),
}
FONTE = ImageFont.truetype(str(Path(matplotlib.get_data_path()) / "fonts" / "ttf" / "DejaVuSans.ttf"), 13)


def _figura_em_imagem(figura) -> Image.Image:
    memoria = io.BytesIO()
    figura.savefig(memoria, format="png")
    memoria.seek(0)
    return Image.open(memoria).convert("RGB")


def _linhas(texto: str, largura: int) -> list[str]:
    """Quebra o texto em linhas que cabem em ``largura`` pixels (fonte do Streamlit simulada)."""
    saida, atual = [], ""
    for palavra in texto.split():
        tentativa = f"{atual} {palavra}".strip()
        if FONTE.getlength(tentativa) <= largura:
            atual = tentativa
        else:
            saida.append(atual)
            atual = palavra
    return saida + [atual] if atual else saida


def montar_tela(figura, nome_tela: str, compacto: bool, legenda_expander: bool = True) -> Image.Image:
    """Figura ajustada à largura útil da tela + textos nativos (modo compacto) + indicação da tabela de apoio."""
    largura_tela, largura_util, _ = TELAS[nome_tela]
    if compacto:
        graficos.ajustar_compacto(figura)  # o mesmo ajuste que a página aplica antes de exibir
    imagem = _figura_em_imagem(figura)
    imagem = imagem.resize((largura_util, round(imagem.height * largura_util / imagem.width)), Image.LANCZOS)
    margem = 16 if largura_tela < 600 else 24
    barra = 280 if largura_tela > 1000 else 0  # barra lateral do Streamlit no desktop
    textos = []
    notas = getattr(figura, "sinesp_notas", None)
    if compacto and notas:
        textos += [notas["interpretacao"], notas["rodape"]]
    linhas = [l for t in textos for l in _linhas(t, largura_util) + [""]]
    altura_texto = 18 * len(linhas) + (34 if legenda_expander else 0)
    tela = Image.new("RGB", (largura_tela, imagem.height + altura_texto + 2 * margem), "white")
    desenho = ImageDraw.Draw(tela)
    if barra:
        desenho.rectangle([0, 0, barra, tela.height], fill="#F0F2F6")
        desenho.text((16, 16), "Streamlit — barra lateral", fill="#555555", font=FONTE)
    x = barra + margem if barra else margem
    tela.paste(imagem, (x, margem))
    y = margem + imagem.height + 6
    for linha in linhas:
        desenho.text((x, y), linha, fill="#555555", font=FONTE)
        y += 18
    if legenda_expander:
        desenho.rectangle([x, y + 4, x + largura_util, y + 30], outline="#CCCCCC")
        desenho.text((x + 8, y + 10), "▸ Valores usados neste gráfico (tabela)", fill="#333333", font=FONTE)
    desenho.rectangle([0, 0, tela.width - 1, tela.height - 1], outline="#DDDDDD")
    return tela


def _figura(sinesp, evento, abrangencia, grafico, compacto, anos=ANOS):
    with graficos.modo_compacto(compacto):
        return GRAFICOS[grafico][1](sinesp, evento, abrangencia, anos)


def gerar(saida: Path) -> list[dict]:
    sinesp = dp.carregar_sinesp()
    registros = []
    for nome_tela, (_, _, compacto) in TELAS.items():
        (saida / "telas" / nome_tela).mkdir(parents=True, exist_ok=True)
        for prefixo, evento, abrangencia in SERIES:
            for grafico in GRAFICOS:
                figura = _figura(sinesp, evento, abrangencia, grafico, compacto)
                arquivo = f"{prefixo}__{grafico}.png"
                if figura is None:
                    registros.append({"tela": nome_tela, "serie": prefixo, "grafico": grafico, "arquivo": None})
                    continue
                montar_tela(figura, nome_tela, compacto).save(saida / "telas" / nome_tela / arquivo)
                registros.append({"tela": nome_tela, "serie": prefixo, "grafico": grafico, "arquivo": arquivo})
    return registros


SELECAO = [
    # (arquivo, tela, série, gráfico, modo, anos, o que demonstra)
    ("01_homicidio_acumulado_desktop", "desktop_1366", "homicidio_doloso", "acumulado", False, ANOS, "Desktop: rótulos finais sem colisão; 2026 parcial identificado"),
    ("02_homicidio_acumulado_celular390", "celular_390", "homicidio_doloso", "acumulado", True, ANOS, "Celular 390: legenda com o valor final de cada ano, abaixo do gráfico"),
    ("03_ANTES_homicidio_acumulado_celular390", "celular_390", "homicidio_doloso", "acumulado", False, ANOS, "ANTES: a figura completa reduzida à largura do celular (texto ilegível)"),
    ("04_prf_mensal_desktop", "desktop_1366", "mortes_transito_prf", "mensal", False, ANOS, "Desktop: sete anos na mesma figura"),
    ("05_prf_mensal_celular390_3anos", "celular_390", "mortes_transito_prf", "mensal", True, [2024, 2025, 2026], "Celular 390: três anos escolhidos (o seletor informa 'Exibindo 3 de 7'); PRF termina em agosto/2026"),
    ("06_ANTES_prf_mensal_celular390", "celular_390", "mortes_transito_prf", "mensal", False, ANOS, "ANTES: sete linhas e legenda reduzidas ao celular"),
    ("07_mandados_faixas_desktop", "desktop_1366", "mandados_estadual", "histograma", False, ANOS, "Desktop: faixas de contagem; zero próprio; sem faixa vazia entre 0 e 31"),
    ("08_mandados_faixas_celular390", "celular_390", "mandados_estadual", "histograma", True, ANOS, "Celular 390: mesmas frequências, rótulos inclinados legíveis"),
    ("09_homicidio_outliers_desktop", "desktop_1366", "homicidio_doloso", "outliers", False, ANOS, "Desktop: Q1–Q3, mediana, limite superior (9,5) e os dois pontos fora"),
    ("10_homicidio_outliers_celular390", "celular_390", "homicidio_doloso", "outliers", True, ANOS, "Celular 390: legenda curta; detalhes no texto e na tabela abaixo"),
    ("11_latrocinio_outliers_celular350", "celular_350", "latrocinio", "outliers", True, ANOS, "Celular 350: método IQR não informativo (mensagem quebrada em linhas)"),
    ("12_zerada_mapa_calor_celular350", "celular_350", "todos_zero_mortes_a_esclarecer", "mapa_calor", True, ANOS, "Celular 350: série toda zero; aviso fora das células; meses sem valor em cinza"),
    ("13_homicidio_mapa_calor_celular390", "celular_390", "homicidio_doloso", "mapa_calor", True, ANOS, "Celular 390: meses por extenso nas linhas, anos nas colunas"),
    ("14_feminicidio_boxplot_celular350", "celular_350", "feminicidio", "boxplot", True, ANOS, "Celular 350: boxplot com poucos eventos e IQR = 0"),
    ("15_homicidio_boxplot_celular390", "celular_390", "homicidio_doloso", "boxplot", True, ANOS, "Celular 390: sete anos, pontos atípicos e n por ano"),
    ("16_homicidio_periodos_celular390", "celular_390", "homicidio_doloso", "periodos", True, ANOS, "Celular 390: janeiro–setembro por ano (períodos equivalentes)"),
]


def gerar_selecao(saida: Path) -> list[tuple]:
    sinesp = dp.carregar_sinesp()
    destino = saida / "selecao_aprovacao"
    destino.mkdir(parents=True, exist_ok=True)
    series = {prefixo: (evento, abrangencia) for prefixo, evento, abrangencia in SERIES}
    for arquivo, tela, serie, grafico, compacto, anos, _ in SELECAO:
        evento, abrangencia = series[serie]
        figura = _figura(sinesp, evento, abrangencia, grafico, compacto, anos)
        montar_tela(figura, tela, compacto).save(destino / f"{arquivo}.png")
    return SELECAO


def escrever_indice(saida: Path, registros: list[dict]) -> None:
    gerados = sum(1 for r in registros if r["arquivo"])
    linhas = [
        "# Revisão visual — modo compacto (Etapa 20.2)", "",
        "Imagens geradas por `python -m ferramentas.gerar_revisao_visual` a partir dos dados publicados (nenhum dado fictício). Pasta local, ignorada pelo Git.", "",
        "> **Simulação por imagens.** Cada PNG monta o gráfico em uma tela com a largura do dispositivo (desktop 1366, celular 390 e celular 350). "
        "Mostra tamanhos, cortes e legibilidade, mas **não é uma validação real da interface**: falta o teste em navegador e em celular de verdade.", "",
        "## Seleção para aprovação (`selecao_aprovacao/`)", "", "| Arquivo | O que demonstra |", "|---|---|",
    ]
    linhas += [f"| `{a}.png` | {d} |" for a, _, _, _, _, _, d in SELECAO]
    linhas += ["", f"## Grade completa (`telas/`) — {gerados} imagens", "",
               "Pastas `desktop_1366/` (figura completa), `celular_390/` e `celular_350/` (figura compacta). Nome: `<série>__<gráfico>.png`.",
               "Séries: " + ", ".join(p for p, _, _ in SERIES) + ".", "Gráficos: " + ", ".join(GRAFICOS) + ".", "",
               "## O que avaliar", "",
               "título e subtítulo inteiros · fonte e unidade · legenda sem corte nem sobreposição · rótulos legíveis no tamanho do celular · "
               "valores inteiros e eixo a partir de zero · avisos metodológicos (IQR, série sem variação) · cores consistentes por ano.", ""]
    (saida / "INDICE.md").write_text("\n".join(linhas), encoding="utf-8", newline="\n")


def main(argv: list[str] | None = None) -> int:
    analisador = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    analisador.add_argument("--saida", type=Path, default=RAIZ / "revisao_visual", help="pasta de saída (padrão: revisao_visual/)")
    argumentos = analisador.parse_args(argv)
    registros = gerar(argumentos.saida)
    gerar_selecao(argumentos.saida)
    escrever_indice(argumentos.saida, registros)
    print(f"{sum(1 for r in registros if r['arquivo'])} telas em {argumentos.saida / 'telas'}; {len(SELECAO)} imagens em {argumentos.saida / 'selecao_aprovacao'}. "
          f"Índice: {argumentos.saida / 'INDICE.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
