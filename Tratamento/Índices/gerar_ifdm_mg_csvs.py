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
