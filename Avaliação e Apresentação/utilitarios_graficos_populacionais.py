
import math

import numpy as np
import pandas as pd

from utilitarios_comuns import (
    COLUNA_REGIONAL,
    MULTIPLICADOR_TAXA,
    PASTA_SELECAO_TRANSFORMACAO,
    SUFIXO_COLUNA_TAXA,
    extrair_ano_da_coluna,
    registrar_log,
)
from configuracao_layout_graficos import (
    MOSTRAR_VALOR_NAS_BARRAS,
    MOSTRAR_VALOR_NA_LINHA,
    FORMATO_VALOR_BARRA,
    FORMATO_VALOR_LINHA,
    POSICAO_VALOR_BARRA,
    POSICAO_VALOR_LINHA,
    TAMANHO_FONTE_VALOR_BARRA,
    TAMANHO_FONTE_VALOR_LINHA,
    TAMANHO_FONTE_ROTULO_EMPILHADO,
    TAMANHO_FONTE_TITULO,
    TAMANHO_FONTE_TITULO_EIXO,
    TAMANHO_FONTE_TICK_EIXO,
    TAMANHO_FONTE_LEGENDA,
    TAMANHO_FONTE_TITULO_GRAFICO_LINHA,
    TAMANHO_FONTE_TITULO_EIXO_GRAFICO_LINHA,
    TAMANHO_FONTE_TICK_EIXO_GRAFICO_LINHA,
    TAMANHO_FONTE_LEGENDA_GRAFICO_LINHA,
    COR_SEM_INFORMACAO,
    CORES_CATEGORIAS_CUSTOMIZADAS,
    LARGURA_MINIMA_POR_CATEGORIA,
    NORMALIZAR_PARA_100_PORCENTO,
    LIMIAR_MOSTRAR_ROTULO,
    tamanho_fonte,
)

import plotly.colors as pcolors
import plotly.graph_objects as go
from plotly.subplots import make_subplots

ROTULO_EIXO_TAXA_PADRAO = "Taxa / 100k hab."

# Leitura da taxa por Regional
def carregar_taxa_por_regional(caminho_csv):
    return pd.read_csv(caminho_csv)


CAMINHO_MUNICIPIOS_REGIONAIS = PASTA_SELECAO_TRANSFORMACAO / "Municípios" / "tabela_municipios_regionais.csv"


def carregar_mapa_regional_original(caminho_csv=CAMINHO_MUNICIPIOS_REGIONAIS):
    '''
    Lê tabela_municipios_regionais.csv e devolve um dicionário
    {REGIONAL NORMALIZADA -> REGIONAL ORIGINAL} -- usado para exibir o
    nome "de verdade" da Regional (com acentos e maiúsculas) em
    gráficos e mapas, já que todo o pipeline de dados usa a versão
    normalizada (normalizar_regional, em utilitarios_comuns.py) como
    chave de junção/agrupamento.
    '''
    tabela = pd.read_csv(caminho_csv)
    return (
        tabela[["REGIONAL NORMALIZADA", "REGIONAL ORIGINAL"]]
        .drop_duplicates()
        .set_index("REGIONAL NORMALIZADA")["REGIONAL ORIGINAL"]
        .to_dict()
    )


def nomes_regional_originais(serie_normalizada, mapa_regional_original=None):
    if mapa_regional_original is None:
        mapa_regional_original = carregar_mapa_regional_original()

    valores_sem_correspondencia = sorted({
        valor for valor in pd.unique(serie_normalizada)
        if pd.notna(valor) and valor not in mapa_regional_original
    })
    if valores_sem_correspondencia:
        registrar_log(
            f"ATENÇÃO: {len(valores_sem_correspondencia)} nome(s) de Regional sem "
            f"correspondência em tabela_municipios_regionais.csv -- usando .title() "
            f"como fallback: {valores_sem_correspondencia}"
        )

    def _mapear(valor):
        return valor if pd.isna(valor) else mapa_regional_original.get(valor, str(valor).title())

    if hasattr(serie_normalizada, "map"):
        return serie_normalizada.map(_mapear)
    return pd.Series(serie_normalizada).map(_mapear)

def agregar_periodo_por_regional(tabela_taxa_regional, colunas_de_valor):
    '''
    Para cada Regional de Saúde, soma a QUANTIDADE (já calculada por
    Regional em calculo_taxa.ipynb) de TODAS as colunas informadas (todo
    o período disponível da variável) -- valor absoluto acumulado, sem
    taxa (não há necessidade de taxa/população nos consumidores atuais,
    todos mapas de valor absoluto).

    Devolve um DataFrame com uma linha por regional: REGIONAL,
    QUANTIDADE -- ordenado por QUANTIDADE decrescente.
    '''
    resultado = pd.DataFrame({
        COLUNA_REGIONAL: tabela_taxa_regional[COLUNA_REGIONAL],
        "QUANTIDADE": tabela_taxa_regional[colunas_de_valor].sum(axis=1, min_count=1),
    })
    return resultado.sort_values("QUANTIDADE", ascending=False).reset_index(drop=True)


def preparar_simples_por_regional_ano(tabela_taxa_regional, colunas_de_valor):
    '''
    Converte uma tabela de taxa por Regional de uma variável SIMPLES
    (sem subcategoria -- Casos, Mortalidade, Mamografia; colunas_de_valor
    já filtradas com somente_total=True em selecionar_colunas_de_valor,
    uma única coluna "<ano>_TOTAL" por ano) em formato longo: uma linha
    por (Regional, Ano), com TAXA e QUANTIDADE lado a lado -- sem
    reconstruir nenhum valor a partir da taxa, ambos já vêm prontos do
    CSV de calculo_taxa.ipynb.

    Usado pelo heatmap Regional × Ano, que precisa da taxa (cor) e da
    quantidade (rótulo dentro da célula) na mesma granularidade
    (Regional, Ano).
    '''
    registros = []
    for coluna in colunas_de_valor:
        ano = extrair_ano_da_coluna(coluna)
        coluna_taxa = f"{coluna}{SUFIXO_COLUNA_TAXA}"
        registros.append(pd.DataFrame({
            COLUNA_REGIONAL: tabela_taxa_regional[COLUNA_REGIONAL],
            "ANO": ano,
            "TAXA": (
                tabela_taxa_regional[coluna_taxa]
                if coluna_taxa in tabela_taxa_regional.columns else pd.NA
            ),
            "QUANTIDADE": tabela_taxa_regional[coluna],
        }))
    return pd.concat(registros, ignore_index=True)


def preparar_categorica_estadual_por_ano(tabela_agregada_estadual, sufixo_variavel, ano_inicial, ano_final):
    '''
    Recorta, do CSV agregado estadual por ano (calculo_taxa.ipynb,
    NOME_ARQUIVO_AGREGADO_CATEGORICO_POR_ANO -- uma linha por ANO,
    colunas "<categoria>_<SUFIXO>" e "<categoria>_<SUFIXO>_TAXA" de
    várias variáveis lado a lado), as colunas de UMA variável (pelo seu
    sufixo, SUFIXO_VARIAVEL_ESTADUAL em utilitarios_comuns.py), sem
    reconstruir nenhum valor -- TAXA e QUANTIDADE já vêm prontas do
    CSV. Filtra pelo intervalo de anos da variável.

    Exclui a categoria "TOTAL" -- soma das categorias reais, não é mais
    uma categoria (incluí-la dobraria a contagem no gráfico empilhado);
    relevante porque, no CSV, o TOTAL de uma variável simples (ex.:
    "TOTAL_CASOS") compartilha sufixo com sua quebra categórica (ex.:
    "0-9_CASOS", de "Casos por Faixa Etária") e apareceria aqui junto.

    Devolve duas tabelas pivotadas (index=ANO, columns=CATEGORIA),
    prontas para o gráfico: tabela_pivotada_taxa, tabela_pivotada_quantidade.
    '''
    sufixo_ = f"_{sufixo_variavel}"
    sufixo_taxa_ = f"{sufixo_}{SUFIXO_COLUNA_TAXA}"

    tabela_do_periodo = tabela_agregada_estadual[
        (tabela_agregada_estadual["ANO"] >= ano_inicial) & (tabela_agregada_estadual["ANO"] <= ano_final)
    ].set_index("ANO")

    colunas_categoria_taxa = []
    for coluna in tabela_do_periodo.columns:
        if coluna.endswith(sufixo_taxa_) and coluna[: -len(sufixo_taxa_)] != "TOTAL":
            colunas_categoria_taxa.append(coluna)

    categorias = []
    for coluna in colunas_categoria_taxa:
        categorias.append(coluna[: -len(sufixo_taxa_)])

    tabela_pivotada_taxa = tabela_do_periodo[colunas_categoria_taxa].copy()
    tabela_pivotada_taxa.columns = categorias

    colunas_categoria_quantidade = []
    for categoria in categorias:
        colunas_categoria_quantidade.append(f"{categoria}{sufixo_}")
    tabela_pivotada_quantidade = tabela_do_periodo[colunas_categoria_quantidade].copy()
    tabela_pivotada_quantidade.columns = categorias

    return tabela_pivotada_taxa, tabela_pivotada_quantidade


def ordenar_categorias(categorias_presentes, ordem_customizada=None):
    if ordem_customizada:
        categorias_na_ordem_customizada = []
        for categoria in ordem_customizada:
            if categoria in categorias_presentes:
                categorias_na_ordem_customizada.append(categoria)
        return categorias_na_ordem_customizada

    categorias_normais = []
    tem_categoria_sem_informacao = False
    for categoria in categorias_presentes:
        if categoria.strip().upper() == "SEM INFORMAÇÃO":
            tem_categoria_sem_informacao = True
        else:
            categorias_normais.append(categoria)
    categorias_normais = sorted(categorias_normais)

    if tem_categoria_sem_informacao:
        return categorias_normais + ["SEM INFORMAÇÃO"]
    return categorias_normais

# ESCALA_COR = [
#     "#E6E6E6",  # cinza claro
#     "#F6E7AC",  # amarelo muito claro
#     "#F2E33C",  # amarelo claro
#     "#E8AD3F",  # amarelo/laranja
#     "#E66C08",  # laranja
#     "#F30C0C",  # laranja avermelhado
#     "#D24545",  # vermelho claro
#     "#850505"   # vermelho forte
# ]

PLASMA = [
    "#242BB3",
    "#833DA4",
    "#BF09C3",
    "#980C42",
    "#DA0C2B",
    "#E36D06",
    "#F6EA4C",
    "#D7D4A1"
]

def gerar_paleta_cores(categorias_ordenadas, escala_cor=PLASMA):
    '''
    Cor por categoria: CORES_CATEGORIAS_CUSTOMIZADAS (configuracao_layout_graficos.py)
    tem prioridade, "SEM INFORMAÇÃO" cai em COR_SEM_INFORMACAO -- as
    demais recebem uma cor amostrada de escala_cor (Plasma por padrão),
    igualmente espaçada ao longo da escala, na ordem em que aparecem em
    categorias_ordenadas.
    '''
    categorias_a_amostrar = []
    for categoria in categorias_ordenadas:
        if categoria in CORES_CATEGORIAS_CUSTOMIZADAS:
            continue
        if categoria.strip().upper() == "SEM INFORMAÇÃO":
            continue
        categorias_a_amostrar.append(categoria)

    n = len(categorias_a_amostrar)
    if n == 1:
        pontos = [0.5]
    else:
        pontos = []
        for i in range(n):
            pontos.append(i / (n - 1))
    cores_amostradas = pcolors.sample_colorscale(escala_cor, pontos) if n else []
    cor_por_categoria_amostrada = dict(zip(categorias_a_amostrar, cores_amostradas))

    paleta = {}
    for categoria in categorias_ordenadas:
        if categoria in CORES_CATEGORIAS_CUSTOMIZADAS:
            paleta[categoria] = CORES_CATEGORIAS_CUSTOMIZADAS[categoria]
        elif categoria.strip().upper() == "SEM INFORMAÇÃO":
            paleta[categoria] = COR_SEM_INFORMACAO
        else:
            paleta[categoria] = cor_por_categoria_amostrada[categoria]
    return paleta


def _largura_ajustada(largura, n_categorias):
    '''
    largura= nas chamadas de montar_grafico_* é um mínimo: com muitas
    categorias no eixo X, reserva pelo menos LARGURA_MINIMA_POR_CATEGORIA
    px para cada uma (configuracao_layout_graficos.py), alargando a
    figura automaticamente para os rótulos de valor de pontos vizinhos
    não se sobreporem.
    '''
    return max(largura, n_categorias * LARGURA_MINIMA_POR_CATEGORIA)


# --- Cálculo automático de margem inferior / posição da legenda ---
# A legenda horizontal fica abaixo dos rótulos do eixo X; como esses
# rótulos são rotacionados e de comprimento variável (nomes de
# Regional, por exemplo), uma margem fixa não acompanha o espaço que
# eles realmente ocupam e a legenda acaba desenhada por cima deles.
# Estima a altura ocupada pelo maior rótulo já rotacionado e reserva
# margem suficiente para rótulos + legenda, encaixando a legenda no
# espaço logo abaixo dos rótulos.
_MARGEM_SUPERIOR_PADRAO = 100
_LARGURA_MEDIA_CARACTERE_EM_FONTE = 0.6
_ESPACO_ENTRE_ROTULOS_E_TITULO = 8
_ESPACO_ENTRE_ROTULOS_E_LEGENDA = 15
_ALTURA_LINHA_LEGENDA = 26
_ESPACO_ENTRE_LEGENDA_E_BORDA = 10


def _altura_rotulos_eixo_x(rotulos_eixo_x, tickangle_eixo_x, tamanho_fonte_tick):
    maior_rotulo = max((str(rotulo) for rotulo in rotulos_eixo_x), key=len, default="")
    largura_rotulo_px = len(maior_rotulo) * tamanho_fonte_tick * _LARGURA_MEDIA_CARACTERE_EM_FONTE
    angulo_rad = math.radians(tickangle_eixo_x or 0)
    return abs(largura_rotulo_px * math.sin(angulo_rad)) + abs(tamanho_fonte_tick * math.cos(angulo_rad))


def _calcular_margem_inferior_e_legenda(rotulos_eixo_x, tickangle_eixo_x, altura, margem_inferior=None,
                                         tamanho_fonte_tick_eixo=TAMANHO_FONTE_TICK_EIXO,
                                         tamanho_fonte_titulo_eixo=TAMANHO_FONTE_TITULO_EIXO):
    '''
    O eixo X sempre desenha, de cima para baixo: rótulos (tick) ->
    título do eixo -> legenda. Bug corrigido aqui: a versão anterior só
    reservava espaço para os rótulos antes de posicionar a legenda,
    esquecendo o título do eixo -- com rótulos curtos e pouco rodados
    (ex.: anos "1985", "1986"...) a legenda acabava desenhada em cima
    do título "Ano". Por isso a altura do título do eixo entra na conta
    tanto na margem quanto na posição da legenda.
    '''
    altura_rotulos = _altura_rotulos_eixo_x(
        rotulos_eixo_x, tickangle_eixo_x, tamanho_fonte(tamanho_fonte_tick_eixo)
    )
    altura_titulo_eixo = tamanho_fonte(tamanho_fonte_titulo_eixo)
    altura_rotulos_e_titulo = altura_rotulos + _ESPACO_ENTRE_ROTULOS_E_TITULO + altura_titulo_eixo

    if margem_inferior is None:
        margem_inferior = (
            altura_rotulos_e_titulo + _ESPACO_ENTRE_ROTULOS_E_LEGENDA
            + _ALTURA_LINHA_LEGENDA + _ESPACO_ENTRE_LEGENDA_E_BORDA
        )

    altura_area_grafico = max(altura - _MARGEM_SUPERIOR_PADRAO - margem_inferior, 1)
    legenda_y = -(altura_rotulos_e_titulo + _ESPACO_ENTRE_ROTULOS_E_LEGENDA) / altura_area_grafico
    return margem_inferior, legenda_y


# Gráfico -- barra (valor absoluto) + linha (taxa por 100 mil)

def montar_grafico_barra_linha(eixo_x, valores_absolutos, valores_taxa, titulo, nome_absoluto,
                                cor_barras, cor_linha, titulo_eixo_x, largura, altura,
                                eixo_x_ano_continuo=False, tickangle_eixo_x=None,
                                margem_inferior=None,
                                rotulo_eixo_taxa=ROTULO_EIXO_TAXA_PADRAO,
                                mostrar_valor_barras=None, mostrar_valor_linha=None):
    '''
    mostrar_valor_barras / mostrar_valor_linha: liga ou desliga os
    rótulos de valor em cima das barras / da linha, sobrepondo o
    padrão global (MOSTRAR_VALOR_NAS_BARRAS / MOSTRAR_VALOR_NA_LINHA em
    configuracao_layout_graficos.py) para este gráfico específico --
    útil para séries com muitos pontos (ex.: Mortalidade, quase 50
    anos), onde os rótulos se sobrepõem e viram um borrão ilegível.

    margem_inferior: por padrão (None) é calculada automaticamente a
    partir do comprimento do maior rótulo do eixo X e do ângulo de
    rotação, para a legenda nunca sobrepor os rótulos -- pode ser
    sobrescrita manualmente informando um valor fixo.
    '''
    if mostrar_valor_barras is None:
        mostrar_valor_barras = MOSTRAR_VALOR_NAS_BARRAS
    if mostrar_valor_linha is None:
        mostrar_valor_linha = MOSTRAR_VALOR_NA_LINHA

    largura = _largura_ajustada(largura, len(eixo_x))

    figura = go.Figure()

    texto_barras = None
    if mostrar_valor_barras:
        texto_barras = []
        for valor in valores_absolutos:
            texto_barras.append(f"{valor:{FORMATO_VALOR_BARRA}}")

    texto_linha = None
    if mostrar_valor_linha:
        texto_linha = []
        for valor in valores_taxa:
            texto_linha.append(f"{valor:{FORMATO_VALOR_LINHA}}")

    modo_da_linha = "lines+markers+text" if mostrar_valor_linha else "lines+markers"

    figura.add_trace(go.Bar(
        x=eixo_x, y=valores_absolutos, name=f"{nome_absoluto} (eixo esq.)",
        marker_color=cor_barras, yaxis="y1", text=texto_barras,
        textposition=POSICAO_VALOR_BARRA,
        textfont=dict(size=tamanho_fonte(TAMANHO_FONTE_VALOR_BARRA), color=cor_barras),
    ))
    figura.add_trace(go.Scatter(
        x=eixo_x, y=valores_taxa, name="Taxa — /100k hab. (eixo dir.)",
        mode=modo_da_linha, marker=dict(color=cor_linha, size=7), line=dict(color=cor_linha, width=3),
        text=texto_linha, textposition=POSICAO_VALOR_LINHA,
        textfont=dict(size=tamanho_fonte(TAMANHO_FONTE_VALOR_LINHA), color=cor_linha), yaxis="y2",
    ))

    eixo_x_config = dict(
        title=dict(text=titulo_eixo_x, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
        tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
    )
    if eixo_x_ano_continuo:
        eixo_x_config["type"] = "category"
    if tickangle_eixo_x is not None:
        eixo_x_config["tickangle"] = tickangle_eixo_x

    margem_inferior, legenda_y = _calcular_margem_inferior_e_legenda(
        eixo_x, tickangle_eixo_x, altura, margem_inferior
    )

    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO))),
        template="plotly_white", width=largura, height=altura,
        margin=dict(l=60, r=60, t=_MARGEM_SUPERIOR_PADRAO, b=margem_inferior),
        xaxis=eixo_x_config,
        yaxis=dict(
            title=dict(text=nome_absoluto, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
            tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)), side="left",
        ),
        yaxis2=dict(
            title=dict(text=rotulo_eixo_taxa, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
            tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
            overlaying="y", side="right", showgrid=False,
        ),
        legend=dict(
            orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5,
            font=dict(size=tamanho_fonte(TAMANHO_FONTE_LEGENDA)),
        ),
    )
    return figura


def montar_grafico_empilhado_taxa(eixo_x, tabela_pivotada_taxa, titulo, paleta_cores, titulo_eixo_x,
                                   ordem_categorias, largura, altura,
                                   tickangle_eixo_x=0, margem_inferior=None,
                                   eixo_x_ano_continuo=False, rotulo_eixo_taxa=None):
    '''
    margem_inferior: por padrão (None) é calculada automaticamente a
    partir do comprimento do maior rótulo do eixo X e do ângulo de
    rotação, para a legenda nunca sobrepor os rótulos -- pode ser
    sobrescrita manualmente informando um valor fixo.
    '''
    largura = _largura_ajustada(largura, len(eixo_x))

    figura = go.Figure()
    for categoria in ordem_categorias:
        if categoria in tabela_pivotada_taxa.columns:
            valores_taxa = tabela_pivotada_taxa[categoria]
        else:
            valores_taxa = pd.Series(0.0, index=tabela_pivotada_taxa.index)

        texto = []
        for v in valores_taxa:
            texto.append(f"{v:.2f}")

        figura.add_trace(go.Bar(
            x=eixo_x, y=valores_taxa, name=categoria.title(), marker_color=paleta_cores[categoria],
            text=texto, textposition="inside", constraintext="none",
            textfont=dict(size=tamanho_fonte(TAMANHO_FONTE_ROTULO_EMPILHADO), color="white"),
        ))
    if rotulo_eixo_taxa is None:
        rotulo_eixo_taxa = f"Taxa / {MULTIPLICADOR_TAXA} hab."

    eixo_x_config = dict(
        title=dict(text=titulo_eixo_x, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
        tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
        tickangle=tickangle_eixo_x,
    )
    if eixo_x_ano_continuo:
        eixo_x_config["type"] = "category"

    margem_inferior, legenda_y = _calcular_margem_inferior_e_legenda(
        eixo_x, tickangle_eixo_x, altura, margem_inferior
    )

    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO))),
        template="plotly_white", barmode="stack", width=largura, height=altura,
        margin=dict(l=60, r=60, t=_MARGEM_SUPERIOR_PADRAO, b=margem_inferior),
        xaxis=eixo_x_config,
        yaxis=dict(
            title=dict(text=rotulo_eixo_taxa, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
            tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
        ),
        legend=dict(
            orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5,
            font=dict(size=tamanho_fonte(TAMANHO_FONTE_LEGENDA)),
        ),
    )
    return figura


def montar_grafico_empilhado_absoluto(eixo_x, tabela_pivotada_quantidade, titulo, paleta_cores, titulo_eixo_x,
                                       ordem_categorias, largura, altura,
                                       tickangle_eixo_x=0, margem_inferior=None,
                                       eixo_x_ano_continuo=False,
                                       normalizar_para_100_porcento=None,
                                       limiar_mostrar_rotulo=None,
                                       rotulo_eixo_y=None):
    '''
    Versão em valor absoluto (QUANTIDADE) de montar_grafico_empilhado_taxa.
    normalizar_para_100_porcento=None usa o padrão global
    (NORMALIZAR_PARA_100_PORCENTO, em configuracao_layout_graficos.py);
    quando ligado, cada barra é reescalada para somar 100% (participação
    percentual), mas o rótulo dentro da fatia continua mostrando o valor
    absoluto -- só a altura da barra muda. limiar_mostrar_rotulo=None usa
    o padrão global (LIMIAR_MOSTRAR_ROTULO) -- avaliado sempre como
    participação percentual da fatia no total da barra, mesmo quando a
    barra não está normalizada, para o limiar ter o mesmo significado
    nos dois modos.
    '''
    if normalizar_para_100_porcento is None:
        normalizar_para_100_porcento = NORMALIZAR_PARA_100_PORCENTO
    if limiar_mostrar_rotulo is None:
        limiar_mostrar_rotulo = LIMIAR_MOSTRAR_ROTULO

    largura = _largura_ajustada(largura, len(eixo_x))

    tabela_valores = tabela_pivotada_quantidade.reindex(columns=ordem_categorias, fill_value=0.0)
    total_por_x = tabela_valores.sum(axis=1)
    total_valido = total_por_x.where(total_por_x != 0)
    participacao_percentual = tabela_valores.div(total_valido, axis=0) * 100

    if normalizar_para_100_porcento:
        tabela_plotada = participacao_percentual.fillna(0.0)
        rotulo_eixo_y_final = rotulo_eixo_y or "% do total"
    else:
        tabela_plotada = tabela_valores
        rotulo_eixo_y_final = rotulo_eixo_y or "Quantidade"

    figura = go.Figure()
    for categoria in ordem_categorias:
        valores_plotados = tabela_plotada[categoria]
        participacao = participacao_percentual[categoria]
        texto = []
        for valor_absoluto, p in zip(tabela_valores[categoria], participacao):
            if pd.notna(p) and p >= limiar_mostrar_rotulo:
                if normalizar_para_100_porcento:
                    texto.append(f"{p:.1f}%")
                else:
                    texto.append(f"{valor_absoluto:,.0f}".replace(",", "."))
            else:
                texto.append("")
        figura.add_trace(go.Bar(
            x=eixo_x, y=valores_plotados, name=categoria.title(), marker_color=paleta_cores[categoria],
            text=texto, textposition="inside", constraintext="none",
            textfont=dict(size=tamanho_fonte(TAMANHO_FONTE_ROTULO_EMPILHADO), color="white"),
        ))

    eixo_x_config = dict(
        title=dict(text=titulo_eixo_x, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
        tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
        tickangle=tickangle_eixo_x,
    )
    if eixo_x_ano_continuo:
        eixo_x_config["type"] = "category"

    margem_inferior, legenda_y = _calcular_margem_inferior_e_legenda(
        eixo_x, tickangle_eixo_x, altura, margem_inferior
    )

    eixo_y_config = dict(
        title=dict(text=rotulo_eixo_y_final, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
        tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
    )
    if normalizar_para_100_porcento:
        eixo_y_config["range"] = [0, 100]

    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO))),
        template="plotly_white", barmode="stack", width=largura, height=altura,
        margin=dict(l=60, r=60, t=_MARGEM_SUPERIOR_PADRAO, b=margem_inferior),
        xaxis=eixo_x_config, yaxis=eixo_y_config,
        legend=dict(
            orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5,
            font=dict(size=tamanho_fonte(TAMANHO_FONTE_LEGENDA)),
        ),
    )
    return figura


def montar_grafico_linha_taxa(eixo_x, tabela_pivotada_taxa, titulo, paleta_cores, titulo_eixo_x,
                               ordem_categorias, largura, altura,
                               tickangle_eixo_x=0, margem_inferior=None,
                               eixo_x_ano_continuo=False, rotulo_eixo_taxa=None):
    '''
    Versão em linhas de montar_grafico_empilhado_taxa -- mesmos dados,
    eixos e título, mas uma linha por categoria (cor da linha = cor da
    categoria na paleta) em vez de barras empilhadas.
    '''
    largura = _largura_ajustada(largura, len(eixo_x))

    figura = go.Figure()
    for categoria in ordem_categorias:
        if categoria in tabela_pivotada_taxa.columns:
            valores_taxa = tabela_pivotada_taxa[categoria]
        else:
            valores_taxa = pd.Series(0.0, index=tabela_pivotada_taxa.index)

        figura.add_trace(go.Scatter(
            x=eixo_x, y=valores_taxa, name=categoria.title(), mode="lines+markers",
            line=dict(color=paleta_cores[categoria]), marker=dict(color=paleta_cores[categoria]),
        ))
    if rotulo_eixo_taxa is None:
        rotulo_eixo_taxa = f"Taxa / {MULTIPLICADOR_TAXA} hab."

    eixo_x_config = dict(
        title=dict(text=titulo_eixo_x, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
        tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
        tickangle=tickangle_eixo_x,
    )
    if eixo_x_ano_continuo:
        eixo_x_config["type"] = "category"

    margem_inferior, legenda_y = _calcular_margem_inferior_e_legenda(
        eixo_x, tickangle_eixo_x, altura, margem_inferior
    )

    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO))),
        template="plotly_white", width=largura, height=altura,
        margin=dict(l=60, r=60, t=_MARGEM_SUPERIOR_PADRAO, b=margem_inferior),
        xaxis=eixo_x_config,
        yaxis=dict(
            title=dict(text=rotulo_eixo_taxa, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
            tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
        ),
        legend=dict(
            orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5,
            font=dict(size=tamanho_fonte(TAMANHO_FONTE_LEGENDA)),
        ),
    )
    return figura


def montar_grafico_linha_absoluto(eixo_x, tabela_pivotada_quantidade, titulo, paleta_cores, titulo_eixo_x,
                                   ordem_categorias, largura, altura,
                                   tickangle_eixo_x=0, margem_inferior=None,
                                   eixo_x_ano_continuo=False,
                                   normalizar_para_100_porcento=None,
                                   rotulo_eixo_y=None):
    '''
    Versão em linhas de montar_grafico_empilhado_absoluto -- mesmos
    dados, eixos e título, mas uma linha por categoria em vez de barras
    empilhadas. normalizar_para_100_porcento=None usa o padrão global
    (NORMALIZAR_PARA_100_PORCENTO, em configuracao_layout_graficos.py);
    quando ligado, cada linha mostra participação percentual da
    categoria no total daquele Ano, em vez do valor absoluto.
    '''
    if normalizar_para_100_porcento is None:
        normalizar_para_100_porcento = NORMALIZAR_PARA_100_PORCENTO

    largura = _largura_ajustada(largura, len(eixo_x))

    tabela_valores = tabela_pivotada_quantidade.reindex(columns=ordem_categorias, fill_value=0.0)

    if normalizar_para_100_porcento:
        total_por_x = tabela_valores.sum(axis=1)
        total_valido = total_por_x.where(total_por_x != 0)
        tabela_plotada = (tabela_valores.div(total_valido, axis=0) * 100).fillna(0.0)
        rotulo_eixo_y_final = rotulo_eixo_y or "% do total"
    else:
        tabela_plotada = tabela_valores
        rotulo_eixo_y_final = rotulo_eixo_y or "Quantidade"

    figura = go.Figure()
    for categoria in ordem_categorias:
        figura.add_trace(go.Scatter(
            x=eixo_x, y=tabela_plotada[categoria], name=categoria.title(), mode="lines+markers",
            line=dict(color=paleta_cores[categoria]), marker=dict(color=paleta_cores[categoria]),
        ))

    eixo_x_config = dict(
        title=dict(text=titulo_eixo_x, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
        tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
        tickangle=tickangle_eixo_x,
    )
    if eixo_x_ano_continuo:
        eixo_x_config["type"] = "category"

    margem_inferior, legenda_y = _calcular_margem_inferior_e_legenda(
        eixo_x, tickangle_eixo_x, altura, margem_inferior
    )

    eixo_y_config = dict(
        title=dict(text=rotulo_eixo_y_final, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
        tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
    )
    if normalizar_para_100_porcento:
        eixo_y_config["range"] = [0, 100]

    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO))),
        template="plotly_white", width=largura, height=altura,
        margin=dict(l=60, r=60, t=_MARGEM_SUPERIOR_PADRAO, b=margem_inferior),
        xaxis=eixo_x_config, yaxis=eixo_y_config,
        legend=dict(
            orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5,
            font=dict(size=tamanho_fonte(TAMANHO_FONTE_LEGENDA)),
        ),
    )
    return figura


def montar_grafico_area_absoluto(eixo_x, tabela_pivotada_quantidade, titulo, paleta_cores, titulo_eixo_x,
                                  ordem_categorias, largura, altura,
                                  tickangle_eixo_x=0, margem_inferior=None,
                                  eixo_x_ano_continuo=False,
                                  normalizar_para_100_porcento=None,
                                  rotulo_eixo_y=None):
    '''
    Versão em área empilhada ("montanha") de montar_grafico_empilhado_
    absoluto -- mesmos dados, eixos e título, mas cada categoria é uma
    área colorida empilhada (preenchimento até a área da categoria
    anterior) em vez de uma barra. normalizar_para_100_porcento=None usa
    o padrão global (NORMALIZAR_PARA_100_PORCENTO, em configuracao_
    layout_graficos.py); quando ligado, a pilha é normalizada para 100%
    (participação percentual) em cada Ano, em vez de escala absoluta.
    '''
    if normalizar_para_100_porcento is None:
        normalizar_para_100_porcento = NORMALIZAR_PARA_100_PORCENTO

    largura = _largura_ajustada(largura, len(eixo_x))

    tabela_valores = tabela_pivotada_quantidade.reindex(columns=ordem_categorias, fill_value=0.0)

    if normalizar_para_100_porcento:
        total_por_x = tabela_valores.sum(axis=1)
        total_valido = total_por_x.where(total_por_x != 0)
        tabela_plotada = (tabela_valores.div(total_valido, axis=0) * 100).fillna(0.0)
        rotulo_eixo_y_final = rotulo_eixo_y or "% do total"
    else:
        tabela_plotada = tabela_valores
        rotulo_eixo_y_final = rotulo_eixo_y or "Quantidade"

    figura = go.Figure()
    for categoria in ordem_categorias:
        figura.add_trace(go.Scatter(
            x=eixo_x, y=tabela_plotada[categoria], name=categoria.title(), mode="lines",
            stackgroup="total", line=dict(color=paleta_cores[categoria], width=0.5),
            fillcolor=paleta_cores[categoria],
        ))

    eixo_x_config = dict(
        title=dict(text=titulo_eixo_x, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
        tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
        tickangle=tickangle_eixo_x,
    )
    if eixo_x_ano_continuo:
        eixo_x_config["type"] = "category"

    margem_inferior, legenda_y = _calcular_margem_inferior_e_legenda(
        eixo_x, tickangle_eixo_x, altura, margem_inferior
    )

    eixo_y_config = dict(
        title=dict(text=rotulo_eixo_y_final, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO))),
        tickfont=dict(size=tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)),
    )
    if normalizar_para_100_porcento:
        eixo_y_config["range"] = [0, 100]

    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO))),
        template="plotly_white", width=largura, height=altura,
        margin=dict(l=60, r=60, t=_MARGEM_SUPERIOR_PADRAO, b=margem_inferior),
        xaxis=eixo_x_config, yaxis=eixo_y_config,
        legend=dict(
            orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5,
            font=dict(size=tamanho_fonte(TAMANHO_FONTE_LEGENDA)),
        ),
    )
    return figura


def montar_grafico_linha_dupla(eixo_x, tabela_pivotada_quantidade, tabela_pivotada_taxa, titulo,
                                paleta_cores, titulo_eixo_x, ordem_categorias, largura, altura,
                                tickangle_eixo_x=0, margem_inferior=None,
                                eixo_x_ano_continuo=False,
                                rotulo_eixo_quantidade=None, rotulo_eixo_taxa=None,
                                tamanho_fonte_titulo=TAMANHO_FONTE_TITULO_GRAFICO_LINHA,
                                tamanho_fonte_titulo_eixo=TAMANHO_FONTE_TITULO_EIXO_GRAFICO_LINHA,
                                tamanho_fonte_tick_eixo=TAMANHO_FONTE_TICK_EIXO_GRAFICO_LINHA,
                                tamanho_fonte_legenda=TAMANHO_FONTE_LEGENDA_GRAFICO_LINHA):
    '''
    Combina, num único gráfico, uma linha de QUANTIDADE (eixo Y
    primário -- à esquerda) com uma linha de TAXA (eixo Y secundário --
    à direita, sobreposto ao mesmo eixo X) por categoria, cada par na
    mesma cor da paleta (linha de taxa tracejada, pra se distinguir da
    de quantidade). NADA é empilhado -- cada categoria começa do seu
    próprio valor real, direto comparável com as demais no mesmo eixo
    (diferente de uma área empilhada, onde só a ESPESSURA da fatia
    representa o valor da categoria, não a altura do topo dela).

    Tamanhos de fonte usam um padrão próprio (TAMANHO_FONTE_*_GRAFICO_LINHA,
    em vez do padrão global TAMANHO_FONTE_*), maior -- para igualar o
    tamanho de fonte usado nos mapas (mapa_regional_valores_absolutos.ipynb).
    '''
    largura = _largura_ajustada(largura, len(eixo_x))

    tabela_plotada_quantidade = tabela_pivotada_quantidade.reindex(columns=ordem_categorias, fill_value=0.0)
    rotulo_eixo_quantidade_final = rotulo_eixo_quantidade or "Valor Absoluto"

    if rotulo_eixo_taxa is None:
        rotulo_eixo_taxa = f"Taxa {MULTIPLICADOR_TAXA // 1000}k hab."

    figura = go.Figure()
    for categoria in ordem_categorias:
        figura.add_trace(go.Scatter(
            x=eixo_x, y=tabela_plotada_quantidade[categoria], name=categoria.title(), mode="lines+markers",
            line=dict(color=paleta_cores[categoria], width=2),
            marker=dict(color=paleta_cores[categoria], size=6),
            legendgroup=categoria,
        ))
    for categoria in ordem_categorias:
        if categoria in tabela_pivotada_taxa.columns:
            valores_taxa = tabela_pivotada_taxa[categoria]
        else:
            valores_taxa = pd.Series(0.0, index=tabela_pivotada_taxa.index)

        figura.add_trace(go.Scatter(
            x=eixo_x, y=valores_taxa, name=f"{categoria.title()} (Taxa)", mode="lines+markers",
            line=dict(color=paleta_cores[categoria], dash="dot", width=3),
            marker=dict(color=paleta_cores[categoria], line=dict(color="white", width=1)),
            legendgroup=categoria, yaxis="y2",
        ))

    eixo_x_config = dict(
        title=dict(text=titulo_eixo_x, font=dict(size=tamanho_fonte(tamanho_fonte_titulo_eixo))),
        tickfont=dict(size=tamanho_fonte(tamanho_fonte_tick_eixo)),
        tickangle=tickangle_eixo_x,
    )
    if eixo_x_ano_continuo:
        eixo_x_config["type"] = "category"

    margem_inferior, legenda_y = _calcular_margem_inferior_e_legenda(
        eixo_x, tickangle_eixo_x, altura, margem_inferior,
        tamanho_fonte_tick_eixo=tamanho_fonte_tick_eixo, tamanho_fonte_titulo_eixo=tamanho_fonte_titulo_eixo,
    )

    eixo_y_config = dict(
        title=dict(text=rotulo_eixo_quantidade_final, font=dict(size=tamanho_fonte(tamanho_fonte_titulo_eixo))),
        tickfont=dict(size=tamanho_fonte(tamanho_fonte_tick_eixo)),
    )

    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(tamanho_fonte_titulo))),
        template="plotly_white", width=largura, height=altura,
        margin=dict(l=60, r=60, t=_MARGEM_SUPERIOR_PADRAO, b=margem_inferior),
        xaxis=eixo_x_config, yaxis=eixo_y_config,
        yaxis2=dict(
            title=dict(text=rotulo_eixo_taxa, font=dict(size=tamanho_fonte(tamanho_fonte_titulo_eixo))),
            tickfont=dict(size=tamanho_fonte(tamanho_fonte_tick_eixo)),
            overlaying="y", side="right", showgrid=False,
        ),
        legend=dict(
            orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5,
            font=dict(size=tamanho_fonte(tamanho_fonte_legenda)),
        ),
    )
    return figura


FONTE_FAMILIA_HEATMAP = "Helvetica Neue, Arial, sans-serif"
COR_TEXTO_HEATMAP = "#333333"
COR_LINHA_CELULA_HEATMAP = "#FFFFFF"

# Largura mínima reservada por coluna de Ano, em px -- o mesmo espírito
# de LARGURA_MINIMA_POR_CATEGORIA (configuracao_layout_graficos.py),
# mas calibrada para caber confortavelmente um valor formatado tipo
# "100.366" dentro da célula. "largura=" na chamada é só um mínimo:
# variáveis com poucos anos (ex.: Mamografia, ~13 colunas) já cabem
# nele, mas variáveis com décadas de histórico (Casos, Mortalidade,
# ~40-46 colunas) precisam de uma figura mais larga para cada célula
# ficar tão legível quanto a de Mamografia -- sem isso, o mesmo
# largura= fixo espremeria muito mais colunas no mesmo espaço.
LARGURA_MINIMA_POR_CELULA_HEATMAP = 58


def _paleta_refinada(escala_cor, n_pontos=11, contraste=1.35):
    '''
    Reamostra uma colorscale nomeada do Plotly (ex.: "Reds", "Purples",
    "Blues") em mais pontos e aplica uma curva de potência às posições
    -- não às cores -- para que os tons claros (valores baixos) fiquem
    concentrados numa faixa mais estreita da escala e os tons escuros
    (valores altos) avancem mais rápido perto do topo. O resultado é a
    MESMA identidade de cor por variável, só com mais contraste entre
    célula de valor baixo e célula de valor alto do que o degradê
    linear padrão do Plotly.
    '''
    posicoes = np.linspace(0, 1, n_pontos)
    posicoes_amostradas = posicoes ** contraste
    cores = pcolors.sample_colorscale(escala_cor, posicoes_amostradas.tolist())
    return list(zip(posicoes.tolist(), cores))


def _formatar_numero_ptbr(valor, formato):
    '''
    Formata um número com o separador de milhar "." e decimal "," (padrão
    BR) em vez do "," / "." do Python -- usado só nos textos escritos
    dentro das células do heatmap (texttemplate="%{text}" insere texto
    literal, não passa pelo locale do d3-format do Plotly, então não é
    coberto por figura.update_layout(separators=...)).
    '''
    texto = f"{valor:{formato}}"
    return texto.replace(",", "\x00").replace(".", ",").replace("\x00", ".")


def montar_par_heatmaps_regional_ano(tabela_pivotada_quantidade, tabela_pivotada_taxa, titulo,
                                      escala_cor_quantidade, escala_cor_taxa,
                                      titulo_barra_cor_quantidade, titulo_barra_cor_taxa,
                                      largura, altura,
                                      tamanho_fonte_titulo_eixo=None, tamanho_fonte_tick_eixo=None,
                                      titulo_subplot_quantidade="Quantidade",
                                      titulo_subplot_taxa="Taxa / 100k hab.",
                                      espacamento_vertical=0.14, margem=None,
                                      mostrar_valores=True, tamanho_fonte_valor=None,
                                      formato_valor_quantidade=",.0f", formato_valor_taxa=",.1f"):
    '''
    Dois heatmaps Regional (eixo Y) × Ano (eixo X), UM EMBAIXO DO OUTRO
    (subplots 2x1 -- cada um usa a largura toda da figura, mais legível
    para as 28 Regionais e dezenas de anos do que lado a lado) -- um
    colorido por QUANTIDADE (valor absoluto), outro por TAXA, cada um
    com sua própria escala/barra de cor. Quando mostrar_valores=True
    (padrão), cada heatmap escreve dentro da célula o seu PRÓPRIO valor
    (quantidade no de quantidade, taxa no de taxa) -- não mistura as
    duas dimensões no mesmo heatmap (cor de uma, texto de outra), como
    uma versão anterior deste gráfico fazia.

    tamanho_fonte_titulo_eixo/tamanho_fonte_tick_eixo/tamanho_fonte_
    valor=None usam o padrão global (tamanho_fonte(TAMANHO_FONTE_
    TITULO_EIXO)/tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)/o próprio
    tamanho_fonte_tick_eixo, em configuracao_layout_graficos.py) --
    sobrescreva por chamada para aumentar a legibilidade com as 28
    Regionais no eixo Y.
    '''
    if tamanho_fonte_titulo_eixo is None:
        tamanho_fonte_titulo_eixo = tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO)
    if tamanho_fonte_tick_eixo is None:
        tamanho_fonte_tick_eixo = tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)
    if tamanho_fonte_valor is None:
        tamanho_fonte_valor = tamanho_fonte_tick_eixo
    if margem is None:
        margem = dict(l=200, r=140, t=110, b=60)

    n_colunas_ano = max(len(tabela_pivotada_quantidade.columns), len(tabela_pivotada_taxa.columns))
    largura = max(
        largura,
        n_colunas_ano * LARGURA_MINIMA_POR_CELULA_HEATMAP + margem.get("l", 0) + margem.get("r", 0),
    )

    figura = make_subplots(
        rows=2, cols=1, vertical_spacing=espacamento_vertical,
        subplot_titles=(titulo_subplot_quantidade, titulo_subplot_taxa),
    )

    # Domínio vertical de cada linha (aproximado a partir de
    # vertical_spacing, já que make_subplots não devolve os domínios
    # calculados antes de a figura existir) -- centraliza a colorbar de
    # cada heatmap na sua própria linha, sem sobrepor a da outra.
    metade_domino = (1 - espacamento_vertical) / 2
    centro_linha_1 = 1 - metade_domino / 2
    centro_linha_2 = metade_domino / 2

    texto_quantidade = texto_taxa = None
    if mostrar_valores:
        texto_quantidade = []
        for linha in tabela_pivotada_quantidade.to_numpy():
            linha_texto = []
            for v in linha:
                if pd.notna(v):
                    linha_texto.append(_formatar_numero_ptbr(v, formato_valor_quantidade))
                else:
                    linha_texto.append("")
            texto_quantidade.append(linha_texto)

        texto_taxa = []
        for linha in tabela_pivotada_taxa.to_numpy():
            linha_texto = []
            for v in linha:
                if pd.notna(v):
                    linha_texto.append(_formatar_numero_ptbr(v, formato_valor_taxa))
                else:
                    linha_texto.append("")
            texto_taxa.append(linha_texto)

    # Barra de cor com largura/altura proporcionais à linha do subplot
    # que ela representa (não um tamanho fixo), título em duas linhas
    # legível e ticks com o mesmo formato numérico do valor escrito
    # dentro da célula -- e uma borda fina para separá-la visualmente
    # do heatmap, dando um acabamento mais "pronto para publicação".
    fonte_titulo_barra_cor = dict(size=tamanho_fonte_tick_eixo + 1, color=COR_TEXTO_HEATMAP,
                                   family=FONTE_FAMILIA_HEATMAP)
    layout_barra_cor_comum = dict(
        thickness=18, outlinewidth=1, outlinecolor="#D9D9D9",
        tickfont=dict(size=tamanho_fonte_tick_eixo - 1, color=COR_TEXTO_HEATMAP,
                      family=FONTE_FAMILIA_HEATMAP),
    )

    # xgap/ygap desenham uma linha fina entre as células (mesma cor do
    # fundo da figura) -- separa visualmente Regional/Ano adjacentes
    # sem precisar de gridlines por cima do heatmap.
    figura.add_trace(go.Heatmap(
        z=tabela_pivotada_quantidade.to_numpy(), x=tabela_pivotada_quantidade.columns,
        y=tabela_pivotada_quantidade.index, colorscale=_paleta_refinada(escala_cor_quantidade),
        xgap=1.5, ygap=1.5,
        colorbar=dict(title=dict(text=titulo_barra_cor_quantidade, font=fonte_titulo_barra_cor),
                      y=centro_linha_1, len=metade_domino,
                      yanchor="middle", tickformat=formato_valor_quantidade, **layout_barra_cor_comum),
        text=texto_quantidade, texttemplate="%{text}" if mostrar_valores else None,
        textfont=dict(size=tamanho_fonte_valor, family=FONTE_FAMILIA_HEATMAP),
        hovertemplate="Regional: %{y}<br>Ano: %{x}<br>Quantidade: %{z:,.0f}<extra></extra>",
    ), row=1, col=1)

    figura.add_trace(go.Heatmap(
        z=tabela_pivotada_taxa.to_numpy(), x=tabela_pivotada_taxa.columns,
        y=tabela_pivotada_taxa.index, colorscale=_paleta_refinada(escala_cor_taxa),
        xgap=1.5, ygap=1.5,
        colorbar=dict(title=dict(text=titulo_barra_cor_taxa, font=fonte_titulo_barra_cor),
                      y=centro_linha_2, len=metade_domino,
                      yanchor="middle", tickformat=formato_valor_taxa, **layout_barra_cor_comum),
        text=texto_taxa, texttemplate="%{text}" if mostrar_valores else None,
        textfont=dict(size=tamanho_fonte_valor, family=FONTE_FAMILIA_HEATMAP),
        hovertemplate="Regional: %{y}<br>Ano: %{x}<br>Taxa: %{z:.2f}<extra></extra>",
    ), row=2, col=1)

    figura.update_xaxes(
        type="category",
        title=dict(text="Ano", font=dict(size=tamanho_fonte_titulo_eixo, color=COR_TEXTO_HEATMAP,
                                          family=FONTE_FAMILIA_HEATMAP)),
        tickfont=dict(size=tamanho_fonte_tick_eixo, color=COR_TEXTO_HEATMAP, family=FONTE_FAMILIA_HEATMAP),
        showline=True, linewidth=1, linecolor="#D9D9D9", ticks="outside", tickcolor="#D9D9D9",
    )
    figura.update_yaxes(
        title=dict(text=COLUNA_REGIONAL.title(), font=dict(size=tamanho_fonte_titulo_eixo, color=COR_TEXTO_HEATMAP,
                                                             family=FONTE_FAMILIA_HEATMAP)),
        tickfont=dict(size=tamanho_fonte_tick_eixo, color=COR_TEXTO_HEATMAP, family=FONTE_FAMILIA_HEATMAP),
        showline=True, linewidth=1, linecolor="#D9D9D9", ticks="outside", tickcolor="#D9D9D9",
    )

    # Título dos subplots ("Quantidade" / "Taxa / 100k hab.") em negrito
    # e com a mesma família de fonte do resto da figura -- por padrão
    # make_subplots os cria como anotações soltas, sem herdar isso.
    for anotacao in figura.layout.annotations:
        anotacao.update(
            text=f"<b>{anotacao.text}</b>",
            font=dict(size=tamanho_fonte_titulo_eixo + 1, color=COR_TEXTO_HEATMAP, family=FONTE_FAMILIA_HEATMAP),
        )

    figura.update_layout(
        title=dict(text=f"<b>{titulo}</b>", font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO) + 2,
                                                        color=COR_TEXTO_HEATMAP, family=FONTE_FAMILIA_HEATMAP),
                   x=0.02, xanchor="left"),
        font=dict(family=FONTE_FAMILIA_HEATMAP, color=COR_TEXTO_HEATMAP),
        template="plotly_white", width=largura, height=altura, margin=margem,
        paper_bgcolor="#FFFFFF", plot_bgcolor=COR_LINHA_CELULA_HEATMAP,
        separators=",.",  # decimal "," / milhar "." (pt-BR) nos ticks da barra de cor e no hover
    )
    return figura


def remover_anos_sem_dado(*tabelas_pivotadas):
    '''
    Remove do índice (ANO) as linhas em que TODAS as tabelas informadas
    têm todas as colunas (categorias) NaN -- um ano sem nenhum
    registro/dado em nenhuma das tabelas (ex.: taxa e quantidade de uma
    mesma variável) não deve aparecer como uma barra vazia/zerada no
    eixo X do gráfico empilhado. Mantém um ano se ele tiver ao menos um
    valor não nulo em QUALQUER uma das tabelas informadas.

    Devolve as tabelas filtradas na mesma ordem recebida, sem preencher
    NaN -- o chamador decide o fillna(0) depois do filtro (categorias
    isoladas ausentes num ano que já tem outras categorias com dado
    continuam virando 0 na pilha, só o ano inteiramente vazio é
    removido).
    '''
    anos_com_algum_dado = None
    for tabela in tabelas_pivotadas:
        mascara = tabela.notna().any(axis=1)
        anos_com_algum_dado = mascara if anos_com_algum_dado is None else (anos_com_algum_dado | mascara)
    return tuple(tabela.loc[anos_com_algum_dado] for tabela in tabelas_pivotadas)


def _classificar_em_faixas_por_quantil(valores, n_faixas):
    '''
    Discretiza uma série contínua em n_faixas faixas usando cortes por
    quantil -- cada faixa recebe aproximadamente o mesmo número de
    regionais. Lógica de corte compartilhada por
    classificar_em_degraus_bolha (tamanho de bolha) e
    classificar_em_faixas_cor (cor de fundo do mapa) -- as duas só
    diferem no que mapeiam para cada rótulo de faixa (tamanho vs. cor).

    Devolve (rótulo da faixa por índice, lista de rótulos ordenados do
    menor para o maior valor).
    '''
    valores_validos = valores.fillna(0)
    try:
        cortes = sorted(set(pd.qcut(valores_validos, q=n_faixas, retbins=True, duplicates="drop")[1]))
    except ValueError:
        cortes = sorted(set(pd.cut(valores_validos, bins=n_faixas, retbins=True)[1]))
    if len(cortes) < 2:
        cortes = [valores_validos.min() - 1, valores_validos.max() + 1]

    rotulos_ordenados = []
    for i in range(len(cortes) - 1):
        # Faixa mais baixa começa em 1, não em 0 -- são contagens (casos,
        # mortes, mamografias, hospitais), toda Regional no mapa tem pelo
        # menos 1 ocorrência no período; rotular a partir de 0 sugeriria
        # Regionais com zero ocorrências, que não é o caso.
        limite_inferior = 1 if i == 0 else cortes[i]
        rotulos_ordenados.append(
            f"{limite_inferior:,.0f}–{cortes[i + 1]:,.0f}".replace(",", ".")
        )

    rotulo_por_indice = pd.cut(
        valores_validos, bins=cortes, labels=rotulos_ordenados, include_lowest=True,
    ).astype(str)

    return rotulo_por_indice, rotulos_ordenados


def classificar_em_degraus_bolha(valores, n_degraus, tamanho_minimo=8, tamanho_maximo=34):
    '''
    Discretiza uma série contínua (ex.: QUANTIDADE acumulada por
    Regional) em n_degraus categorias de tamanho de bolha (mapa de
    bolha proporcional discreta, não escala contínua) -- ver
    _classificar_em_faixas_por_quantil para a lógica de corte.

    Devolve (rótulo do degrau por índice, lista de rótulos ordenados do
    menor para o maior valor, tamanho em pixels por rótulo) -- pronto
    para plotar como uma trace por degrau (legenda com tamanhos
    discretos e o intervalo de valores de cada um).
    '''
    rotulo_por_indice, rotulos_ordenados = _classificar_em_faixas_por_quantil(valores, n_degraus)
    tamanhos = np.linspace(tamanho_minimo, tamanho_maximo, num=len(rotulos_ordenados))
    tamanho_por_rotulo = dict(zip(rotulos_ordenados, tamanhos))
    return rotulo_por_indice, rotulos_ordenados, tamanho_por_rotulo


def classificar_em_faixas_cor(valores, n_faixas, escala_cor):
    '''
    Discretiza uma série contínua (ex.: QUANTIDADE acumulada por
    Regional) em n_faixas faixas de cor -- mapa coroplético CATEGÓRICO
    (legenda de quadradinhos rotulados, uma faixa por cor), em vez de
    escala contínua com colorbar em gradiente. Ver
    _classificar_em_faixas_por_quantil para a lógica de corte.

    escala_cor aceita o nome de uma colorscale contínua do Plotly (ex.:
    "Reds") ou uma lista de cores -- amostrada em n_faixas pontos
    igualmente espaçados (mais claro -> mais escuro) via
    plotly.colors.sample_colorscale, para reaproveitar a mesma paleta
    "Reds"/"Purples"/etc. já usada nos outros gráficos do projeto.

    Devolve (rótulo da faixa por índice, lista de rótulos ordenados do
    menor para o maior valor, cor por rótulo).
    '''
    rotulo_por_indice, rotulos_ordenados = _classificar_em_faixas_por_quantil(valores, n_faixas)
    n = len(rotulos_ordenados)
    if n == 1:
        pontos = [0.5]
    else:
        pontos = []
        for i in range(n):
            pontos.append(i / (n - 1))
    cores = pcolors.sample_colorscale(escala_cor, pontos)
    cor_por_rotulo = dict(zip(rotulos_ordenados, cores))
    return rotulo_por_indice, rotulos_ordenados, cor_por_rotulo


def montar_base_mapa_coropletico(geojson, tabela_regional, coluna_id_geojson, coluna_regional,
                                  coluna_cor, titulo_barra_cor, escala_cor,
                                  titulo, largura, altura,
                                  espessura_linha_contorno=1.2, cor_linha_contorno="#2b2b2b",
                                  posicao_colorbar=None, posicao_legenda=None,
                                  dominio_geo_x=None, margem=None, coluna_regional_exibicao=None):
    '''
    Mapa coroplético de fundo contínuo (coluna_cor, escala_cor), SEM
    bolhas -- a base reaproveitada tanto por um mapa com uma única
    camada de bolha quanto por um mapa com várias camadas sobrepostas
    (ex.: uma por TIPO de hospital); bolhas são adicionadas depois com
    adicionar_camada_de_bolhas, uma ou mais vezes, sobre a figura
    devolvida aqui.

    posicao_colorbar (dict de kwargs de go.choropleth.ColorBar, ex.:
    {"x": -0.15, "y": 0.5, "len": 0.75}) e posicao_legenda (dict de
    kwargs de layout.Legend) ficam em lados opostos da figura por
    padrão -- colorbar (variável contínua de fundo) à esquerda, legenda
    de bolha (discreta) à direita -- para nenhuma sobrepor a outra. Os
    dois usam x fora do intervalo [0, 1] (ex.: x=-0.12, x=1.02) de
    propósito: nessas coordenadas de papel, ficam DENTRO da margem
    reservada por margem (l/r), sem consumir nenhuma área do mapa em
    si -- por isso dominio_geo_x (opcional, None por padrão = mapa
    ocupa toda a área de plotagem) só deve ser usado se ainda faltar
    espaço além do que a margem já reserva; usá-lo por padrão encolhe o
    mapa em cima da margem, duas vezes.

    geojson precisa ter, em cada feature, properties[coluna_id_geojson]
    == o valor correspondente em tabela_regional[coluna_regional] (ex.:
    nome normalizado da Regional).

    coluna_regional_exibicao (opcional) -- coluna de tabela_regional com
    o nome "de verdade" da Regional (ex.: nomes_regional_originais),
    mostrado no hover no lugar de coluna_regional (que precisa
    permanecer normalizado, é a chave de junção com o geojson). None
    (padrão) usa coluna_regional também no hover.
    '''
    if posicao_colorbar is None:
        posicao_colorbar = dict(x=-0.1, y=0.5, len=0.75)
    if posicao_legenda is None:
        posicao_legenda = dict(x=1.02, y=0.5, xanchor="left", yanchor="middle")
    if margem is None:
        margem = dict(l=120, r=190, t=90, b=30)

    coluna_regional_exibicao = coluna_regional_exibicao or coluna_regional
    figura = go.Figure()

    figura.add_trace(go.Choropleth(
        geojson=geojson, locations=tabela_regional[coluna_regional], z=tabela_regional[coluna_cor],
        featureidkey=f"properties.{coluna_id_geojson}", colorscale=escala_cor,
        colorbar=dict(title=dict(text=titulo_barra_cor), **posicao_colorbar),
        marker_line_width=espessura_linha_contorno, marker_line_color=cor_linha_contorno,
        customdata=tabela_regional[coluna_regional_exibicao],
        hovertemplate="%{customdata}<br>" + titulo_barra_cor + ": %{z:,.0f}<extra></extra>",
    ))

    geos_kwargs = dict(fitbounds="locations", visible=False)
    if dominio_geo_x is not None:
        geos_kwargs["domain"] = dict(x=dominio_geo_x)
    figura.update_geos(**geos_kwargs)
    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(TAMANHO_FONTE_TITULO))),
        width=largura, height=altura, template="plotly_white",
        legend=dict(font=dict(size=tamanho_fonte(TAMANHO_FONTE_LEGENDA)), **posicao_legenda),
        margin=margem,
    )
    return figura


def montar_base_mapa_coropletico_discreto(geojson, tabela_regional, coluna_id_geojson, coluna_regional,
                                           coluna_rotulo_faixa, ordem_rotulos_faixa, cor_por_rotulo,
                                           titulo_legenda_cor,
                                           titulo, largura, altura,
                                           espessura_linha_contorno=1.2, cor_linha_contorno="#2b2b2b",
                                           posicao_legenda_cor=None, posicao_legenda_bolha=None,
                                           margem=None, coluna_regional_exibicao=None,
                                           tamanho_fonte_legenda=None, tamanho_fonte_titulo=None):
    '''
    Mesma ideia de montar_base_mapa_coropletico, mas com o fundo
    DISCRETO (categórico) em vez de escala contínua: a variável de cor
    já vem classificada em faixas (classificar_em_faixas_cor, no
    notebook chamador) e cada faixa vira uma trace própria de
    go.Choropleth com uma única cor sólida -- um Choropleth mostra sua
    entrada de legenda como um quadradinho preenchido (ícone de área),
    diferente do círculo de marcador de um Scattergeo, então a legenda
    de faixas sai "de quadradinhos" sem nenhum truque -- em vez da
    colorbar em gradiente contínuo de montar_base_mapa_coropletico.

    Usa duas legendas independentes do Plotly (>=5.15, "legend" e
    "legend2"): esta função preenche "legend" com as faixas de cor de
    fundo; bolhas adicionadas depois com adicionar_camada_de_bolhas
    devem passar nome_legenda="legend2" para cair na legenda
    secundária -- as duas nunca se misturam nem se sobrepõem, cada uma
    com sua própria posição (posicao_legenda_cor/posicao_legenda_bolha).

    geojson precisa ter, em cada feature, properties[coluna_id_geojson]
    == o valor correspondente em tabela_regional[coluna_regional] (ex.:
    nome normalizado da Regional).

    coluna_regional_exibicao (opcional) -- coluna de tabela_regional com
    o nome "de verdade" da Regional (ex.: nomes_regional_originais),
    mostrado no hover no lugar de coluna_regional (que precisa
    permanecer normalizado, é a chave de junção com o geojson). None
    (padrão) usa coluna_regional também no hover.
    '''
    if posicao_legenda_cor is None:
        posicao_legenda_cor = dict(
            orientation="h", x=0.5, xanchor="center", y=-0.05, yanchor="top",
            title=dict(text=titulo_legenda_cor),
        )
    if posicao_legenda_bolha is None:
        posicao_legenda_bolha = dict(orientation="h", x=0.5, xanchor="center", y=-0.15, yanchor="top")
    if margem is None:
        margem = dict(l=40, r=40, t=150, b=150)
    if tamanho_fonte_legenda is None:
        tamanho_fonte_legenda = TAMANHO_FONTE_LEGENDA
    if tamanho_fonte_titulo is None:
        tamanho_fonte_titulo = TAMANHO_FONTE_TITULO

    coluna_regional_exibicao = coluna_regional_exibicao or coluna_regional
    figura = go.Figure()

    for rotulo in ordem_rotulos_faixa:
        mascara = (tabela_regional[coluna_rotulo_faixa] == rotulo).to_numpy()
        if not mascara.any():
            continue
        cor = cor_por_rotulo[rotulo]
        locais = tabela_regional.loc[mascara, coluna_regional]
        nomes_exibidos = tabela_regional.loc[mascara, coluna_regional_exibicao]
        figura.add_trace(go.Choropleth(
            geojson=geojson, locations=locais, z=[0] * len(locais),
            featureidkey=f"properties.{coluna_id_geojson}",
            colorscale=[[0, cor], [1, cor]], showscale=False, zmin=0, zmax=1,
            marker_line_width=espessura_linha_contorno, marker_line_color=cor_linha_contorno,
            name=rotulo, legend="legend", showlegend=True,
            customdata=nomes_exibidos,
            hovertemplate="%{customdata}<br>" + titulo_legenda_cor + f": {rotulo}<extra></extra>",
        ))

    figura.update_geos(fitbounds="locations", visible=False)
    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(tamanho_fonte_titulo)), x=0.5, xanchor="center"),
        width=largura, height=altura, template="plotly_white",
        legend=dict(font=dict(size=tamanho_fonte(tamanho_fonte_legenda)), **posicao_legenda_cor),
        legend2=dict(font=dict(size=tamanho_fonte(tamanho_fonte_legenda)), **posicao_legenda_bolha),
        margin=margem,
    )
    return figura


def adicionar_camada_de_bolhas(figura, tabela_regional, coluna_regional,
                                coluna_valor, cor_bolha, nome_serie_bolha,
                                centroides_lon, centroides_lat,
                                n_degraus, tamanho_minimo, tamanho_maximo,
                                deslocamento_lon=0.0, deslocamento_lat=0.0,
                                mostrar_valores=False, ocultar_valor_zero=True,
                                simbolo_bolha="circle", nome_legenda="legend",
                                coluna_regional_exibicao=None):
    '''
    Adiciona UMA camada de bolhas proporcionais discretas a uma figura
    já existente (base de montar_base_mapa_coropletico ou de
    montar_base_mapa_coropletico_discreto) -- uma trace por degrau de
    tamanho (classificar_em_degraus_bolha), para a legenda mostrar o
    intervalo de valores de cada tamanho, em vez de uma escala
    contínua. Chamar mais de uma vez sobre a mesma figura, com
    deslocamento_lon/deslocamento_lat diferentes a cada chamada, produz
    bolhas levemente deslocadas em vez de perfeitamente concêntricas --
    nenhuma camada fica totalmente escondida atrás de outra mesmo quando
    os valores das camadas se aproximam (usado para uma bolha por TIPO
    de hospital habilitado, por exemplo).

    ocultar_valor_zero=True (padrão) não desenha bolha nas Regionais
    onde coluna_valor é 0 ou NaN -- ausência da categoria, não um
    círculo minúsculo no tamanho mínimo.

    simbolo_bolha (padrão "circle") controla o marcador desenhado no
    mapa e, junto, o ícone mostrado na legenda -- o Plotly não permite
    um ícone de legenda diferente do marcador real.

    nome_legenda (padrão "legend", a legenda principal) -- passe
    "legend2" ao usar montar_base_mapa_coropletico_discreto, cuja
    legenda de faixas de cor já ocupa "legend": assim a legenda de
    bolhas cai na legenda secundária, sem se misturar com a de cor.

    coluna_regional_exibicao (opcional) -- coluna de tabela_regional com
    o nome "de verdade" da Regional (ex.: nomes_regional_originais),
    mostrado no hover no lugar de coluna_regional. None (padrão) usa
    coluna_regional também no hover.
    '''
    coluna_regional_exibicao = coluna_regional_exibicao or coluna_regional
    valores = tabela_regional[coluna_valor]
    if ocultar_valor_zero:
        valores = valores.where(valores > 0)

    rotulo_por_indice, ordem_rotulos, tamanho_por_rotulo = classificar_em_degraus_bolha(
        valores, n_degraus, tamanho_minimo, tamanho_maximo,
    )

    for rotulo in ordem_rotulos:
        mascara = (rotulo_por_indice == rotulo).to_numpy() & valores.notna().to_numpy()
        if not mascara.any():
            continue
        texto_bolha = None
        if mostrar_valores:
            texto_bolha = []
            for v in valores[mascara]:
                texto_bolha.append(f"{v:,.0f}".replace(",", "."))
        figura.add_trace(go.Scattergeo(
            lon=np.asarray(centroides_lon)[mascara] + deslocamento_lon,
            lat=np.asarray(centroides_lat)[mascara] + deslocamento_lat,
            mode="markers+text" if mostrar_valores else "markers",
            marker=dict(
                size=tamanho_por_rotulo[rotulo], color=cor_bolha, symbol=simbolo_bolha,
                line=dict(width=0.5, color="white"),
            ),
            text=texto_bolha, textposition="middle center",
            name=f"{nome_serie_bolha}: {rotulo}",
            legendgroup=nome_serie_bolha, legend=nome_legenda,
            hovertext=tabela_regional.loc[mascara, coluna_regional_exibicao].tolist(),
            hoverinfo="text",
        ))
    return figura


def salvar_figura(figura, nome_do_arquivo, pasta_saida):
    pasta_saida.mkdir(parents=True, exist_ok=True)
    caminho_png = pasta_saida / f"{nome_do_arquivo}.png"
    caminho_svg = pasta_saida / f"{nome_do_arquivo}.svg"
    caminho_html = pasta_saida / f"{nome_do_arquivo}.html"
    figura.write_image(caminho_png, scale=5)
    figura.write_image(caminho_svg)  # vetorial, resolução infinita -- ideal para o TCC impresso/LaTeX
    figura.write_html(caminho_html)
    registrar_log(f"Figura PNG salva em : {caminho_png}")
    registrar_log(f"Figura SVG salva em : {caminho_svg}")
    registrar_log(f"Figura HTML salva em: {caminho_html}")
