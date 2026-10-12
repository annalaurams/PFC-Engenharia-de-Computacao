import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from kneed import KneeLocator
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
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
    PASTA_POPULACAO,
    SUFIXO_COLUNA_TAXA,
    ESPECIFICACOES_VARIAVEIS,
    ESPECIFICACOES_VARIAVEIS_CATEGORICAS,
    registrar_log,
)

PASTA_TAXA = PASTA_POPULACAO / "Taxa"

# Constantes de configuração

SEMENTE_ALEATORIA = 42


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

# Silhueta desligada: as colunas de silhueta ficam NaN
CALCULAR_SILHUETA = False
RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA = 0.10
VARIANCIA_EXPLICADA_ALVO = 0.85
NUMERO_MAXIMO_DE_COMPONENTES = 10

# Variância de PC1 acima da qual se alerta para uma direção dominante
VARIANCIA_PC1_ALERTA = 0.75

# Escolha de k pelo cotovelo da curva de inércia
K_MINIMO = 2
K_MAXIMO = 12  # teto da varredura de k
SENSIBILIDADE_COTOVELO = 1.0  # parâmetro S do KneeLocator
SEMENTES_DA_BUSCA = [0, 10, 30, 42, 66]  # sementes para testar a sensibilidade à inicialização
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
                          semente=SEMENTE_ALEATORIA, usar_pca=USAR_PCA):
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


def preparar_projecao_2d(matriz_padronizada, matriz_reduzida, pca, semente=SEMENTE_ALEATORIA):
    """Projeção PC1 x PC2 apenas para visualização."""
    if pca is not None:
        return matriz_reduzida[:, :2], pca.explained_variance_ratio_[:2]
    pca_2d = PCA(n_components=2, random_state=semente).fit(matriz_padronizada)
    return pca_2d.transform(matriz_padronizada), pca_2d.explained_variance_ratio_


def pesos_das_variaveis_no_componente(pca, colunas, componente=1):
    """Pesos (loadings) dos atributos no componente indicado, ordenados por magnitude."""
    if pca is None:
        raise ValueError("pesos_das_variaveis_no_componente requer PCA aplicado (pca is None).")
    pesos = pd.Series(pca.components_[componente - 1], index=colunas, name=f"PC{componente}")
    return pesos.reindex(pesos.abs().sort_values(ascending=False).index)


# Escolha de k pelo cotovelo da curva de inércia


def calcular_inercia_e_silhueta_por_k(matriz, k_minimo=K_MINIMO, k_maximo=K_MAXIMO,
                                       semente=SEMENTE_ALEATORIA, n_init=NUMERO_DE_INICIALIZACOES,
                                       max_iter=MAXIMO_DE_ITERACOES):
    """Calcula inércia (WCSS) e silhueta do KMeans para cada k da faixa."""
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
        rotulos = modelo.labels_
        silhueta = np.nan
        if CALCULAR_SILHUETA and k >= 2 and len(matriz) > k:
            silhueta = float(silhouette_score(matriz, rotulos))
        linhas.append({
            "k": k,
            "inercia": float(modelo.inertia_),
            "silhueta": silhueta,
            "n_iter_": int(modelo.n_iter_),
        })

    tabela = pd.DataFrame(linhas)
    medidas_calculadas = "Inércia"
    if CALCULAR_SILHUETA:
        medidas_calculadas = "Inércia e silhueta"
    registrar_log(
        f"{medidas_calculadas} calculada(s) para k = {k_minimo}..{limite_superior} ({len(tabela)} valor(es) de k)."
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
    """Calcula inércia e silhueta para cada combinação (k, semente)."""
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
        rotulos = modelo.labels_
        silhueta = np.nan
        if CALCULAR_SILHUETA and k >= 2 and len(matriz) > k:
            silhueta = float(silhouette_score(matriz, rotulos))
        linhas.append({
            "k": k,
            "semente": semente,
            "inercia": float(modelo.inertia_),
            "silhueta": silhueta,
            "n_iter_": int(modelo.n_iter_),
        })

    return pd.DataFrame(linhas).sort_values(["k", "semente"]).reset_index(drop=True)


def maximo_de_iteracoes_usadas(*tabelas):
    """Maior n_iter_ entre todas as execuções de KMeans das tabelas."""
    return max(int(tabela["n_iter_"].max()) for tabela in tabelas)


# Execução do KMeans


def executar_kmeans(matriz, k, semente=SEMENTE_ALEATORIA, n_init=NUMERO_DE_INICIALIZACOES,
                     max_iter=MAXIMO_DE_ITERACOES):
    """Roda o KMeans e devolve os rótulos numerados a partir de 1 (Cluster 1..k) e o modelo."""
    modelo = KMeans(n_clusters=k, random_state=semente, n_init=n_init, max_iter=max_iter).fit(matriz)
    return modelo.labels_ + 1, modelo


def resumir_agrupamento_kmeans(matriz, rotulos, modelo):
    """Devolve nº de clusters, inércia e silhueta do agrupamento."""
    n_clusters = len(set(rotulos))
    silhueta = np.nan
    if CALCULAR_SILHUETA and n_clusters >= 2 and len(matriz) > n_clusters:
        silhueta = float(silhouette_score(matriz, rotulos))
    return n_clusters, float(modelo.inertia_), silhueta


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


def montar_resumo_parametros_kmeans(k, inercia, silhueta, usar_robust_scaler, pca, variancia_acumulada,
                                     n_linhas, n_atributos, n_clusters):
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
        "SILHUETA": silhueta,
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


def calcular_iqr_geral(matriz):
    """IQR de cada variável com o mesmo Q1/Q3 do RobustScaler; NaN onde o IQR é 0."""
    q1, q3 = np.nanpercentile(matriz.to_numpy(dtype=float), [25, 75], axis=0)
    iqr = pd.Series(q3 - q1, index=matriz.columns)
    return iqr.where(iqr > 0)


def calcular_caracterizacao_por_cluster(matriz, rotulos):
    """Diferença entre a média do cluster e a média geral em unidades de IQR geral, ordenada por módulo."""
    colunas = matriz.columns.tolist()
    media_geral = matriz.mean()
    iqr_geral = calcular_iqr_geral(matriz)

    tabela_pertencimento = montar_tabela_pertencimento(matriz.index, rotulos)
    matriz_com_cluster = matriz.reset_index(drop=True).copy()
    matriz_com_cluster["CLUSTER"] = tabela_pertencimento["CLUSTER"].to_numpy()
    medias_por_cluster = matriz_com_cluster.groupby("CLUSTER")[colunas].mean()

    tabela = medias_por_cluster.stack().rename("MEDIA_CLUSTER").reset_index()
    tabela.columns = ["CLUSTER", "VARIAVEL", "MEDIA_CLUSTER"]
    tabela["MEDIA_GERAL"] = tabela["VARIAVEL"].map(media_geral)
    diferenca = tabela["MEDIA_CLUSTER"] - tabela["MEDIA_GERAL"]
    tabela["DIFERENCA_PADRONIZADA"] = diferenca / tabela["VARIAVEL"].map(iqr_geral)
    tabela["DIFERENCA_PERCENTUAL"] = np.where(
        tabela["MEDIA_GERAL"] != 0, diferenca / tabela["MEDIA_GERAL"].abs() * 100, np.nan,
    )

    tabela["_DIFERENCA_ABS"] = tabela["DIFERENCA_PADRONIZADA"].abs()
    tabela = tabela.sort_values(["CLUSTER", "_DIFERENCA_ABS"], ascending=[True, False], na_position="last")
    tabela = tabela.drop(columns="_DIFERENCA_ABS").reset_index(drop=True)
    sem_iqr = iqr_geral[iqr_geral.isna()].index.tolist()
    if sem_iqr:
        registrar_log(f"ATENÇÃO: {len(sem_iqr)} variável(is) com IQR geral = 0 (sem diferença padronizada): {sem_iqr}")
    registrar_log(
        f"Caracterização por cluster: {matriz_com_cluster['CLUSTER'].nunique()} cluster(s) x "
        f"{len(colunas)} variável(is)."
    )
    return tabela


def selecionar_variaveis_mais_discriminantes(tabela_caracterizacao, top_n=NUMERO_DE_VARIAVEIS_DISCRIMINANTES):
    """Seleciona as `top_n` variáveis de maior diferença padronizada em módulo por cluster."""
    return tabela_caracterizacao.groupby("CLUSTER", group_keys=False).head(top_n).reset_index(drop=True)


def descrever_caracterizacao_por_cluster(caracterizacao_por_cluster, resumo_por_cluster,
                                          top_n=NUMERO_DE_VARIAVEIS_DISCRIMINANTES):
    """Gera um parágrafo em Markdown por cluster descrevendo suas variáveis mais discriminantes."""
    tamanhos = resumo_por_cluster.set_index("CLUSTER")["N_PARES"]
    paragrafos = []
    for cluster, grupo in caracterizacao_por_cluster.groupby("CLUSTER"):
        partes = []
        for _, linha in grupo.head(top_n).iterrows():
            if pd.isna(linha["DIFERENCA_PADRONIZADA"]):
                continue

            sentido = "abaixo"
            if linha["DIFERENCA_PADRONIZADA"] >= 0:
                sentido = "acima"

            descricao = (
                f"**{linha['VARIAVEL']}** {sentido} da média geral "
                f"em {abs(linha['DIFERENCA_PADRONIZADA']):.2f} IQR"
            )
            if pd.notna(linha["DIFERENCA_PERCENTUAL"]):
                descricao += f" ({linha['DIFERENCA_PERCENTUAL']:+.1f}%)"
            partes.append(descricao)

        n_pares = int(tamanhos.get(cluster, np.nan))
        paragrafos.append(
            f"- **Cluster {cluster}** ({n_pares} pares Regional-Ano): " + "; ".join(partes) + "."
        )
    return "\n".join(paragrafos)


# Decomposição da distância² de cada par Regional-Ano ao centroide do seu cluster


def calcular_parcelas_distancia_ao_centroide(matriz_para_kmeans, modelo, indice, colunas):
    """Parcela (valor − centroide)² de cada variável por linha; somadas dão a distância² ao centroide usada pelo KMeans."""
    valores = np.asarray(matriz_para_kmeans, dtype=float)
    if valores.shape != (len(indice), len(colunas)) or len(modelo.labels_) != len(indice):
        raise ValueError(
            f"Dimensões incompatíveis: matriz {valores.shape}, índice {len(indice)}, colunas {len(colunas)}, "
            f"rótulos do modelo {len(modelo.labels_)} -- use a mesma matriz em que o KMeans foi ajustado."
        )
    parcelas = (valores - modelo.cluster_centers_[modelo.labels_]) ** 2

    tabela = pd.DataFrame(parcelas, index=indice, columns=pd.Index(list(colunas), name="VARIAVEL"))
    tabela["CLUSTER"] = modelo.labels_ + 1
    tabela = tabela.set_index("CLUSTER", append=True).stack().rename("PARCELA_DISTANCIA").reset_index()
    return tabela.sort_values(
        [COLUNA_REGIONAL, COLUNA_ANO, "PARCELA_DISTANCIA"], ascending=[True, True, False],
    ).reset_index(drop=True)
