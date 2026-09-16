import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from utilitarios_agrupamento_kmeansManual import (
    COLUNA_ANO, COLUNA_REGIONAL, VARIANCIA_PC1_ALERTA,
    pesos_das_variaveis_no_componente,
)

# Módulo AUTOCONTIDO do KMeans: não importa nada de 'DBSCAN/'. O KMeans
# não tem rótulo de ruído (-1) -- todo ponto pertence a algum cluster --
# então, diferente da paleta do DBSCAN, aqui não há cor reservada para
# "ruído".
PALETA = px.colors.qualitative.Safe


def rotulo_do_cluster(numero):
    return f"Cluster {numero}"


def cores_dos_clusters(rotulos_presentes):
    return {rotulo: PALETA[indice % len(PALETA)] for indice, rotulo in enumerate(rotulos_presentes)}


def grafico_variancia_explicada(pca, variancia_acumulada, limiar_alerta=VARIANCIA_PC1_ALERTA):

    proporcoes = pca.explained_variance_ratio_
    rotulos_componentes = [f"PC{i}" for i in range(1, len(proporcoes) + 1)]
    pc1_domina = proporcoes[0] > limiar_alerta
    cores_barras = ["#C0392B" if i == 0 and pc1_domina else "#2E5C8A" for i in range(len(proporcoes))]

    figura = go.Figure()
    figura.add_trace(go.Bar(
        x=rotulos_componentes, y=proporcoes, name="Variância por componente",
        marker=dict(color=cores_barras),
    ))
    figura.add_trace(go.Scatter(
        x=rotulos_componentes, y=variancia_acumulada, mode="lines+markers",
        name="Variância acumulada", line=dict(color="#1B7F3A", width=2),
    ))
    if pc1_domina:
        figura.add_annotation(
            x=rotulos_componentes[0], y=proporcoes[0],
            text=f"PC1 = {proporcoes[0]:.1%} > {limiar_alerta:.0%}",
            showarrow=True, arrowhead=2, font=dict(color="#C0392B"), ay=-40,
        )
    figura.update_layout(
        title="Variância explicada por componente principal",
        template="plotly_white", width=900, height=480,
        xaxis=dict(title="Componente"), yaxis=dict(title="Proporção da variância", tickformat=".0%"),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=80),
    )
    return figura


def grafico_pesos_da_componente(pca, colunas, componente=1, top_n=15):

    pesos = pesos_das_variaveis_no_componente(pca, colunas, componente=componente).head(top_n)
    figura = go.Figure(go.Bar(
        x=pesos.to_numpy()[::-1], y=list(pesos.index)[::-1], orientation="h",
        marker=dict(color=["#C0392B" if v < 0 else "#2E5C8A" for v in pesos.to_numpy()[::-1]]),
    ))
    figura.update_layout(
        title=f"Maiores pesos (loadings) de PC{componente}",
        template="plotly_white", width=800, height=max(320, 24 * top_n),
        xaxis=dict(title="Peso no componente"), yaxis=dict(title=""),
        margin=dict(l=220),
    )
    return figura


def grafico_cotovelo_inercia(tabela_k, indice_do_cotovelo, k_escolhido):
    figura = go.Figure()
    figura.add_trace(go.Scatter(
        x=tabela_k["k"], y=tabela_k["inercia"], mode="lines+markers",
        name="Inércia (WCSS)", line=dict(color="#2E5C8A"),
    ))
    linha_escolhida = tabela_k[tabela_k["k"] == k_escolhido]
    figura.add_trace(go.Scatter(
        x=linha_escolhida["k"], y=linha_escolhida["inercia"], mode="markers",
        name=f"k escolhido = {k_escolhido}",
        marker=dict(color="#C0392B", size=16, symbol="star"),
    ))
    figura.update_layout(
        title="Curva de inércia (cotovelo, Thorndike 1953) — escolha de k",
        template="plotly_white", width=1050, height=520,
        xaxis=dict(title="k"), yaxis=dict(title="Inércia (WCSS)"),
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        margin=dict(t=80),
    )
    return figura


def grafico_silhueta_por_k(tabela_k, k_escolhido):
    figura = go.Figure()
    figura.add_trace(go.Scatter(
        x=tabela_k["k"], y=tabela_k["silhueta"], mode="lines+markers",
        name="Silhueta", line=dict(color="#2E5C8A"),
    ))
    linha_escolhida = tabela_k[tabela_k["k"] == k_escolhido]
    figura.add_trace(go.Scatter(
        x=linha_escolhida["k"], y=linha_escolhida["silhueta"], mode="markers",
        name=f"k escolhido = {k_escolhido}",
        marker=dict(color="#C0392B", size=16, symbol="star"),
    ))
    figura.update_layout(
        title="Silhueta em função de k (validação complementar ao cotovelo)",
        template="plotly_white", width=1050, height=520,
        xaxis=dict(title="k"), yaxis=dict(title="Silhueta"),
        legend=dict(orientation="h", yanchor="top", y=-0.18, xanchor="center", x=0.5),
        margin=dict(t=80),
    )
    return figura


def grafico_dispersao_pc1_pc2_kmeans(matriz_2d, rotulos, indice, variancia_explicada, k):
    rotulos_presentes = sorted(set(rotulos))
    paleta = cores_dos_clusters(rotulos_presentes)
    regionais = indice.get_level_values(COLUNA_REGIONAL)
    anos = indice.get_level_values(COLUNA_ANO)

    figura = go.Figure()
    for rotulo in rotulos_presentes:
        selecao = rotulos == rotulo
        figura.add_trace(go.Scatter(
            x=matriz_2d[selecao, 0], y=matriz_2d[selecao, 1], mode="markers",
            name=rotulo_do_cluster(rotulo),
            marker=dict(color=paleta[rotulo], size=9, line=dict(width=1, color="white")),
            text=[f"{r} — {a}" for r, a in zip(regionais[selecao], anos[selecao])],
            hovertemplate="<b>%{text}</b><br>PC1: %{x:.2f}<br>PC2: %{y:.2f}<extra></extra>",
        ))
    figura.update_layout(
        title=f"Agrupamento dos pares Regional-Ano — KMeans (k={k})",
        template="plotly_white", width=1050, height=680,
        xaxis=dict(title=f"PC1 ({variancia_explicada[0]:.1%} da variância)"),
        yaxis=dict(title=f"PC2 ({variancia_explicada[1]:.1%} da variância)"),
        legend=dict(orientation="h", yanchor="top", y=-0.12, xanchor="center", x=0.5),
        margin=dict(t=80),
    )
    return figura


def grafico_dispersao_pc1_pc2_por_ano(matriz_2d, rotulos, indice, variancia_explicada, colunas_por_linha=4):

    anos = indice.get_level_values(COLUNA_ANO)
    regionais = indice.get_level_values(COLUNA_REGIONAL)
    anos_unicos = sorted(anos.unique())

    numero_de_linhas = int(np.ceil(len(anos_unicos) / colunas_por_linha))
    figura = make_subplots(
        rows=numero_de_linhas, cols=colunas_por_linha,
        subplot_titles=[str(ano) for ano in anos_unicos],
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
                go.Scatter(
                    x=matriz_2d[selecao, 0], y=matriz_2d[selecao, 1], mode="markers",
                    name=rotulo_do_cluster(rotulo), legendgroup=rotulo_do_cluster(rotulo),
                    showlegend=rotulo not in rotulos_ja_na_legenda,
                    marker=dict(color=paleta[rotulo], size=7, line=dict(width=1, color="white")),
                    text=list(regionais[selecao]),
                    hovertemplate="<b>%{text}</b><br>PC1: %{x:.2f}<br>PC2: %{y:.2f}<extra></extra>",
                ),
                row=linha + 1, col=coluna + 1,
            )
            rotulos_ja_na_legenda.add(rotulo)

    margem = 0.05
    amplitude_x = matriz_2d[:, 0].max() - matriz_2d[:, 0].min()
    amplitude_y = matriz_2d[:, 1].max() - matriz_2d[:, 1].min()
    eixo_x_fixo = [matriz_2d[:, 0].min() - margem * amplitude_x, matriz_2d[:, 0].max() + margem * amplitude_x]
    eixo_y_fixo = [matriz_2d[:, 1].min() - margem * amplitude_y, matriz_2d[:, 1].max() + margem * amplitude_y]
    figura.update_xaxes(range=eixo_x_fixo)
    figura.update_yaxes(range=eixo_y_fixo)

    figura.update_layout(
        title=dict(
            text=f"Agrupamento por ano — dispersão PC1 x PC2 "
                 f"(PC1 {variancia_explicada[0]:.1%}, PC2 {variancia_explicada[1]:.1%} da variância; "
                 f"eixos fixos em todos os painéis)",
            font=dict(size=16),
        ),
        template="plotly_white", height=260 * numero_de_linhas, width=260 * colunas_por_linha,
        font=dict(size=11),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5),
        margin=dict(t=120),
    )
    return figura


def grafico_heatmap_regional_ano(visao_agregada_regional_ano):
    """Heatmap Regional (linha) x Ano (coluna), uma cor por CLUSTER. Par
    regional-ano sem dado fica em branco."""
    tabela = visao_agregada_regional_ano
    rotulos_presentes = sorted({v for v in tabela.to_numpy().flatten() if pd.notna(v)})
    if not rotulos_presentes:
        raise ValueError("Nenhum CLUSTER presente em `visao_agregada_regional_ano` -- nada para desenhar.")
    paleta = cores_dos_clusters(rotulos_presentes)
    indice_por_rotulo = {rotulo: indice for indice, rotulo in enumerate(rotulos_presentes)}
    n = len(rotulos_presentes)

    z = tabela.map(lambda v: indice_por_rotulo[v] if pd.notna(v) else np.nan).to_numpy()
    texto = tabela.map(lambda v: rotulo_do_cluster(int(v)) if pd.notna(v) else "Sem dado").to_numpy()

    colorscale = []
    for indice, rotulo in enumerate(rotulos_presentes):
        colorscale.append([indice / n, paleta[rotulo]])
        colorscale.append([(indice + 1) / n, paleta[rotulo]])

    figura = go.Figure(go.Heatmap(
        z=z, x=[str(ano) for ano in tabela.columns], y=list(tabela.index),
        text=texto, hovertemplate="<b>%{y} — %{x}</b><br>%{text}<extra></extra>",
        colorscale=colorscale, zmin=0, zmax=n, zauto=False,
        xgap=1.5, ygap=1.5,
        colorbar=dict(
            tickmode="array",
            tickvals=[indice + 0.5 for indice in range(n)],
            ticktext=[rotulo_do_cluster(rotulo) for rotulo in rotulos_presentes],
            title="Agrupamento",
        ),
    ))
    figura.update_layout(
        title="Agrupamento por Regional de Saúde e Ano",
        template="plotly_white",
        width=1100, height=max(500, 22 * len(tabela.index)),
        xaxis=dict(title="Ano", type="category"),
        yaxis=dict(title="", autorange="reversed"),
        margin=dict(l=200),
    )
    return figura


def _grafico_distribuicao(resultado, coluna_x, titulo, largura):
    contagem = resultado.groupby([coluna_x, "CLUSTER"]).size().reset_index(name="QUANTIDADE")
    contagem["CLUSTER_ROTULO"] = contagem["CLUSTER"].map(rotulo_do_cluster)
    rotulos_presentes = sorted(resultado["CLUSTER"].unique())
    paleta = {rotulo_do_cluster(r): cor for r, cor in cores_dos_clusters(rotulos_presentes).items()}

    figura = px.bar(
        contagem, x=coluna_x, y="QUANTIDADE", color="CLUSTER_ROTULO",
        color_discrete_map=paleta, labels={"CLUSTER_ROTULO": "Agrupamento"},
    )
    figura.update_layout(title=titulo, template="plotly_white", width=largura, height=560, xaxis_tickangle=-60)
    return figura


def grafico_distribuicao_por_regional(resultado):
    return _grafico_distribuicao(resultado, COLUNA_REGIONAL, "Distribuição dos agrupamentos por Regional de Saúde", 1200)


def grafico_distribuicao_por_ano(resultado):
    return _grafico_distribuicao(resultado, COLUNA_ANO, "Distribuição dos agrupamentos por Ano", 1050)
