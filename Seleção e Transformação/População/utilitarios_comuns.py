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
COLUNA_TAXA = "TAXA_POR_100_MIL"

PREFIXO_COLUNA_TOTAL_ANO = "TOTAL_"
SUFIXO_COLUNA_TOTAL = "_TOTAL"
SUFIXO_COLUNA_QUANTIDADE = "_QUANTIDADE"
SUFIXO_COLUNA_POPULACAO_AGREGADA = "_POPULACAO"
MULTIPLICADOR_TAXA = 100_000

POPULACAO_MINIMA_VALIDA = 1

# Localizado a partir do próprio arquivo (não de um caminho absoluto
# fixo) -- funciona em qualquer clone do repositório, não só em
# /home/anna/tcc. PASTA_POPULACAO é a pasta onde este módulo mora
# (Seleção e Transformação/População); os demais caminhos compartilhados
# derivam dela.
PASTA_POPULACAO = Path(__file__).resolve().parent
PASTA_SELECAO_TRANSFORMACAO = PASTA_POPULACAO.parent

CAMINHO_POPULACAO = PASTA_POPULACAO / "populacao_interpolacao_extrapolacao.csv"


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
    if nome_da_coluna.startswith(PREFIXO_COLUNA_TOTAL_ANO):
        return int(nome_da_coluna.replace(PREFIXO_COLUNA_TOTAL_ANO, ""))

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

        if coluna.endswith(SUFIXO_COLUNA_QUANTIDADE) or coluna.endswith(SUFIXO_COLUNA_POPULACAO_AGREGADA):
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


# Especificações de cada variável -- caminho de entrada, período e
# nome do CSV de taxa gerado por calculo_taxa.ipynb. Fonte única: os
# notebooks de gráfico (grafico_taxa_por_ano.ipynb,
# grafico_taxa_por_regional.ipynb) leem NOME_ARQUIVO_SAIDA_TAXA daqui
# em vez de repetir os nomes de arquivo -- um nome trocado aqui não
# precisa ser caçado em cada notebook que consome o CSV.

ESPECIFICACOES_VARIAVEIS = {
    "Casos": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Casos" / "incidencia _ano_diagnostico.csv",
        "ANO_INICIAL": 1985,
        "ANO_FINAL": 2023,
        "NOME_ARQUIVO_SAIDA_TAXA": "casos_ano_diagnostico_taxa.csv",
    },
    "Mortalidade": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Mortalidade" / "tabela_mortalidade_faixa_etaria.csv",
        "ANO_INICIAL": 1979,
        "ANO_FINAL": 2024,
        "NOME_ARQUIVO_SAIDA_TAXA": "mortalidade_taxa.csv",
    },
    "Mamografia": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Mamografias" / "tabela_mamografia.csv",
        "ANO_INICIAL": 2013,
        "ANO_FINAL": 2025,
        "NOME_ARQUIVO_SAIDA_TAXA": "mamografia_taxa.csv",
    },
    "Hospitais": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Hospitais" / "tabela_hospitais_habilitados.csv",
        "ANO_INICIAL": 2023,
        "ANO_FINAL": 2023,
        "NOME_ARQUIVO_SAIDA_TAXA": "hospitais_taxa.csv",
    },
}

ESPECIFICACOES_VARIAVEIS_CATEGORICAS = {
    "Casos por Escolaridade": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Casos" / "incidencia _escolaridade.csv",
        "ANO_INICIAL": 1998,
        "ANO_FINAL": 2023,
        "NOME_ARQUIVO_SAIDA_TAXA": "casos_escolaridade_taxa.csv",
    },
    "Casos por Raça e Cor": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Casos" / "incidencia _raca_cor.csv",
        "ANO_INICIAL": 1998,
        "ANO_FINAL": 2023,
        "NOME_ARQUIVO_SAIDA_TAXA": "casos_raca_cor_taxa.csv",
    },
    "Casos por Faixa Etária": {
        "CAMINHO_ENTRADA": PASTA_SELECAO_TRANSFORMACAO / "Casos" / "incidencia _faixa_etaria.csv",
        "ANO_INICIAL": 1985,
        "ANO_FINAL": 2023,
        "NOME_ARQUIVO_SAIDA_TAXA": "casos_faixa_etaria_taxa.csv",
    },
}
