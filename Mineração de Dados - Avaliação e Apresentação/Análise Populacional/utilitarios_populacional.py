import re

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

COLUNA_MUNICIPIO = "MUNICÍPIOS"
COLUNA_CODIGO_IBGE = "CÓDIGO IBGE"
COLUNA_REGIONAL = "REGIONAL NORMALIZADA"
COLUNA_ANO = "ANO"
COLUNA_TIPO = "TIPO"
COLUNA_QUANTIDADE = "QUANTIDADE"
COLUNA_POPULACAO = "POPULACAO"
COLUNA_TAXA = "TAXA_POR_100_MIL"

PREFIXO_COLUNA_TOTAL_ANO = "TOTAL_"
MULTIPLICADOR_TAXA = 100_000
POPULACAO_MINIMA_VALIDA = 1

MOSTRAR_VALOR_NAS_BARRAS = True
MOSTRAR_VALOR_NA_LINHA = True
FORMATO_VALOR_BARRA = ",.0f"
FORMATO_VALOR_LINHA = ".1f"
TAMANHO_FONTE_VALOR_BARRA = 13
TAMANHO_FONTE_VALOR_LINHA = 13
POSICAO_VALOR_BARRA = "outside"
POSICAO_VALOR_LINHA = "top center"

NORMALIZAR_PARA_100_PORCENTO = True
TAMANHO_FONTE_ROTULO_EMPILHADO = 12
LIMIAR_MOSTRAR_ROTULO = 3
COR_SEM_INFORMACAO = "#B0B0B0"
PALETA_QUALITATIVA = px.colors.qualitative.Safe


def registrar_log(mensagem):
    '''Imprime uma mensagem de andamento no console.'''
    print(f"[LOG] {mensagem}")


def normalizar_codigo_ibge(serie_codigo_ibge):
    '''
    Normaliza a coluna de Código IBGE para um único tipo consistente
    (inteiro anulável — Int64), eliminando divergências entre CSVs que
    '''
    return pd.to_numeric(
        serie_codigo_ibge.astype(str).str.strip(),
        errors="coerce",
    ).astype("Int64")


# Método Geométrico — interpolação e extrapolação populacional

def calcular_taxa_geometrica(populacao_inicial, populacao_final, tempo_total):
    populacao_inicial_valida = populacao_inicial.where(populacao_inicial >= POPULACAO_MINIMA_VALIDA)
    razao = populacao_final / populacao_inicial_valida
    return razao ** (1 / tempo_total) - 1


def estimar_populacao_geometrica(populacao_inicial, r_g, tempo_decorrido):
    return populacao_inicial * (1 + r_g) ** tempo_decorrido

# Método Exponencial (crescimento geométrico contínuo) — usado só na
# extrapolação (2023-2025), conforme Silva et al. (2023). 
def calcular_taxa_exponencial(populacao_inicial, populacao_final, tempo_total):
    '''
    Calcula k_g (taxa de crescimento geométrico contínua) a partir de
    duas populações e do tempo decorrido entre elas, via log natural.
    Use para extrapolar população após o último censo (P_t = P_0 * e^(k_g*(t-t_0))).
    '''
    populacao_inicial_valida = populacao_inicial.where(populacao_inicial >= POPULACAO_MINIMA_VALIDA)
    populacao_final_valida = populacao_final.where(populacao_final >= POPULACAO_MINIMA_VALIDA)
    return (np.log(populacao_final_valida) - np.log(populacao_inicial_valida)) / tempo_total


def estimar_populacao_exponencial(populacao_referencia, k_g, tempo_decorrido):
    '''
    P_t = P_0 * e^(k_g * (t - t_0)).
    '''
    return populacao_referencia * np.exp(k_g * tempo_decorrido)


# Método Aritmético (Linear) — interpolação e extrapolação populacional

def calcular_taxa_aritmetica(populacao_inicial, populacao_final, tempo_total):
    return (populacao_final - populacao_inicial) / tempo_total


def estimar_populacao_aritmetica(populacao_inicial, k_a, tempo_decorrido):
    return populacao_inicial + k_a * tempo_decorrido

# Validação — Erro Percentual (usada pelos notebooks erro_populacional_*,

def resumir_ep(tabela_ep, nome_validacao):
    ep = tabela_ep["EP"].dropna()
    return {
        "Validação": nome_validacao,
        "EP médio (%)": round(ep.mean(), 3),
        "EP mediano (%)": round(ep.median(), 3),
        "MAPE (%)": round(ep.abs().mean(), 3),
        "Desvio-padrão (%)": round(ep.std(), 3),
    }


def agregar_ep_estadual(tabela_ep):
    tabela_valida = tabela_ep.dropna(subset=["POPULACAO_ESTIMADA"])

    agregado = tabela_valida.groupby(["ANO_TESTADO", "TIPO"], as_index=False).agg(
        POPULACAO_OBSERVADA=("POPULACAO_OBSERVADA", "sum"),
        POPULACAO_ESTIMADA=("POPULACAO_ESTIMADA", "sum"),
    )
    agregado["EP_ESTADO"] = (
        (agregado["POPULACAO_ESTIMADA"] - agregado["POPULACAO_OBSERVADA"]) / agregado["POPULACAO_OBSERVADA"]
    ) * 100
    return agregado

def carregar_taxa(caminho_csv, ano_inicial=None, ano_final=None, normalizar_ibge=False):
    '''
    Carrega um CSV de taxa já calculado e, se informado, filtra pelo
    intervalo de anos desejado. `normalizar_ibge=True` quando o
    resultado ainda vai ser cruzado por Código IBGE (ex.: mapeamento
    de Regional de Saúde) — não é necessário para agregações só por
    ANO ou TIPO.
    '''
    tabela = pd.read_csv(caminho_csv)
    if normalizar_ibge:
        tabela[COLUNA_CODIGO_IBGE] = normalizar_codigo_ibge(tabela[COLUNA_CODIGO_IBGE])
    if ano_inicial is not None and ano_final is not None:
        tabela = tabela[(tabela[COLUNA_ANO] >= ano_inicial) & (tabela[COLUNA_ANO] <= ano_final)]
    return tabela


def montar_grafico_barra_linha(eixo_x, valores_absolutos, valores_taxa, titulo, nome_absoluto,
                                cor_barras, cor_linha, titulo_eixo_x, largura, altura,
                                eixo_x_ano_continuo=False, tickangle_eixo_x=None,
                                margem_inferior=90, legenda_y=-0.15):
    figura = go.Figure()

    texto_barras = [f"{valor:{FORMATO_VALOR_BARRA}}" for valor in valores_absolutos] if MOSTRAR_VALOR_NAS_BARRAS else None
    texto_linha = [f"{valor:{FORMATO_VALOR_LINHA}}" for valor in valores_taxa] if MOSTRAR_VALOR_NA_LINHA else None
    modo_da_linha = "lines+markers+text" if MOSTRAR_VALOR_NA_LINHA else "lines+markers"

    figura.add_trace(go.Bar(
        x=eixo_x,
        y=valores_absolutos,
        name=f"{nome_absoluto} (eixo esq.)",
        marker_color=cor_barras,
        yaxis="y1",
        text=texto_barras,
        textposition=POSICAO_VALOR_BARRA,
        textfont=dict(size=TAMANHO_FONTE_VALOR_BARRA, color=cor_barras),
    ))

    figura.add_trace(go.Scatter(
        x=eixo_x,
        y=valores_taxa,
        name="Taxa Ajustada — /100k hab. (eixo dir.)",
        mode=modo_da_linha,
        marker=dict(color=cor_linha, size=7),
        line=dict(color=cor_linha, width=3),
        text=texto_linha,
        textposition=POSICAO_VALOR_LINHA,
        textfont=dict(size=TAMANHO_FONTE_VALOR_LINHA, color=cor_linha),
        yaxis="y2",
    ))

    eixo_x_config = dict(title=titulo_eixo_x)
    if eixo_x_ano_continuo:
        eixo_x_config.update(tickmode="linear", dtick=1)
    if tickangle_eixo_x is not None:
        eixo_x_config["tickangle"] = tickangle_eixo_x

    figura.update_layout(
        title=titulo,
        template="plotly_white",
        width=largura,
        height=altura,
        margin=dict(l=60, r=60, t=100, b=margem_inferior),
        xaxis=eixo_x_config,
        yaxis=dict(title=nome_absoluto, side="left"),
        yaxis2=dict(title="Taxa / 100k hab.", overlaying="y", side="right", showgrid=False),
        legend=dict(orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5),
    )

    return figura


def salvar_figura(figura, nome_do_arquivo, pasta_saida):
    '''Salva a figura em PNG e HTML na pasta de saída.'''
    pasta_saida.mkdir(parents=True, exist_ok=True)

    caminho_png = pasta_saida / f"{nome_do_arquivo}.png"
    caminho_html = pasta_saida / f"{nome_do_arquivo}.html"

    figura.write_image(caminho_png, scale=3)
    figura.write_html(caminho_html)

    registrar_log(f"Figura PNG salva em : {caminho_png}")
    registrar_log(f"Figura HTML salva em: {caminho_html}")


# Gráficos empilhados — composição por categoria (Faixa Etária,

def melt_variavel_categorica(tabela, coluna_codigo_ibge):
    '''
    Converte uma tabela larga com colunas '<ano>_<categoria>' para
    formato longo, com colunas ANO, CATEGORIA e VALOR.
    '''
    colunas_categoria = [c for c in tabela.columns if re.fullmatch(r"\d{4}_.+", c)]
    tabela_longa = tabela.melt(
        id_vars=[coluna_codigo_ibge],
        value_vars=colunas_categoria,
        var_name="ANO_CATEGORIA",
        value_name="VALOR",
    )
    partes = tabela_longa["ANO_CATEGORIA"].str.split("_", n=1, expand=True)
    tabela_longa["ANO"] = partes[0].astype(int)
    tabela_longa["CATEGORIA"] = partes[1]
    return tabela_longa.drop(columns=["ANO_CATEGORIA"])


def ordenar_categorias(categorias_presentes, ordem_customizada=None):
    '''
    Define a ordem de empilhamento/legenda. Usa ordem_customizada se
    fornecida; senão, ordena alfabeticamente com SEM INFORMAÇÃO por
    último (mais fácil de comparar visualmente as categorias válidas).
    '''
    if ordem_customizada:
        return [c for c in ordem_customizada if c in categorias_presentes]

    categorias_normais = sorted(
        c for c in categorias_presentes if c.strip().upper() != "SEM INFORMAÇÃO"
    )
    if any(c.strip().upper() == "SEM INFORMAÇÃO" for c in categorias_presentes):
        return categorias_normais + ["SEM INFORMAÇÃO"]
    return categorias_normais


def gerar_paleta_cores(categorias_ordenadas):
    '''
    Atribui uma cor a cada categoria. SEM INFORMAÇÃO é sempre cinza,
    as demais seguem a paleta qualitativa na ordem informada.
    '''
    paleta = {}
    indice_cor = 0
    for categoria in categorias_ordenadas:
        if categoria.strip().upper() == "SEM INFORMAÇÃO":
            paleta[categoria] = COR_SEM_INFORMACAO
        else:
            paleta[categoria] = PALETA_QUALITATIVA[indice_cor % len(PALETA_QUALITATIVA)]
            indice_cor += 1
    return paleta


def montar_grafico_empilhado(eixo_x, tabela_pivotada, titulo, paleta_cores, titulo_eixo_x,
                              ordem_categorias, largura, altura,
                              tickangle_eixo_x=0, margem_inferior=120, legenda_y=-0.25):
    figura = go.Figure()

    total_por_barra = tabela_pivotada[ordem_categorias].sum(axis=1)

    for categoria in ordem_categorias:
        valores_absolutos = tabela_pivotada[categoria] if categoria in tabela_pivotada.columns else pd.Series(0, index=tabela_pivotada.index)

        if NORMALIZAR_PARA_100_PORCENTO:
            y_valores = (valores_absolutos / total_por_barra) * 100
            texto = [f"{v:.1f}%" if v >= LIMIAR_MOSTRAR_ROTULO else "" for v in y_valores]
        else:
            y_valores = valores_absolutos
            texto = [f"{v:,.0f}" if v >= LIMIAR_MOSTRAR_ROTULO else "" for v in y_valores]

        figura.add_trace(go.Bar(
            x=eixo_x,
            y=y_valores,
            name=categoria.title(),
            marker_color=paleta_cores[categoria],
            text=texto,
            textposition="inside",
            textfont=dict(size=TAMANHO_FONTE_ROTULO_EMPILHADO, color="white"),
        ))

    figura.update_layout(
        title=titulo,
        template="plotly_white",
        barmode="stack",
        width=largura,
        height=altura,
        margin=dict(l=60, r=60, t=100, b=margem_inferior),
        xaxis=dict(title=titulo_eixo_x, tickangle=tickangle_eixo_x),
        yaxis=dict(title="Participação (%)" if NORMALIZAR_PARA_100_PORCENTO else "Quantidade Absoluta"),
        legend=dict(orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5),
    )

    if NORMALIZAR_PARA_100_PORCENTO:
        figura.update_yaxes(range=[0, 100])

    return figura
