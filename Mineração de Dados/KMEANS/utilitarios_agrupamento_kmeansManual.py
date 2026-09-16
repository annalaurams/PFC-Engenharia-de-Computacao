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


# Módulo AUTOCONTIDO do KMeans: não importa nada de 'DBSCAN/'. Mesmas
# regras de decisão do DBSCAN (montagem de painel a partir dos CSVs de
# taxa, janela comum, tratamento de nulos sem imputar, RobustScaler + PCA
# condicional) são replicadas aqui -- de propósito, para que os dois
# algoritmos possam ser configurados/editados de forma independente, sem
# um afetar o outro. Só o utilitário de baixíssimo nível do projeto
# ('Seleção e Transformação/População/utilitarios_comuns.py', a base
# comum sob DBSCAN e KMeans) é reaproveitado.
def _preparar_sys_path():
    raiz_do_projeto = Path(__file__).resolve().parent.parent.parent
    candidatos = [
        raiz_do_projeto / "Seleção e Transformação" / "População",
        Path.home() / "tcc" / "Seleção e Transformação" / "População",
    ]
    pasta = next((p for p in candidatos if (p / "utilitarios_comuns.py").exists()), None)
    if pasta is None:
        raise ModuleNotFoundError(
            "Não encontrei 'utilitarios_comuns.py' em nenhum destes caminhos:\n"
            + "\n".join(f"  - {p}" for p in candidatos)
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


# CONSTANTES DE CONFIGURAÇÃO

SEMENTE_ALEATORIA = 42


def _bloco(nome, prefixo, especificacao):
    return {
        "NOME": nome, "PREFIXO": prefixo,
        "ARQUIVO": especificacao["NOME_ARQUIVO_SAIDA_TAXA"],
        "ANO_INICIAL": especificacao["ANO_INICIAL"],
        "ANO_FINAL": especificacao["ANO_FINAL"],
    }


BLOCOS_DE_TAXA = [
    _bloco("Casos por Faixa Etária", "casos-faixa", ESPECIFICACOES_VARIAVEIS_CATEGORICAS["Casos por Faixa Etária"]),
    _bloco("Casos por Escolaridade", "casos-escolaridade", ESPECIFICACOES_VARIAVEIS_CATEGORICAS["Casos por Escolaridade"]),
    _bloco("Casos por Raça e Cor", "casos-raca-cor", ESPECIFICACOES_VARIAVEIS_CATEGORICAS["Casos por Raça e Cor"]),
    _bloco("Mortalidade", "mortalidade", ESPECIFICACOES_VARIAVEIS["Mortalidade"]),
    _bloco("Mamografia", "mamografia", ESPECIFICACOES_VARIAVEIS["Mamografia"]),
]

SLUGS_DE_CATEGORIA_DESCARTADOS = ("sem-informacao", "total")

USAR_JANELA_COMUM = False
ANO_INICIAL_COMUM = 2013
ANO_FINAL_COMUM = 2023

# Nos CSVs de taxa, uma célula fica em branco (NaN) quando a soma bruta da
# categoria-ano-regional é NaN em TODOS os municípios da regional --
# ambiguidade proposital (não dá para distinguir "zero eventos" de "sem
# população válida para calcular"). Por isso NaN nunca vira 0 aqui.
LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA = 0.70

# --- Padronização / redução de dimensionalidade ---
# USAR_PCA=None (padrão): decide sozinho pela razão nº de atributos / nº de
# linhas. USAR_PCA=True força PCA; USAR_PCA=False pula o PCA inteiramente
# -- em ambos os casos o critério automático é ignorado.
USAR_PCA = True
RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA = 0.10
VARIANCIA_EXPLICADA_ALVO = 0.85
NUMERO_MAXIMO_DE_COMPONENTES = 10

# PC1 explicando mais que isto sinaliza uma direção dominante isolada --
# indício de porte/volume da observação, não perfis distintos.
VARIANCIA_PC1_ALERTA = 0.75

# --- Escolha de k (cotovelo da curva de inércia, Thorndike, 1953) ---
K_MINIMO = 2
K_MAXIMO = 15  # teto da varredura -- ajuste conforme o tamanho da amostra
SENSIBILIDADE_COTOVELO = 1.0  # mesma convenção do parâmetro S do joelho de eps no DBSCAN
SEMENTES_DA_BUSCA = [SEMENTE_ALEATORIA]  # mais de uma semente testa sensibilidade à inicialização
NUMERO_DE_INICIALIZACOES = 10  # n_init do KMeans

# Aviso pós-hoc (sem efeito sobre o resultado): o KMeans aloca todo ponto a
# algum cluster -- não existe "ruído" como no DBSCAN.
MINIMO_DE_ELEMENTOS_POR_CLUSTER = 4


# Etapa 1: leitura dos CSVs de taxa e reformatação largo -> painel
def _slug(texto):
    """'SEM INFORMAÇÃO' -> 'sem-informacao'. Sem acento, minúsculo, hifenizado."""
    sem_acento = unicodedata.normalize("NFKD", str(texto).strip().lower())
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return "-".join(sem_acento.split())


def ler_csv_taxa_em_painel(caminho_csv, prefixo):
    """
    Lê um CSV de taxa (formato largo, colunas '<ano>_<categoria>_TAXA') e
    devolve o painel: índice (REGIONAL DE SAÚDE, ANO), uma coluna por
    categoria, prefixada. Só as colunas de TAXA entram (nunca o valor
    absoluto) -- o agrupamento compara regionais entre si, e por isso
    precisa de uma variável já ajustada por população.
    """
    tabela = pd.read_csv(caminho_csv)
    colunas_de_taxa = [c for c in tabela.columns if c.endswith(SUFIXO_COLUNA_TAXA)]
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

    paineis = [ler_csv_taxa_em_painel(pasta_taxa / bloco["ARQUIVO"], bloco["PREFIXO"]) for bloco in blocos]
    matriz = pd.concat(paineis, axis=1, join="outer").sort_index()

    colunas_duplicadas = matriz.columns[matriz.columns.duplicated()].tolist()
    if colunas_duplicadas:
        raise ValueError(f"Colunas duplicadas na matriz: {colunas_duplicadas}.")

    registrar_log(
        f"Painel montado: {matriz.shape[0]} par(es) regional-ano x {matriz.shape[1]} variável(is), "
        f"{matriz.index.get_level_values(COLUNA_REGIONAL).nunique()} regional(is)."
    )
    return matriz


def calcular_janela_comum(blocos=BLOCOS_DE_TAXA, ano_inicial_manual=None, ano_final_manual=None):
    """
    Janela comum a todos os blocos: por padrão, a interseção das coberturas
    declaradas (ANO_INICIAL/ANO_FINAL) de cada bloco. Com argumentos
    manuais, usa o período informado e avisa se ele ultrapassa a
    interseção calculada.
    """
    ano_inicial_calculado = max(bloco["ANO_INICIAL"] for bloco in blocos)
    ano_final_calculado = min(bloco["ANO_FINAL"] for bloco in blocos)
    if ano_inicial_calculado > ano_final_calculado:
        raise ValueError(
            f"Interseção vazia entre as coberturas dos blocos: {ano_inicial_calculado} > {ano_final_calculado}."
        )

    if ano_inicial_manual is None and ano_final_manual is None:
        registrar_log(f"Janela comum (interseção dos períodos declarados de cada bloco): {ano_inicial_calculado}-{ano_final_calculado}.")
        return ano_inicial_calculado, ano_final_calculado

    ano_inicial = ano_inicial_manual if ano_inicial_manual is not None else ano_inicial_calculado
    ano_final = ano_final_manual if ano_final_manual is not None else ano_final_calculado
    if ano_inicial < ano_inicial_calculado or ano_final > ano_final_calculado:
        registrar_log(
            f"ATENÇÃO: janela comum manual {ano_inicial}-{ano_final} ultrapassa a interseção "
            f"calculada das coberturas ({ano_inicial_calculado}-{ano_final_calculado}) -- algum "
            "bloco terá anos sem dado (NaN) dentro dessa janela."
        )
    registrar_log(f"Janela comum: {ano_inicial}-{ano_final} (definida manualmente).")
    return ano_inicial, ano_final


def restringir_a_janela_comum(matriz, janela):
    ano_inicial, ano_final = janela
    anos = matriz.index.get_level_values(COLUNA_ANO)
    matriz_restrita = matriz[(anos >= ano_inicial) & (anos <= ano_final)]
    registrar_log(
        f"Restrita à janela comum {ano_inicial}-{ano_final}: "
        f"{matriz_restrita.shape[0]} de {matriz.shape[0]} par(es) regional-ano."
    )
    return matriz_restrita


# Etapa 2: descarte de colunas e tratamento de nulos
def descartar_colunas_sem_informacao_e_total(matriz, slugs_descartados=SLUGS_DE_CATEGORIA_DESCARTADOS):
    """Remove colunas cuja categoria (parte do nome após o prefixo do
    bloco) é 'sem informação' ou 'total'."""
    colunas_a_descartar = [c for c in matriz.columns if c.rsplit("_", 1)[-1] in slugs_descartados]
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


# Etapa 3: padronização e PCA
def padronizar_e_reduzir(matriz, razao_maxima_atributos_por_linha=RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA,
                          variancia_alvo=VARIANCIA_EXPLICADA_ALVO,
                          numero_maximo_de_componentes=NUMERO_MAXIMO_DE_COMPONENTES,
                          semente=SEMENTE_ALEATORIA, usar_pca=USAR_PCA):
    """
    RobustScaler (mediana / IQR) sempre. PCA conforme `usar_pca`: None
    (padrão) decide sozinho pela razão nº de atributos / nº de linhas
    (aplica se ultrapassar `razao_maxima_atributos_por_linha`); True força
    PCA; False pula o PCA inteiramente.

    Devolve (matriz_padronizada, matriz_reduzida, pca, variancia_acumulada).
    pca/variancia_acumulada ficam None quando o PCA não é aplicado.
    """
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

    motivo_aplicado = (
        f"razão atributos/linhas = {razao:.3f} (> {razao_maxima_atributos_por_linha})" if usar_pca is None
        else f"USAR_PCA=True (forçado; razão atributos/linhas = {razao:.3f})"
    )
    registrar_log(
        f"PCA aplicado: {motivo_aplicado} -> {numero_de_componentes} componente(s), "
        f"{variancia_acumulada[numero_de_componentes - 1]:.1%} da variância acumulada."
    )
    return matriz_padronizada, matriz_reduzida, pca, variancia_acumulada


def preparar_projecao_2d(matriz_padronizada, matriz_reduzida, pca, semente=SEMENTE_ALEATORIA):
    """PC1 x PC2 para visualização -- meramente ilustrativa quando o PCA
    não foi aplicado no agrupamento (não influencia os rótulos)."""
    if pca is not None:
        return matriz_reduzida[:, :2], pca.explained_variance_ratio_[:2]
    pca_2d = PCA(n_components=2, random_state=semente).fit(matriz_padronizada)
    return pca_2d.transform(matriz_padronizada), pca_2d.explained_variance_ratio_


def pesos_das_variaveis_no_componente(pca, colunas, componente=1):
    """Peso ('loading') de cada atributo original no componente principal
    indicado (1-based), ordenado por magnitude."""
    if pca is None:
        raise ValueError("pesos_das_variaveis_no_componente requer PCA aplicado (pca is None).")
    pesos = pd.Series(pca.components_[componente - 1], index=colunas, name=f"PC{componente}")
    return pesos.reindex(pesos.abs().sort_values(ascending=False).index)


# Etapa 4: escolha de k (cotovelo da curva de inércia)
def calcular_inercia_e_silhueta_por_k(matriz, k_minimo=K_MINIMO, k_maximo=K_MAXIMO,
                                       semente=SEMENTE_ALEATORIA, n_init=NUMERO_DE_INICIALIZACOES):
    """
    Inércia (WCSS) e silhueta do KMeans para cada k em [k_minimo, k_maximo]
    (limitado por len(matriz)-1). A inércia decresce monotonicamente com k
    -- o cotovelo (ver `escolher_k_pelo_cotovelo`) é o critério principal;
    a silhueta entra como validação complementar.
    """
    limite_superior = min(k_maximo, len(matriz) - 1)
    if k_minimo > limite_superior:
        raise ValueError(
            f"Nenhum k testável: k_minimo={k_minimo} > limite superior={limite_superior} "
            f"(len(matriz)-1={len(matriz) - 1}). A amostra tem poucas linhas demais para a "
            "faixa de k configurada -- reduza K_MINIMO ou aumente o tamanho da amostra."
        )
    linhas = []
    for k in range(k_minimo, limite_superior + 1):
        modelo = KMeans(n_clusters=k, random_state=semente, n_init=n_init).fit(matriz)
        rotulos = modelo.labels_
        silhueta = float(silhouette_score(matriz, rotulos)) if k >= 2 and len(matriz) > k else np.nan
        linhas.append({"k": k, "inercia": float(modelo.inertia_), "silhueta": silhueta})

    tabela = pd.DataFrame(linhas)
    registrar_log(f"Inércia e silhueta calculadas para k = {k_minimo}..{limite_superior} ({len(tabela)} valor(es) de k).")
    return tabela


def escolher_k_pelo_cotovelo(tabela_k, sensibilidade=SENSIBILIDADE_COTOVELO):
    """
    Cotovelo da curva de inércia (Thorndike, 1953) via kneed
    (curve='convex', direction='decreasing') -- não fixado à mão. Mesma
    técnica (KneeLocator) usada para estimar eps no DBSCAN, aplicada agora
    à curva de inércia em função de k.
    """
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
                      n_init=NUMERO_DE_INICIALIZACOES):
    """Validação complementar ao cotovelo: inércia e silhueta de cada
    combinação (k, semente) via ParameterGrid."""
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
        modelo = KMeans(n_clusters=k, random_state=semente, n_init=n_init).fit(matriz)
        rotulos = modelo.labels_
        silhueta = float(silhouette_score(matriz, rotulos)) if k >= 2 and len(matriz) > k else np.nan
        linhas.append({"k": k, "semente": semente, "inercia": float(modelo.inertia_), "silhueta": silhueta})

    return pd.DataFrame(linhas).sort_values(["k", "semente"]).reset_index(drop=True)


# Etapa 5: KMeans
def executar_kmeans(matriz, k, semente=SEMENTE_ALEATORIA, n_init=NUMERO_DE_INICIALIZACOES):
    modelo = KMeans(n_clusters=k, random_state=semente, n_init=n_init).fit(matriz)
    return modelo.labels_, modelo


def resumir_agrupamento_kmeans(matriz, rotulos, modelo):
    """KMeans não tem ruído (todo ponto pertence a algum cluster) -- por
    isso a silhueta aqui é uma única versão, sobre todos os pontos."""
    n_clusters = len(set(rotulos))
    silhueta = np.nan
    if n_clusters >= 2 and len(matriz) > n_clusters:
        silhueta = float(silhouette_score(matriz, rotulos))
    return n_clusters, float(modelo.inertia_), silhueta


def diagnostico_tamanho_dos_clusters(rotulos, minimo=MINIMO_DE_ELEMENTOS_POR_CLUSTER):
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
    n_componentes_pca = int(pca.n_components_) if pca is not None else np.nan
    variancia_explicada = float(variancia_acumulada[n_componentes_pca - 1]) if pca is not None else np.nan
    return pd.DataFrame([{
        "K": k,
        "ESCALONADOR": "RobustScaler" if usar_robust_scaler else "nenhum",
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
    """Uma linha por CLUSTER: quantidade de pares, quantas Regionais
    distintas caem nele e a lista de 'REGIONAL (ANO)' membros."""
    def _membros(grupo):
        return ", ".join(f"{r} ({a})" for r, a in zip(grupo[COLUNA_REGIONAL], grupo[COLUNA_ANO]))

    resumo = tabela_pertencimento.groupby("CLUSTER").apply(
        lambda grupo: pd.Series({
            "N_PARES": len(grupo),
            "N_REGIONAIS_DISTINTAS": grupo[COLUNA_REGIONAL].nunique(),
            "MEMBROS": _membros(grupo),
        }),
        include_groups=False,
    ).reset_index().sort_values("CLUSTER").reset_index(drop=True)
    return resumo
