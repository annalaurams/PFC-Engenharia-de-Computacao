
import math

import numpy as np
import pandas as pd

from utilitarios_comuns import (
    COLUNA_REGIONAL,
    PASTA_SELECAO_TRANSFORMACAO,
    SUFIXO_COLUNA_TAXA,
    SUFIXO_COLUNA_TOTAL,
    extrair_ano_da_coluna,
    registrar_log,
)
from configuracao_layout_graficos import (
    FORMATO_VALOR_BARRA,
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
    PALETA_CATEGORIAS_FORTE,
    MARCADORES_CATEGORIAS,
    MARCADOR_SEM_INFORMACAO,
    TAMANHO_MARCADOR_LINHA_CATEGORICA,
    LARGURA_BORDA_MARCADOR_LINHA_CATEGORICA,
    COR_BORDA_MARCADOR_LINHA_CATEGORICA,
    FREQUENCIA_ROTULO_LINHA_CATEGORICA,
    ANO_ANCORA_ROTULO_LINHA_CATEGORICA,
    TAMANHO_FONTE_VALOR_LINHA_CATEGORICA,
    POSICOES_ROTULO_LINHA_CATEGORICA,
    LIMIAR_ROTULO_LINHA_CATEGORICA,
    LARGURA_MINIMA_POR_ANO_LINHA_CATEGORICA,
    COR_LINHA_POPULACAO_TOTAL,
    TAMANHO_MARCADOR_CENSITARIO_POPULACAO,
    TAMANHO_MARCADOR_ESTIMADO_POPULACAO,
    OPACIDADE_MARCADOR_ESTIMADO_POPULACAO,
    COR_LINHA_DESTAQUE_ANO_CENSITARIO,
    LARGURA_LINHA_DESTAQUE_ANO_CENSITARIO,
    OPACIDADE_LINHA_DESTAQUE_ANO_CENSITARIO,
    TAMANHO_FONTE_TITULO_PAINEL_POPULACAO,
    ESPACAMENTO_VERTICAL_PAINEIS_POPULACAO,
    tamanho_fonte,
)

import plotly.colors as pcolors
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def carregar_taxa_por_regional(caminho_csv):
    """Lê o CSV de taxa por Regional."""
    return pd.read_csv(caminho_csv)


CAMINHO_MUNICIPIOS_REGIONAIS = PASTA_SELECAO_TRANSFORMACAO / "Municípios" / "tabela_municipios_regionais.csv"


def carregar_mapa_regional_original(caminho_csv=CAMINHO_MUNICIPIOS_REGIONAIS):
    """Devolve {REGIONAL NORMALIZADA -> REGIONAL ORIGINAL}, para exibir o nome da Regional com acentos e maiúsculas."""
    tabela = pd.read_csv(caminho_csv)
    return (
        tabela[["REGIONAL NORMALIZADA", "REGIONAL ORIGINAL"]]
        .drop_duplicates()
        .set_index("REGIONAL NORMALIZADA")["REGIONAL ORIGINAL"]
        .to_dict()
    )


def nomes_regional_originais(serie_normalizada, mapa_regional_original=None):
    """Converte nomes normalizados de Regional para os nomes originais; sem correspondência, usa .title()."""
    if mapa_regional_original is None:
        mapa_regional_original = carregar_mapa_regional_original()

    sem_correspondencia = set()
    for valor in pd.unique(serie_normalizada):
        if pd.notna(valor) and valor not in mapa_regional_original:
            sem_correspondencia.add(valor)
    valores_sem_correspondencia = sorted(sem_correspondencia)
    if valores_sem_correspondencia:
        registrar_log(
            f"ATENÇÃO: {len(valores_sem_correspondencia)} nome(s) de Regional sem "
            f"correspondência em tabela_municipios_regionais.csv -- usando .title() "
            f"como fallback: {valores_sem_correspondencia}"
        )

    def _mapear(valor):
        if pd.isna(valor):
            return valor
        return mapa_regional_original.get(valor, str(valor).title())

    if hasattr(serie_normalizada, "map"):
        return serie_normalizada.map(_mapear)
    return pd.Series(serie_normalizada).map(_mapear)


def agregar_periodo_por_regional(tabela_taxa_regional, colunas_de_valor):
    """Soma a QUANTIDADE das colunas informadas por Regional, ordenada de forma decrescente."""
    resultado = pd.DataFrame({
        COLUNA_REGIONAL: tabela_taxa_regional[COLUNA_REGIONAL],
        "QUANTIDADE": tabela_taxa_regional[colunas_de_valor].sum(axis=1, min_count=1),
    })
    return resultado.sort_values("QUANTIDADE", ascending=False).reset_index(drop=True)


def preparar_simples_por_regional_ano(tabela_taxa_regional, colunas_de_valor):
    """Converte a tabela de taxa de uma variável simples para o formato longo (Regional, Ano, TAXA, QUANTIDADE)."""
    registros = []
    for coluna in colunas_de_valor:
        ano = extrair_ano_da_coluna(coluna)
        coluna_taxa = f"{coluna}{SUFIXO_COLUNA_TAXA}"
        taxa = pd.NA
        if coluna_taxa in tabela_taxa_regional.columns:
            taxa = tabela_taxa_regional[coluna_taxa]
        registros.append(pd.DataFrame({
            COLUNA_REGIONAL: tabela_taxa_regional[COLUNA_REGIONAL],
            "ANO": ano,
            "TAXA": taxa,
            "QUANTIDADE": tabela_taxa_regional[coluna],
        }))
    return pd.concat(registros, ignore_index=True)


def preparar_categorica_estadual_por_ano(tabela_agregada_estadual, sufixo_variavel, ano_inicial, ano_final):
    """Recorta do CSV agregado estadual as colunas de uma variável e devolve as tabelas de taxa e quantidade (ANO x CATEGORIA), sem a categoria TOTAL."""
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
    """Ordena as categorias alfabeticamente, com 'SEM INFORMAÇÃO' por último, ou segundo a ordem customizada."""
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


def gerar_paleta_categorica_forte(categorias_ordenadas, paleta=None):
    """Atribui a cada categoria uma cor da paleta qualitativa; 'SEM INFORMAÇÃO' recebe a cor neutra."""
    if paleta is None:
        paleta = PALETA_CATEGORIAS_FORTE

    paleta_final = {}
    indice_cor = 0
    for categoria in categorias_ordenadas:
        if categoria in CORES_CATEGORIAS_CUSTOMIZADAS:
            paleta_final[categoria] = CORES_CATEGORIAS_CUSTOMIZADAS[categoria]
        elif categoria.strip().upper() == "SEM INFORMAÇÃO":
            paleta_final[categoria] = COR_SEM_INFORMACAO
        else:
            paleta_final[categoria] = paleta[indice_cor % len(paleta)]
            indice_cor += 1
    return paleta_final


def gerar_marcadores_categoria(categorias_ordenadas, marcadores=None):
    """Atribui a cada categoria um símbolo de marcador; 'SEM INFORMAÇÃO' recebe o marcador aberto."""
    if marcadores is None:
        marcadores = MARCADORES_CATEGORIAS

    marcadores_final = {}
    indice_marcador = 0
    for categoria in categorias_ordenadas:
        if categoria.strip().upper() == "SEM INFORMAÇÃO":
            marcadores_final[categoria] = MARCADOR_SEM_INFORMACAO
        else:
            marcadores_final[categoria] = marcadores[indice_marcador % len(marcadores)]
            indice_marcador += 1
    return marcadores_final


def gerar_posicoes_rotulo_categoria(categorias_ordenadas, posicoes=None):
    """Alterna a posição do rótulo de valor (textposition) entre as categorias."""
    if posicoes is None:
        posicoes = POSICOES_ROTULO_LINHA_CATEGORICA
    posicoes_por_categoria = {}
    for indice, categoria in enumerate(categorias_ordenadas):
        posicoes_por_categoria[categoria] = posicoes[indice % len(posicoes)]
    return posicoes_por_categoria


def _largura_ajustada(largura, n_categorias, largura_minima_por_item=None):
    """Garante uma largura mínima por item do eixo X."""
    if largura_minima_por_item is None:
        largura_minima_por_item = LARGURA_MINIMA_POR_CATEGORIA
    return max(largura, n_categorias * largura_minima_por_item)


# Constantes do cálculo automático de margem inferior e posição da legenda
_MARGEM_SUPERIOR_PADRAO = 100
_LARGURA_MEDIA_CARACTERE_EM_FONTE = 0.6
_ESPACO_ENTRE_ROTULOS_E_TITULO = 8
_ESPACO_ENTRE_ROTULOS_E_LEGENDA = 15
_ALTURA_LINHA_LEGENDA = 26
_ESPACO_ENTRE_LEGENDA_E_BORDA = 10


def _altura_rotulos_eixo_x(rotulos_eixo_x, tickangle_eixo_x, tamanho_fonte_tick):
    """Estima a altura, em px, ocupada pelo maior rótulo do eixo X já rotacionado."""
    maior_rotulo = max((str(rotulo) for rotulo in rotulos_eixo_x), key=len, default="")
    largura_rotulo_px = len(maior_rotulo) * tamanho_fonte_tick * _LARGURA_MEDIA_CARACTERE_EM_FONTE
    angulo_rad = math.radians(tickangle_eixo_x or 0)
    return abs(largura_rotulo_px * math.sin(angulo_rad)) + abs(tamanho_fonte_tick * math.cos(angulo_rad))


def _altura_linha_legenda(tamanho_fonte_legenda):
    """Altura, em px, de uma linha de legenda horizontal -- escala com o tamanho de fonte da legenda.

    `_ALTURA_LINHA_LEGENDA` foi calibrado para `TAMANHO_FONTE_LEGENDA` (15px); gráficos com fonte de
    legenda maior (ex.: `TAMANHO_FONTE_LEGENDA_GRAFICO_LINHA`, 27px) precisam de mais altura, senão o
    texto da legenda é cortado embaixo da figura.
    """
    return _ALTURA_LINHA_LEGENDA * tamanho_fonte(tamanho_fonte_legenda) / TAMANHO_FONTE_LEGENDA


def _calcular_margem_inferior_e_legenda(rotulos_eixo_x, tickangle_eixo_x, altura, margem_inferior=None,
                                         tamanho_fonte_tick_eixo=TAMANHO_FONTE_TICK_EIXO,
                                         tamanho_fonte_titulo_eixo=TAMANHO_FONTE_TITULO_EIXO,
                                         tamanho_fonte_legenda=TAMANHO_FONTE_LEGENDA):
    """Calcula a margem inferior e a posição vertical da legenda, abaixo dos rótulos e do título do eixo X."""
    altura_rotulos = _altura_rotulos_eixo_x(
        rotulos_eixo_x, tickangle_eixo_x, tamanho_fonte(tamanho_fonte_tick_eixo)
    )
    altura_titulo_eixo = tamanho_fonte(tamanho_fonte_titulo_eixo)
    altura_rotulos_e_titulo = altura_rotulos + _ESPACO_ENTRE_ROTULOS_E_TITULO + altura_titulo_eixo

    if margem_inferior is None:
        margem_inferior = (
            altura_rotulos_e_titulo + _ESPACO_ENTRE_ROTULOS_E_LEGENDA
            + _altura_linha_legenda(tamanho_fonte_legenda) + _ESPACO_ENTRE_LEGENDA_E_BORDA
        )

    altura_area_grafico = max(altura - _MARGEM_SUPERIOR_PADRAO - margem_inferior, 1)
    legenda_y = -(altura_rotulos_e_titulo + _ESPACO_ENTRE_ROTULOS_E_LEGENDA) / altura_area_grafico
    return margem_inferior, legenda_y


# Ciclo de posições dos rótulos, alternando cima/baixo a cada rank de valor
_CICLO_POSICOES_ROTULO_SEM_SOBREPOSICAO = [
    "top center", "bottom center", "top right", "bottom left", "top left", "bottom right",
]


# Fração da escala do eixo Y abaixo da qual dois valores vizinhos são considerados próximos demais
_LIMIAR_PROXIMIDADE_ROTULO = 0.05


def _posicoes_e_textos_rotulo(pontos_com_rotulo_por_ano, formato_valor, escala_total):
    """Define, ano a ano, a posição e o texto de cada rótulo visível, alternando cima/baixo pelo ranking de valor para evitar sobreposição."""
    ciclo = _CICLO_POSICOES_ROTULO_SEM_SOBREPOSICAO
    limiar_proximidade = _LIMIAR_PROXIMIDADE_ROTULO * escala_total if escala_total else 0

    resultado = {}
    for ano, candidatos in pontos_com_rotulo_por_ano.items():
        candidatos_ordenados = sorted(candidatos, key=lambda par: par[1])
        n_candidatos = len(candidatos_ordenados)
        for indice, (categoria, valor) in enumerate(candidatos_ordenados):
            posicao = ciclo[indice % len(ciclo)]
            texto = f"{valor:{formato_valor}}"

            perto_do_vizinho_abaixo = (
                indice > 0 and (valor - candidatos_ordenados[indice - 1][1]) < limiar_proximidade
            )
            perto_do_vizinho_acima = (
                indice < n_candidatos - 1 and (candidatos_ordenados[indice + 1][1] - valor) < limiar_proximidade
            )
            if perto_do_vizinho_abaixo or perto_do_vizinho_acima:
                if posicao.startswith("top"):
                    texto = texto + "<br> "
                else:
                    texto = " <br>" + texto

            resultado[(ano, categoria)] = (posicao, texto)
    return resultado


def montar_grafico_linha_categorica_absoluto(eixo_x, tabela_pivotada_quantidade, titulo, paleta_cores,
                                              marcadores_categorias, titulo_eixo_x, ordem_categorias,
                                              largura, altura, tickangle_eixo_x=0, margem_inferior=None,
                                              eixo_x_ano_continuo=False, rotulo_eixo_y=None,
                                              dtick_eixo_y=None,
                                              mostrar_valores=True, frequencia_rotulo=None,
                                              ano_ancora_rotulo=None,
                                              posicoes_rotulo=None, limiar_rotulo=None,
                                              formato_valor=FORMATO_VALOR_BARRA,
                                              tamanho_fonte_titulo=TAMANHO_FONTE_TITULO_GRAFICO_LINHA,
                                              tamanho_fonte_titulo_eixo=TAMANHO_FONTE_TITULO_EIXO_GRAFICO_LINHA,
                                              tamanho_fonte_tick_eixo=TAMANHO_FONTE_TICK_EIXO_GRAFICO_LINHA,
                                              tamanho_fonte_legenda=TAMANHO_FONTE_LEGENDA_GRAFICO_LINHA,
                                              tamanho_fonte_valor=TAMANHO_FONTE_VALOR_LINHA_CATEGORICA,
                                              tamanho_marcador=TAMANHO_MARCADOR_LINHA_CATEGORICA):
    """Gráfico de linhas com uma linha por categoria (valor absoluto), com cores e marcadores distintos e rótulos de valor espaçados."""
    if frequencia_rotulo is None:
        frequencia_rotulo = FREQUENCIA_ROTULO_LINHA_CATEGORICA
    if ano_ancora_rotulo is None:
        ano_ancora_rotulo = ANO_ANCORA_ROTULO_LINHA_CATEGORICA
    if posicoes_rotulo is None:
        posicoes_rotulo = gerar_posicoes_rotulo_categoria(ordem_categorias)
    if limiar_rotulo is None:
        limiar_rotulo = LIMIAR_ROTULO_LINHA_CATEGORICA

    largura = _largura_ajustada(largura, len(eixo_x), LARGURA_MINIMA_POR_ANO_LINHA_CATEGORICA)

    tabela_valores = tabela_pivotada_quantidade.reindex(columns=ordem_categorias, fill_value=0.0)
    rotulo_eixo_y_final = rotulo_eixo_y or "Quantidade"

    # Pontos (ano, categoria) com rótulo visível: ano na grade da âncora e valor acima do limiar da categoria
    maximo_por_categoria = {}
    for categoria in ordem_categorias:
        maximo_por_categoria[categoria] = tabela_valores[categoria].max()
    pontos_com_rotulo_por_ano = {}
    if mostrar_valores:
        for ano in tabela_valores.index:
            if (ano - ano_ancora_rotulo) % frequencia_rotulo != 0:
                continue
            candidatos = []
            for categoria in ordem_categorias:
                valor = tabela_valores.loc[ano, categoria]
                if valor >= limiar_rotulo * maximo_por_categoria[categoria]:
                    candidatos.append((categoria, valor))
            pontos_com_rotulo_por_ano[ano] = candidatos

    escala_total = 0.0
    if mostrar_valores:
        escala_total = float(tabela_valores.to_numpy().max())
    mapa_rotulos = _posicoes_e_textos_rotulo(pontos_com_rotulo_por_ano, formato_valor, escala_total)

    figura = go.Figure()
    # Uma trace de linha por categoria; quando `mostrar_valores`, cada ponto recebe seu próprio
    # texto/posição vindos de `mapa_rotulos` (pontos sem rótulo visível ficam com texto vazio)
    for categoria in ordem_categorias:
        valores = tabela_valores[categoria]

        texto = None
        posicoes_pontos = None
        if mostrar_valores:
            texto = []
            posicoes_pontos = []
            for ano, _valor in valores.items():
                posicao_e_texto = mapa_rotulos.get((ano, categoria))
                if posicao_e_texto is not None:
                    posicao, texto_formatado = posicao_e_texto
                    texto.append(texto_formatado)
                    posicoes_pontos.append(posicao)
                else:
                    texto.append("")
                    posicoes_pontos.append(posicoes_rotulo[categoria])

        modo = "lines+markers"
        posicao_do_texto = posicoes_rotulo[categoria]
        if mostrar_valores:
            modo = "lines+markers+text"
            posicao_do_texto = posicoes_pontos

        figura.add_trace(go.Scatter(
            x=eixo_x, y=valores, name=categoria.title(),
            mode=modo,
            line=dict(color=paleta_cores[categoria], width=2),
            marker=dict(
                color=paleta_cores[categoria], size=tamanho_marcador,
                symbol=marcadores_categorias[categoria],
                line=dict(color=COR_BORDA_MARCADOR_LINHA_CATEGORICA, width=LARGURA_BORDA_MARCADOR_LINHA_CATEGORICA),
            ),
            text=texto, textposition=posicao_do_texto,
            textfont=dict(size=tamanho_fonte(tamanho_fonte_valor), color=paleta_cores[categoria]),
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
        tamanho_fonte_legenda=tamanho_fonte_legenda,
    )

    eixo_y_config = dict(
        title=dict(text=rotulo_eixo_y_final, font=dict(size=tamanho_fonte(tamanho_fonte_titulo_eixo))),
        tickfont=dict(size=tamanho_fonte(tamanho_fonte_tick_eixo)),
    )
    if dtick_eixo_y is not None:
        eixo_y_config["dtick"] = dtick_eixo_y

    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(tamanho_fonte_titulo))),
        template="plotly_white", width=largura, height=altura,
        margin=dict(l=70, r=60, t=_MARGEM_SUPERIOR_PADRAO, b=margem_inferior),
        xaxis=eixo_x_config, yaxis=eixo_y_config,
        legend=dict(
            orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5,
            font=dict(size=tamanho_fonte(tamanho_fonte_legenda)),
        ),
    )
    return figura


# Espaço estimado, em px, ocupado pelo ícone + espaçamento de cada item da legenda horizontal
_LARGURA_ICONE_E_ESPACO_ITEM_LEGENDA = 60


def _largura_minima_para_legenda_em_uma_linha(rotulos_legenda, tamanho_fonte_legenda):
    """Estima a largura, em px, necessária para todos os itens da legenda caberem numa única linha."""
    largura_total = 0.0
    for rotulo in rotulos_legenda:
        largura_texto = len(rotulo) * tamanho_fonte_legenda * _LARGURA_MEDIA_CARACTERE_EM_FONTE
        largura_total += _LARGURA_ICONE_E_ESPACO_ITEM_LEGENDA + largura_texto
    return largura_total


def agregar_populacao_estadual_por_ano(tabela_populacao, faixas_etarias, anos):
    """Soma a população (TOTAL e cada faixa etária) de todos os municípios de MG, por ano.

    Devolve a série do TOTAL (índice = ano) e a tabela por faixa etária
    (índice = ano, uma coluna por faixa), ambas somando `tabela_populacao`
    (uma linha por município) ao longo de todas as linhas.
    """
    serie_total = pd.Series(
        {ano: tabela_populacao[f"{ano}{SUFIXO_COLUNA_TOTAL}"].sum() for ano in anos},
        name="TOTAL",
    )
    serie_total.index.name = "ANO"

    tabela_por_faixa = pd.DataFrame(
        {faixa: {ano: tabela_populacao[f"{ano}_{faixa}"].sum() for ano in anos} for faixa in faixas_etarias},
        index=anos,
    )
    tabela_por_faixa.index.name = "ANO"

    return serie_total, tabela_por_faixa


def _tamanhos_e_opacidades_censitario(anos, anos_censitarios_set, tamanho_marcador_censitario,
                                       tamanho_marcador_estimado, opacidade_marcador_estimado):
    """Marcador maior e opaco nos anos censitários (dado real do IBGE); menor e translúcido nos demais."""
    tamanhos = []
    opacidades = []
    for ano in anos:
        if ano in anos_censitarios_set:
            tamanhos.append(tamanho_marcador_censitario)
            opacidades.append(1.0)
        else:
            tamanhos.append(tamanho_marcador_estimado)
            opacidades.append(opacidade_marcador_estimado)
    return tamanhos, opacidades


def _tickvals_e_texto_com_destaque_censitario(anos, anos_censitarios):
    """Eixo X dividido pelos anos censitários (dado real do IBGE), em negrito -- sem grade regular.

    Antes a grade regular (a cada `dtick` anos, contada a partir do ano
    inicial) podia deixar um ano censitário de fora e sem rótulo escrito.
    Agora o eixo só é dividido pelos anos censitários, que são o dado
    prioritário do gráfico.
    """
    anos_set = set(anos)
    anos_censitarios_set = set(anos_censitarios) & anos_set
    tickvals = sorted(anos_censitarios_set)
    ticktext = [f"<b>{v}</b>" for v in tickvals]
    return tickvals, ticktext


def montar_grafico_linha_populacao_com_destaque_censitario(
        series_por_categoria, anos_censitarios, titulo, titulo_eixo_x, titulo_eixo_y,
        largura, altura, paleta_cores=None, marcadores_categorias=None, ordem_categorias=None,
        tickangle_eixo_x=-45, dtick_eixo_y=None,
        tamanho_marcador_censitario=TAMANHO_MARCADOR_CENSITARIO_POPULACAO,
        tamanho_marcador_estimado=TAMANHO_MARCADOR_ESTIMADO_POPULACAO,
        opacidade_marcador_estimado=OPACIDADE_MARCADOR_ESTIMADO_POPULACAO,
        tamanho_fonte_titulo=TAMANHO_FONTE_TITULO_GRAFICO_LINHA,
        tamanho_fonte_titulo_eixo=TAMANHO_FONTE_TITULO_EIXO_GRAFICO_LINHA,
        tamanho_fonte_tick_eixo=TAMANHO_FONTE_TICK_EIXO_GRAFICO_LINHA,
        tamanho_fonte_legenda=TAMANHO_FONTE_LEGENDA_GRAFICO_LINHA):
    """Gráfico de linha (uma linha por chave de `series_por_categoria`), com um ponto por ano.

    Mesmos marcadores do gráfico de linha categórico de Casos (cor da
    `PALETA_CATEGORIAS_FORTE` + símbolo de `MARCADORES_CATEGORIAS`, um por
    categoria). Os anos em `anos_censitarios` (dado real do IBGE) recebem
    marcador maior e opaco; os demais anos (interpolados/extrapolados)
    recebem marcador menor e translúcido -- a linha em si é contínua, só o
    marcador muda, já que a série completa (real + estimada) é uma única
    sequência sem corte.
    """
    if ordem_categorias is None:
        ordem_categorias = list(series_por_categoria.keys())
    if paleta_cores is None:
        if len(ordem_categorias) == 1:
            paleta_cores = {ordem_categorias[0]: COR_LINHA_POPULACAO_TOTAL}
        else:
            paleta_cores = gerar_paleta_categorica_forte(ordem_categorias)
    if marcadores_categorias is None:
        marcadores_categorias = gerar_marcadores_categoria(ordem_categorias)

    rotulos_legenda = [str(categoria).title() for categoria in ordem_categorias]
    rotulos_legenda += ["Ano censitário (IBGE)", "Estimado (interpolação/extrapolação)"]
    largura = max(largura, _largura_minima_para_legenda_em_uma_linha(
        rotulos_legenda, tamanho_fonte(tamanho_fonte_legenda),
    ))

    anos_censitarios_set = set(anos_censitarios)

    figura = go.Figure()
    for categoria in ordem_categorias:
        valores = series_por_categoria[categoria]
        cor = paleta_cores[categoria]
        simbolo = marcadores_categorias[categoria]
        anos = list(valores.index)

        tamanhos, opacidades = _tamanhos_e_opacidades_censitario(
            anos, anos_censitarios_set, tamanho_marcador_censitario,
            tamanho_marcador_estimado, opacidade_marcador_estimado,
        )

        figura.add_trace(go.Scatter(
            x=anos, y=valores.values, name=str(categoria).title(), mode="lines+markers",
            line=dict(color=cor, width=2),
            marker=dict(
                color=cor, size=tamanhos, opacity=opacidades, symbol=simbolo,
                line=dict(color=COR_BORDA_MARCADOR_LINHA_CATEGORICA, width=LARGURA_BORDA_MARCADOR_LINHA_CATEGORICA),
            ),
            hovertemplate=(
                f"{str(categoria).title()}<br>Ano: %{{x}}<br>População: %{{y:,.0f}}<extra></extra>"
            ),
        ))

    # Traces "fantasma" (sem dado) só para a legenda explicar o que o tamanho do marcador significa
    figura.add_trace(go.Scatter(
        x=[None], y=[None], mode="markers",
        marker=dict(
            color="#555555", size=tamanho_marcador_censitario, symbol="circle",
            line=dict(color=COR_BORDA_MARCADOR_LINHA_CATEGORICA, width=LARGURA_BORDA_MARCADOR_LINHA_CATEGORICA),
        ),
        name="Ano censitário (IBGE)", showlegend=True,
    ))
    figura.add_trace(go.Scatter(
        x=[None], y=[None], mode="markers",
        marker=dict(
            color="#555555", size=tamanho_marcador_estimado, opacity=opacidade_marcador_estimado, symbol="circle",
            line=dict(color=COR_BORDA_MARCADOR_LINHA_CATEGORICA, width=LARGURA_BORDA_MARCADOR_LINHA_CATEGORICA),
        ),
        name="Estimado (interpolação/extrapolação)", showlegend=True,
    ))

    todos_os_anos = list(anos_censitarios_set | set(valores.index))
    tickvals, ticktext = _tickvals_e_texto_com_destaque_censitario(
        todos_os_anos, anos_censitarios_set,
    )

    margem_inferior, legenda_y = _calcular_margem_inferior_e_legenda(
        todos_os_anos, tickangle_eixo_x, altura,
        tamanho_fonte_tick_eixo=tamanho_fonte_tick_eixo, tamanho_fonte_titulo_eixo=tamanho_fonte_titulo_eixo,
        tamanho_fonte_legenda=tamanho_fonte_legenda,
    )

    for ano in anos_censitarios_set:
        figura.add_vline(
            x=ano, line_width=LARGURA_LINHA_DESTAQUE_ANO_CENSITARIO, line_dash="dot",
            line_color=COR_LINHA_DESTAQUE_ANO_CENSITARIO, opacity=OPACIDADE_LINHA_DESTAQUE_ANO_CENSITARIO,
            layer="below",
        )

    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(tamanho_fonte_titulo))),
        template="plotly_white", width=largura, height=altura,
        margin=dict(l=70, r=60, t=100, b=margem_inferior),
        xaxis=dict(
            title=dict(text=titulo_eixo_x, font=dict(size=tamanho_fonte(tamanho_fonte_titulo_eixo))),
            tickfont=dict(size=tamanho_fonte(tamanho_fonte_tick_eixo)),
            tickmode="array", tickvals=tickvals, ticktext=ticktext,
            tickangle=tickangle_eixo_x,
        ),
        yaxis=dict(
            title=dict(text=titulo_eixo_y, font=dict(size=tamanho_fonte(tamanho_fonte_titulo_eixo))),
            tickfont=dict(size=tamanho_fonte(tamanho_fonte_tick_eixo)),
            dtick=dtick_eixo_y,
        ),
        legend=dict(
            orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5,
            font=dict(size=tamanho_fonte(tamanho_fonte_legenda)),
        ),
    )
    return figura


def montar_paineis_populacao_total_e_por_faixa(
        serie_total, tabela_por_faixa, anos_censitarios,
        titulo_eixo_x, titulo_eixo_y,
        largura, altura,
        ordem_categorias=None, paleta_cores=None, marcadores_categorias=None,
        titulo_painel_a="A) Evolução da população feminina estimada de MG (1970–2025)",
        titulo_painel_b="B) Evolução da população de MG por faixa etária (1970–2025)",
        tickangle_eixo_x=0, dtick_eixo_y=None,
        tamanho_marcador_censitario=TAMANHO_MARCADOR_CENSITARIO_POPULACAO,
        tamanho_marcador_estimado=TAMANHO_MARCADOR_ESTIMADO_POPULACAO,
        opacidade_marcador_estimado=OPACIDADE_MARCADOR_ESTIMADO_POPULACAO,
        tamanho_fonte_titulo_painel=TAMANHO_FONTE_TITULO_PAINEL_POPULACAO,
        tamanho_fonte_titulo_eixo=TAMANHO_FONTE_TITULO_EIXO_GRAFICO_LINHA,
        tamanho_fonte_tick_eixo=TAMANHO_FONTE_TICK_EIXO_GRAFICO_LINHA,
        tamanho_fonte_legenda=TAMANHO_FONTE_LEGENDA_GRAFICO_LINHA,
        espacamento_vertical=ESPACAMENTO_VERTICAL_PAINEIS_POPULACAO):
    """Painel A (população total) empilhado sobre o painel B (uma linha por faixa etária), numa só figura.

    Os dois gráficos de `montar_grafico_linha_populacao_com_destaque_censitario`
    (população total e população por faixa etária) viram os painéis A e B de
    uma única imagem, com fonte, altura e espaçamento padronizados entre eles
    e eixo X compartilhado. Os anos censitários (dado real do IBGE) recebem
    marcador maior/opaco, rótulo em negrito e uma linha vertical pontilhada
    atravessando os dois painéis -- são o dado prioritário do gráfico.
    """
    if ordem_categorias is None:
        ordem_categorias = list(tabela_por_faixa.columns)
    if paleta_cores is None:
        paleta_cores = gerar_paleta_categorica_forte(ordem_categorias)
    if marcadores_categorias is None:
        marcadores_categorias = gerar_marcadores_categoria(ordem_categorias)

    anos_censitarios_set = set(anos_censitarios)

    figura = make_subplots(
        rows=2, cols=1, shared_xaxes=True, vertical_spacing=espacamento_vertical,
        subplot_titles=(titulo_painel_a, titulo_painel_b),
    )

    # Painel A -- população total (uma única linha)
    anos_total = list(serie_total.index)
    tamanhos_total, opacidades_total = _tamanhos_e_opacidades_censitario(
        anos_total, anos_censitarios_set, tamanho_marcador_censitario,
        tamanho_marcador_estimado, opacidade_marcador_estimado,
    )
    figura.add_trace(go.Scatter(
        x=anos_total, y=serie_total.values, name="População Total", mode="lines+markers",
        line=dict(color=COR_LINHA_POPULACAO_TOTAL, width=2),
        marker=dict(
            color=COR_LINHA_POPULACAO_TOTAL, size=tamanhos_total, opacity=opacidades_total, symbol="circle",
            line=dict(color=COR_BORDA_MARCADOR_LINHA_CATEGORICA, width=LARGURA_BORDA_MARCADOR_LINHA_CATEGORICA),
        ),
        hovertemplate="População Total<br>Ano: %{x}<br>População: %{y:,.0f}<extra></extra>",
        showlegend=False,
    ), row=1, col=1)

    # Painel B -- uma linha por faixa etária
    for categoria in ordem_categorias:
        valores = tabela_por_faixa[categoria]
        anos = list(valores.index)
        tamanhos, opacidades = _tamanhos_e_opacidades_censitario(
            anos, anos_censitarios_set, tamanho_marcador_censitario,
            tamanho_marcador_estimado, opacidade_marcador_estimado,
        )
        figura.add_trace(go.Scatter(
            x=anos, y=valores.values, name=str(categoria).title(), mode="lines+markers",
            line=dict(color=paleta_cores[categoria], width=2),
            marker=dict(
                color=paleta_cores[categoria], size=tamanhos, opacity=opacidades,
                symbol=marcadores_categorias[categoria],
                line=dict(color=COR_BORDA_MARCADOR_LINHA_CATEGORICA, width=LARGURA_BORDA_MARCADOR_LINHA_CATEGORICA),
            ),
            hovertemplate=f"{str(categoria).title()}<br>Ano: %{{x}}<br>População: %{{y:,.0f}}<extra></extra>",
        ), row=2, col=1)

    # Traces "fantasma" (sem dado) só para a legenda explicar o tamanho/opacidade do marcador, uma vez só
    # -- "legend2", numa linha própria abaixo da legenda das faixas etárias
    figura.add_trace(go.Scatter(
        x=[None], y=[None], mode="markers",
        marker=dict(
            color="#555555", size=tamanho_marcador_censitario, symbol="circle",
            line=dict(color=COR_BORDA_MARCADOR_LINHA_CATEGORICA, width=LARGURA_BORDA_MARCADOR_LINHA_CATEGORICA),
        ),
        name="Ano censitário (IBGE)", showlegend=True, legend="legend2",
    ), row=2, col=1)
    figura.add_trace(go.Scatter(
        x=[None], y=[None], mode="markers",
        marker=dict(
            color="#555555", size=tamanho_marcador_estimado, opacity=opacidade_marcador_estimado, symbol="circle",
            line=dict(color=COR_BORDA_MARCADOR_LINHA_CATEGORICA, width=LARGURA_BORDA_MARCADOR_LINHA_CATEGORICA),
        ),
        name="Estimado (interpolação/extrapolação)", showlegend=True, legend="legend2",
    ), row=2, col=1)

    # Linha vertical pontilhada nos anos censitários, atravessando os dois painéis
    for ano in anos_censitarios_set:
        figura.add_vline(
            x=ano, line_width=LARGURA_LINHA_DESTAQUE_ANO_CENSITARIO, line_dash="dot",
            line_color=COR_LINHA_DESTAQUE_ANO_CENSITARIO, opacity=OPACIDADE_LINHA_DESTAQUE_ANO_CENSITARIO,
            layer="below", row="all", col=1,
        )

    todos_os_anos = sorted(set(anos_total) | set(tabela_por_faixa.index))
    tickvals, ticktext = _tickvals_e_texto_com_destaque_censitario(
        todos_os_anos, anos_censitarios_set,
    )

    # Números do eixo X na horizontal, visíveis nos dois painéis (não só no de baixo)
    figura.update_xaxes(
        tickmode="array", tickvals=tickvals, ticktext=ticktext, tickangle=tickangle_eixo_x,
        tickfont=dict(size=tamanho_fonte(tamanho_fonte_tick_eixo)), showticklabels=True,
    )
    figura.update_xaxes(
        title=dict(text=titulo_eixo_x, font=dict(size=tamanho_fonte(tamanho_fonte_titulo_eixo))),
        row=2, col=1,
    )
    figura.update_yaxes(
        title=dict(text=titulo_eixo_y, font=dict(size=tamanho_fonte(tamanho_fonte_titulo_eixo))),
        tickfont=dict(size=tamanho_fonte(tamanho_fonte_tick_eixo)), dtick=dtick_eixo_y, automargin=True,
    )

    # Padroniza os títulos A)/B): mesma fonte, negrito, alinhados à esquerda do painel
    for anotacao in figura.layout.annotations:
        anotacao.update(
            text=f"<b>{anotacao.text}</b>",
            font=dict(size=tamanho_fonte(tamanho_fonte_titulo_painel)),
            x=0, xanchor="left",
        )

    # Legenda das faixas etárias (uma linha só) e, abaixo dela, a legenda do marcador
    # (ano censitário/estimado) -- "uma do lado da outra" dentro de cada linha, duas linhas no total
    rotulos_legenda_categorias = [str(categoria).title() for categoria in ordem_categorias]
    largura = max(largura, _largura_minima_para_legenda_em_uma_linha(
        rotulos_legenda_categorias, tamanho_fonte(tamanho_fonte_legenda),
    ))

    margem_inferior, legenda_y = _calcular_margem_inferior_e_legenda(
        todos_os_anos, tickangle_eixo_x, altura,
        tamanho_fonte_tick_eixo=tamanho_fonte_tick_eixo, tamanho_fonte_titulo_eixo=tamanho_fonte_titulo_eixo,
        tamanho_fonte_legenda=tamanho_fonte_legenda,
    )
    altura_area_grafico = max(altura - _MARGEM_SUPERIOR_PADRAO - margem_inferior, 1)
    altura_linha_legenda2 = _altura_linha_legenda(tamanho_fonte_legenda) + 6
    legenda2_y = legenda_y - altura_linha_legenda2 / altura_area_grafico
    margem_inferior += altura_linha_legenda2

    figura.update_layout(
        template="plotly_white", width=largura, height=altura,
        margin=dict(l=15, r=10, t=_MARGEM_SUPERIOR_PADRAO, b=margem_inferior),
        legend=dict(
            orientation="h", yanchor="top", y=legenda_y, xanchor="center", x=0.5,
            font=dict(size=tamanho_fonte(tamanho_fonte_legenda)),
        ),
        legend2=dict(
            orientation="h", yanchor="top", y=legenda2_y, xanchor="center", x=0.5,
            font=dict(size=tamanho_fonte(tamanho_fonte_legenda)),
        ),
    )
    return figura


def montar_grafico_barras_populacao_total(
        serie_total, anos_censitarios, titulo, titulo_eixo_x, titulo_eixo_y,
        largura, altura, cor_barra=COR_LINHA_POPULACAO_TOTAL,
        tickangle_eixo_x=-45, dtick_eixo_y=None,
        tamanho_fonte_titulo=TAMANHO_FONTE_TITULO_GRAFICO_LINHA,
        tamanho_fonte_titulo_eixo=TAMANHO_FONTE_TITULO_EIXO_GRAFICO_LINHA,
        tamanho_fonte_tick_eixo=TAMANHO_FONTE_TICK_EIXO_GRAFICO_LINHA):
    """Barras verticais com a população total por ano (já somada de todos os municípios/faixas).

    Mesma série de `montar_grafico_linha_populacao_com_destaque_censitario` (população total),
    só com barras em vez de linha -- anos censitários (IBGE) ficam opacos, o resto (interpolado/
    extrapolado) fica translúcido.
    """
    anos = list(serie_total.index)
    anos_censitarios_set = set(anos_censitarios)
    opacidades = [1.0 if ano in anos_censitarios_set else 0.55 for ano in anos]

    figura = go.Figure(go.Bar(
        x=anos, y=serie_total.values, marker=dict(color=cor_barra, opacity=opacidades),
        hovertemplate="Ano: %{x}<br>População: %{y:,.0f}<extra></extra>",
    ))

    tickvals, ticktext = _tickvals_e_texto_com_destaque_censitario(anos, anos_censitarios_set)

    margem_inferior, _ = _calcular_margem_inferior_e_legenda(
        anos, tickangle_eixo_x, altura,
        tamanho_fonte_tick_eixo=tamanho_fonte_tick_eixo, tamanho_fonte_titulo_eixo=tamanho_fonte_titulo_eixo,
    )

    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(tamanho_fonte_titulo))),
        template="plotly_white", width=largura, height=altura,
        margin=dict(l=15, r=10, t=65, b=margem_inferior),
        xaxis=dict(
            title=dict(text=titulo_eixo_x, font=dict(size=tamanho_fonte(tamanho_fonte_titulo_eixo))),
            tickfont=dict(size=tamanho_fonte(tamanho_fonte_tick_eixo)),
            tickmode="array", tickvals=tickvals, ticktext=ticktext,
            tickangle=tickangle_eixo_x, type="category", automargin=True,
        ),
        yaxis=dict(
            title=dict(text=titulo_eixo_y, font=dict(size=tamanho_fonte(tamanho_fonte_titulo_eixo))),
            tickfont=dict(size=tamanho_fonte(tamanho_fonte_tick_eixo)),
            dtick=dtick_eixo_y, automargin=True,
        ),
        bargap=0.15,
    )
    return figura


FONTE_FAMILIA_HEATMAP = "Helvetica Neue, Arial, sans-serif"
COR_TEXTO_HEATMAP = "#333333"
COR_LINHA_CELULA_HEATMAP = "#FFFFFF"

# Largura mínima por coluna de Ano, em px, para caber o valor escrito na célula
LARGURA_MINIMA_POR_CELULA_HEATMAP = 58


def _paleta_refinada(escala_cor, n_pontos=11, contraste=1.35):
    """Reamostra uma colorscale do Plotly aplicando uma curva de potência às posições, para aumentar o contraste."""
    posicoes = np.linspace(0, 1, n_pontos)
    posicoes_amostradas = posicoes ** contraste
    cores = pcolors.sample_colorscale(escala_cor, posicoes_amostradas.tolist())
    return list(zip(posicoes.tolist(), cores))


def _formatar_numero_ptbr(valor, formato):
    """Formata o número com milhar '.' e decimal ',' (padrão brasileiro)."""
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
    """Dois heatmaps Regional x Ano empilhados: um colorido pela quantidade e outro pela taxa."""
    if tamanho_fonte_titulo_eixo is None:
        tamanho_fonte_titulo_eixo = tamanho_fonte(TAMANHO_FONTE_TITULO_EIXO)
    if tamanho_fonte_tick_eixo is None:
        tamanho_fonte_tick_eixo = tamanho_fonte(TAMANHO_FONTE_TICK_EIXO)
    if tamanho_fonte_valor is None:
        tamanho_fonte_valor = tamanho_fonte_tick_eixo + 2
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

    # Centraliza a barra de cor de cada heatmap na sua própria linha
    metade_domino = (1 - espacamento_vertical) / 2
    centro_linha_1 = 1 - metade_domino / 2
    centro_linha_2 = metade_domino / 2

    texto_quantidade = None
    texto_taxa = None
    template_texto = None
    if mostrar_valores:
        template_texto = "%{text}"
        texto_quantidade = []
        for linha in tabela_pivotada_quantidade.to_numpy():
            linha_texto = []
            for valor in linha:
                if pd.notna(valor):
                    linha_texto.append(_formatar_numero_ptbr(valor, formato_valor_quantidade))
                else:
                    linha_texto.append("")
            texto_quantidade.append(linha_texto)

        texto_taxa = []
        for linha in tabela_pivotada_taxa.to_numpy():
            linha_texto = []
            for valor in linha:
                if pd.notna(valor):
                    linha_texto.append(_formatar_numero_ptbr(valor, formato_valor_taxa))
                else:
                    linha_texto.append("")
            texto_taxa.append(linha_texto)

    # Estilo comum das barras de cor
    fonte_titulo_barra_cor = dict(size=tamanho_fonte_tick_eixo + 1, color=COR_TEXTO_HEATMAP,
                                   family=FONTE_FAMILIA_HEATMAP)
    layout_barra_cor_comum = dict(
        thickness=18, outlinewidth=1, outlinecolor="#D9D9D9",
        tickfont=dict(size=tamanho_fonte_tick_eixo - 1, color=COR_TEXTO_HEATMAP,
                      family=FONTE_FAMILIA_HEATMAP),
    )

    figura.add_trace(go.Heatmap(
        z=tabela_pivotada_quantidade.to_numpy(), x=tabela_pivotada_quantidade.columns,
        y=tabela_pivotada_quantidade.index, colorscale=_paleta_refinada(escala_cor_quantidade),
        xgap=1.5, ygap=1.5,
        colorbar=dict(title=dict(text=titulo_barra_cor_quantidade, font=fonte_titulo_barra_cor),
                      y=centro_linha_1, len=metade_domino,
                      yanchor="middle", tickformat=formato_valor_quantidade, **layout_barra_cor_comum),
        text=texto_quantidade, texttemplate=template_texto,
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
        text=texto_taxa, texttemplate=template_texto,
        textfont=dict(size=tamanho_fonte_valor, family=FONTE_FAMILIA_HEATMAP),
        hovertemplate="Regional: %{y}<br>Ano: %{x}<br>Taxa: %{z:.2f}<extra></extra>",
    ), row=2, col=1)

    figura.update_xaxes(
        type="category",
        title=dict(text="Ano", font=dict(size=tamanho_fonte_titulo_eixo, color=COR_TEXTO_HEATMAP,
                                          family=FONTE_FAMILIA_HEATMAP)),
        tickfont=dict(size=tamanho_fonte_tick_eixo, color=COR_TEXTO_HEATMAP, family=FONTE_FAMILIA_HEATMAP),
        showline=True, linewidth=1, linecolor="#D9D9D9", ticks="outside", tickcolor="#D9D9D9",
        automargin=True,
    )
    figura.update_yaxes(
        title=dict(text=COLUNA_REGIONAL.title(), font=dict(size=tamanho_fonte_titulo_eixo, color=COR_TEXTO_HEATMAP,
                                                             family=FONTE_FAMILIA_HEATMAP)),
        tickfont=dict(size=tamanho_fonte_tick_eixo, color=COR_TEXTO_HEATMAP, family=FONTE_FAMILIA_HEATMAP),
        showline=True, linewidth=1, linecolor="#D9D9D9", ticks="outside", tickcolor="#D9D9D9",
        automargin=True,
    )

    # Títulos dos subplots em negrito e com a fonte da figura
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
        separators=",.",
    )
    return figura


def remover_anos_sem_dado(*tabelas_pivotadas):
    """Remove os anos em que todas as tabelas informadas estão totalmente vazias, sem preencher NaN."""
    anos_com_algum_dado = None
    for tabela in tabelas_pivotadas:
        mascara = tabela.notna().any(axis=1)
        if anos_com_algum_dado is None:
            anos_com_algum_dado = mascara
        else:
            anos_com_algum_dado = anos_com_algum_dado | mascara
    return tuple(tabela.loc[anos_com_algum_dado] for tabela in tabelas_pivotadas)


def _classificar_em_faixas_por_quantil(valores, n_faixas):
    """Discretiza a série em faixas por quantil; devolve o rótulo por índice e os rótulos ordenados."""
    valores_validos = valores.fillna(0)
    try:
        cortes = sorted(set(pd.qcut(valores_validos, q=n_faixas, retbins=True, duplicates="drop")[1]))
    except ValueError:
        cortes = sorted(set(pd.cut(valores_validos, bins=n_faixas, retbins=True)[1]))
    if len(cortes) < 2:
        cortes = [valores_validos.min() - 1, valores_validos.max() + 1]

    rotulos_ordenados = []
    for i in range(len(cortes) - 1):
        # A faixa mais baixa começa em 1: toda Regional tem ao menos uma ocorrência
        if i == 0:
            limite_inferior = 1
        else:
            limite_inferior = cortes[i]
        rotulos_ordenados.append(
            f"{limite_inferior:,.0f}–{cortes[i + 1]:,.0f}".replace(",", ".")
        )

    rotulo_por_indice = pd.cut(
        valores_validos, bins=cortes, labels=rotulos_ordenados, include_lowest=True,
    ).astype(str)

    return rotulo_por_indice, rotulos_ordenados


def classificar_em_degraus_bolha(valores, n_degraus, tamanho_minimo=8, tamanho_maximo=34):
    """Classifica a série em degraus de tamanho de bolha; devolve rótulo por índice, rótulos ordenados e tamanho por rótulo."""
    rotulo_por_indice, rotulos_ordenados = _classificar_em_faixas_por_quantil(valores, n_degraus)
    tamanhos = np.linspace(tamanho_minimo, tamanho_maximo, num=len(rotulos_ordenados))
    tamanho_por_rotulo = dict(zip(rotulos_ordenados, tamanhos))
    return rotulo_por_indice, rotulos_ordenados, tamanho_por_rotulo


def classificar_em_faixas_cor(valores, n_faixas, escala_cor):
    """Classifica a série em faixas de cor; devolve rótulo por índice, rótulos ordenados e cor por rótulo."""
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


def montar_base_mapa_coropletico_discreto(geojson, tabela_regional, coluna_id_geojson, coluna_regional,
                                           coluna_rotulo_faixa, ordem_rotulos_faixa, cor_por_rotulo,
                                           titulo_legenda_cor,
                                           titulo, largura, altura,
                                           espessura_linha_contorno=1.2, cor_linha_contorno="#2b2b2b",
                                           posicao_legenda_cor=None, posicao_legenda_bolha=None,
                                           margem=None, coluna_regional_exibicao=None,
                                           tamanho_fonte_legenda=None, tamanho_fonte_titulo=None):
    """Figura-base de mapa coroplético com uma trace por faixa de cor (legenda 'legend'); bolhas usam 'legend2'."""
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
        width=largura, height=altura, template="plotly_white",
        legend=dict(font=dict(size=tamanho_fonte(tamanho_fonte_legenda)), **posicao_legenda_cor),
        legend2=dict(
            font=dict(size=tamanho_fonte(tamanho_fonte_legenda)),
            grouptitlefont=dict(size=tamanho_fonte(tamanho_fonte_legenda) + 1),
            tracegroupgap=14,
            **posicao_legenda_bolha,
        ),
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
                                coluna_regional_exibicao=None, mostrar_titulo_grupo=True):
    """Adiciona uma camada de bolhas proporcionais discretas (uma trace por degrau de tamanho) à figura."""
    coluna_regional_exibicao = coluna_regional_exibicao or coluna_regional
    valores = tabela_regional[coluna_valor]
    if ocultar_valor_zero:
        valores = valores.where(valores > 0)

    rotulo_por_indice, ordem_rotulos, tamanho_por_rotulo = classificar_em_degraus_bolha(
        valores, n_degraus, tamanho_minimo, tamanho_maximo,
    )

    grupo_legenda = None
    if mostrar_titulo_grupo:
        grupo_legenda = nome_serie_bolha

    eh_primeiro_degrau_com_dado = True
    for rotulo in ordem_rotulos:
        mascara = (rotulo_por_indice == rotulo).to_numpy() & valores.notna().to_numpy()
        if not mascara.any():
            continue
        texto_bolha = None
        modo = "markers"
        if mostrar_valores:
            modo = "markers+text"
            texto_bolha = []
            for valor in valores[mascara]:
                texto_bolha.append(f"{valor:,.0f}".replace(",", "."))

        titulo_grupo_legenda = None
        if mostrar_titulo_grupo and eh_primeiro_degrau_com_dado:
            titulo_grupo_legenda = nome_serie_bolha

        figura.add_trace(go.Scattergeo(
            lon=np.asarray(centroides_lon)[mascara] + deslocamento_lon,
            lat=np.asarray(centroides_lat)[mascara] + deslocamento_lat,
            mode=modo,
            marker=dict(
                size=tamanho_por_rotulo[rotulo], color=cor_bolha, symbol=simbolo_bolha,
                line=dict(width=0.5, color="white"),
            ),
            text=texto_bolha, textposition="middle center",
            name=rotulo,
            legendgroup=grupo_legenda,
            legendgrouptitle_text=titulo_grupo_legenda,
            legend=nome_legenda,
            hovertext=tabela_regional.loc[mascara, coluna_regional_exibicao].tolist(),
            hoverinfo="text",
        ))
        eh_primeiro_degrau_com_dado = False
    return figura


def adicionar_rotulos_regionais(figura, centroides_lon, centroides_lat, nomes,
                                tamanho_fonte_rotulo=11, cor_texto="#1a1a1a", cor_contorno="white",
                                espessura_contorno=2, negrito=True,
                                deslocamento_lat=0.0, quebrar_linha=True):
    """Escreve o nome de cada Regional sobre o mapa, no centroide, com contorno opcional.

    `tamanho_fonte_rotulo` aceita tanto um número único quanto uma lista/array com um
    tamanho por rótulo (por exemplo, fonte menor nas Regionais menores, para reduzir sobreposição).
    """
    e = espessura_contorno
    direcoes = ((-e, -e), (0, -e), (e, -e), (-e, 0), (e, 0), (-e, e), (0, e), (e, e))
    if cor_contorno is None:
        sombra_contorno = "none"
    else:
        sombras = []
        for dx, dy in direcoes:
            sombras.append(f"{dx}px {dy}px 0 {cor_contorno}")
        sombra_contorno = ", ".join(sombras)

    textos = []
    for nome in nomes:
        if quebrar_linha:
            textos.append(str(nome).replace(" ", "<br>", 1))
        else:
            textos.append(str(nome))

    peso_fonte = "normal"
    if negrito:
        peso_fonte = "bold"
    tamanhos_fonte = tamanho_fonte_rotulo
    if np.isscalar(tamanhos_fonte):
        tamanhos_fonte = [tamanhos_fonte] * len(textos)
    else:
        tamanhos_fonte = list(tamanhos_fonte)
    figura.add_trace(go.Scattergeo(
        lon=np.asarray(centroides_lon), lat=np.asarray(centroides_lat) + deslocamento_lat,
        mode="text", text=textos, textposition="middle center",
        textfont=dict(size=tamanhos_fonte, color=cor_texto, shadow=sombra_contorno, weight=peso_fonte),
        showlegend=False, hoverinfo="skip",
    ))
    return figura


def montar_mapa_referencia_regionais(geojson, geometria_regionais, coluna_id_geojson,
                                     coluna_regional_exibicao, titulo,
                                     cor_preenchimento="#AEB9C7", cor_nome="#0b1772",
                                     cor_linha_contorno="white",
                                     cor_linha_contorno_externa=None, espessura_linha_contorno_externa=2.5,
                                     largura=1500, altura=1050,
                                     espessura_linha_contorno=1.6, tamanho_fonte_nome=15,
                                     tamanho_fonte_nome_minimo=None,
                                     tamanho_fonte_titulo=None, fundo_transparente=False):
    """Mapa de referência sem dados: todas as Regionais com a mesma cor e o nome escrito sobre cada uma.

    `cor_linha_contorno_externa`, se informada, desenha o contorno do estado (união de todas as
    Regionais) numa cor/espessura separada das divisas internas, já que `marker_line_*` do
    Choropleth não distingue divisa externa de interna.

    `tamanho_fonte_nome_minimo`, se informado, faz a fonte do nome variar entre ele e
    `tamanho_fonte_nome` conforme a área de cada Regional (menor Regional -> fonte menor),
    para reduzir sobreposição de rótulos em regiões com Regionais pequenas e próximas.
    """
    if tamanho_fonte_titulo is None:
        tamanho_fonte_titulo = TAMANHO_FONTE_TITULO
    figura = go.Figure(go.Choropleth(
        geojson=geojson, locations=geometria_regionais[coluna_id_geojson], z=[0] * len(geometria_regionais),
        featureidkey=f"properties.{coluna_id_geojson}",
        colorscale=[[0, cor_preenchimento], [1, cor_preenchimento]], showscale=False, zmin=0, zmax=1,
        marker_line_width=espessura_linha_contorno, marker_line_color=cor_linha_contorno,
        customdata=geometria_regionais[coluna_regional_exibicao],
        hovertemplate="%{customdata}<extra></extra>",
    ))
    margem_superior = 90 if titulo else 20
    figura.update_geos(fitbounds="locations", visible=False)
    figura.update_layout(
        title=dict(text=titulo, font=dict(size=tamanho_fonte(tamanho_fonte_titulo)), x=0.5, xanchor="center"),
        width=largura, height=altura, template="plotly_white",
        margin=dict(l=40, r=40, t=margem_superior, b=40),
    )
    if fundo_transparente:
        figura.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
        figura.update_geos(bgcolor="rgba(0,0,0,0)")

    if cor_linha_contorno_externa is not None:
        from shapely.ops import unary_union

        # Buffer positivo antes do union fecha pequenas falhas de topologia entre Regionais vizinhas
        # (senão o union gera lascas/vãos minúsculos, que aparecem como um contorno irregular e
        # pontilhado por cima de todo o mapa); o buffer negativo devolve o traçado ao tamanho original.
        folga_graus = 0.01
        contorno_estado = unary_union([geom.buffer(folga_graus) for geom in geometria_regionais.geometry])
        contorno_estado = contorno_estado.buffer(-folga_graus)
        poligonos = getattr(contorno_estado, "geoms", [contorno_estado])
        for poligono in poligonos:
            aneis = [poligono.exterior, *poligono.interiors]
            for anel in aneis:
                lon_anel, lat_anel = anel.xy
                figura.add_trace(go.Scattergeo(
                    lon=list(lon_anel), lat=list(lat_anel), mode="lines",
                    line=dict(color=cor_linha_contorno_externa, width=espessura_linha_contorno_externa),
                    showlegend=False, hoverinfo="skip",
                ))

    tamanho_fonte_rotulo = tamanho_fonte_nome
    if tamanho_fonte_nome_minimo is not None:
        raiz_area = np.sqrt(geometria_regionais.geometry.area.to_numpy())
        area_min, area_max = raiz_area.min(), raiz_area.max()
        if area_max > area_min:
            proporcao = (raiz_area - area_min) / (area_max - area_min)
        else:
            proporcao = np.ones_like(raiz_area)
        tamanho_fonte_rotulo = tamanho_fonte_nome_minimo + proporcao * (tamanho_fonte_nome - tamanho_fonte_nome_minimo)

    adicionar_rotulos_regionais(
        figura, centroides_lon=geometria_regionais["_LON"], centroides_lat=geometria_regionais["_LAT"],
        nomes=geometria_regionais[coluna_regional_exibicao], tamanho_fonte_rotulo=tamanho_fonte_rotulo,
        cor_texto=cor_nome, cor_contorno=None,
    )
    return figura


def _espacar_posicoes(desejadas, espacamento, limite_inferior, limite_superior):
    """Ajusta posições (em ordem decrescente) para manterem ao menos `espacamento` entre vizinhas, dentro dos limites."""
    posicoes = np.minimum(np.asarray(desejadas, dtype=float), limite_superior)
    # Passada de cima para baixo: empurra cada posição para baixo se estiver muito perto da anterior
    for i in range(1, len(posicoes)):
        posicoes[i] = min(posicoes[i], posicoes[i - 1] - espacamento)
    if len(posicoes):
        posicoes[-1] = max(posicoes[-1], limite_inferior)
    # Passada de baixo para cima: se o empurrão anterior estourou o limite inferior, reabre espaço
    # empurrando as posições de volta para cima, mantendo o espaçamento mínimo entre vizinhas
    for i in range(len(posicoes) - 2, -1, -1):
        posicoes[i] = max(posicoes[i], posicoes[i + 1] + espacamento)
    return posicoes


def _segmentos_se_cruzam(a, b, c, d):
    """Indica se os segmentos a-b e c-d se cruzam."""
    def orientacao(p, q, r):
        return np.sign((q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0]))
    return (orientacao(a, b, c) != orientacao(a, b, d)) and (orientacao(c, d, a) != orientacao(c, d, b))


def _descruzar_linhas(lons, lats, lon_coluna, lat_coluna, max_iteracoes=200):
    """Reordena os slots dos nomes até que nenhuma linha centroide-nome se cruze."""
    # `ordem[i]` é o índice do centroide ligado ao slot de nome `i`; trocar dois índices troca a
    # ligação, sem mover os slots -- repete até estabilizar (ou até `max_iteracoes`) porque desfazer
    # um cruzamento pode criar outro em outro par.
    ordem = list(range(len(lons)))
    for _ in range(max_iteracoes):
        trocou = False
        for i in range(len(ordem)):
            for j in range(i + 1, len(ordem)):
                a, b = ordem[i], ordem[j]
                if _segmentos_se_cruzam((lons[a], lats[a]), (lon_coluna, lat_coluna[i]),
                                        (lons[b], lats[b]), (lon_coluna, lat_coluna[j])):
                    ordem[i], ordem[j] = b, a
                    trocou = True
        if not trocou:
            break
    return ordem


def adicionar_rotulos_regionais_laterais(figura, centroides_lon, centroides_lat, nomes, limites,
                                         tamanho_fonte_rotulo=12, cor_texto="#1a1a1a",
                                         cor_linha="#4a4a4a", espessura_linha=1, tamanho_ponto=5,
                                         distancia_borda_graus=0.8, espacamento_minimo_graus=0.35,
                                         negrito=False):
    """Escreve os nomes das Regionais em duas colunas fora do mapa, ligados ao centroide por uma linha."""
    lon_min, lat_min, lon_max, lat_max = limites
    peso_fonte = "normal"
    if negrito:
        peso_fonte = "bold"

    tabela = pd.DataFrame({
        "lon": np.asarray(centroides_lon), "lat": np.asarray(centroides_lat),
        "nome": [str(n) for n in nomes],
    })
    mediana_lon = tabela["lon"].median()
    lados = {
        "esquerda": (tabela[tabela["lon"] <= mediana_lon], lon_min - distancia_borda_graus, "middle left"),
        "direita": (tabela[tabela["lon"] > mediana_lon], lon_max + distancia_borda_graus, "middle right"),
    }

    linhas_lon, linhas_lat = [], []
    for sub, lon_coluna, posicao_texto in lados.values():
        sub = sub.sort_values("lat", ascending=False).reset_index(drop=True)
        lat_coluna = _espacar_posicoes(sub["lat"].to_numpy(), espacamento_minimo_graus, lat_min, lat_max)
        ordem = _descruzar_linhas(sub["lon"].to_numpy(), sub["lat"].to_numpy(), lon_coluna, lat_coluna)
        sub = sub.iloc[ordem].reset_index(drop=True)
        for (_, linha), lat_nome in zip(sub.iterrows(), lat_coluna):
            linhas_lon += [linha["lon"], lon_coluna, None]
            linhas_lat += [linha["lat"], lat_nome, None]
        figura.add_trace(go.Scattergeo(
            lon=[lon_coluna] * len(sub), lat=lat_coluna,
            mode="text", text=sub["nome"].tolist(), textposition=posicao_texto,
            textfont=dict(size=tamanho_fonte_rotulo, color=cor_texto, weight=peso_fonte),
            showlegend=False, hoverinfo="skip",
        ))

    figura.add_trace(go.Scattergeo(
        lon=linhas_lon, lat=linhas_lat, mode="lines",
        line=dict(width=espessura_linha, color=cor_linha),
        showlegend=False, hoverinfo="skip",
    ))
    figura.add_trace(go.Scattergeo(
        lon=tabela["lon"], lat=tabela["lat"], mode="markers",
        marker=dict(size=tamanho_ponto, color=cor_linha),
        showlegend=False, hoverinfo="skip",
    ))
    return figura


def salvar_figura(figura, nome_do_arquivo, pasta_saida):
    """Salva a figura em PNG, SVG e HTML na pasta de saída."""
    pasta_saida.mkdir(parents=True, exist_ok=True)
    caminho_png = pasta_saida / f"{nome_do_arquivo}.png"
    caminho_svg = pasta_saida / f"{nome_do_arquivo}.svg"
    caminho_html = pasta_saida / f"{nome_do_arquivo}.html"
    figura.write_image(caminho_png, scale=6)
    figura.write_image(caminho_svg)
    figura.write_html(caminho_html)
    registrar_log(f"Figura PNG salva em : {caminho_png}")
    registrar_log(f"Figura SVG salva em : {caminho_svg}")
    registrar_log(f"Figura HTML salva em: {caminho_html}")
