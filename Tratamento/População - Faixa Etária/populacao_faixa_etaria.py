from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_DIR = PROJECT_ROOT / "Variáveis" / "População - Faixa Etária"
ARQUIVO_SAIDA = Path(__file__).with_name("tabela_populacao_faixa_etaria.csv")

KEY_COLUMNS = ["Sigla", "Código", "Município"]
AGE_LABEL_ORDER = [
    "0 a 9",
    "10 a 19",
    "20 a 29",
    "30 a 39",
    "40 a 49",
    "50 a 59",
    "60 a 69",
    "70 anos ou mais",
]

FAIXA_PADRAO = {
    "0 a 9": "0-9",
    "10 a 19": "10-19",
    "20 a 29": "20-29",
    "30 a 39": "30-39",
    "40 a 49": "40-49",
    "50 a 59": "50-59",
    "60 a 69": "60-69",
    "70 anos ou mais": "70 ou mais",
}

def normalizar_texto(texto: str) -> str:
    texto = "" if pd.isna(texto) else str(texto).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return texto.lower()

def limpar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(coluna).strip() for coluna in df.columns]
    return df.loc[:, ~df.columns.str.match(r"^Unnamed")].copy()

def ler_arquivo_csv(caminho: Path) -> pd.DataFrame:
    return limpar_colunas(pd.read_csv(caminho, sep=";", encoding="utf-8"))

def extrair_ano_e_parte(caminho: Path) -> tuple[int, int]:
    match = re.fullmatch(r"([12])-(\d{4})\.csv", caminho.name)
    if not match:
        raise ValueError(f"Nome de arquivo inesperado: {caminho.name}")
    parte = int(match.group(1))
    ano = int(match.group(2))
    return ano, parte

def faixa_decenal(nome_coluna: str) -> str | None:
    intervalo = re.search(r"pessoas (\d+) a (\d+) anos", nome_coluna)
    if intervalo:
        inicio = int(intervalo.group(1))
        inicio_decada = (inicio // 10) * 10
        fim_decada = inicio_decada + 9
        return f"{inicio_decada} a {fim_decada}"

    if re.search(r"pessoas 70 anos ou mais", nome_coluna):
        return "70 anos ou mais"

    return None

def nome_coluna_saida(ano: int, faixa: str) -> str:
    return f"{ano}_{FAIXA_PADRAO[faixa]}"

def montar_tabela_ano(ano: int, arquivos_do_ano: dict[int, Path]) -> pd.DataFrame:
    partes_faltantes = {1, 2} - set(arquivos_do_ano)
    if partes_faltantes:
        raise ValueError(f"Faltam arquivos do ano {ano}: {sorted(partes_faltantes)}")

    df_1 = ler_arquivo_csv(arquivos_do_ano[1])
    df_2 = ler_arquivo_csv(arquivos_do_ano[2])

    colunas_df_2 = [col for col in df_2.columns if col not in KEY_COLUMNS]
    combinado = df_1.merge(df_2[KEY_COLUMNS + colunas_df_2], on=KEY_COLUMNS, how="inner")

    resultado_ano = combinado[KEY_COLUMNS].copy()
    for faixa in AGE_LABEL_ORDER:
        resultado_ano[faixa] = 0

    colunas_populacao = [col for col in combinado.columns if col not in KEY_COLUMNS]
    for coluna in colunas_populacao:
        faixa = faixa_decenal(coluna)
        if faixa is None:
            continue

        resultado_ano[faixa] = (
            resultado_ano[faixa]
            + pd.to_numeric(combinado[coluna], errors="coerce").fillna(0)
        )

    resultado_ano = resultado_ano.rename(
        columns={faixa: nome_coluna_saida(ano, faixa) for faixa in AGE_LABEL_ORDER}
    )
    return resultado_ano


def main() -> None:
    source_files = sorted(SOURCE_DIR.glob("*.csv"))
    if not source_files:
        raise FileNotFoundError(f"Nenhum arquivo CSV encontrado em: {SOURCE_DIR}")

    arquivos_por_ano: dict[int, dict[int, Path]] = {}
    for arquivo in source_files:
        ano, parte = extrair_ano_e_parte(arquivo)
        arquivos_por_ano.setdefault(ano, {})[parte] = arquivo

    tabelas_por_ano = [
        montar_tabela_ano(ano, arquivos_por_ano[ano])
        for ano in sorted(arquivos_por_ano)
    ]

    tabela_final = tabelas_por_ano[0].copy()
    for tabela_ano in tabelas_por_ano[1:]:
        colunas_novas = [col for col in tabela_ano.columns if col not in KEY_COLUMNS]
        tabela_final = tabela_final.merge(
            tabela_ano[KEY_COLUMNS + colunas_novas],
            on=KEY_COLUMNS,
            how="outer",
        )

    ordem_colunas = KEY_COLUMNS + [
        nome_coluna_saida(ano, faixa)
        for ano in sorted(arquivos_por_ano)
        for faixa in AGE_LABEL_ORDER
    ]

    tabela_final = tabela_final[ordem_colunas].sort_values("Município").reset_index(drop=True)
    for coluna in tabela_final.columns:
        if coluna not in KEY_COLUMNS:
            tabela_final[coluna] = tabela_final[coluna].fillna(0).astype(int)

    colunas_numericas = [coluna for coluna in tabela_final.columns if coluna not in KEY_COLUMNS]
    tabela_final["TOTAL_POPULACAO"] = tabela_final[colunas_numericas].sum(axis=1).astype(int)

    tabela_final = tabela_final.drop(columns=["Sigla", "Código"])
    tabela_final["Município"] = tabela_final["Município"].map(normalizar_texto)

    tabela_final.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")
    print(f"Pasta de entrada: {SOURCE_DIR}")
    print(f"CSV gerado em: {ARQUIVO_SAIDA}")
    print(f"Total de linhas: {len(tabela_final)}")


if __name__ == "__main__":
    main()
