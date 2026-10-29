# ETL ÚNICO — SEGURANÇA PÚBLICA DE JOINVILLE/SC (Sinesp/MJSP e SSP/SC)
#
# Este roteiro lê os arquivos oficiais, trata, confere e grava as tabelas de Joinville/SC.
# Como executar (na pasta do projeto, com o ambiente virtual criado):
#   - VS Code: abra este arquivo e use "Run Cell" em cada bloco "# %%" (Python Interactive).
#   - Terminal: .\.venv\Scripts\python.exe scripts\etl_joinville.py
#
# Fontes (sempre separadas; nunca somadas entre si):
#   - Sinesp/MJSP: um XLSX nacional por ano (dados/brutos/sinesp/bancovde-ANO.xlsx); fica só Joinville/SC.
#   - SSP/SC: 45 relatórios em PDF (dados/brutos/ssp_sc/); violência doméstica e homicídios de Joinville.
#
# Segurança: o roteiro grava somente em dados/processados/etl_joinville/. A base publicada no painel
# (dashboard/data_publica/) nunca é alterada aqui; ela só muda pela atualização controlada do projeto.


# %% ETAPA 01 - IMPORTAÇÃO DAS BIBLIOTECAS
import hashlib
import json
import os
import sys
from pathlib import Path

import pandas as pd

# Pasta do projeto (a pasta acima de "scripts"); no VS Code Interactive usa-se a pasta atual.
raiz = Path(__file__).resolve().parent.parent if "__file__" in globals() else Path.cwd()
sys.path.insert(0, str(raiz))

# Partes do próprio projeto, já validadas:
from dashboard import dados_publicos as dp          # manifesto da versão aprovada e colunas oficiais
from src.pipeline import atualizacao_dados as au    # leitura do XLSX (só as linhas de Joinville)
from src.pipeline import ssp_sc                     # leitura e conferência dos PDFs da SSP/SC
from src.pipeline import versionamento_dados as vv  # lista oficial de indicadores e unidades

# Faz o terminal do Windows mostrar acentos e deixa as tabelas impressas mais largas.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
pd.set_option("display.width", 200)
pd.set_option("display.max_columns", 30)

# display() mostra tabelas formatadas no VS Code Interactive; no terminal comum, usamos print().
try:
    from IPython.display import display
except ImportError:
    display = print

print(f"Pandas {pd.__version__}")


# %% ETAPA 02 - DEFINIÇÃO DAS PASTAS
anos = list(range(2020, 2027))  # anos dos arquivos do Sinesp
pasta_xlsx = Path(os.environ.get("SINESP_PASTA_XLSX", raiz / "dados" / "brutos" / "sinesp"))
pasta_saida = Path(os.environ.get("ETL_PASTA_SAIDA", raiz / "dados" / "processados" / "etl_joinville"))

print(f"Arquivos do Sinesp: {pasta_xlsx}")
print(f"Arquivos da SSP/SC: {ssp_sc.PASTA_BRUTOS}")
print(f"Saída do ETL:       {pasta_saida}")


# %% ETAPA 03 - LEITURA DOS DADOS BRUTOS DO SINESP
# O manifesto da versão aprovada guarda o SHA-256 ("impressão digital") de cada XLSX oficial.
# Só é usado o arquivo cujo hash é igual ao registrado: assim o ETL reproduz exatamente a base aprovada.
manifesto = dp.carregar_manifesto()
hashes_aprovados = manifesto["origem_dos_dados"]["sinesp_xlsx_sha256"]

arquivos = {}
for ano in anos:
    for candidato in sorted(pasta_xlsx.rglob(f"bancovde-{ano}.xlsx")):
        if hashlib.sha256(candidato.read_bytes()).hexdigest() == hashes_aprovados[str(ano)]:
            arquivos[ano] = candidato
            break
    if ano not in arquivos:
        raise FileNotFoundError(f"XLSX de {ano} não encontrado (ou de outra edição) em {pasta_xlsx}. "
                                "Veja no README como obter os arquivos oficiais do Sinesp.")

# Cada XLSX nacional tem cerca de 24 MB; a função lê o XML da planilha e guarda só SC/JOINVILLE (14 colunas originais).
recortes = {}
for ano, caminho in arquivos.items():
    recortes[ano] = au.ler_sinesp_xlsx(caminho)
    print(f"{ano}: {caminho.name} -> {len(recortes[ano])} linhas de Joinville")


# %% ETAPA 04 - INSPEÇÃO DOS DATAFRAMES
# pd.concat() empilha as tabelas dos sete anos; ignore_index=True renumera as linhas.
dados_brutos = pd.concat(recortes.values(), ignore_index=True)
print(f"Dados brutos de Joinville: {dados_brutos.shape[0]} linhas x {dados_brutos.shape[1]} colunas")
display(dados_brutos.head())
dados_brutos.info()
# total_vitima é a medida dos indicadores de vítimas; total é a medida dos mandados de prisão.
print("Indicadores:", sorted(dados_brutos["evento"].unique()))
print("Classificações institucionais (abrangência):", sorted(dados_brutos["abrangencia"].unique()))


# %% ETAPA 05 - VERIFICAÇÃO DE DUPLICIDADES
# Nenhuma linha é apagada. A nota oficial do Sinesp diz que "Tentativa de homicídio" e "Estupro" podem ter
# mais de uma linha no mesmo mês (parcelas que devem ser somadas, na etapa 09). Em outro indicador, repetição é erro.
linhas_identicas = int(dados_brutos.duplicated().sum())
repeticoes_de_chave = int(dados_brutos.duplicated(subset=["evento", "abrangencia", "data_referencia"], keep=False).sum())
print(f"Linhas totalmente idênticas: {linhas_identicas}")
print(f"Linhas que repetem indicador + abrangência + mês: {repeticoes_de_chave}")


# %% ETAPA 06 - VERIFICAÇÃO DE VALORES AUSENTES
# Zero publicado é uma informação (a fonte disse "0"); valor ausente é a falta de informação e nunca vira zero.
# Na camada original, os campos vazios de total_vitima e total só mostram que cada linha usa uma das duas medidas.
ausencias = dados_brutos.isna().sum().rename("ausências").to_frame()
ausencias["%"] = (ausencias["ausências"] / len(dados_brutos) * 100).round(2)
display(ausencias)


# %% ETAPA 07 - TRATAMENTO DOS DADOS
# Cada linha original vira uma observação padronizada: ano, mes, evento, abrangencia, unidade e valor.
observacoes = []
for ano, recorte in recortes.items():
    for linha in recorte.itertuples(index=False):
        if linha.evento not in vv.NATUREZAS:
            raise ValueError(f"Indicador não previsto: {linha.evento!r} (exige decisão metodológica).")
        if pd.isna(linha.abrangencia):
            raise ValueError("Abrangência ausente.")
        # A data vem como número serial do Excel (dias contados a partir de 30/12/1899); deve ser dia 1 do ano do arquivo.
        if pd.isna(linha.data_referencia) or float(linha.data_referencia) != int(linha.data_referencia):
            raise ValueError(f"Data inválida: {linha.data_referencia!r}")
        data = pd.Timestamp("1899-12-30") + pd.Timedelta(days=int(linha.data_referencia))
        if data.day != 1 or data.year != ano:
            raise ValueError(f"Competência inesperada ({data.date()}) no arquivo de {ano}.")
        # Vítimas e mandados têm unidades diferentes e nunca são somados.
        mandado = linha.evento == vv.EVENTO_MANDADO
        valor = linha.total if mandado else linha.total_vitima
        if pd.isna(valor):
            valor = pd.NA                      # ausência continua ausência
        elif valor < 0 or float(valor) != int(valor):
            raise ValueError(f"Valor inválido (esperado inteiro não negativo): {valor!r}")
        else:
            valor = int(valor)
        observacoes.append({"ano": data.year, "mes": data.month, "evento": linha.evento, "abrangencia": str(linha.abrangencia),
                            "unidade": vv.UNIDADE_MANDADOS if mandado else vv.UNIDADE_VITIMAS, "valor": valor})

dados_tratados = pd.DataFrame(observacoes)
# Int64 (com "I" maiúsculo) é o inteiro do pandas que aceita ausência (<NA>); o int64 comum obrigaria a inventar um número.
dados_tratados[["ano", "mes"]] = dados_tratados[["ano", "mes"]].astype("int64")
dados_tratados["valor"] = dados_tratados["valor"].astype("Int64")
print(f"Observações padronizadas: {len(dados_tratados)}")
print(f"Valores ausentes: {int(dados_tratados['valor'].isna().sum())} | zeros publicados: {int(dados_tratados['valor'].eq(0).sum())}")
display(dados_tratados.head())


# %% ETAPA 08 - FILTRO DO MUNICÍPIO DE JOINVILLE
# O filtro foi feito na leitura (etapa 03), porque o arquivo nacional tem milhões de linhas. Aqui conferimos o resultado.
print(f"Todas as linhas são de SC: {bool(dados_brutos['uf'].eq('SC').all())}")
print(f"Todas as linhas são de JOINVILLE: {bool(dados_brutos['municipio'].eq('JOINVILLE').all())}")
print(f"Linhas de outros municípios: {int((~dados_brutos['municipio'].eq('JOINVILLE')).sum())}")


# %% ETAPA 09 - ORGANIZAÇÃO DOS INDICADORES SINESP
# Objetivo: uma linha por série (indicador + classificação) e mês.
# groupby() junta as linhas de mesma chave e soma os valores; sum(min_count=1) devolve <NA> (e não 0) se todas as parcelas são vazias.
chave = ["evento", "abrangencia", "ano", "mes"]
repetidas = dados_tratados[dados_tratados.duplicated(chave, keep=False)]
nao_permitidos = set(repetidas["evento"]) - set(vv.EVENTOS_COM_LINHAS_MULTIPLAS)
if nao_permitidos:
    raise ValueError(f"Repetição sem nota oficial de soma em: {sorted(nao_permitidos)}")
print(f"Linhas repetidas somadas conforme a nota oficial: {len(repetidas)}")

dados_processados = dados_tratados.groupby(chave + ["unidade"], as_index=False, sort=False)["valor"].agg(lambda parcelas: parcelas.sum(min_count=1))
dados_processados = dados_processados[dp.COLUNAS_SINESP]  # volta à ordem oficial das colunas
dados_processados = dados_processados.sort_values(chave, kind="stable").reset_index(drop=True)
dados_processados["valor"] = dados_processados["valor"].astype("Int64")
dados_processados[["ano", "mes"]] = dados_processados[["ano", "mes"]].astype("int64")

# Catálogo: resumo de cada série (início, fim, meses, meses com valor, zeros publicados e ausências).
competencia = dados_processados["ano"].astype(str) + "-" + dados_processados["mes"].astype(str).str.zfill(2)
catalogo = (dados_processados.assign(competencia=competencia).groupby(["evento", "abrangencia", "unidade"])
            .agg(inicio=("competencia", "min"), fim=("competencia", "max"), meses=("valor", "size"), com_valor=("valor", "count"),
                 zeros=("valor", lambda valores: int((valores == 0).sum()))).reset_index())
catalogo["sem_valor"] = catalogo["meses"] - catalogo["com_valor"]
display(catalogo)


# %% ETAPA 10 - CONFERÊNCIA DOS RESULTADOS
# Regras de qualidade da base mensal. Índice contínuo de meses = ano x 12 + mês (para ver se alguma série pula meses).
indice_mes = dados_processados["ano"] * 12 + dados_processados["mes"] - 1
sem_lacuna = all((indices.sort_values().diff().dropna() == 1).all()
                 for _, indices in indice_mes.groupby([dados_processados["evento"], dados_processados["abrangencia"]]))
regras = {
    "colunas na ordem oficial": list(dados_processados.columns) == dp.COLUNAS_SINESP,
    "sem competência repetida": not dados_processados.duplicated(chave).any(),
    "séries com meses consecutivos": sem_lacuna,
    "uma unidade por série": bool(dados_processados.groupby(["evento", "abrangencia"])["unidade"].nunique().eq(1).all()),
    "valores inteiros não negativos (ou ausentes)": bool((dados_processados["valor"].dropna() >= 0).all()),
}
for regra, aprovada in regras.items():
    print(f"{'OK ' if aprovada else 'ERRO'} {regra}")

# Comparação com a base aprovada e publicada no painel (valores, tipos, ordem) e com o hash do manifesto.
base_publicada = dp.carregar_sinesp()
catalogo_publicado = dp.carregar_catalogo_sinesp()
csv_mensal = dados_processados.to_csv(index=False, lineterminator="\n", na_rep="").encode("utf-8")  # sem caminho: nada é gravado
hash_gerado = dp.sha256_normalizado(csv_mensal)
hash_aprovado = next(f["sha256"] for f in manifesto["arquivos"] if f["arquivo"] == dp.ARQ_SINESP)
base_igual = dados_processados.astype(base_publicada.dtypes.to_dict()).equals(base_publicada)
catalogo_igual = (catalogo["meses"].tolist() == catalogo_publicado["meses_observados"].astype(int).tolist()
                  and catalogo["fim"].tolist() == catalogo_publicado["fim"].tolist()
                  and catalogo[["evento", "abrangencia"]].reset_index(drop=True).equals(catalogo_publicado[["evento", "abrangencia"]].reset_index(drop=True)))
print(f"Observações: {len(dados_processados)} | séries: {len(catalogo)} | zeros publicados: {int(dados_processados['valor'].eq(0).sum())} | "
      f"valores ausentes: {int(dados_processados['valor'].isna().sum())} | último mês: {catalogo['fim'].max()}")
print(f"Base reconstruída igual à publicada: {base_igual}")
print(f"SHA-256 reconstruído igual ao do manifesto: {hash_gerado == hash_aprovado}")
print(f"Catálogo igual ao publicado: {catalogo_igual}")
# Se algo divergir, o roteiro para aqui: nada diferente da versão aprovada é gravado.
assert all(regras.values()) and base_igual and hash_gerado == hash_aprovado and catalogo_igual, "A reconstrução diverge da base aprovada: revisar."


# %% ETAPA 11 - LEITURA DOS DADOS SSP/SC
# Fonte: 45 relatórios em PDF (42 boletins mensais e 3 relatórios de violência doméstica), cada um com um CSV que indica a
# página, a tabela e a linha de cada célula. O CSV localiza os valores; o PDF continua sendo o documento oficial.
if not ssp_sc.acervo_disponivel():
    raise FileNotFoundError("Acervo da SSP/SC incompleto: são esperados 45 PDFs e 45 CSVs em dados/brutos/ssp_sc/.")
inventario = ssp_sc.inventariar_acervo()
print(f"PDFs: {len(inventario)} | pares PDF + CSV completos: {int(inventario['par_completo'].sum())} | PDFs repetidos: {int(inventario['pdf_duplicado'].sum())}")
display(inventario[["arquivo_pdf", "tipo_documento", "bytes_pdf", "par_completo"]].head())


# %% ETAPA 12 - TRATAMENTO E CONFERÊNCIA DA SSP/SC
# processar() lê o bloco de JOINVILLE de cada relatório, trata e confere cada célula usada contra a tabela do próprio PDF.
# Cada valor é rastreável até o PDF, a página, a tabela e a linha.
resultado = ssp_sc.processar()
violencia = resultado["vd"]
verificacoes = resultado["verificacoes"]
homicidios_grupos = resultado["grupos"]

print(f"Violência doméstica: {len(violencia)} observações | {violencia['indicador'].nunique()} categorias | "
      f"{violencia[['ano', 'mes']].drop_duplicates().shape[0]} meses | zeros publicados: {int(violencia['valor'].eq(0).sum())} | "
      f"ausentes: {int(violencia['valor'].isna().sum())}")
print(f"Unidade: {sorted(violencia['unidade'].unique())} (definição operacional não identificada nos documentos analisados;"
      " não é tratada como vítimas nem como ocorrências únicas)")
print(f"Verificações contra os PDFs: {int(verificacoes['ok'].sum())} aprovadas de {len(verificacoes)}")
print(f"Homicídios: {len(homicidios_grupos)} números republicados em mais de uma edição, {int(homicidios_grupos['divergente'].sum())} com versões "
      "diferentes (nenhuma versão é escolhida)")
assert len(violencia) == 216 and violencia["indicador"].nunique() == 9 and violencia["valor"].isna().sum() == 0
assert list(violencia["unidade"].unique()) == [ssp_sc.UNIDADE_VD] and bool(verificacoes["ok"].all())


# %% ETAPA 13 - EXPORTAÇÃO DOS DADOS TRATADOS
# Sinesp e SSP/SC são gravados em pastas separadas: as duas fontes não são misturadas nem somadas.
pasta_sinesp = pasta_saida / "sinesp"
pasta_ssp = pasta_saida / "ssp_sc"
assert pasta_saida.resolve() != dp.DIRETORIO_DADOS.resolve(), "O ETL não pode gravar sobre a base publicada no painel."
pasta_sinesp.mkdir(parents=True, exist_ok=True)
pasta_ssp.mkdir(parents=True, exist_ok=True)

# Sinesp
dados_brutos.to_csv(pasta_sinesp / "etl_recorte_joinville_bruto.csv", index=False, encoding="utf-8", lineterminator="\n")
(pasta_sinesp / "etl_sinesp_joinville_mensal.csv").write_bytes(csv_mensal)   # o mesmo conteúdo conferido na etapa 10
catalogo.to_csv(pasta_sinesp / "etl_catalogo_series.csv", index=False, encoding="utf-8", lineterminator="\n")
relatorio_sinesp = {
    "observacoes": int(len(dados_processados)), "series": int(len(catalogo)), "zeros_publicados": int(dados_processados["valor"].eq(0).sum()),
    "valores_ausentes": int(dados_processados["valor"].isna().sum()), "competencia_final": str(catalogo["fim"].max()),
    "sha256_base_mensal": hash_gerado, "igual_a_base_publicada": bool(base_igual), "versao_publicada": manifesto["versao"],
    "xlsx": {str(ano): {"arquivo": caminho.name, "sha256": hashes_aprovados[str(ano)]} for ano, caminho in arquivos.items()},
}
(pasta_sinesp / "etl_relatorio.json").write_text(json.dumps(relatorio_sinesp, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# SSP/SC
tabelas_ssp = {
    "inventario_acervo_ssp_sc.csv": resultado["inventario"],
    "violencia_domestica_joinville_tratada.csv": violencia,
    "homicidios_boletins_joinville_versoes.csv": resultado["versoes"],
    "homicidios_republicacoes_grupos.csv": homicidios_grupos.astype({"valores_publicados_distintos": str}),
    "verificacoes_extracao_ssp_sc.csv": verificacoes,
    "rastreabilidade_celulas_ssp_sc.csv": resultado["rastreabilidade"],
}
for nome, tabela in tabelas_ssp.items():
    tabela.to_csv(pasta_ssp / nome, index=False, encoding="utf-8", lineterminator="\n")
originais_inalterados = ssp_sc.inventariar_acervo()["sha256_pdf"].tolist() == inventario["sha256_pdf"].tolist()
relatorio_ssp = {**resultado["resumo"], "originais_inalterados": originais_inalterados, "arquivos_gerados": sorted(tabelas_ssp)}
(pasta_ssp / "relatorio_auditoria_ssp_sc.json").write_text(json.dumps(relatorio_ssp, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"Arquivos gravados em {pasta_saida}:")
for arquivo in sorted(pasta_saida.rglob("*.*")):
    print(f"  {arquivo.relative_to(pasta_saida).as_posix()} ({arquivo.stat().st_size} bytes)")


# %% ETAPA 14 - VALIDAÇÕES FINAIS
# Relê os arquivos gravados (não as variáveis em memória) e confere os números de referência.
mensal_gravado = pd.read_csv(pasta_sinesp / "etl_sinesp_joinville_mensal.csv")
vd_gravada = pd.read_csv(pasta_ssp / "violencia_domestica_joinville_tratada.csv")
sinesp_ok = (len(mensal_gravado) == 911 and int(mensal_gravado["valor"].eq(0).sum()) == 401 and int(mensal_gravado["valor"].isna().sum()) == 0
             and mensal_gravado[["evento", "abrangencia"]].drop_duplicates().shape[0] == 12)
ssp_ok = (len(vd_gravada) == 216 and vd_gravada["indicador"].nunique() == 9 and int(vd_gravada["valor"].eq(0).sum()) == 27
          and set(vd_gravada["unidade"]) == {"Fato Comunicado"})
print(f"Sinesp: 911 observações, 12 séries, 401 zeros publicados, 0 ausentes -> {'OK' if sinesp_ok else 'ERRO'}")
print(f"SSP/SC: 216 observações, 9 categorias, 27 zeros publicados, unidade 'Fato Comunicado' -> {'OK' if ssp_ok else 'ERRO'}")
print(f"PDFs da SSP/SC inalterados: {originais_inalterados} | versão publicada no painel: {manifesto['versao']} (não alterada)")
assert sinesp_ok and ssp_ok and originais_inalterados
print("ETL concluído sem divergências.")
