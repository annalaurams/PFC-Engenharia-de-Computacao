# pyright: reportUnknownMemberType=false

import unicodedata
from pathlib import Path

import pandas as pd

ENTRADA = Path("/home/anna/tcc/Tratamento/Hospitais/hospitais_de_mg.csv")
SAIDA = Path("/home/anna/tcc/Tratamento/Hospitais/hospitais_de_mg_normalizado.csv")


COLUNAS_REMOVER = [
    "UF",
    "CNES",
    "CÓDIGO",
    "CNPJ",
    "GESTÃO",
    "TIPO DE HABILITAÇÃO (CÓDIGO DO CNES)",
    "TIPO DE HABILITAÇÃO (Descrição)",
    "IBGE",
    "MACRORREGIÃO DE SAÚDE",
]


def remover_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def normalizar_municipio(valor: object) -> object:
    if isinstance(valor, str):
        return remover_acentos(valor.strip()).lower()
    return valor


def main() -> None:
    df = pd.read_csv(ENTRADA, encoding="utf-8-sig")

    colunas_existentes = [c for c in COLUNAS_REMOVER if c in df.columns]
    df = df.drop(columns=colunas_existentes)

    df["MUNICÍPIO"] = df["MUNICÍPIO"].map(normalizar_municipio)

    cols = ["MUNICÍPIO"] + [c for c in df.columns if c != "MUNICÍPIO"]
    df = df[cols]

    df.to_csv(SAIDA, index=False, encoding="utf-8-sig")

    print(f"Entrada:  {ENTRADA}")
    print(f"Saída:    {SAIDA}")
    print(f"Colunas finais: {list(df.columns)}")
    print(f"Total de linhas: {len(df)}")


if __name__ == "__main__":
    main()
