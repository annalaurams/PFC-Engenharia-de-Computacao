from __future__ import annotations

from pathlib import Path
import unicodedata

import pandas as pd


BASE_CASOS = Path("/home/anna/tcc/Tratamento/Casos")
ARQUIVO_MUNICIPIOS = Path(
    "/home/anna/tcc/Tratamento/Municípios/municipios_regionais_normalizados.csv"
)
ARQUIVOS_CASOS = [
    "resultado_ano_diagnostico_casos.csv",
    "resultado_escolaridade_casos.csv",
    "resultado_faixa_etaria_casos.csv",
    "resultado_raca_cor_casos.csv",
    "resultado_casos_unificado.csv",
]


def remover_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def normalizar_municipio(valor: object) -> object:
    if not isinstance(valor, str):
        return valor

    texto = remover_acentos(valor.strip()).lower()
    texto = " ".join(texto.replace(".", " ").replace("-", " ").split())

    aliases = {
        "gov valadares": "governador valadares",
        "sao joao del rei": "sao joao del rei",
        "dona eusebia": "dona euzebia",
        "sao thome das letras": "sao tome das letras",
    }
    return aliases.get(texto, texto)


def carregar_mapa_codigos() -> dict[str, int]:
    df_municipios = pd.read_csv(ARQUIVO_MUNICIPIOS, encoding="utf-8-sig")
    colunas_obrigatorias = {"codigo_ibge", "municipio_normalizado"}

    faltantes = colunas_obrigatorias - set(df_municipios.columns)
    if faltantes:
        raise ValueError(
            f"Arquivo de municípios sem colunas obrigatórias: {sorted(faltantes)}"
        )

    df_municipios = df_municipios.dropna(subset=["codigo_ibge", "municipio_normalizado"]).copy()
    df_municipios["chave"] = df_municipios["municipio_normalizado"].map(normalizar_municipio)

    return dict(
        zip(
            df_municipios["chave"].astype(str),
            df_municipios["codigo_ibge"].astype(int),
            strict=False,
        )
    )


def localizar_coluna_municipio(df: pd.DataFrame) -> str:
    candidatas = ["MUNICÍPIO", "MUNICIPIO", "Município", "municipio", "Municípios", "MUNICÍPIOS"]
    for coluna in candidatas:
        if coluna in df.columns:
            return coluna
    raise ValueError("Nenhuma coluna de município encontrada no arquivo.")


def processar_arquivo(caminho_csv: Path, mapa_codigos: dict[str, int]) -> list[str]:
    df = pd.read_csv(caminho_csv, encoding="utf-8-sig")
    df = df.copy()

    coluna_municipio_original = localizar_coluna_municipio(df)
    df = df.rename(columns={coluna_municipio_original: "MUNICÍPIO"})

    if "CÓDIGO" in df.columns:
        df = df.drop(columns=["CÓDIGO"])

    df["_chave_municipio"] = df["MUNICÍPIO"].map(normalizar_municipio)
    df["CÓDIGO"] = df["_chave_municipio"].map(mapa_codigos)
    df["CÓDIGO"] = pd.to_numeric(df["CÓDIGO"], errors="coerce").astype("Int64")

    sem_correspondencia = sorted(
        {
            str(municipio)
            for municipio in df.loc[df["CÓDIGO"].isna(), "MUNICÍPIO"].dropna().unique().tolist()
        }
    )

    colunas_reordenadas = ["MUNICÍPIO", "CÓDIGO"] + [
        c for c in df.columns if c not in {"MUNICÍPIO", "CÓDIGO", "_chave_municipio"}
    ]
    df = df[colunas_reordenadas]

    df.to_csv(caminho_csv, index=False, encoding="utf-8-sig")
    return sem_correspondencia


def main() -> None:
    mapa_codigos = carregar_mapa_codigos()

    sem_correspondencia_total: dict[str, list[str]] = {}

    for nome_arquivo in ARQUIVOS_CASOS:
        caminho = BASE_CASOS / nome_arquivo
        if not caminho.exists():
            print(f"[AVISO] Arquivo não encontrado: {caminho}")
            continue

        sem_correspondencia = processar_arquivo(caminho, mapa_codigos)
        if sem_correspondencia:
            sem_correspondencia_total[nome_arquivo] = sem_correspondencia

        print(f"[OK] Atualizado: {nome_arquivo}")

    if sem_correspondencia_total:
        print("\nMunicípios sem correspondência de código:")
        for nome_arquivo, municipios in sem_correspondencia_total.items():
            print(f"- {nome_arquivo}")
            for municipio in municipios:
                print(f"  • {municipio}")
    else:
        print("\nTodos os municípios tiveram código encontrado em todos os arquivos processados.")


if __name__ == "__main__":
    main()
