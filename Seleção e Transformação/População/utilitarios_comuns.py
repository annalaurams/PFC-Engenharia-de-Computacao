import unicodedata
from pathlib import Path

import pandas as pd

COLUNA_MUNICIPIO = "MUNICÍPIO"
COLUNA_CODIGO_IBGE = "CÓDIGO IBGE"
COLUNA_REGIONAL = "REGIONAL DE SAÚDE"
COLUNA_ANO = "ANO"
COLUNA_TIPO = "TIPO"
COLUNA_QUANTIDADE = "QUANTIDADE"
COLUNA_POPULACAO = "POPULACAO"

SUFIXO_COLUNA_TOTAL = "_TOTAL"
SUFIXO_COLUNA_TAXA = "_TAXA"
SUFIXO_COLUNA_POPULACAO_AGREGADA = "_POPULACAO"
MULTIPLICADOR_TAXA = 100_000

POPULACAO_MINIMA_VALIDA = 1

# Faixas etárias decenais padronizadas, usadas tanto nas bases de eventos
# (Casos por Faixa Etária, Mortalidade, Mamografia) quanto na base de
# população -- permite casar coluna de evento com a coluna de população da
# mesma faixa e ano, em vez de sempre usar a população total como denominador.
FAIXAS_ETARIAS_PADRAO = ("0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70 OU MAIS")

PASTA_POPULACAO = Path(__file__).resolve().parent
PASTA_SELECAO_TRANSFORMACAO = PASTA_POPULACAO.parent

CAMINHO_POPULACAO = PASTA_POPULACAO / "Interpolação e Extrapolação" / "populacao_interpolacao_extrapolacao.csv"


def registrar_log(mensagem):
    print(f"[LOG] {mensagem}")


def normalizar_codigo_ibge(serie_codigo_ibge):
    return pd.to_numeric(
        serie_codigo_ibge.astype(str).str.strip(),
        errors="coerce",
    ).astype("Int64")


def normalizar_regional(serie_regional):
    def _normalizar(valor):
        if pd.isna(valor):
            return valor
        texto_sem_acento = unicodedata.normalize("NFKD", str(valor).strip().lower())
        return "".join(caractere for caractere in texto_sem_acento if not unicodedata.combining(caractere))

    return serie_regional.apply(_normalizar)

def extrair_ano_da_coluna(nome_da_coluna):
    ano_em_texto, separador, _ = nome_da_coluna.partition("_")
    if separador and ano_em_texto.isdigit():
        return int(ano_em_texto)

    return None


def selecionar_colunas_de_valor(tabela, ano_inicial, ano_final, colunas_a_ignorar, somente_total=False):
    '''
    somente_total=True restringe a seleção às colunas terminadas em
    SUFIXO_COLUNA_TOTAL ("<ano>_TOTAL") -- uma única coluna de valor
    por ano. Necessário para variáveis "simples" (Casos, Mortalidade,
    Mamografia, Hospitais) cujas bases de origem são segmentadas por
    faixa etária: sem esse filtro, cada ano teria uma coluna
    "<ano>_<faixa>" por faixa ALÉM de "<ano>_TOTAL", todas passando no
    filtro de ano abaixo -- múltiplas colunas de valor para o mesmo
    ano. O padrão (False) preserva o comportamento anterior e é o que
    as variáveis categóricas continuam usando (elas precisam das
    colunas de categoria, não só do total).
    '''
    colunas_selecionadas = []
    for coluna in tabela.columns:
        if coluna in colunas_a_ignorar:
            continue

        if coluna.endswith(SUFIXO_COLUNA_TAXA) or coluna.endswith(SUFIXO_COLUNA_POPULACAO_AGREGADA):
            continue
        if somente_total and not coluna.endswith(SUFIXO_COLUNA_TOTAL):
            continue
        ano = extrair_ano_da_coluna(coluna)
        if ano is not None and ano_inicial <= ano <= ano_final:
            colunas_selecionadas.append(coluna)
    return colunas_selecionadas


def verificar_anos_unicos(colunas_de_valor, nome_da_variavel=""):
    '''
    Levanta ValueError se colunas_de_valor tiver mais de uma coluna
    para o mesmo ano -- sintoma de esquecer somente_total=True numa
    variável simples (base segmentada por faixa etária/categoria).
    Gráficos de barra+linha não detectam isso sozinhos: só produzem
    barras sobrepostas e uma linha ligando pontos fora de ordem, sem
    erro nenhum -- por isso a checagem explícita.
    '''
    anos = [extrair_ano_da_coluna(coluna) for coluna in colunas_de_valor]
    anos_repetidos = sorted({ano for ano in anos if ano is not None and anos.count(ano) > 1})
    if anos_repetidos:
        raise ValueError(
            f"{nome_da_variavel or 'Variável'}: ano(s) repetido(s) {anos_repetidos} em "
            f"colunas_de_valor -- cada ano deve corresponder a uma única coluna de "
            f"valor. Colunas selecionadas: {colunas_de_valor}. Se a base de origem é "
            f"segmentada por categoria, use somente_total=True em "
            f"selecionar_colunas_de_valor."
        )


def filtrar_populacao_valida_por_municipio(tabela_populacao, colunas_de_populacao):
    mascara_invalida = (
        (tabela_populacao[colunas_de_populacao] < POPULACAO_MINIMA_VALIDA)
        | tabela_populacao[colunas_de_populacao].isna()
    )
    total_celulas_invalidas = int(mascara_invalida.values.sum())
    if total_celulas_invalidas > 0:
        municipios_afetados = int(mascara_invalida.any(axis=1).sum())
        registrar_log(
            f"ATENÇÃO: {municipios_afetados} município(s) sem população válida (< "
            f"{POPULACAO_MINIMA_VALIDA}) em ao menos um ano do período -- excluído(s) da "
            f"soma por regional nesses anos."
        )
    tabela_filtrada = tabela_populacao.copy()
    tabela_filtrada[colunas_de_populacao] = tabela_filtrada[colunas_de_populacao].where(~mascara_invalida)
    return tabela_filtrada


def carregar_populacao_por_regional():
    '''
    Carrega a população de referência por município (já interpolada/
    extrapolada) e agrega por Regional de Saúde e ano, excluindo
    municípios sem população válida (< POPULACAO_MINIMA_VALIDA) em cada
    ano -- o mesmo critério usado por calculo_taxa.ipynb para somar a
    população por regional antes de calcular a taxa.

    Devolve um DataFrame indexado por REGIONAL DE SAÚDE, com uma
    coluna "<ano>_TOTAL" por ano disponível -- usado pelos notebooks de
    gráfico para recalcular a população agregada sem depender de uma
    coluna de população no CSV de taxa (que não guarda mais isso).
    '''
    tabela_populacao = pd.read_csv(CAMINHO_POPULACAO)
    tabela_populacao[COLUNA_CODIGO_IBGE] = normalizar_codigo_ibge(tabela_populacao[COLUNA_CODIGO_IBGE])
    tabela_populacao[COLUNA_REGIONAL] = normalizar_regional(tabela_populacao[COLUNA_REGIONAL])

    colunas_de_populacao = [c for c in tabela_populacao.columns if c.endswith(SUFIXO_COLUNA_TOTAL)]
    tabela_populacao_filtrada = filtrar_populacao_valida_por_municipio(tabela_populacao, colunas_de_populacao)

    return (
        tabela_populacao_filtrada.groupby(COLUNA_REGIONAL)[colunas_de_populacao]
        .sum(min_count=1)
    )


# Especificações de cada variável -- caminho de entrada, período e nome do arquivo de saída da taxa. 

ESPECIFICACOES_VARIAVEIS = {
    "Casos": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Casos" / "tabela_casos_por_ano_de_diagnóstico.csv",
        "ANO_INICIAL": 1985,
        "ANO_FINAL": 2023,
        "NOME_ARQUIVO_SAIDA_TAXA": "tabela_casos_por_ano_de_diagnóstico_taxa.csv",
    },
    "Mortalidade": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Mortalidade" / "tabela_mortes_por_faixa_etária.csv",
        "ANO_INICIAL": 1979,
        "ANO_FINAL": 2024,
        "NOME_ARQUIVO_SAIDA_TAXA": "tabela_mortes_por_faixa_etária_taxa.csv",
    },
    "Mamografia": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Mamografias" / "tabela_mamografias_por_faixa_etária.csv",
        "ANO_INICIAL": 2013,
        "ANO_FINAL": 2025,
        "NOME_ARQUIVO_SAIDA_TAXA": "tabela_mamografias_por_faixa_etária_taxa.csv",
    },
    "Hospitais": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Hospitais" / "tabela_hospitais_habilitados.csv",
        "ANO_INICIAL": 2023,
        "ANO_FINAL": 2023,
        "NOME_ARQUIVO_SAIDA_TAXA": "tabela_hospitais_habilitados_taxa.csv",
    },
}

ESPECIFICACOES_VARIAVEIS_CATEGORICAS = {
    "Casos por Escolaridade": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Casos" / "tabela_casos_por_escolaridade.csv",
        "ANO_INICIAL": 1998,
        "ANO_FINAL": 2023,
        "NOME_ARQUIVO_SAIDA_TAXA": "tabela_casos_por_escolaridade_taxa.csv",
    },
    "Casos por Raça e Cor": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Casos" / "tabela_casos_por_raça_e_cor.csv",
        "ANO_INICIAL": 1998,
        "ANO_FINAL": 2023,
        "NOME_ARQUIVO_SAIDA_TAXA": "tabela_casos_por_raça_e_cor_taxa.csv",
    },
    "Casos por Faixa Etária": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Casos" / "tabela_casos_por_faixa_etária.csv",
        "ANO_INICIAL": 1985,
        "ANO_FINAL": 2023,
        "NOME_ARQUIVO_SAIDA_TAXA": "tabela_casos_por_faixa_etária_taxa.csv",
    },
}

# Sufixo de coluna de cada variável dentro do CSV agregado estadual por
# ano (NOME_ARQUIVO_AGREGADO_CATEGORICO_POR_ANO, gerado por
# calculo_taxa.ipynb) -- todas as variáveis (simples e categóricas)
# compartilham um único arquivo, formato "<ano>_<categoria>_<SUFIXO>"
# (ex.: "1979_0-9_MORTES", "1985_TOTAL_CASOS"). "Casos por Escolaridade"
# e "Casos por Raça e Cor" precisam de um sufixo próprio (em vez do
# "CASOS" comum às demais quebras de Casos) porque as duas têm uma
# categoria com o mesmo nome ("SEM INFORMAÇÃO") -- sem isso colidiriam
# na mesma coluna.
SUFIXO_VARIAVEL_ESTADUAL = {
    "Casos": "CASOS",
    "Mortalidade": "MORTES",
    "Mamografia": "MAMOGRAFIAS",
    "Hospitais": "HOSPITAIS",
    "Casos por Escolaridade": "CASOS_ESCOLARIDADE",
    "Casos por Raça e Cor": "CASOS_RACA_COR",
    "Casos por Faixa Etária": "CASOS",
}

NOME_ARQUIVO_AGREGADO_CATEGORICO_POR_ANO = "tabela_regional_agregada_por_ano.csv"
