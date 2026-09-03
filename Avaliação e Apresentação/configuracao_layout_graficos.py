import plotly.express as px

# --- Gráfico de barra + linha ---
MOSTRAR_VALOR_NAS_BARRAS = True
MOSTRAR_VALOR_NA_LINHA = True

FORMATO_VALOR_BARRA = ",.0f" # vírgula = separador de milhar, .0f = zero casas decimais (número inteiro)
FORMATO_VALOR_LINHA = ".1f"
POSICAO_VALOR_BARRA = "outside"
# "top right": Deslocando a linha para a direita, os dois textos
# raramente ocupam o mesmo espaço mesmo quando as alturas coincidem.
POSICAO_VALOR_LINHA = "top right"

# --- Gráfico empilhado ---
COR_SEM_INFORMACAO = "#B0B0B0"
PALETA_QUALITATIVA = px.colors.qualitative.Safe # Cor automática por categoria, se faltar

CORES_CATEGORIAS_CUSTOMIZADAS = {}

# --- Gráfico empilhado —--
NORMALIZAR_PARA_100_PORCENTO = False # mostrar absoluto ou percentual
LIMIAR_MOSTRAR_ROTULO = 3.0 # acima de 3% da barra
LARGURA_MINIMA_POR_CATEGORIA = 65 # espaço entre elas

CORES_VARIAVEIS_PADRAO = {"COR_BARRA": "#428BD4", "COR_LINHA": "#C0392B"}

CORES_VARIAVEIS = {
    "Casos": {"COR_BARRA": "#428BD4", "COR_LINHA": "#C0392B"},
    "Mortalidade": {"COR_BARRA": "#428BD4", "COR_LINHA": "#C0392B"},
    "Mamografia": {"COR_BARRA": "#428BD4", "COR_LINHA": "#C0392B"},
    "Hospitais": {"COR_BARRA": "#428BD4", "COR_LINHA": "#C0392B"},
}

def obter_cores_variavel(nome_da_variavel):
    '''
    Cor de barra/linha da variável, chama
    CORES_VARIAVEIS_PADRAO quando o nome não está em CORES_VARIAVEIS.
    '''
    return CORES_VARIAVEIS.get(nome_da_variavel, CORES_VARIAVEIS_PADRAO)


# --- Tamanhos de fonte ---

MULTIPLICADOR_FONTE_GLOBAL = 1.0

TAMANHO_FONTE_VALOR_BARRA = 13
TAMANHO_FONTE_VALOR_LINHA = 13
TAMANHO_FONTE_ROTULO_EMPILHADO = 12
TAMANHO_FONTE_TITULO = 18
TAMANHO_FONTE_TITULO_EIXO = 14
TAMANHO_FONTE_TICK_EIXO = 12
TAMANHO_FONTE_LEGENDA = 12

# --- Tamanhos de fonte -- gráfico de linha dupla (Quantidade x Taxa
# por categoria) -- maiores que o padrão acima, para igualar o tamanho
# de fonte de título/legenda usado nos mapas
# (mapa_regional_valores_absolutos.ipynb: TAMANHO_FONTE_TITULO_MAPA=24,
# TAMANHO_FONTE_LEGENDA_MAPA=16).
TAMANHO_FONTE_TITULO_GRAFICO_LINHA = 24
TAMANHO_FONTE_TITULO_EIXO_GRAFICO_LINHA = 18
TAMANHO_FONTE_TICK_EIXO_GRAFICO_LINHA = 14
TAMANHO_FONTE_LEGENDA_GRAFICO_LINHA = 16


def tamanho_fonte(tamanho_base):
    return tamanho_base * MULTIPLICADOR_FONTE_GLOBAL
