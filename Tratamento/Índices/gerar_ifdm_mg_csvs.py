from __future__ import annotations

from pathlib import Path
import re
import unicodedata

import pandas as pd


BASE_DIR = Path("/home/anna/tcc/Variáveis/Índices IFDM")
BASE_XLSX = BASE_DIR / "Serie-Historica-IFDM-2013-a-2023.xlsx"
FALLBACK_XLSX = BASE_DIR / "Dados" / "Serie-Historica-IFDM-2013-a-2023.xlsx"
OUTPUT_DIR = Path("/home/anna/tcc/Tratamento/Índices")


SHEETS_TO_FILES = {
    "IFDM Geral": "IFDM-Geral-MG.csv",
    "IFDM Educação": "IFDM-Educacao-MG.csv",
    "IFDM Saúde": "IFDM-Saude-MG.csv",
    "IFDM Emprego&Renda": "IFDM-Emprego-Renda-MG.csv",
}

INDICE_POR_ARQUIVO = {
    "IFDM-Geral-MG.csv": "geral",
    "IFDM-Educacao-MG.csv": "educacao",
    "IFDM-Saude-MG.csv": "saude",
    "IFDM-Emprego-Renda-MG.csv": "emprego_renda",
}


def normalizar_municipio(valor: object) -> str:
    texto = str(valor).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = re.sub(r"\s+", " ", texto).strip().lower()
    return texto


def ordenar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    colunas_ranking = [col for col in df.columns if "Ranking" in col]
    colunas_demais = [
        col for col in df.columns if col not in {"Municípios", "COD_MUNIC", *colunas_ranking}
    ]
    colunas_ordenadas = ["Municípios"]

    if "COD_MUNIC" in df.columns:
        colunas_ordenadas.append("COD_MUNIC")

    colunas_ordenadas.extend(colunas_ranking)
    colunas_ordenadas.extend(colunas_demais)
    return df[colunas_ordenadas]


def _renomear_colunas_indice(df: pd.DataFrame, indice: str) -> pd.DataFrame:
    colunas_base = {"Municípios", "COD_MUNIC"}
    mapeamento = {
        coluna: (coluna if coluna in colunas_base else f"{coluna} [{indice}]")
        for coluna in df.columns
    }
    return df.rename(columns=mapeamento)


def gerar_tabela_ifdm_unificada(
    output_dir: Path = OUTPUT_DIR,
    output_name: str = "IFDM-Unificado-MG.csv",
) -> Path:
    base: pd.DataFrame | None = None

    for arquivo_csv, indice in INDICE_POR_ARQUIVO.items():
        caminho = output_dir / arquivo_csv
        if not caminho.exists():
            continue

        df = pd.read_csv(caminho)
        for coluna in ("Municípios", "COD_MUNIC"):
            if coluna not in df.columns:
                raise ValueError(
                    f"Arquivo '{arquivo_csv}' não possui a coluna obrigatória '{coluna}'."
                )

        df = _renomear_colunas_indice(df, indice=indice)

        if base is None:
            base = df.copy()
        else:
            base = base.merge(df, on=["Municípios", "COD_MUNIC"], how="outer")

    if base is None:
        raise FileNotFoundError(
            "Nenhum CSV de índice encontrado para unificação em "
            f"{output_dir}. Arquivos esperados: {list(INDICE_POR_ARQUIVO)}"
        )

    colunas_base = ["Municípios", "COD_MUNIC"]
    colunas_restantes = [col for col in base.columns if col not in colunas_base]
    base = base[colunas_base + colunas_restantes]
    base = base.sort_values(by=["Municípios", "COD_MUNIC"], ascending=[True, True]).reset_index(drop=True)

    out_path = output_dir / output_name
    base.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(
        f"[OK] {output_name} | linhas: {len(base)} | "
        f"colunas: {len(base.columns)}"
    )
    return out_path


def exportar_ifdm_mg(base_xlsx: Path = BASE_XLSX, output_dir: Path = OUTPUT_DIR) -> None:
    if not base_xlsx.exists() and FALLBACK_XLSX.exists():
        base_xlsx = FALLBACK_XLSX

    if not base_xlsx.exists():
        raise FileNotFoundError(
            "Arquivo base não encontrado. Locais verificados: "
            f"{BASE_XLSX} e {FALLBACK_XLSX}"
        )

    output_dir.mkdir(parents=True, exist_ok=True)

    for sheet_name, output_name in SHEETS_TO_FILES.items():
        df = pd.read_excel(base_xlsx, sheet_name=sheet_name)  # pyright: ignore[reportUnknownMemberType]

        if "SIGLA_UF" not in df.columns:
            raise ValueError(
                f"A aba '{sheet_name}' não possui a coluna 'SIGLA_UF'."
            )

        if "NOME_MUNIC" not in df.columns:
            raise ValueError(
                f"A aba '{sheet_name}' não possui a coluna 'NOME_MUNIC'."
            )

        df_mg = df[df["SIGLA_UF"].astype(str).str.upper().eq("MG")].copy()
        df_mg = df_mg.drop(columns=["SIGLA_UF"])
        df_mg = df_mg.rename(columns={"NOME_MUNIC": "Municípios"})
        df_mg["Municípios"] = df_mg["Municípios"].apply(normalizar_municipio)
        df_mg = ordenar_colunas(df_mg)

        out_path = output_dir / output_name
        df_mg.to_csv(out_path, index=False, encoding="utf-8-sig")

        print(
            f"[OK] {output_name} | linhas: {len(df_mg)} | "
            f"colunas: {len(df_mg.columns)}"
        )


if __name__ == "__main__":
    exportar_ifdm_mg()
    gerar_tabela_ifdm_unificada()
