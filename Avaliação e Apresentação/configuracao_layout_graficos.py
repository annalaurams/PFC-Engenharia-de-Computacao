FORMATO_VALOR_BARRA = ",.0f"  # separador de milhar e nenhuma casa decimal

COR_SEM_INFORMACAO = "#B0B0B0"

CORES_CATEGORIAS_CUSTOMIZADAS = {}

# Gráfico de linha categórico

PALETA_CATEGORIAS_FORTE = [
    "#E41A1C",
    "#F781BF",
    "#A65628",
    "#4DAF4A",
    "#377EB8",
    "#FF7F00",
    "#984EA3",
    "#D4AC0D",
]

# Os símbolos alternam na mesma ordem da paleta
MARCADORES_CATEGORIAS = ["circle", "square", "diamond", "triangle-up", "triangle-down", "star", "cross", "x"]
MARCADOR_SEM_INFORMACAO = "circle-open"

TAMANHO_MARCADOR_LINHA_CATEGORICA = 11
LARGURA_BORDA_MARCADOR_LINHA_CATEGORICA = 1.5
COR_BORDA_MARCADOR_LINHA_CATEGORICA = "#FFFFFF"

# Rótulo de valor só nos anos múltiplos da frequência, a partir do ano âncora
FREQUENCIA_ROTULO_LINHA_CATEGORICA = 4
ANO_ANCORA_ROTULO_LINHA_CATEGORICA = 1999
TAMANHO_FONTE_VALOR_LINHA_CATEGORICA = 14

# Largura mínima por ano no eixo X, em px
LARGURA_MINIMA_POR_ANO_LINHA_CATEGORICA = 73

# Esconde o rótulo de pontos abaixo desta fração do maior valor do gráfico
LIMIAR_ROTULO_LINHA_CATEGORICA = 0.03

# Posição do rótulo de valor (textposition do Plotly), alternada por categoria
POSICOES_ROTULO_LINHA_CATEGORICA = [
    "top center", "bottom center", "top right", "bottom left",
    "middle right", "middle left", "top left", "bottom right",
]

# Largura mínima por categoria no eixo X, em px
LARGURA_MINIMA_POR_CATEGORIA = 65

# Tamanhos de fonte

MULTIPLICADOR_FONTE_GLOBAL = 1.0

TAMANHO_FONTE_TITULO = 18
TAMANHO_FONTE_TITULO_EIXO = 14
TAMANHO_FONTE_TICK_EIXO = 12
TAMANHO_FONTE_LEGENDA = 12

TAMANHO_FONTE_TITULO_GRAFICO_LINHA = 24
TAMANHO_FONTE_TITULO_EIXO_GRAFICO_LINHA = 19
TAMANHO_FONTE_TICK_EIXO_GRAFICO_LINHA = 15
TAMANHO_FONTE_LEGENDA_GRAFICO_LINHA = 20  # o ícone da legenda escala com a fonte


def tamanho_fonte(tamanho_base):
    return tamanho_base * MULTIPLICADOR_FONTE_GLOBAL
