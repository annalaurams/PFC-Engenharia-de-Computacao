import unicodedata

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio
from plotly.subplots import make_subplots

from utilitarios_agrupamento_kmeans import (
    COLUNA_ANO,
    COLUNA_REGIONAL,
    VARIANCIA_PC1_ALERTA,
    pesos_das_variaveis_no_componente,
)
from utilitarios_comuns import PASTA_SELECAO_TRANSFORMACAO, registrar_log  # noqa: E402

# Paleta dos clusters, na ordem Cluster 1, Cluster 2, ...
PALETA = [
    "#264653",
    
    "#E15759",
    "#2A9D8F",
    "#59A14F",
    "#E9C46A",
    "#E76F51",

]
COR_SEM_DADO = "#E3E3E3"
COR_PRINCIPAL = "#2E5C8A"
COR_DESTAQUE = "#C0392B"

# Tipografia e tamanhos padrão dos gráficos
FONTE = "Arial, Helvetica, sans-serif"
COR_TEXTO = "#2B2B2B"
TAMANHO_TITULO = 22
TAMANHO_TITULO_EIXO = 16
TAMANHO_TICK = 14
TAMANHO_LEGENDA = 16

# O botão de download do gráfico exporta PNG em 3x a resolução de tela
CONFIG_PLOTLY = {"displaylogo": False, "toImageButtonOptions": {"format": "png", "scale": 3}}
for _nome in list(pio.renderers):
    if hasattr(pio.renderers[_nome], "config"):
        pio.renderers[_nome].config = dict(CONFIG_PLOTLY)

CAMINHO_MUNICIPIOS_REGIONAIS = PASTA_SELECAO_TRANSFORMACAO / "Municípios" / "tabela_municipios_regionais.csv"
_mapa_regional = None


def nome_da_regional(nome_normalizado):
    """Nome original da Regional (com acentos e maiúsculas) a partir do nome normalizado."""
    global _mapa_regional
    if _mapa_regional is None:
        tabela = pd.read_csv(CAMINHO_MUNICIPIOS_REGIONAIS)
        _mapa_regional = dict(zip(tabela["REGIONAL NORMALIZADA"], tabela["REGIONAL ORIGINAL"]))
    if nome_normalizado not in _mapa_regional:
        registrar_log(f"ATENÇÃO: Regional '{nome_normalizado}' sem nome original -- usando .title().")
        return str(nome_normalizado).title()
    return _mapa_regional[nome_normalizado]


def rotulo_do_cluster(numero):
    """Texto de legenda do cluster, ex.: 'Cluster 1'."""
    return f"Cluster {int(numero)}"


def cores_dos_clusters(rotulos_presentes):
    """Associa cada rótulo de cluster a uma cor da paleta."""
    cores = {}
    for indice, rotulo in enumerate(rotulos_presentes):
        cores[rotulo] = PALETA[indice % len(PALETA)]
    return cores


def aplicar_layout_padrao(figura, titulo, largura, altura, **layout):
    """Aplica o estilo padrão (fontes, eixos, grade, legenda) a uma figura."""
    figura.update_layout(
        template="plotly_white", width=largura, height=altura,
        title=dict(text=titulo, x=0.01, xanchor="left", font=dict(size=TAMANHO_TITULO, color=COR_TEXTO)),
        font=dict(family=FONTE, size=TAMANHO_TICK, color=COR_TEXTO),
        legend=dict(font=dict(size=TAMANHO_LEGENDA), title_font=dict(size=TAMANHO_LEGENDA)),
        hoverlabel=dict(font=dict(family=FONTE, size=TAMANHO_TICK)),
        plot_bgcolor="white", paper_bgcolor="white",
    )
    figura.update_xaxes(
        showline=True, linecolor="#555555", ticks="outside", tickcolor="#555555",
        gridcolor="#EBEBEB", zeroline=False, title_font=dict(size=TAMANHO_TITULO_EIXO),
        tickfont=dict(size=TAMANHO_TICK),
    )
    figura.update_yaxes(
        showline=True, linecolor="#555555", ticks="outside", tickcolor="#555555",
        gridcolor="#EBEBEB", zeroline=False, title_font=dict(size=TAMANHO_TITULO_EIXO),
        tickfont=dict(size=TAMANHO_TICK),
    )
    figura.update_annotations(font=dict(size=TAMANHO_TITULO_EIXO, color=COR_TEXTO))
    if layout:
        figura.update_layout(**layout)
    return figura


LEGENDA_HORIZONTAL_TOPO = dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0)


def grafico_variancia_explicada(pca, variancia_acumulada, limiar_alerta=VARIANCIA_PC1_ALERTA):
    """Barras da variância por componente e linha da variância acumulada (PCA)."""
    proporcoes = pca.explained_variance_ratio_
    rotulos_componentes = [f"PC{i}" for i in range(1, len(proporcoes) + 1)]
    pc1_domina = proporcoes[0] > limiar_alerta

    cores_barras = []
    for indice in range(len(proporcoes)):
        if indice == 0 and pc1_domina:
            cores_barras.append(COR_DESTAQUE)
        else:
            cores_barras.append(COR_PRINCIPAL)

    figura = go.Figure()
    figura.add_trace(go.Bar(
        x=rotulos_componentes, y=proporcoes, name="Variância por componente",
        marker=dict(color=cores_barras),
    ))
    figura.add_trace(go.Scatter(
        x=rotulos_componentes, y=variancia_acumulada, mode="lines+markers",
        name="Variância acumulada", line=dict(color="#1B7F3A", width=3), marker=dict(size=9),
    ))
    if pc1_domina:
        figura.add_annotation(
            x=rotulos_componentes[0], y=proporcoes[0],
            text=f"PC1 = {proporcoes[0]:.1%} > {limiar_alerta:.0%}",
            showarrow=True, arrowhead=2, font=dict(color=COR_DESTAQUE, size=TAMANHO_TICK), ay=-40,
        )
    return aplicar_layout_padrao(
        figura, "Variância explicada por componente principal", 1000, 560,
        xaxis_title="Componente", yaxis=dict(title="Proporção da variância", tickformat=".0%"),
        legend=LEGENDA_HORIZONTAL_TOPO, margin=dict(t=110),
    )


def grafico_pesos_da_componente(pca, colunas, componente=1, top_n=15):
    """Barras horizontais com os maiores pesos (loadings) de um componente do PCA."""
    pesos = pesos_das_variaveis_no_componente(pca, colunas, componente=componente).head(top_n)
    valores = pesos.to_numpy()[::-1]

    cores_barras = []
    for valor in valores:
        if valor < 0:
            cores_barras.append(COR_DESTAQUE)
        else:
            cores_barras.append(COR_PRINCIPAL)

    figura = go.Figure(go.Bar(
        x=valores, y=list(pesos.index)[::-1], orientation="h",
        marker=dict(color=cores_barras),
    ))
    figura.add_vline(x=0, line_color="#555555", line_width=1)
    return aplicar_layout_padrao(
        figura, f"Maiores pesos (loadings) de PC{componente}", 1000, max(420, 32 * top_n),
        xaxis_title="Peso no componente", margin=dict(l=280),
    )


def _grafico_por_k(tabela_k, coluna, nome, k_escolhido, titulo):
    """Linha de uma medida (inércia ou silhueta) por k, com o k escolhido destacado."""
    figura = go.Figure()
    figura.add_trace(go.Scatter(
        x=tabela_k["k"], y=tabela_k[coluna], mode="lines+markers",
        name=nome, line=dict(color=COR_PRINCIPAL, width=3), marker=dict(size=9),
    ))
    linha_escolhida = tabela_k[tabela_k["k"] == k_escolhido]
    figura.add_trace(go.Scatter(
        x=linha_escolhida["k"], y=linha_escolhida[coluna], mode="markers",
        name=f"k escolhido = {k_escolhido}",
        marker=dict(color=COR_DESTAQUE, size=20, symbol="star", line=dict(width=1, color="white")),
    ))
    return aplicar_layout_padrao(
        figura, titulo, 1100, 580,
        xaxis=dict(title="Número de clusters (k)", dtick=1), yaxis_title=nome,
        legend=LEGENDA_HORIZONTAL_TOPO, margin=dict(t=110),
    )


def grafico_cotovelo_inercia(tabela_k, indice_do_cotovelo, k_escolhido):
    """Curva de inércia por k (método do cotovelo)."""
    return _grafico_por_k(tabela_k, "inercia", "Inércia (WCSS)", k_escolhido, "")


def grafico_silhueta_por_k(tabela_k, k_escolhido):
    """Curva de silhueta por k (não usada no pipeline final)."""
    return _grafico_por_k(
        tabela_k, "silhueta", "Silhueta", k_escolhido,
        "Silhueta em função de k (validação complementar ao cotovelo)",
    )


def _trace_de_dispersao(matriz_2d, selecao, rotulo, cor, textos, tamanho, mostrar_legenda=True):
    return go.Scatter(
        x=matriz_2d[selecao, 0], y=matriz_2d[selecao, 1], mode="markers",
        name=rotulo_do_cluster(rotulo), legendgroup=rotulo_do_cluster(rotulo), showlegend=mostrar_legenda,
        marker=dict(color=cor, size=tamanho, opacity=0.9, line=dict(width=1, color="white")),
        text=textos, hovertemplate="<b>%{text}</b><br>PC1: %{x:.2f}<br>PC2: %{y:.2f}<extra></extra>",
    )


def grafico_dispersao_pc1_pc2_kmeans(matriz_2d, rotulos, indice, variancia_explicada, k):
    """Dispersão PC1 x PC2 dos pares Regional-Ano, colorida pelo cluster."""
    rotulos_presentes = sorted(set(rotulos))
    paleta = cores_dos_clusters(rotulos_presentes)
    regionais = [nome_da_regional(r) for r in indice.get_level_values(COLUNA_REGIONAL)]
    anos = indice.get_level_values(COLUNA_ANO)
    textos = np.array([f"{r} — {a}" for r, a in zip(regionais, anos)])

    figura = go.Figure()
    for rotulo in rotulos_presentes:
        selecao = rotulos == rotulo
        figura.add_trace(_trace_de_dispersao(matriz_2d, selecao, rotulo, paleta[rotulo], textos[selecao], 11))
    return aplicar_layout_padrao(
        figura, f"Agrupamento dos pares Regional-Ano — KMeans (k = {k})", 1100, 720,
        xaxis_title=f"PC1 ({variancia_explicada[0]:.1%} da variância)",
        yaxis_title=f"PC2 ({variancia_explicada[1]:.1%} da variância)",
        legend=dict(**LEGENDA_HORIZONTAL_TOPO, itemsizing="constant"), margin=dict(t=110),
    )


def grafico_dispersao_pc1_pc2_por_ano(matriz_2d, rotulos, indice, variancia_explicada, colunas_por_linha=4):
    """Um painel de dispersão PC1 x PC2 por ano, todos na mesma escala."""
    anos = indice.get_level_values(COLUNA_ANO)
    regionais = np.array([nome_da_regional(r) for r in indice.get_level_values(COLUNA_REGIONAL)])
    anos_unicos = sorted(anos.unique())

    numero_de_linhas = int(np.ceil(len(anos_unicos) / colunas_por_linha))
    figura = make_subplots(
        rows=numero_de_linhas, cols=colunas_por_linha,
        subplot_titles=[str(ano) for ano in anos_unicos],
        horizontal_spacing=0.05, vertical_spacing=0.09,
    )

    rotulos_presentes = sorted(set(rotulos))
    paleta = cores_dos_clusters(rotulos_presentes)
    rotulos_ja_na_legenda = set()

    for indice_do_ano, ano in enumerate(anos_unicos):
        linha, coluna = divmod(indice_do_ano, colunas_por_linha)
        selecao_do_ano = anos == ano
        for rotulo in rotulos_presentes:
            selecao = selecao_do_ano & (rotulos == rotulo)
            if not selecao.any():
                continue
            figura.add_trace(
                _trace_de_dispersao(
                    matriz_2d, selecao, rotulo, paleta[rotulo], regionais[selecao], 9,
                    mostrar_legenda=rotulo not in rotulos_ja_na_legenda,
                ),
                row=linha + 1, col=coluna + 1,
            )
            rotulos_ja_na_legenda.add(rotulo)

    margem = 0.05
    amplitude_x = matriz_2d[:, 0].max() - matriz_2d[:, 0].min()
    amplitude_y = matriz_2d[:, 1].max() - matriz_2d[:, 1].min()
    eixo_x_fixo = [matriz_2d[:, 0].min() - margem * amplitude_x, matriz_2d[:, 0].max() + margem * amplitude_x]
    eixo_y_fixo = [matriz_2d[:, 1].min() - margem * amplitude_y, matriz_2d[:, 1].max() + margem * amplitude_y]

    aplicar_layout_padrao(
        figura,
        f"Agrupamento por ano — PC1 ({variancia_explicada[0]:.1%}) x PC2 ({variancia_explicada[1]:.1%}), "
        "mesma escala em todos os painéis",
        330 * colunas_por_linha, 330 * numero_de_linhas + 120,
        legend={**LEGENDA_HORIZONTAL_TOPO, "itemsizing": "constant", "y": 1.04}, margin=dict(t=150),
    )
    figura.update_xaxes(range=eixo_x_fixo, tickfont=dict(size=12))
    figura.update_yaxes(range=eixo_y_fixo, tickfont=dict(size=12))
    return figura


def grafico_heatmap_regional_ano(visao_agregada_regional_ano):
    """Heatmap Regional x Ano colorido pelo cluster de cada par (sem dado em cinza)."""
    tabela = visao_agregada_regional_ano.copy()
    tabela.index = [nome_da_regional(regional) for regional in tabela.index]
    tabela = tabela.sort_index(key=lambda nomes: nomes.map(_chave_alfabetica))

    clusters_presentes = set()
    for valor in tabela.to_numpy().flatten():
        if pd.notna(valor):
            clusters_presentes.add(int(valor))
    rotulos_presentes = sorted(clusters_presentes)
    if not rotulos_presentes:
        raise ValueError("Nenhum CLUSTER presente em `visao_agregada_regional_ano` -- nada para desenhar.")
    paleta = cores_dos_clusters(rotulos_presentes)
    posicao = {rotulo: i for i, rotulo in enumerate(rotulos_presentes)}
    n = len(rotulos_presentes)
    tem_sem_dado = tabela.isna().to_numpy().any()

    def posicao_na_escala(valor):
        if pd.notna(valor):
            return posicao[int(valor)]
        return n

    def texto_da_celula(valor):
        if pd.notna(valor):
            return rotulo_do_cluster(valor)
        return "Sem dado"

    z = tabela.map(posicao_na_escala).to_numpy()
    texto = tabela.map(texto_da_celula).to_numpy()
    cores = [paleta[rotulo] for rotulo in rotulos_presentes] + [COR_SEM_DADO]
    colorscale = []
    for i, cor in enumerate(cores):
        colorscale += [[i / len(cores), cor], [(i + 1) / len(cores), cor]]

    anos = [str(ano) for ano in tabela.columns]
    figura = go.Figure(go.Heatmap(
        z=z, x=anos, y=list(tabela.index), text=texto,
        hovertemplate="<b>%{y} — %{x}</b><br>%{text}<extra></extra>",
        colorscale=colorscale, zmin=-0.5, zmax=len(cores) - 0.5, showscale=False,
        xgap=2, ygap=2,
    ))
    itens_da_legenda = [(rotulo_do_cluster(rotulo), paleta[rotulo]) for rotulo in rotulos_presentes]
    if tem_sem_dado:
        itens_da_legenda.append(("Sem dado", COR_SEM_DADO))
    for nome, cor in itens_da_legenda:
        figura.add_trace(go.Scatter(
            x=[None], y=[None], mode="markers", name=nome, hoverinfo="skip",
            marker=dict(symbol="square", size=18, color=cor, line=dict(width=1, color="#999999")),
        ))

    aplicar_layout_padrao(
        figura, "", 1150, max(560, 30 * len(tabela.index) + 180),
        legend={**LEGENDA_HORIZONTAL_TOPO, "title_text": "", "itemsizing": "constant", "y": 1.01},
        margin=dict(l=190, t=120, r=30),
    )
    figura.update_xaxes(title_text="Ano", type="category", showgrid=False, showline=False, ticks="")
    figura.update_yaxes(
        title_text="Regional de Saúde", automargin=True, autorange="reversed", type="category", categoryorder="array",
        categoryarray=list(tabela.index), showgrid=False, showline=False, ticks="",
    )
    return figura


def _chave_alfabetica(nome):
    """Chave de ordenação alfabética que ignora acentos e maiúsculas."""
    normalizado = unicodedata.normalize("NFKD", str(nome).lower())
    return "".join(caractere for caractere in normalizado if not unicodedata.combining(caractere))


def _grafico_distribuicao(resultado, coluna_x, titulo, titulo_eixo_x, titulo_eixo_y, largura):
    """Barras empilhadas com a contagem de pares por cluster ao longo de `coluna_x`."""
    contagem = resultado.groupby([coluna_x, "CLUSTER"]).size().reset_index(name="QUANTIDADE")
    if coluna_x == COLUNA_REGIONAL:
        contagem[coluna_x] = contagem[coluna_x].map(nome_da_regional)
        ordem_x = sorted(contagem[coluna_x].unique(), key=_chave_alfabetica)
    else:
        contagem[coluna_x] = contagem[coluna_x].astype(str)
        ordem_x = sorted(contagem[coluna_x].unique())
    rotulos_presentes = sorted(resultado["CLUSTER"].unique())
    paleta = cores_dos_clusters(rotulos_presentes)

    figura = go.Figure()
    for rotulo in rotulos_presentes:
        parte = contagem[contagem["CLUSTER"] == rotulo]
        figura.add_trace(go.Bar(
            x=parte[coluna_x], y=parte["QUANTIDADE"], name=rotulo_do_cluster(rotulo),
            marker=dict(color=paleta[rotulo], line=dict(width=0.5, color="white")),
            hovertemplate="<b>%{x}</b><br>" + rotulo_do_cluster(rotulo) + ": %{y}<extra></extra>",
        ))
    por_regional = coluna_x == COLUNA_REGIONAL
    angulo_rotulos = 0
    espacamento_y = None
    margem_inferior = 80
    if por_regional:
        angulo_rotulos = -45
        espacamento_y = 1
        margem_inferior = 140

    return aplicar_layout_padrao(
        figura, titulo, largura, 620, barmode="stack",
        xaxis=dict(
            title=titulo_eixo_x, categoryorder="array", categoryarray=ordem_x,
            tickangle=angulo_rotulos,
        ),
        yaxis=dict(title=titulo_eixo_y, dtick=espacamento_y),
        legend={**LEGENDA_HORIZONTAL_TOPO, "traceorder": "normal"},
        margin=dict(t=110, b=margem_inferior),
    )


def grafico_distribuicao_por_regional(resultado):
    """Distribuição dos clusters por Regional de Saúde."""
    return _grafico_distribuicao(
        resultado, COLUNA_REGIONAL, "Distribuição dos clusters por Regional de Saúde",
        "Regional de Saúde", "Número de anos", 1300,
    )


def grafico_distribuicao_por_ano(resultado):
    """Distribuição dos clusters por ano."""
    return _grafico_distribuicao(
        resultado, COLUNA_ANO, "Distribuição dos clusters por ano", "Ano", "Número de Regionais", 1100,
    )


def grafico_variaveis_discriminantes_por_cluster(variaveis_discriminantes):
    """Um subplot por cluster com a diferença padronizada (IQR) de suas variáveis."""
    rotulos_presentes = sorted(variaveis_discriminantes["CLUSTER"].unique())
    paleta = cores_dos_clusters(rotulos_presentes)
    maximo_de_variaveis = int(variaveis_discriminantes.groupby("CLUSTER").size().max())

    figura = make_subplots(
        rows=len(rotulos_presentes), cols=1,
        subplot_titles=[rotulo_do_cluster(r) for r in rotulos_presentes],
        vertical_spacing=0.3 / len(rotulos_presentes),
    )
    for linha, rotulo in enumerate(rotulos_presentes, start=1):
        grupo = variaveis_discriminantes[variaveis_discriminantes["CLUSTER"] == rotulo].iloc[::-1]
        figura.add_trace(
            go.Bar(
                x=grupo["DIFERENCA_PADRONIZADA"], y=grupo["VARIAVEL"], orientation="h",
                marker=dict(color=paleta[rotulo]), showlegend=False,
                customdata=grupo[["MEDIA_CLUSTER", "MEDIA_GERAL", "DIFERENCA_PERCENTUAL"]].to_numpy(),
                hovertemplate=(
                    "<b>%{y}</b><br>Diferença: %{x:.2f} IQR<br>Média do cluster: %{customdata[0]:.2f}"
                    "<br>Média geral: %{customdata[1]:.2f}<br>Diferença %: %{customdata[2]:+.1f}%<extra></extra>"
                ),
            ),
            row=linha, col=1,
        )
        figura.add_vline(x=0, line_color="#555555", line_width=1, row=linha, col=1)

    aplicar_layout_padrao(
        figura, "",
        1100, max(360, (60 + 30 * maximo_de_variaveis) * len(rotulos_presentes)),
        margin=dict(l=320, t=110),
    )
    figura.update_xaxes(title_text="(média do cluster − média geral) / IQR geral", row=len(rotulos_presentes), col=1)
    return figura
