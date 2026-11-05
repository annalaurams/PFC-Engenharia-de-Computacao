import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from kneed import KneeLocator
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.model_selection import ParameterGrid
from sklearn.preprocessing import RobustScaler


def _preparar_sys_path():
    """Adiciona ao sys.path a pasta de População, onde está utilitarios_comuns.py."""
    raiz_do_projeto = Path(__file__).resolve().parent.parent.parent
    candidatos = [
        raiz_do_projeto / "Seleção e Transformação" / "População",
        Path.home() / "tcc" / "Seleção e Transformação" / "População",
    ]
    pasta = None
    for candidato in candidatos:
        if (candidato / "utilitarios_comuns.py").exists():
            pasta = candidato
            break
    if pasta is None:
        raise ModuleNotFoundError(
            "Não encontrei 'utilitarios_comuns.py' em nenhum destes caminhos:\n"
            + "\n".join(f"  - {candidato}" for candidato in candidatos)
            + f"\n\nDiagnóstico do kernel atual:\n  Python: {sys.executable}\n  CWD: {Path.cwd()}"
        )
    sys.path.append(str(pasta))
    return pasta


_preparar_sys_path()

from utilitarios_comuns import (  # noqa: E402
    COLUNA_ANO,
    COLUNA_REGIONAL,
    FAIXAS_ETARIAS_PADRAO,
    PASTA_POPULACAO,
    PASTA_SELECAO_TRANSFORMACAO,
    SUFIXO_COLUNA_TAXA,
    ESPECIFICACOES_VARIAVEIS,
    ESPECIFICACOES_VARIAVEIS_CATEGORICAS,
    registrar_log,
)

PASTA_TAXA = PASTA_POPULACAO / "Taxa"

CAMINHO_MUNICIPIOS_REGIONAIS = PASTA_SELECAO_TRANSFORMACAO / "Municípios" / "tabela_municipios_regionais.csv"
CAMINHO_POPULACAO_POR_REGIONAL = (
    PASTA_POPULACAO / "Interpolação e Extrapolação" / "populacao_interpolacao_extrapolacao_por_regional.csv"
)

# Constantes de configuração

SEMENTE_ALEATORIA_FIXA = 42  # semente única usada em todo o pipeline principal (não há teste de sensibilidade à semente no TCC)


def _bloco(nome, prefixo, especificacao, ano_inicial_override=None):
    """Monta a configuração de um bloco de taxa; `ano_inicial_override` sobrepõe o ANO_INICIAL declarado."""
    ano_inicial = especificacao["ANO_INICIAL"]
    if ano_inicial_override is not None:
        ano_inicial = ano_inicial_override

    return {
        "NOME": nome,
        "PREFIXO": prefixo,
        "ARQUIVO": especificacao["NOME_ARQUIVO_SAIDA_TAXA"],
        "ANO_INICIAL": ano_inicial,
        "ANO_FINAL": especificacao["ANO_FINAL"],
    }


BLOCOS_DE_TAXA = [
    _bloco("Casos por Faixa Etária", "casos-faixa", ESPECIFICACOES_VARIAVEIS_CATEGORICAS["Casos por Faixa Etária"]),
    _bloco("Casos por Escolaridade", "casos-escolaridade", ESPECIFICACOES_VARIAVEIS_CATEGORICAS["Casos por Escolaridade"]),
    _bloco("Casos por Raça e Cor", "casos-raca-cor", ESPECIFICACOES_VARIAVEIS_CATEGORICAS["Casos por Raça e Cor"]),
    _bloco("Mortalidade", "mortalidade", ESPECIFICACOES_VARIAVEIS["Mortalidade"]),
    _bloco("Mamografia", "mamografia", ESPECIFICACOES_VARIAVEIS["Mamografia"], ano_inicial_override=2014),
]

SLUGS_DE_CATEGORIA_DESCARTADOS = ("sem-informacao", "total")

USAR_JANELA_COMUM = True
ANO_INICIAL_COMUM = 2014
ANO_FINAL_COMUM = 2023

# Proporção máxima de nulos para manter uma coluna
LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA = 0.05

# PCA: None decide pela razão atributos/linhas; True força; False pula
USAR_PCA = False

RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA = 0.10
VARIANCIA_EXPLICADA_ALVO = 0.85
NUMERO_MAXIMO_DE_COMPONENTES = 10

# Escolha de k pelo cotovelo da curva de inércia
K_MINIMO = 2
K_MAXIMO = 12  # teto da varredura de k
SENSIBILIDADE_COTOVELO = 1.0  # parâmetro S do KneeLocator
SEMENTES_DA_BUSCA = [0, 10, 30, 42, 66]  # sementes para testar a sensibilidade à inicialização
EXECUTAR_TESTE_DE_SENSIBILIDADE_DA_SEMENTE = False  # Teste de sensibilidade à semente: não utilizado no TCC
NUMERO_DE_INICIALIZACOES = 10  # n_init do KMeans
MAXIMO_DE_ITERACOES = 30  # max_iter do KMeans; nenhuma execução observada passou de 29

# Tamanho mínimo de cluster abaixo do qual se emite um aviso
MINIMO_DE_ELEMENTOS_POR_CLUSTER = 4


# Leitura dos CSVs de taxa e montagem do painel


def _slug(texto):
    """'SEM INFORMAÇÃO' -> 'sem-informacao'. Sem acento, minúsculo, hifenizado."""
    normalizado = unicodedata.normalize("NFKD", str(texto).strip().lower())
    sem_acento = "".join(caractere for caractere in normalizado if not unicodedata.combining(caractere))
    return "-".join(sem_acento.split())


def ler_csv_taxa_em_painel(caminho_csv, prefixo):
    """Lê um CSV de taxa (formato largo) e devolve o painel (REGIONAL, ANO) x categoria."""
    tabela = pd.read_csv(caminho_csv)
    colunas_de_taxa = [coluna for coluna in tabela.columns if coluna.endswith(SUFIXO_COLUNA_TAXA)]
    if not colunas_de_taxa:
        raise ValueError(
            f"Nenhuma coluna de taxa ('{SUFIXO_COLUNA_TAXA}') em {Path(caminho_csv).name}."
        )

    longa = tabela.melt(
        id_vars=[COLUNA_REGIONAL], value_vars=colunas_de_taxa,
        var_name="ANO_CATEGORIA", value_name="TAXA",
    )
    partes = longa["ANO_CATEGORIA"].str.split("_", n=1, expand=True)
    longa[COLUNA_ANO] = partes[0].astype(int)
    longa["CATEGORIA"] = partes[1].str[: -len(SUFIXO_COLUNA_TAXA)]

    painel = longa.pivot_table(
        index=[COLUNA_REGIONAL, COLUNA_ANO], columns="CATEGORIA",
        values="TAXA", aggfunc="first", dropna=False,
    )
    painel.columns = [f"{prefixo}_{_slug(categoria)}" for categoria in painel.columns]

    registrar_log(
        f"{Path(caminho_csv).name}: {painel.shape[1]} categoria(s), {painel.shape[0]} par(es) regional-ano."
    )
    return painel


def montar_painel(blocos=BLOCOS_DE_TAXA, pasta_taxa=PASTA_TAXA):
    """Junta os painéis de todos os blocos em uma matriz (REGIONAL, ANO) x variável."""
    paineis = []
    for bloco in blocos:
        paineis.append(ler_csv_taxa_em_painel(pasta_taxa / bloco["ARQUIVO"], bloco["PREFIXO"]))
    matriz = pd.concat(paineis, axis=1, join="outer").sort_index()

    colunas_duplicadas = matriz.columns[matriz.columns.duplicated()].tolist()
    if colunas_duplicadas:
        raise ValueError(f"Colunas duplicadas na matriz: {colunas_duplicadas}.")

    registrar_log(
        f"Painel montado: {matriz.shape[0]} par(es) regional-ano x {matriz.shape[1]} variável(is), "
        f"{matriz.index.get_level_values(COLUNA_REGIONAL).nunique()} regional(is)."
    )
    return matriz


# Descarte de colunas e tratamento de nulos


def descartar_colunas_sem_informacao_e_total(matriz, slugs_descartados=SLUGS_DE_CATEGORIA_DESCARTADOS):
    """Remove as colunas de categoria 'sem informação' ou 'total'."""
    colunas_a_descartar = []
    for coluna in matriz.columns:
        if coluna.rsplit("_", 1)[-1] in slugs_descartados:
            colunas_a_descartar.append(coluna)
    if colunas_a_descartar:
        registrar_log(f"Descartada(s) {len(colunas_a_descartar)} coluna(s) sem-informação/total: {colunas_a_descartar}")
        matriz = matriz.drop(columns=colunas_a_descartar)
    return matriz


def descartar_colunas_com_muitos_nulos(matriz, limiar_maximo=LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA):
    """Remove colunas cuja proporção de nulos ultrapassa `limiar_maximo`."""
    proporcao_nula = matriz.isna().mean()
    colunas_a_descartar = proporcao_nula[proporcao_nula > limiar_maximo].index.tolist()
    if colunas_a_descartar:
        registrar_log(
            f"Descartada(s) {len(colunas_a_descartar)} coluna(s) com mais de {limiar_maximo:.0%} "
            f"de nulos: {colunas_a_descartar}"
        )
        matriz = matriz.drop(columns=colunas_a_descartar)
    return matriz


def tratar_nulos_sem_imputar(matriz):
    """Descarta linhas com ao menos um valor ausente -- nenhum valor é imputado."""
    linhas_antes = len(matriz)
    matriz_sem_nulos = matriz.dropna(how="any")
    linhas_descartadas = linhas_antes - len(matriz_sem_nulos)
    if linhas_descartadas:
        registrar_log(
            f"Descartada(s) {linhas_descartadas} de {linhas_antes} linha(s) "
            f"({linhas_descartadas / linhas_antes:.1%}) por ter ao menos um valor ausente -- "
            "nenhum valor foi imputado."
        )
    if matriz_sem_nulos.empty:
        raise ValueError(
            "Nenhuma linha restou depois do dropna -- com USAR_JANELA_COMUM=False (ou uma janela "
            "manual ampla), dificilmente todos os blocos têm dado no mesmo par regional-ano. Ajuste "
            "USAR_JANELA_COMUM/ANO_INICIAL_COMUM/ANO_FINAL_COMUM, ou LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA "
            "para descartar mais atributos esparsos antes desta etapa."
        )
    return matriz_sem_nulos


# Padronização e PCA (testado e não usado no pipeline final)


def padronizar_e_reduzir(matriz, razao_maxima_atributos_por_linha=RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA,
                          variancia_alvo=VARIANCIA_EXPLICADA_ALVO,
                          numero_maximo_de_componentes=NUMERO_MAXIMO_DE_COMPONENTES,
                          semente=SEMENTE_ALEATORIA_FIXA, usar_pca=USAR_PCA):
    """Padroniza com RobustScaler e aplica PCA conforme `usar_pca`."""
    matriz_padronizada = RobustScaler().fit_transform(matriz)
    razao = matriz.shape[1] / matriz.shape[0]

    if usar_pca is None:
        aplicar_pca = razao > razao_maxima_atributos_por_linha
        motivo_pulado = f"razão atributos/linhas = {razao:.3f} (<= {razao_maxima_atributos_por_linha})"
    else:
        aplicar_pca = usar_pca
        motivo_pulado = f"USAR_PCA=False (forçado; razão atributos/linhas = {razao:.3f})"

    if not aplicar_pca:
        registrar_log(f"PCA não aplicado: {motivo_pulado}.")
        return matriz_padronizada, matriz_padronizada, None, None

    pca_exploratorio = PCA(random_state=semente).fit(matriz_padronizada)
    variancia_acumulada = np.cumsum(pca_exploratorio.explained_variance_ratio_)
    componentes_pelo_alvo = int(np.searchsorted(variancia_acumulada, variancia_alvo) + 1)
    numero_de_componentes = max(
        2, min(componentes_pelo_alvo, numero_maximo_de_componentes, matriz_padronizada.shape[1])
    )

    pca = PCA(n_components=numero_de_componentes, random_state=semente)
    matriz_reduzida = pca.fit_transform(matriz_padronizada)

    if usar_pca is None:
        motivo_aplicado = f"razão atributos/linhas = {razao:.3f} (> {razao_maxima_atributos_por_linha})"
    else:
        motivo_aplicado = f"USAR_PCA=True (forçado; razão atributos/linhas = {razao:.3f})"
    registrar_log(
        f"PCA aplicado: {motivo_aplicado} -> {numero_de_componentes} componente(s), "
        f"{variancia_acumulada[numero_de_componentes - 1]:.1%} da variância acumulada."
    )
    return matriz_padronizada, matriz_reduzida, pca, variancia_acumulada


# Escolha de k pelo cotovelo da curva de inércia


def calcular_inercia_por_k(matriz, k_minimo=K_MINIMO, k_maximo=K_MAXIMO,
                            semente=SEMENTE_ALEATORIA_FIXA, n_init=NUMERO_DE_INICIALIZACOES,
                            max_iter=MAXIMO_DE_ITERACOES):
    """Calcula inércia (WCSS) do KMeans para cada k da faixa."""
    limite_superior = min(k_maximo, len(matriz) - 1)
    if k_minimo > limite_superior:
        raise ValueError(
            f"Nenhum k testável: k_minimo={k_minimo} > limite superior={limite_superior} "
            f"(len(matriz)-1={len(matriz) - 1}). A amostra tem poucas linhas demais para a "
            "faixa de k configurada -- reduza K_MINIMO ou aumente o tamanho da amostra."
        )
    linhas = []
    for k in range(k_minimo, limite_superior + 1):
        modelo = KMeans(n_clusters=k, random_state=semente, n_init=n_init, max_iter=max_iter).fit(matriz)
        linhas.append({
            "k": k,
            "inercia": float(modelo.inertia_),
            "n_iter_": int(modelo.n_iter_),
        })

    tabela = pd.DataFrame(linhas)
    registrar_log(
        f"Inércia calculada para k = {k_minimo}..{limite_superior} ({len(tabela)} valor(es) de k)."
    )
    return tabela


def escolher_k_pelo_cotovelo(tabela_k, sensibilidade=SENSIBILIDADE_COTOVELO):
    """Escolhe k pelo cotovelo da curva de inércia (KneeLocator)."""
    localizador = KneeLocator(
        tabela_k["k"].to_numpy(), tabela_k["inercia"].to_numpy(),
        S=sensibilidade, curve="convex", direction="decreasing",
    )
    k_escolhido = localizador.knee
    if k_escolhido is None:
        registrar_log(
            "ATENÇÃO: kneed não encontrou cotovelo na curva de inércia -- usando o k de maior "
            "curvatura discreta (segunda derivada) como reserva."
        )
        segunda_derivada = np.gradient(np.gradient(tabela_k["inercia"].to_numpy()))
        k_escolhido = int(tabela_k["k"].to_numpy()[np.argmax(segunda_derivada)])
    else:
        k_escolhido = int(k_escolhido)

    indice_do_cotovelo = int(tabela_k.index[tabela_k["k"] == k_escolhido][0])
    registrar_log(f"Cotovelo da curva de inércia na posição {indice_do_cotovelo} de {len(tabela_k)} -- k = {k_escolhido}")
    return k_escolhido, indice_do_cotovelo


def busca_em_grade_k(matriz, k_minimo=K_MINIMO, k_maximo=K_MAXIMO, sementes=SEMENTES_DA_BUSCA,
                      n_init=NUMERO_DE_INICIALIZACOES, max_iter=MAXIMO_DE_ITERACOES):
    """Calcula inércia para cada combinação (k, semente)."""
    limite_superior = min(k_maximo, len(matriz) - 1)
    if k_minimo > limite_superior:
        raise ValueError(
            f"Nenhum k testável: k_minimo={k_minimo} > limite superior={limite_superior} "
            f"(len(matriz)-1={len(matriz) - 1}). A amostra tem poucas linhas demais para a "
            "faixa de k configurada -- reduza K_MINIMO ou aumente o tamanho da amostra."
        )
    grade = ParameterGrid({"k": range(k_minimo, limite_superior + 1), "semente": sementes})

    linhas = []
    for combinacao in grade:
        k, semente = combinacao["k"], combinacao["semente"]
        modelo = KMeans(n_clusters=k, random_state=semente, n_init=n_init, max_iter=max_iter).fit(matriz)
        linhas.append({
            "k": k,
            "semente": semente,
            "inercia": float(modelo.inertia_),
            "n_iter_": int(modelo.n_iter_),
        })

    return pd.DataFrame(linhas).sort_values(["k", "semente"]).reset_index(drop=True)


def maximo_de_iteracoes_usadas(*tabelas):
    """Maior n_iter_ entre todas as execuções de KMeans das tabelas."""
    return max(int(tabela["n_iter_"].max()) for tabela in tabelas)


# Execução do KMeans


def executar_kmeans(matriz, k, semente=SEMENTE_ALEATORIA_FIXA, n_init=NUMERO_DE_INICIALIZACOES,
                     max_iter=MAXIMO_DE_ITERACOES):
    """Roda o KMeans e devolve os rótulos numerados a partir de 1 (Cluster 1..k) e o modelo."""
    modelo = KMeans(n_clusters=k, random_state=semente, n_init=n_init, max_iter=max_iter).fit(matriz)
    return modelo.labels_ + 1, modelo


def resumir_agrupamento_kmeans(matriz, rotulos, modelo):
    """Devolve nº de clusters e inércia do agrupamento."""
    n_clusters = len(set(rotulos))
    return n_clusters, float(modelo.inertia_)


def diagnostico_tamanho_dos_clusters(rotulos, minimo=MINIMO_DE_ELEMENTOS_POR_CLUSTER):
    """Devolve o tamanho de cada cluster e avisa sobre os menores que `minimo`."""
    tamanhos = pd.Series(rotulos).value_counts().sort_index()
    pequenos = tamanhos[tamanhos < minimo]
    if not pequenos.empty:
        registrar_log(
            f"ATENÇÃO: {len(pequenos)} cluster(s) com menos de {minimo} elemento(s) -- "
            f"{pequenos.to_dict()}. O KMeans aloca todo ponto a algum cluster (não existe "
            "'ruído' como no DBSCAN); um cluster muito pequeno tende a ser um outlier "
            "isolado, não um perfil compartilhado -- considere reduzir k ou tratar esses "
            "pontos como atípicos na interpretação."
        )
    return tamanhos


# Saídas finais em DataFrame


def montar_resumo_parametros_kmeans(k, inercia, usar_robust_scaler, pca,
                                     variancia_acumulada, n_linhas, n_atributos, n_clusters):
    """Resume em uma linha os parâmetros e resultados do agrupamento."""
    n_componentes_pca = np.nan
    variancia_explicada = np.nan
    if pca is not None:
        n_componentes_pca = int(pca.n_components_)
        variancia_explicada = float(variancia_acumulada[n_componentes_pca - 1])

    escalonador = "nenhum"
    if usar_robust_scaler:
        escalonador = "RobustScaler"

    return pd.DataFrame([{
        "K": k,
        "ESCALONADOR": escalonador,
        "PCA_APLICADO": pca is not None,
        "PCA_N_COMPONENTES": n_componentes_pca,
        "PCA_VARIANCIA_EXPLICADA": variancia_explicada,
        "N_LINHAS": n_linhas,
        "N_ATRIBUTOS": n_atributos,
        "N_CLUSTERS": n_clusters,
        "INERCIA": inercia,
    }])


def montar_tabela_pertencimento(indice, rotulos):
    """REGIONAL DE SAÚDE, ANO, CLUSTER -- uma linha por par agrupado."""
    tabela = indice.to_frame(index=False)
    tabela["CLUSTER"] = rotulos
    return tabela


def montar_visao_agregada_regional_ano(tabela_pertencimento):
    """Regional (linha) x Ano (coluna) -> CLUSTER."""
    return tabela_pertencimento.pivot(index=COLUNA_REGIONAL, columns=COLUNA_ANO, values="CLUSTER")


def montar_resumo_por_cluster(tabela_pertencimento):
    """Resumo por CLUSTER: nº de pares, nº de Regionais distintas e lista de membros."""
    def _membros(grupo):
        membros = []
        for regional, ano in zip(grupo[COLUNA_REGIONAL], grupo[COLUNA_ANO]):
            membros.append(f"{regional} ({ano})")
        return ", ".join(membros)

    resumo = tabela_pertencimento.groupby("CLUSTER").apply(
        lambda grupo: pd.Series({
            "N_PARES": len(grupo),
            "N_REGIONAIS_DISTINTAS": grupo[COLUNA_REGIONAL].nunique(),
            "MEMBROS": _membros(grupo),
        }),
        include_groups=False,
    ).reset_index().sort_values("CLUSTER").reset_index(drop=True)
    return resumo


# Caracterização dos clusters pelas variáveis originais (sem teste de significância, que seria circular)
NUMERO_DE_VARIAVEIS_DISCRIMINANTES = 15


def selecionar_variaveis_mais_discriminantes(tabela_caracterizacao, top_n=NUMERO_DE_VARIAVEIS_DISCRIMINANTES):
    """Seleciona as `top_n` primeiras linhas de cada cluster de uma tabela já ordenada por relevância."""
    return tabela_caracterizacao.groupby("CLUSTER", group_keys=False).head(top_n).reset_index(drop=True)


# Caracterização dos clusters pela mediana -- compara a mediana de cada variável em cada
# cluster com a mediana geral, normalizada pelo IQR geral.


def calcular_caracterizacao_por_mediana(matriz, rotulos):
    """d_cj = (Med_cj − Med_j) / IQR_j por (cluster, variável), nos valores originais."""
    colunas = matriz.columns.tolist()
    mediana_geral = matriz.median()
    iqr_geral = (matriz.quantile(0.75) - matriz.quantile(0.25)).where(lambda serie: serie > 0)

    tabela_pertencimento = montar_tabela_pertencimento(matriz.index, rotulos)
    matriz_com_cluster = matriz.reset_index(drop=True).copy()
    matriz_com_cluster["CLUSTER"] = tabela_pertencimento["CLUSTER"].to_numpy()
    mediana_por_cluster = matriz_com_cluster.groupby("CLUSTER")[colunas].median()

    tabela = mediana_por_cluster.stack().rename("MEDIANA_CLUSTER").reset_index()
    tabela.columns = ["CLUSTER", "VARIAVEL", "MEDIANA_CLUSTER"]
    tabela["MEDIANA_GERAL"] = tabela["VARIAVEL"].map(mediana_geral)
    tabela["IQR_GERAL"] = tabela["VARIAVEL"].map(iqr_geral)
    tabela["D_CJ"] = (tabela["MEDIANA_CLUSTER"] - tabela["MEDIANA_GERAL"]) / tabela["IQR_GERAL"]

    tabela["_D_CJ_ABS"] = tabela["D_CJ"].abs()
    tabela = tabela.sort_values(["CLUSTER", "_D_CJ_ABS"], ascending=[True, False], na_position="last")
    tabela = tabela.drop(columns="_D_CJ_ABS").reset_index(drop=True)
    sem_iqr = iqr_geral[iqr_geral.isna()].index.tolist()
    if sem_iqr:
        registrar_log(f"ATENÇÃO: {len(sem_iqr)} variável(is) com IQR geral = 0 (sem d_cj): {sem_iqr}")
    return tabela[["CLUSTER", "VARIAVEL", "MEDIANA_CLUSTER", "MEDIANA_GERAL", "IQR_GERAL", "D_CJ"]]


# Conferências descritivas: cluster por ano e cobertura de escolaridade/raça-cor por cluster


def tabela_cluster_por_ano(resultado):
    """Contagem de pares Regional-Ano por (CLUSTER, ANO) -- cluster nas linhas, ano nas colunas."""
    return pd.crosstab(resultado["CLUSTER"], resultado[COLUNA_ANO])


def tabela_clusters_por_regional(resultado):
    """Para cada Regional, os clusters em que ela aparece e quantos são distintos, do maior pro menor."""
    agrupado = resultado.groupby(COLUNA_REGIONAL)["CLUSTER"].agg(lambda serie: sorted(serie.unique()))
    tabela = agrupado.rename("CLUSTERS").reset_index()
    tabela["N_CLUSTERS_DISTINTOS"] = tabela["CLUSTERS"].apply(len)
    return tabela.sort_values("N_CLUSTERS_DISTINTOS", ascending=False).reset_index(drop=True)


def resumir_cobertura_por_cluster(matriz, rotulos, prefixos=("casos-escolaridade_", "casos-raca-cor_")):
    """Média, mediana e proporção de zeros por (cluster, variável), nas variáveis originais com os `prefixos` dados."""
    colunas = [coluna for coluna in matriz.columns if coluna.startswith(prefixos)]
    valores = matriz[colunas].copy()
    valores["CLUSTER"] = np.asarray(rotulos)
    agrupado = valores.groupby("CLUSTER")[colunas]

    tabela = agrupado.mean().stack().rename("MEDIA").reset_index()
    tabela.columns = ["CLUSTER", "VARIAVEL", "MEDIA"]
    tabela["MEDIANA"] = agrupado.median().stack().to_numpy()
    tabela["PROPORCAO_ZERO"] = agrupado.apply(lambda grupo: (grupo == 0).mean()).stack().to_numpy()
    return tabela.sort_values(["CLUSTER", "VARIAVEL"]).reset_index(drop=True)


# Investigação complementar: sub-representação de Pirapora e Ituiutaba no conjunto final
#
# Não altera o pipeline (o dropna de `tratar_nulos_sem_imputar` permanece como está) -- só
# documenta, com números e tabelas separadas, por que algumas Regionais perdem mais pares
# (Regional, Ano) do que outras na janela comum.


def contar_pares_ausentes_por_regional(matriz_antes_do_dropna, matriz_depois_do_dropna):
    """Para cada Regional: quantos pares (Regional, Ano) existem antes/depois do dropna, na janela comum.

    `ANOS_ESPERADOS` é o nº de anos distintos da janela comum (ex.: 10, para 2014-2023) -- o
    mesmo para toda Regional, já que a janela é definida globalmente, não por Regional.
    """
    anos_esperados = matriz_antes_do_dropna.index.get_level_values(COLUNA_ANO).nunique()
    regionais = matriz_antes_do_dropna.index.get_level_values(COLUNA_REGIONAL)
    regionais_depois = matriz_depois_do_dropna.index.get_level_values(COLUNA_REGIONAL)

    pares_no_final = regionais_depois.value_counts()
    tabela = pd.DataFrame({COLUNA_REGIONAL: regionais.unique()})
    tabela["ANOS_ESPERADOS"] = anos_esperados
    tabela["PARES_NO_FINAL"] = tabela[COLUNA_REGIONAL].map(pares_no_final).fillna(0).astype(int)
    tabela["PARES_AUSENTES"] = tabela["ANOS_ESPERADOS"] - tabela["PARES_NO_FINAL"]
    tabela["PROPORCAO_AUSENTE"] = tabela["PARES_AUSENTES"] / tabela["ANOS_ESPERADOS"]

    return tabela.sort_values(
        ["PARES_AUSENTES", COLUNA_REGIONAL], ascending=[False, True]
    ).reset_index(drop=True)


def contar_municipios_por_regional(caminho=CAMINHO_MUNICIPIOS_REGIONAIS):
    """Nº de municípios por Regional de Saúde (mesma tabela usada no enriquecimento geográfico da EDA)."""
    tabela_municipios = pd.read_csv(caminho)
    contagem = (
        tabela_municipios.groupby("REGIONAL NORMALIZADA")
        .size()
        .rename("N_MUNICIPIOS")
        .reset_index()
        .rename(columns={"REGIONAL NORMALIZADA": COLUNA_REGIONAL})
    )
    return contagem.sort_values("N_MUNICIPIOS", ascending=True).reset_index(drop=True)


def listar_nulos_por_regional(matriz_antes_do_dropna, regionais):
    """Para as `regionais` dadas, cada (Regional, Ano, Variável) nulo na janela comum, antes do dropna.

    Aponta exatamente quais das variáveis (já agregadas por Regional-Ano, antes do descarte de
    linha) carregam o nulo que tira aquele par do conjunto final -- não imputado em nenhuma etapa.
    """
    subconjunto = matriz_antes_do_dropna.loc[
        matriz_antes_do_dropna.index.get_level_values(COLUNA_REGIONAL).isin(regionais)
    ]
    nulos = subconjunto.isna()
    linhas_com_nulo = nulos[nulos.any(axis=1)]

    registros = []
    for (regional, ano), linha in linhas_com_nulo.iterrows():
        for variavel in linha[linha].index:
            registros.append({COLUNA_REGIONAL: regional, COLUNA_ANO: ano, "VARIAVEL": variavel})

    tabela = pd.DataFrame(registros, columns=[COLUNA_REGIONAL, COLUNA_ANO, "VARIAVEL"])
    return tabela.sort_values([COLUNA_REGIONAL, COLUNA_ANO, "VARIAVEL"]).reset_index(drop=True)


def resumir_variaveis_nulas_por_regional(tabela_nulos_por_regional):
    """Para cada Regional, quais variáveis aparecem nulas e com que frequência (a partir de `listar_nulos_por_regional`)."""
    return (
        tabela_nulos_por_regional.groupby([COLUNA_REGIONAL, "VARIAVEL"])
        .size()
        .rename("N_OCORRENCIAS")
        .reset_index()
        .sort_values([COLUNA_REGIONAL, "N_OCORRENCIAS"], ascending=[True, False])
        .reset_index(drop=True)
    )


def populacao_feminina_media_por_regional(regionais, ano_inicial, ano_final,
                                           caminho=CAMINHO_POPULACAO_POR_REGIONAL,
                                           faixas_etarias=FAIXAS_ETARIAS_PADRAO):
    """População feminina total média (soma das faixas etárias) de cada Regional, na janela dada.

    Mesma fonte/interpolação usada como denominador das taxas (ver 2.1 de DECISOES.md) -- não é
    um novo cálculo de população, só uma leitura agregada por Regional para comparar o tamanho
    da população de risco entre Regionais.
    """
    tabela_populacao = pd.read_csv(caminho).set_index(COLUNA_REGIONAL)
    linhas = []
    for regional in regionais:
        populacao_por_ano = []
        for ano in range(ano_inicial, ano_final + 1):
            colunas_do_ano = [f"{ano}_{faixa}" for faixa in faixas_etarias]
            populacao_por_ano.append(tabela_populacao.loc[regional, colunas_do_ano].sum())
        linhas.append({
            COLUNA_REGIONAL: regional,
            "POPULACAO_FEMININA_MEDIA": float(np.mean(populacao_por_ano)),
        })
    return pd.DataFrame(linhas)


def montar_tabela_consolidada_ausencia(tabela_ausencia_pares, tabela_municipios, tabela_populacao,
                                        tabela_nulos_por_regional, regionais):
    """Tabela final: Regional | nº municípios (+ranking) | população feminina média (+ranking) |

    % de pares ausentes | principais variáveis nulas. O ranking é a posição da Regional entre
    as 28 (1º = menor), para situar Pirapora/Ituiutaba no conjunto, não só mostrar o valor isolado.
    """
    resumo_variaveis = resumir_variaveis_nulas_por_regional(tabela_nulos_por_regional)

    def _principais_variaveis(regional):
        grupo = resumo_variaveis[resumo_variaveis[COLUNA_REGIONAL] == regional]
        if grupo.empty:
            return "-"
        return ", ".join(f"{linha.VARIAVEL} ({linha.N_OCORRENCIAS}x)" for linha in grupo.itertuples())

    n_total_regionais = len(tabela_municipios)
    ranking_municipios = tabela_municipios.set_index(COLUNA_REGIONAL)["N_MUNICIPIOS"].rank(method="min").astype(int)
    ranking_populacao = tabela_populacao.set_index(COLUNA_REGIONAL)["POPULACAO_FEMININA_MEDIA"].rank(method="min").astype(int)

    tabela = tabela_ausencia_pares[tabela_ausencia_pares[COLUNA_REGIONAL].isin(regionais)].copy()
    tabela = tabela.merge(tabela_municipios, on=COLUNA_REGIONAL, how="left")
    tabela = tabela.merge(tabela_populacao, on=COLUNA_REGIONAL, how="left")
    tabela["RANKING_N_MUNICIPIOS"] = tabela[COLUNA_REGIONAL].map(
        lambda regional: f"{ranking_municipios.get(regional, '?')}º de {n_total_regionais} (menor)"
    )
    tabela["RANKING_POPULACAO_FEMININA"] = tabela[COLUNA_REGIONAL].map(
        lambda regional: f"{ranking_populacao.get(regional, '?')}º de {len(ranking_populacao)} (menor)"
    )
    tabela["PRINCIPAIS_VARIAVEIS_NULAS"] = tabela[COLUNA_REGIONAL].map(_principais_variaveis)

    return tabela[[
        COLUNA_REGIONAL, "N_MUNICIPIOS", "RANKING_N_MUNICIPIOS",
        "POPULACAO_FEMININA_MEDIA", "RANKING_POPULACAO_FEMININA",
        "PROPORCAO_AUSENTE", "PRINCIPAIS_VARIAVEIS_NULAS",
    ]].sort_values("PROPORCAO_AUSENTE", ascending=False).reset_index(drop=True)


def decodificar_faixa_etaria_da_variavel(variavel, prefixo="mortalidade_", faixas_etarias=FAIXAS_ETARIAS_PADRAO):
    """'mortalidade_70-ou-mais' -> '70 OU MAIS' (nome da coluna agregada -> faixa etária padrão)."""
    sufixo = variavel[len(prefixo):] if variavel.startswith(prefixo) else variavel
    for faixa in faixas_etarias:
        if sufixo == faixa.lower().replace(" ", "-"):
            return faixa
    raise ValueError(f"Não encontrei a faixa etária correspondente a '{variavel}'.")


def listar_combinacoes_nulas_de_mortalidade(tabela_nulos_por_regional):
    """(Regional, Ano, Faixa) de cada nulo em `mortalidade_*`; Regional no formato (Título) do CSV bruto."""
    mortalidade = tabela_nulos_por_regional[
        tabela_nulos_por_regional["VARIAVEL"].str.startswith("mortalidade_")
    ].copy()
    mortalidade[COLUNA_REGIONAL] = mortalidade[COLUNA_REGIONAL].str.title()
    mortalidade["FAIXA"] = mortalidade["VARIAVEL"].apply(decodificar_faixa_etaria_da_variavel)
    return mortalidade[[COLUNA_REGIONAL, COLUNA_ANO, "FAIXA"]].reset_index(drop=True)


def comparar_populacao_de_risco(tabela_combinacoes, caminho=CAMINHO_POPULACAO_POR_REGIONAL):
    """Para cada (Regional, Ano, Faixa) nula: população feminina da Regional vs. mediana estadual

    e posição no ranking estadual (1º = menor população entre as Regionais com dado na coluna).
    """
    tabela_populacao = pd.read_csv(caminho).set_index(COLUNA_REGIONAL)
    linhas = []
    for _, linha in tabela_combinacoes.iterrows():
        regional_slug = linha[COLUNA_REGIONAL].lower()
        coluna = f"{linha[COLUNA_ANO]}_{linha['FAIXA']}"
        serie_coluna = tabela_populacao[coluna]
        populacao_regional = serie_coluna.loc[regional_slug]
        posicao = int(serie_coluna.rank(method="min").loc[regional_slug])
        linhas.append({
            COLUNA_REGIONAL: linha[COLUNA_REGIONAL],
            COLUNA_ANO: linha[COLUNA_ANO],
            "FAIXA": linha["FAIXA"],
            "POPULACAO_FEMININA_DA_REGIONAL": populacao_regional,
            "MEDIANA_ESTADUAL_NA_FAIXA_ANO": serie_coluna.median(),
            "POSICAO_NO_RANKING_ESTADUAL": f"{posicao}º de {serie_coluna.notna().sum()} (menor)",
        })
    return pd.DataFrame(linhas)
