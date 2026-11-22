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
TAMANHO_FONTE_TITULO_EIXO = 17
TAMANHO_FONTE_TICK_EIXO = 14
TAMANHO_FONTE_LEGENDA = 15

TAMANHO_FONTE_TITULO_GRAFICO_LINHA = 26
TAMANHO_FONTE_TITULO_EIXO_GRAFICO_LINHA = 26
TAMANHO_FONTE_TICK_EIXO_GRAFICO_LINHA = 22
TAMANHO_FONTE_LEGENDA_GRAFICO_LINHA = 27  # o ícone da legenda escala com a fonte

# Gráfico de linha de população interpolada/extrapolada, com destaque para anos censitários

COR_LINHA_POPULACAO_TOTAL = "#377EB8"

TAMANHO_MARCADOR_CENSITARIO_POPULACAO = 16
TAMANHO_MARCADOR_ESTIMADO_POPULACAO = 8
OPACIDADE_MARCADOR_ESTIMADO_POPULACAO = 0.55

# Destaque visual (linha vertical) dos anos censitários, nos painéis de população
COR_LINHA_DESTAQUE_ANO_CENSITARIO = "#999999"
LARGURA_LINHA_DESTAQUE_ANO_CENSITARIO = 1
OPACIDADE_LINHA_DESTAQUE_ANO_CENSITARIO = 0.6

# Painéis A/B de população (população total + por faixa etária) na mesma figura
TAMANHO_FONTE_TITULO_PAINEL_POPULACAO = TAMANHO_FONTE_TITULO_EIXO_GRAFICO_LINHA + 1
ESPACAMENTO_VERTICAL_PAINEIS_POPULACAO = 0.16


def tamanho_fonte(tamanho_base):
    """Aplica o multiplicador global de fonte a um tamanho base, para escalar todos os gráficos de uma vez."""
    return tamanho_base * MULTIPLICADOR_FONTE_GLOBAL
