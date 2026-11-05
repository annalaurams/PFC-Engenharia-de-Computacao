import unicodedata

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.io as pio

from utilitarios_agrupamento_kmeans import COLUNA_ANO, COLUNA_REGIONAL
from utilitarios_comuns import PASTA_SELECAO_TRANSFORMACAO, registrar_log  # noqa: E402

COR_SEM_DADO = "#E3E3E3"
COR_PRINCIPAL = "#2E5C8A"
COR_DESTAQUE = "#C0392B"

# Paleta fixa por número de cluster, usada no heatmap Regional x Ano e no mapa espacial
CLUSTER_COLORS = {
    1: "#053061",
    2: "#B3594B",
    3: "#e5d180",
    4: "#92C5DE",
    5: "#850505",
}
NO_DATA_COLOR = "#E5E5E5"

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


def _grafico_por_k(tabela_k, coluna, nome, k_escolhido, titulo):
    """Linha de uma medida por k, com o k escolhido destacado."""
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
    paleta = CLUSTER_COLORS
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
    cores = [paleta[rotulo] for rotulo in rotulos_presentes] + [NO_DATA_COLOR]
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
        itens_da_legenda.append(("Sem dado", NO_DATA_COLOR))
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


def grafico_mapa_clusters(geojson_regionais, geometria_regionais, tabela_cluster_regional,
                           coluna_regional=COLUNA_REGIONAL, coluna_id_geojson=None, ano_referencia=None):
    """Mapa coroplético de MG colorido pelo cluster de cada Regional em um ano (um recorte, não a série completa).

    Uma trace `go.Choropleth` por cluster (cor qualitativa, mesma paleta do heatmap cluster x
    (Regional, Ano)), sem camada de bolhas. Regionais sem cluster no ano pedido ficam em cinza.
    """
    coluna_id_geojson = coluna_id_geojson or coluna_regional
    tabela = geometria_regionais.merge(
        tabela_cluster_regional[[coluna_regional, "CLUSTER"]], on=coluna_regional, how="left",
    )
    coluna_exibicao = "REGIONAL_EXIBICAO" if "REGIONAL_EXIBICAO" in tabela.columns else coluna_regional

    rotulos_presentes = sorted(int(c) for c in tabela["CLUSTER"].dropna().unique())
    paleta = CLUSTER_COLORS

    figura = go.Figure()
    for cluster in rotulos_presentes:
        mascara = (tabela["CLUSTER"] == cluster).to_numpy()
        locais = tabela.loc[mascara, coluna_regional]
        figura.add_trace(go.Choropleth(
            geojson=geojson_regionais, locations=locais, z=[0] * len(locais),
            featureidkey=f"properties.{coluna_id_geojson}",
            colorscale=[[0, paleta[cluster]], [1, paleta[cluster]]], showscale=False, zmin=0, zmax=1,
            marker_line_width=1.2, marker_line_color="#2b2b2b",
            name=rotulo_do_cluster(cluster), showlegend=True,
            customdata=tabela.loc[mascara, coluna_exibicao],
            hovertemplate="%{customdata}<br>" + rotulo_do_cluster(cluster) + "<extra></extra>",
        ))

    mascara_sem_dado = tabela["CLUSTER"].isna().to_numpy()
    if mascara_sem_dado.any():
        locais_sem_dado = tabela.loc[mascara_sem_dado, coluna_regional]
        figura.add_trace(go.Choropleth(
            geojson=geojson_regionais, locations=locais_sem_dado, z=[0] * len(locais_sem_dado),
            featureidkey=f"properties.{coluna_id_geojson}",
            colorscale=[[0, NO_DATA_COLOR], [1, NO_DATA_COLOR]], showscale=False, zmin=0, zmax=1,
            marker_line_width=1.2, marker_line_color="#2b2b2b",
            name="Sem dado", showlegend=True,
            customdata=tabela.loc[mascara_sem_dado, coluna_exibicao],
            hovertemplate="%{customdata}<br>Sem dado<extra></extra>",
        ))

    figura.update_geos(fitbounds="locations", visible=False)
    aplicar_layout_padrao(
        figura, "", 1150, 620,
        legend=dict(
            orientation="h", yanchor="top", y=-0.03, xanchor="center", x=0.5,
            title_text="", itemsizing="constant",
        ),
        margin=dict(l=20, r=20, t=20, b=90),
    )
    return figura


def _chave_alfabetica(nome):
    """Chave de ordenação alfabética que ignora acentos e maiúsculas."""
    normalizado = unicodedata.normalize("NFKD", str(nome).lower())
    return "".join(caractere for caractere in normalizado if not unicodedata.combining(caractere))


def grafico_heatmap_caracterizacao(caracterizacao_por_mediana):
    """Heatmap único variável x cluster (todas as variáveis), colorido por d_cj (RdBu_r, centrado em 0); NaN em cinza, sem número."""
    maximo_absoluto_por_variavel = (
        caracterizacao_por_mediana.groupby("VARIAVEL")["D_CJ"].apply(lambda serie: serie.abs().max())
    )
    variaveis = maximo_absoluto_por_variavel.sort_values(ascending=False).index.tolist()
    clusters = sorted(caracterizacao_por_mediana["CLUSTER"].unique())

    pivot = caracterizacao_por_mediana.pivot(index="VARIAVEL", columns="CLUSTER", values="D_CJ")
    pivot = pivot.reindex(index=variaveis, columns=clusters)

    z = pivot.to_numpy(dtype=float)
    texto = np.where(np.isnan(z), "", np.round(z, 2).astype(str))
    limite_escala = 2

    x = [rotulo_do_cluster(c) for c in clusters]
    y = list(pivot.index)

    figura = go.Figure()
    figura.add_trace(go.Heatmap(
        z=np.zeros_like(z), x=x, y=y,
        colorscale=[[0, COR_SEM_DADO], [1, COR_SEM_DADO]], showscale=False,
        hoverinfo="skip", xgap=2, ygap=2,
    ))
    figura.add_trace(go.Heatmap(
        z=z, x=x, y=y, text=texto, texttemplate="%{text}",
        colorscale="RdBu_r", zmid=0, zmin=-limite_escala, zmax=limite_escala,
        hovertemplate="<b>%{y} — %{x}</b><br>d_cj: %{z:.2f}<extra></extra>",
        colorbar=dict(title="d_cj"), xgap=2, ygap=2,
    ))

    aplicar_layout_padrao(
        figura, "", 1150, max(560, 30 * len(y) + 180),
        margin=dict(l=320, t=120, r=30),
    )
    figura.update_xaxes(type="category", showgrid=False, showline=False, ticks="")
    figura.update_yaxes(
        automargin=True, autorange="reversed", type="category", categoryorder="array",
        categoryarray=y, showgrid=False, showline=False, ticks="",
    )
    return figura


def grafico_cluster_por_ano(tabela_cluster_por_ano):
    """Heatmap simples: contagem de pares Regional-Ano por (CLUSTER, ANO)."""
    anos = [str(ano) for ano in tabela_cluster_por_ano.columns]
    rotulos_y = [rotulo_do_cluster(cluster) for cluster in tabela_cluster_por_ano.index]
    z = tabela_cluster_por_ano.to_numpy()

    figura = go.Figure(go.Heatmap(
        z=z, x=anos, y=rotulos_y, text=z, texttemplate="%{text}",
        colorscale="Blues", xgap=2, ygap=2, showscale=False,
        hovertemplate="<b>%{y} — %{x}</b><br>%{z} par(es)<extra></extra>",
    ))
    return aplicar_layout_padrao(
        figura, "Cluster por ano -- contagem de pares Regional-Ano",
        900, max(300, 60 * len(rotulos_y)),
        xaxis_title="Ano", yaxis_title="Cluster",
    )
