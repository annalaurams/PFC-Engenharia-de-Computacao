import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from kneed import KneeLocator
from sklearn.cluster import DBSCAN
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from sklearn.neighbors import BallTree, KDTree, NearestNeighbors
from sklearn.preprocessing import RobustScaler


# Localização dos utilitários comuns do projeto
def _preparar_sys_path():
    candidatos = [
        Path.cwd().parent.parent / "Seleção e Transformação" / "População",
        Path.home() / "tcc" / "Seleção e Transformação" / "População",
        Path.cwd() / "Seleção e Transformação" / "População",
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

ROTULO_RUIDO = -1
PASTA_TAXA = PASTA_POPULACAO / "Taxa"


# CONSTANTES DE CONFIGURAÇÃO

SEMENTE_ALEATORIA = 42

# Blocos de taxa que compõem o painel -- cada um é lido e reformatado de
# largo para painel (REGIONAL, ANO) x categoria, e prefixado para não
# colidir com as categorias dos demais blocos. Hospitais fica de fora:
# só tem dado para 2023, não cabe em formato painel.
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


USAR_JANELA_COMUM = True
ANO_INICIAL_COMUM = 2013
ANO_FINAL_COMUM = 2023

# Nos CSVs de taxa, uma célula fica em branco (NaN) quando a soma bruta da
# categoria-ano-regional é NaN em TODOS os municípios da regional -- e
# calculo_taxa.ipynb preserva essa ambiguidade de propósito (sum(min_count=1)):
# não dá para distinguir "zero eventos" de "sem população válida para
# calcular" só olhando a taxa. Por isso NaN nunca vira 0 aqui. Colunas cuja
# proporção de nulos (dentro da janela comum) ultrapassa este limiar são
# descartadas -- tipicamente categorias clinicamente quase inexistentes
# (ex.: mortalidade por câncer de mama em faixas etárias jovens) que,
# mantidas, esvaziariam a base inteira no dropna sem imputação.
LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA = 0.70

# --- Estimativa de eps (Monko & Kimura, 2023) ---
K_VIZINHOS_EPS = 5           # k: nº de vizinhos mais próximos por ponto
QUANTIDADE_DE_ESTRATOS = 10  # p: nº de estratos de mesma amplitude
AMOSTRAS_POR_ESTRATO = 5     # m: nº de pontos amostrados por estrato
GRAU_POLINOMIO_EPS = 3
SENSIBILIDADE_JOELHO = 1.0

# --- Estimativa de MinPts (grid search, eps fixo) ---
MIN_SAMPLES_MINIMO = 3
# Teto do grid search: NÃO é mais um valor fixo (era MIN_SAMPLES_MAXIMO=100,
# força bruta desnecessária para o tamanho deste painel -- 28 regionais).
# Regra de bolso de Sander et al. (1998, "Density-Based Clustering in
# Spatial Databases: The Algorithm GDBSCAN and Its Applications", Data
# Mining and Knowledge Discovery 2(2)): MinPts ~ 2 x dimensionalidade dos
# dados já é suficiente para estimar densidade local em espaços de
# baixa/média dimensão. MULTIPLICADOR_MIN_SAMPLES_MAXIMO dobra essa
# referência (4x a dimensionalidade) para dar folga à busca em grade sem
# reintroduzir um teto arbitrariamente alto -- ver `buscar_min_samples`,
# onde o teto ainda é limitado por len(matriz)-1.
MULTIPLICADOR_MIN_SAMPLES_MAXIMO = 4
MIN_SAMPLES_PASSO = 1

# --- Padronização / redução de dimensionalidade ---
# USAR_PCA=None (padrão): decide sozinho pela razão nº de atributos / nº
# de linhas (aplica PCA quando ultrapassa RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA
# -- muitos atributos para poucas observações torna a distância euclidiana
# pouco informativa, maldição da dimensionalidade). USAR_PCA=True força
# PCA mesmo com poucos atributos; USAR_PCA=False pula o PCA inteiramente,
# mesmo com muitos -- útil para diagnosticar se a alta dimensionalidade é
# de fato a causa de algum comportamento do DBSCAN (ex.: eps grande demais).
USAR_PCA = False
RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA = 0.10
VARIANCIA_EXPLICADA_ALVO = 0.85
NUMERO_MAXIMO_DE_COMPONENTES = 10

# PC1 explicando mais que isto sinaliza uma direção dominante isolada --
# indício de que os atributos medem majoritariamente a mesma coisa
# (tipicamente porte/volume da observação), não perfis distintos. Usado só
# para destacar o alerta em `grafico_variancia_explicada` (graficos_agrupamentoManual.py).
VARIANCIA_PC1_ALERTA = 0.75

# --- DBSCAN ---
METRICA_DISTANCIA = "euclidean"  # "euclidean", "manhattan", "cosine", etc. (ver sklearn)


# Etapa 1: leitura dos CSVs de taxa e reformatação largo -> painel

def _slug(texto):
    """'SEM INFORMAÇÃO' -> 'sem-informacao'. Sem acento, minúsculo, hifenizado."""
    sem_acento = unicodedata.normalize("NFKD", str(texto).strip().lower())
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return "-".join(sem_acento.split())


def ler_csv_taxa_em_painel(caminho_csv, prefixo):
    """
    Lê um CSV de taxa (formato largo, colunas '<ano>_<categoria>_TAXA',
    esquema gerado por calculo_taxa.ipynb) e devolve o painel: índice
    (REGIONAL DE SAÚDE, ANO), uma coluna por categoria, prefixada.

    Só as colunas de TAXA entram (nunca o valor absoluto) -- o agrupamento
    compara regionais entre si, e por isso precisa de uma variável já
    ajustada por população. Nenhuma taxa é recalculada aqui, a etapa é
    só de reformatação (largo -> longo -> painel).
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
    Janela comum a todos os blocos.

    Sem argumentos manuais, é a interseção das coberturas declaradas
    (ANO_INICIAL/ANO_FINAL) de cada bloco -- fora dela um bloco
    simplesmente não tem dado (o CSV não cobre aquele ano), o que é uma
    questão de cobertura, não um valor ausente a tratar.

    Com ano_inicial_manual/ano_final_manual, o período usado é o
    informado diretamente -- a interseção calculada continua servindo de
    checagem: se o período manual for mais amplo do que ela, um aviso é
    emitido (algum bloco terá anos sem dado dentro do período pedido).
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
    """
    Remove colunas cuja proporção de nulos ultrapassa `limiar_maximo`.
    """
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
    """
    Descarta linhas com ao menos um valor ausente
    """
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
            "manual ampla), dificilmente todos os blocos têm dado no mesmo par regional-ano. "
            "Ajuste USAR_JANELA_COMUM/ANO_INICIAL_COMUM/ANO_FINAL_COMUM, ou "
            "LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA para descartar mais atributos esparsos antes desta etapa."
        )
    return matriz_sem_nulos


# Etapa 3: padronização e PCA
def padronizar_e_reduzir(matriz, razao_maxima_atributos_por_linha=RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA,
                          variancia_alvo=VARIANCIA_EXPLICADA_ALVO,
                          numero_maximo_de_componentes=NUMERO_MAXIMO_DE_COMPONENTES,
                          semente=SEMENTE_ALEATORIA, usar_pca=USAR_PCA):
    """
    RobustScaler (mediana / IQR) sempre. PCA conforme `usar_pca`:
    None (padrão) decide sozinho pela razão nº de atributos / nº de linhas
    (aplica se ultrapassar `razao_maxima_atributos_por_linha`); True força
    PCA; False pula o PCA inteiramente -- em ambos os casos o critério
    automático é ignorado.

    Devolve (matriz_padronizada, matriz_para_dbscan, pca, variancia_acumulada).
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
    """
    PC1 x PC2 para visualização. Se o PCA já foi aplicado (>= 2
    componentes), reaproveita as duas primeiras -- é o mesmo espaço em
    que o DBSCAN rodou. Senão, ajusta um PCA de 2 componentes só para
    posicionar os pontos no plano; essa projeção é MERAMENTE ILUSTRATIVA,
    não influencia o agrupamento.
    """
    if pca is not None:
        return matriz_reduzida[:, :2], pca.explained_variance_ratio_[:2]
    pca_2d = PCA(n_components=2, random_state=semente).fit(matriz_padronizada)
    return pca_2d.transform(matriz_padronizada), pca_2d.explained_variance_ratio_


def pesos_das_variaveis_no_componente(pca, colunas, componente=1):
    """
    Peso (\"loading\") de cada atributo original no componente principal
    indicado (1-based), ordenado por magnitude -- interpreta o que aquele
    eixo representa: pesos concentrados num pequeno grupo de atributos
    correlacionados (ex.: só categorias de \"casos\") sugerem que o
    componente captura volume/porte da regional; pesos distribuídos entre
    atributos de blocos distintos (casos, mortalidade, mamografia...)
    sugerem um eixo de perfil epidemiológico, não de porte.
    """
    if pca is None:
        raise ValueError("pesos_das_variaveis_no_componente requer PCA aplicado (pca is None).")
    pesos = pd.Series(pca.components_[componente - 1], index=colunas, name=f"PC{componente}")
    return pesos.reindex(pesos.abs().sort_values(ascending=False).index)


# Etapa 4: estimativa de eps (Monko & Kimura, 2023)
def distancia_media_aos_k_vizinhos(matriz, k, metric=METRICA_DISTANCIA):
    """Para cada ponto, a média das distâncias euclidianas aos k vizinhos
    mais próximos (exclui o próprio ponto)."""
    vizinhanca = NearestNeighbors(n_neighbors=k + 1, metric=metric).fit(matriz)
    distancias, _ = vizinhanca.kneighbors(matriz)
    return distancias[:, 1:].mean(axis=1)


def amostragem_estratificada(curva_ordenada, p, m, semente=SEMENTE_ALEATORIA):
    """
    Divide `curva_ordenada` (já ordenada de forma crescente) em p
    estratos de MESMA AMPLITUDE (não de mesma contagem) entre o mínimo e
    o máximo, e amostra até m pontos de cada estrato -- reduz o ruído da
    curva antes do ajuste polinomial sem perder a variação ao longo de
    toda a faixa de distâncias.
    """
    rng = np.random.default_rng(semente)
    limites = np.linspace(curva_ordenada.min(), curva_ordenada.max(), p + 1)

    indices_amostrados = []
    for i in range(p):
        inferior, superior = limites[i], limites[i + 1]
        if i < p - 1:
            mascara = (curva_ordenada >= inferior) & (curva_ordenada < superior)
        else:
            mascara = (curva_ordenada >= inferior) & (curva_ordenada <= superior)
        indices_do_estrato = np.flatnonzero(mascara)
        if len(indices_do_estrato) == 0:
            continue
        quantidade = min(m, len(indices_do_estrato))
        indices_amostrados.append(rng.choice(indices_do_estrato, size=quantidade, replace=False))

    return np.sort(np.concatenate(indices_amostrados))


def estimar_eps_monko_kimura(matriz, k=K_VIZINHOS_EPS, p=QUANTIDADE_DE_ESTRATOS, m=AMOSTRAS_POR_ESTRATO,
                              grau_polinomio=GRAU_POLINOMIO_EPS, sensibilidade=SENSIBILIDADE_JOELHO,
                              semente=SEMENTE_ALEATORIA, metric=METRICA_DISTANCIA):
    """
    Estimativa de eps por Monko & Kimura (2023):
      1) distância média de cada ponto aos k vizinhos mais próximos;
      2) curva ordenada de forma crescente + amostragem estratificada
         (p estratos de mesma amplitude, m pontos cada);
      3) ajuste polinomial sobre a amostra;
      4) joelho da curva ajustada (kneed, curve='convex',
         direction='increasing') -> eps.
    """
    curva_ordenada = np.sort(distancia_media_aos_k_vizinhos(matriz, k, metric=metric))
    indices_amostrados = amostragem_estratificada(curva_ordenada, p, m, semente=semente)
    x_amostra = indices_amostrados
    y_amostra = curva_ordenada[indices_amostrados]

    grau = min(grau_polinomio, len(x_amostra) - 1)
    coeficientes = np.polyfit(x_amostra, y_amostra, deg=grau)
    x_completo = np.arange(len(curva_ordenada))
    curva_ajustada = np.polyval(coeficientes, x_completo)

    localizador = KneeLocator(x_completo, curva_ajustada, S=sensibilidade, curve="convex", direction="increasing")
    indice_joelho = localizador.knee
    if indice_joelho is None:
        registrar_log(
            "ATENÇÃO: kneed não encontrou joelho na curva ajustada -- usando o ponto de maior "
            "curvatura discreta (segunda derivada) como reserva."
        )
        indice_joelho = int(np.argmax(np.gradient(np.gradient(curva_ajustada))))

    eps = float(curva_ordenada[indice_joelho])
    registrar_log(
        f"eps (Monko & Kimura, k={k}, p={p}, m={m}, grau={grau}): {eps:.4f} "
        f"no índice {indice_joelho} de {len(curva_ordenada)}."
    )
    return {
        "eps": eps, "curva": curva_ordenada, "curva_ajustada": curva_ajustada,
        "amostra_x": x_amostra, "amostra_y": y_amostra, "indice_joelho": indice_joelho,
    }


# Etapa 5: DBSCAN -- escolha de algoritmo de indexação e estimativa de MinPts
def _algoritmo_por_metrica(metric):
    """
    Escolhe a estrutura de indexação espacial do DBSCAN para a busca de
    vizinhança -- nunca algorithm='brute' (varredura par a par, O(n^2)).
    kd_tree quando a métrica é compatível; ball_tree como alternativa para
    métricas que o kd_tree não suporta mas o ball_tree sim (ex.: métricas
    que não obedecem à decomposição por eixos do kd_tree). Se nenhuma das
    duas suportar a métrica (ex.: 'cosine', que exige 'brute'), levanta
    erro em vez de cair silenciosamente em 'brute'.

    Preserva a complexidade média de busca O(n log n) da indexação
    espacial, análoga em espírito à árvore R* usada por Ester et al.
    (1996, "A Density-Based Algorithm for Discovering Clusters in Large
    Spatial Databases with Noise", KDD-96) -- e não a varredura par a par
    de 'brute'.
    """
    if metric in KDTree.valid_metrics:
        return "kd_tree"
    if metric in BallTree.valid_metrics:
        return "ball_tree"
    raise ValueError(
        f"Métrica '{metric}' não é suportada por kd_tree nem por ball_tree -- só seria "
        "possível com algorithm='brute' (varredura par a par), que este projeto não usa "
        "(ver _algoritmo_por_metrica). Escolha outra métrica ou trate este caso explicitamente."
    )


def executar_dbscan(matriz, eps, min_samples, metric=METRICA_DISTANCIA):
    algoritmo = _algoritmo_por_metrica(metric)
    return DBSCAN(eps=eps, min_samples=min_samples, metric=metric, algorithm=algoritmo, n_jobs=-1).fit(matriz)


def buscar_min_samples(matriz, eps, minimo=MIN_SAMPLES_MINIMO, maximo=None,
                        passo=MIN_SAMPLES_PASSO, metric=METRICA_DISTANCIA):
    """
    Grid search de Monko & Kimura (2023): eps FIXO, varia só MinPts em
    [minimo, maximo] (passo `passo`), avaliado pela maior silhueta SEM
    ruído (ver `resumir_agrupamento` para a ressalva sobre a versão com
    ruído). Empate na silhueta (e no nº de agrupamentos) -> menor MinPts.
    MinPts nunca fica abaixo de 3.

    `maximo=None` (padrão) deriva o teto de MULTIPLICADOR_MIN_SAMPLES_MAXIMO
    x nº de atributos de `matriz` (ver comentário da constante) em vez de
    um valor fixo; ainda é limitado por len(matriz)-1.
    """
    minimo = max(minimo, 3)
    if maximo is None:
        maximo = max(minimo, MULTIPLICADOR_MIN_SAMPLES_MAXIMO * matriz.shape[1])
    limite_superior = min(maximo, len(matriz) - 1)
    candidatos = list(range(minimo, limite_superior + 1, passo))

    linhas = []
    for min_samples in candidatos:
        rotulos = executar_dbscan(matriz, eps, min_samples, metric=metric).labels_
        n_clusters, n_ruido, silhueta, silhueta_com_ruido = resumir_agrupamento(matriz, rotulos)
        linhas.append({
            "min_samples": min_samples, "n_clusters": n_clusters, "n_ruido": n_ruido,
            "silhueta": silhueta, "silhueta_com_ruido": silhueta_com_ruido,
        })

    tabela = pd.DataFrame(linhas)
    candidatos_validos = tabela.dropna(subset=["silhueta"])

    if candidatos_validos.empty:
        registrar_log(
            "ATENÇÃO: nenhum MinPts da grade produziu >= 2 agrupamentos válidos para a "
            "silhueta -- mantendo o menor MinPts testado."
        )
        min_samples_escolhido = int(tabela["min_samples"].min())
    else:
        silhueta_maxima = candidatos_validos["silhueta"].max()
        empatados = candidatos_validos[np.isclose(candidatos_validos["silhueta"], silhueta_maxima)]
        min_samples_escolhido = int(empatados["min_samples"].min())  # empate -> menor MinPts

    registrar_log(f"MinPts escolhido: {min_samples_escolhido} (grade {minimo}-{limite_superior}, passo {passo}).")
    return min_samples_escolhido, tabela


def resumir_agrupamento(matriz, rotulos):
    """
    Silhueta em DUAS versões: SEM ruído (rótulo -1 excluído -- é o
    critério usado por `buscar_min_samples` para escolher MinPts) e COM
    ruído (tratado como um rótulo de cluster igual aos demais).

    A versão com ruído distorce a métrica: silhouette_score assume que
    cada rótulo é de fato um agrupamento, e o ruído do DBSCAN representa
    ausência de agrupamento, não um agrupamento válido -- por isso ela é
    só reportada, nunca usada como critério de seleção.
    """
    n_clusters = len(set(rotulos) - {ROTULO_RUIDO})
    n_ruido = int(np.sum(rotulos == ROTULO_RUIDO))
    sem_ruido = rotulos != ROTULO_RUIDO

    silhueta_sem_ruido = np.nan
    if n_clusters >= 2 and sem_ruido.sum() > n_clusters:
        silhueta_sem_ruido = float(silhouette_score(matriz[sem_ruido], rotulos[sem_ruido]))

    rotulos_presentes = set(rotulos)
    silhueta_com_ruido = np.nan
    if len(rotulos_presentes) >= 2 and len(matriz) > len(rotulos_presentes):
        silhueta_com_ruido = float(silhouette_score(matriz, rotulos))

    return n_clusters, n_ruido, silhueta_sem_ruido, silhueta_com_ruido


# Saídas finais em DataFrame

def montar_resumo_parametros(k, p, m, eps, min_samples, metric, usar_robust_scaler, pca,
                              variancia_acumulada, n_linhas, n_atributos, n_clusters, n_ruido,
                              silhueta_sem_ruido, silhueta_com_ruido):
    n_componentes_pca = int(pca.n_components_) if pca is not None else np.nan
    variancia_explicada = float(variancia_acumulada[n_componentes_pca - 1]) if pca is not None else np.nan
    return pd.DataFrame([{
        "K_VIZINHOS_EPS": k,
        "QUANTIDADE_DE_ESTRATOS": p,
        "AMOSTRAS_POR_ESTRATO": m,
        "EPS": eps,
        "MIN_SAMPLES": min_samples,
        "METRICA_DISTANCIA": metric,
        "ESCALONADOR": "RobustScaler" if usar_robust_scaler else "nenhum",
        "PCA_APLICADO": pca is not None,
        "PCA_N_COMPONENTES": n_componentes_pca,
        "PCA_VARIANCIA_EXPLICADA": variancia_explicada,
        "N_LINHAS": n_linhas,
        "N_ATRIBUTOS": n_atributos,
        "N_CLUSTERS": n_clusters,
        "N_RUIDO": n_ruido,
        "SILHUETA_SEM_RUIDO": silhueta_sem_ruido,
        "SILHUETA_COM_RUIDO": silhueta_com_ruido,
    }])


def montar_tabela_pertencimento(indice, rotulos):
    """REGIONAL DE SAÚDE, ANO, CLUSTER -- uma linha por par agrupado."""
    tabela = indice.to_frame(index=False)
    tabela["CLUSTER"] = rotulos
    return tabela


def montar_visao_agregada_regional_ano(tabela_pertencimento):
    """Regional (linha) x Ano (coluna) -> CLUSTER. Mostra em quais
    agrupamentos e em quais anos cada Regional de Saúde caiu."""
    return tabela_pertencimento.pivot(index=COLUNA_REGIONAL, columns=COLUNA_ANO, values="CLUSTER")


def montar_resumo_por_cluster(tabela_pertencimento):
    """
    Uma linha por CLUSTER (ruído incluído): quantidade de pares, quantas
    Regionais distintas caem nele e a lista de 'REGIONAL (ANO)' membros.

    A dispersão PC1 x PC2 é uma projeção -- dois clusters distintos no
    espaço original podem se sobrepor visualmente em 2D. Esta tabela lista
    a composição real de cada CLUSTER encontrado pelo DBSCAN, sem depender
    da leitura do gráfico.
    """
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


# =======================================================================
# Diagnóstico de parâmetros (usado por diagnostico_parametrosManual.ipynb)
# =======================================================================
def estatisticas_da_curva(curva):
    """
    Estatísticas descritivas da curva de k-distâncias -- caracteriza a
    forma da curva (amplitude, salto máximo entre pontos consecutivos e
    sua posição relativa) sem depender só da leitura visual do gráfico.
    """
    saltos = np.diff(curva)
    amplitude = curva.max() - curva.min()
    return {
        "amplitude_curva": amplitude,
        "salto_maximo": saltos.max(),
        "razao_salto_amplitude": saltos.max() / amplitude,
        "indice_maior_salto_pct": np.argmax(saltos) / len(curva),
    }


def rodar_cenario_diagnostico(nome, matriz_dbscan, k_eps=K_VIZINHOS_EPS):
    """
    Roda o pipeline eps -> MinPts -> DBSCAN num cenário de diagnóstico
    (mesmas funções do pipeline principal, só variando parâmetros de
    entrada -- nenhuma lógica nova) e resume o resultado num dicionário
    para comparação em tabela.
    """
    resultado_eps_cenario = estimar_eps_monko_kimura(matriz_dbscan, k=k_eps)
    eps_cenario = resultado_eps_cenario["eps"]
    min_samples_cenario, _ = buscar_min_samples(matriz_dbscan, eps_cenario)
    modelo_cenario = executar_dbscan(matriz_dbscan, eps_cenario, min_samples_cenario)
    n_clusters_cenario, n_ruido_cenario, silhueta_sem_ruido_cenario, silhueta_com_ruido_cenario = (
        resumir_agrupamento(matriz_dbscan, modelo_cenario.labels_)
    )
    return {
        "CENARIO": nome, "N_DIMENSOES": matriz_dbscan.shape[1], "K_VIZINHOS_EPS": k_eps,
        "EPS": eps_cenario, "MIN_SAMPLES": min_samples_cenario,
        "N_CLUSTERS": n_clusters_cenario, "N_RUIDO": n_ruido_cenario,
        "SILHUETA_SEM_RUIDO": silhueta_sem_ruido_cenario,
        "SILHUETA_COM_RUIDO": silhueta_com_ruido_cenario,
        **estatisticas_da_curva(resultado_eps_cenario["curva"]),
    }
