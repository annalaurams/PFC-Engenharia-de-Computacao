# pyright: reportUnknownMemberType=false

import re
import unicodedata
from pathlib import Path

import pandas as pd

ARQUIVO_ENTRADA = Path("/home/anna/tcc/Variáveis/Socioeconômica/tabela_raca_cor.csv")
ARQUIVO_MUNICIPIOS = Path("/home/anna/tcc/Tratamento/Municípios/tabela_municipios_regionais.csv")

PASTA_SAIDA = Path("/home/anna/tcc/Tratamento/Socioeconômico")
ARQUIVO_SAIDA = PASTA_SAIDA / "tabela_raca_cor.csv"


def remover_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def normalizar_municipio(valor: object) -> object:
    if not isinstance(valor, str):
        return valor

    txt = valor.strip()
    # remove sufixos tipo "(MG)" e variações
    txt = re.sub(r"\s*\(\s*mg\s*\)\s*$", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\s*-\s*mg\s*$", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\s+mg\s*$", "", txt, flags=re.IGNORECASE)

    txt = remover_acentos(txt).lower()
    # sem pontuação
    txt = re.sub(r"[^0-9a-z]+", " ", txt)
    txt = " ".join(txt.split())

    aliases = {
        "barao do monte alto": "barao de monte alto",
    }
    return aliases.get(txt, txt)


def carregar_mapa_codigo_ibge() -> dict[str, int]:
    if not ARQUIVO_MUNICIPIOS.exists():
        raise FileNotFoundError(f"Arquivo de municípios não encontrado: {ARQUIVO_MUNICIPIOS}")

    ref = pd.read_csv(ARQUIVO_MUNICIPIOS, encoding="utf-8")
    obrig = {"codigo_ibge", "municipio_normalizado"}
    falt = obrig - set(ref.columns)
    if falt:
        raise ValueError(f"Arquivo de municípios sem colunas obrigatórias: {sorted(falt)}")

    ref = ref.dropna(subset=["codigo_ibge", "municipio_normalizado"]).copy()
    ref["municipio_normalizado"] = ref["municipio_normalizado"].astype(str).map(normalizar_municipio)
    ref["codigo_ibge"] = pd.to_numeric(ref["codigo_ibge"], errors="coerce")
    ref = ref.dropna(subset=["codigo_ibge", "municipio_normalizado"])

    ref = ref.drop_duplicates(subset=["municipio_normalizado"], keep="first")
    return dict(zip(ref["municipio_normalizado"].astype(str), ref["codigo_ibge"].astype(int), strict=False))


def ler_base() -> pd.DataFrame:
    if not ARQUIVO_ENTRADA.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {ARQUIVO_ENTRADA}")

    # Até a linha 5 o arquivo contém metadados/cabeçalhos não tabulares.
    # A linha 6 contém o cabeçalho real com colunas duplicadas (Total/Branca/... para Total e Mulheres).
    df = pd.read_csv(
        ARQUIVO_ENTRADA,
        sep=";",
        header=0,
        skiprows=5,
        encoding="utf-8",
        quotechar='"',
        dtype=str,
        engine="python",
    )

    col_mun = "Unidade da Federação e Município"
    col_classe = "Classes de rendimento nominal mensal domiciliar per capita"
    if col_mun not in df.columns or col_classe not in df.columns:
        raise ValueError("Formato inesperado: colunas principais não encontradas após pular cabeçalho")

    # Mantém somente a linha de classe Total.
    df = df.dropna(subset=[col_mun, col_classe]).copy()
    df[col_mun] = df[col_mun].astype(str).str.strip()
    df[col_classe] = df[col_classe].astype(str).str.strip()

    df = df[df[col_classe].str.lower() == "total"].copy()

    # Remove agregado do estado.
    df = df[df[col_mun].str.lower() != "minas gerais"].copy()

    # Mantém somente municípios (no arquivo, vêm como "Nome (MG)").
    df = df[df[col_mun].str.contains(r"\(\s*mg\s*\)\s*$", case=False, regex=True, na=False)].copy()

    df["Municípios"] = df[col_mun].map(normalizar_municipio)

    return df


def para_inteiro(serie: pd.Series) -> pd.Series:
    s = serie.fillna("0").astype(str).str.strip()
    s = s.replace({"-": "0", "": "0"})
    s = s.str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
    return pd.to_numeric(s, errors="coerce").fillna(0).astype(int)


def gerar_tabela() -> pd.DataFrame:
    df = ler_base()

    # Colunas femininas vêm como as duplicatas com sufixo ".1" (mangle de pandas)
    # Ex.: Total.1, Branca.1, Preta.1, Amarela.1, Parda.1, Indígena.1
    col_total_mulheres = "Total.1"
    col_branca_mulheres = "Branca.1"
    col_amarela_mulheres = "Amarela.1"
    col_parda_mulheres = "Parda.1"
    col_indigena_mulheres = "Indígena.1"

    falt = [
        c
        for c in [
            col_total_mulheres,
            col_branca_mulheres,
            col_amarela_mulheres,
            col_parda_mulheres,
            col_indigena_mulheres,
        ]
        if c not in df.columns
    ]
    if falt:
        raise ValueError(f"Formato inesperado: colunas femininas não encontradas: {falt}")

    tabela = pd.DataFrame(
        {
            "Municípios": df["Municípios"],
            "Total mulheres": para_inteiro(df[col_total_mulheres]),
            "Parda mulheres": para_inteiro(df[col_parda_mulheres]),
            "Amarela mulheres": para_inteiro(df[col_amarela_mulheres]),
            "Branca mulheres": para_inteiro(df[col_branca_mulheres]),
            "Indígena mulheres": para_inteiro(df[col_indigena_mulheres]),
        }
    )

    # Agrega caso exista repetição (não esperado, mas deixa robusto)
    tabela = (
        tabela.groupby("Municípios", as_index=False)
        .agg(
            {
                "Total mulheres": "sum",
                "Parda mulheres": "sum",
                "Amarela mulheres": "sum",
                "Branca mulheres": "sum",
                "Indígena mulheres": "sum",
            }
        )
        .copy()
    )

    mapa_codigos = carregar_mapa_codigo_ibge()
    tabela["Código"] = tabela["Municípios"].map(mapa_codigos)

    sem = (
        tabela.loc[tabela["Código"].isna(), "Municípios"]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )
    if sem:
        print(f"[AVISO] Municípios sem código IBGE ({len(sem)}):")
        for m in sem[:50]:
            print(f"  - {m}")
        if len(sem) > 50:
            print("  ...")

    tabela["Código"] = pd.to_numeric(tabela["Código"], errors="coerce").astype("Int64")

    # Reordena
    tabela = tabela[[
        "Municípios",
        "Código",
        "Total mulheres",
        "Parda mulheres",
        "Amarela mulheres",
        "Branca mulheres",
        "Indígena mulheres",
    ]]

    tabela = tabela.sort_values(["Código", "Municípios"], na_position="last").reset_index(drop=True)
    return tabela


def main() -> None:
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

    tabela = gerar_tabela()
    tabela.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8")

    print(f"Arquivo gerado: {ARQUIVO_SAIDA}")
    print(f"Linhas: {len(tabela)}")


if __name__ == "__main__":
    main()
