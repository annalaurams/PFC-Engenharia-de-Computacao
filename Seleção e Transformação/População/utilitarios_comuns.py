import unicodedata
from pathlib import Path

import pandas as pd

COLUNA_MUNICIPIO = "MUNICÍPIO"
COLUNA_CODIGO_IBGE = "CÓDIGO IBGE"
COLUNA_REGIONAL = "REGIONAL DE SAÚDE"
COLUNA_ANO = "ANO"
COLUNA_TIPO = "TIPO"

SUFIXO_COLUNA_TOTAL = "_TOTAL"
SUFIXO_COLUNA_TAXA = "_TAXA"
SUFIXO_COLUNA_POPULACAO_AGREGADA = "_POPULACAO"
MULTIPLICADOR_TAXA = 100_000

POPULACAO_MINIMA_VALIDA = 1

# Faixas etárias decenais comuns às bases de eventos e à de população.
FAIXAS_ETARIAS_PADRAO = ("0-9", "10-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70 OU MAIS")

PASTA_POPULACAO = Path(__file__).resolve().parent
PASTA_SELECAO_TRANSFORMACAO = PASTA_POPULACAO.parent

CAMINHO_POPULACAO = PASTA_POPULACAO / "Interpolação e Extrapolação" / "populacao_interpolacao_extrapolacao.csv"


def registrar_log(mensagem):
    print(f"[LOG] {mensagem}")


def normalizar_codigo_ibge(serie_codigo_ibge):
    """Converte o código IBGE para inteiro anulável."""
    return pd.to_numeric(
        serie_codigo_ibge.astype(str).str.strip(),
        errors="coerce",
    ).astype("Int64")


def normalizar_regional(serie_regional):
    """Normaliza o nome da Regional (minúsculo e sem acentos)."""

    def _normalizar(valor):
        if pd.isna(valor):
            return valor
        texto_sem_acento = unicodedata.normalize("NFKD", str(valor).strip().lower())
        return "".join(caractere for caractere in texto_sem_acento if not unicodedata.combining(caractere))

    return serie_regional.apply(_normalizar)


def extrair_ano_da_coluna(nome_da_coluna):
    """Extrai o ano do prefixo "<ano>_" da coluna; None se não houver."""
    ano_em_texto, separador, _ = nome_da_coluna.partition("_")
    if separador and ano_em_texto.isdigit():
        return int(ano_em_texto)

    return None


def selecionar_colunas_de_valor(tabela, ano_inicial, ano_final, colunas_a_ignorar, somente_total=False):
    """Seleciona as colunas "<ano>_..." do período; somente_total=True mantém só "<ano>_TOTAL"."""
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
    """Levanta ValueError se houver mais de uma coluna de valor para o mesmo ano."""
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
    """Anula a população inválida (ausente ou abaixo do mínimo) para ela não entrar na soma por Regional."""
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


# Especificações de cada variável: entrada, período e arquivo de saída da taxa

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

# Sufixo de cada variável no CSV agregado estadual por ano (formato "<ano>_<categoria>_<SUFIXO>")
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
