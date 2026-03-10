"""Gera 4 arquivos CSV do IFDM apenas para Minas Gerais (SIGLA_UF == 'MG').

Fonte:
    /home/anna/tcc/variaveis/Índices IFDM/Serie-Historica-IFDM-2013-a-2023 (2).xlsx

Saída padrão:
    /home/anna/tcc/variaveis/Índices IFDM/Dados

Arquivos gerados:
    - IFDM-Geral-MG.csv
    - IFDM-Educacao-MG.csv
    - IFDM-Saude-MG.csv
    - IFDM-Emprego-Renda-MG.csv

Requisitos:
    pip install pandas openpyxl
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd


BASE_DIR = Path("/home/anna/tcc/variaveis/Índices IFDM")
BASE_XLSX = BASE_DIR / "Serie-Historica-IFDM-2013-a-2023 (2).xlsx"
FALLBACK_XLSX = BASE_DIR / "Dados" / "Serie-Historica-IFDM-2013-a-2023 (2).xlsx"
OUTPUT_DIR = Path("/home/anna/tcc/variaveis/Índices IFDM/Dados")


SHEETS_TO_FILES = {
    "IFDM Geral": "IFDM-Geral-MG.csv",
    "IFDM Educação": "IFDM-Educacao-MG.csv",
    "IFDM Saúde": "IFDM-Saude-MG.csv",
    "IFDM Emprego&Renda": "IFDM-Emprego-Renda-MG.csv",
}


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
        df = pd.read_excel(base_xlsx, sheet_name=sheet_name)

        if "SIGLA_UF" not in df.columns:
            raise ValueError(
                f"A aba '{sheet_name}' não possui a coluna 'SIGLA_UF'."
            )

        df_mg = df[df["SIGLA_UF"].astype(str).str.upper().eq("MG")].copy()

        out_path = output_dir / output_name
        df_mg.to_csv(out_path, index=False, encoding="utf-8-sig")

        print(
            f"[OK] {output_name} | linhas: {len(df_mg)} | "
            f"colunas: {len(df_mg.columns)}"
        )


if __name__ == "__main__":
    exportar_ifdm_mg()
