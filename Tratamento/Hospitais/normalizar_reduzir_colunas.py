# pyright: reportUnknownMemberType=false

import unicodedata
from pathlib import Path

import pandas as pd

ENTRADA = Path("/home/anna/tcc/Tratamento/Hospitais/hospitais_de_mg.csv")
SAIDA = Path("/home/anna/tcc/Tratamento/Hospitais/hospitais_de_mg_normalizado.csv")
ARQUIVO_MUNICIPIOS = Path(
    "/home/anna/tcc/Tratamento/Municípios/municipios_regionais_normalizados.csv"
)


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


def normalizar_chave_municipio(valor: object) -> object:
    if not isinstance(valor, str):
        return valor

    texto = normalizar_municipio(valor)
    texto = " ".join(str(texto).replace(".", " ").replace("-", " ").split())

    aliases = {
        "gov valadares": "governador valadares",
        "sao joao del rei": "sao joao del rei",
    }
    return aliases.get(texto, texto)


def carregar_mapa_codigo_municipio() -> dict[str, int]:
    df_municipios = pd.read_csv(ARQUIVO_MUNICIPIOS, encoding="utf-8-sig")

    colunas_obrigatorias = {"codigo_ibge", "municipio_normalizado"}
    faltantes = colunas_obrigatorias - set(df_municipios.columns)
    if faltantes:
        raise ValueError(
            f"Arquivo de municípios sem colunas obrigatórias: {sorted(faltantes)}"
        )

    df_municipios["municipio_chave"] = df_municipios["municipio_normalizado"].map(
        normalizar_chave_municipio
    )
    df_municipios = df_municipios.dropna(subset=["municipio_chave", "codigo_ibge"])

    return dict(
        zip(
            df_municipios["municipio_chave"].astype(str),
            df_municipios["codigo_ibge"].astype(int),
            strict=False,
        )
    )


def main() -> None:
    df = pd.read_csv(ENTRADA, encoding="utf-8-sig")
    mapa_codigo = carregar_mapa_codigo_municipio()

    colunas_existentes = [c for c in COLUNAS_REMOVER if c in df.columns]
    df = df.drop(columns=colunas_existentes)

    df["MUNICÍPIO"] = df["MUNICÍPIO"].map(normalizar_municipio)
    df["municipio_chave"] = df["MUNICÍPIO"].map(normalizar_chave_municipio)
    df["CÓDIGO"] = df["municipio_chave"].map(mapa_codigo)

    municipios_sem_codigo = sorted(
        {
            str(municipio)
            for municipio in df.loc[df["CÓDIGO"].isna(), "MUNICÍPIO"].dropna().unique().tolist()
        }
    )

    if municipios_sem_codigo:
        print("Municípios sem correspondência de código:")
        for municipio in municipios_sem_codigo:
            print(f"- {municipio}")
    else:
        print("Todos os municípios tiveram código encontrado.")

    df["CÓDIGO"] = pd.to_numeric(df["CÓDIGO"], errors="coerce").astype("Int64")
    df = df.drop(columns=["municipio_chave"])

    cols = ["MUNICÍPIO", "CÓDIGO"] + [
        c for c in df.columns if c not in {"MUNICÍPIO", "CÓDIGO"}
    ]
    df = df[cols]

    df.to_csv(SAIDA, index=False, encoding="utf-8-sig")

    print(f"Entrada:  {ENTRADA}")
    print(f"Saída:    {SAIDA}")
    print(f"Colunas finais: {list(df.columns)}")
    print(f"Total de linhas: {len(df)}")


if __name__ == "__main__":
    main()
