# pyright: reportUnknownMemberType=false

from pathlib import Path

import pandas as pd

DADOS_DIR = Path("/home/anna/tcc/Variáveis/Hospitais Habilitados")
SAIDA_DIR = Path("/home/anna/tcc/Tratamento/Hospitais")
SAIDA_DIR.mkdir(parents=True, exist_ok=True)


def carregar_dados() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df_onco = pd.read_excel(
        DADOS_DIR / "hospitais-habilitados-em-oncologia-abril-2025.xlsx",
        header=1,
    )  # pyright: ignore[reportUnknownMemberType]
    df_onco.columns = df_onco.columns.str.strip()
    cols_ffill_onco = [df_onco.columns[0], df_onco.columns[1], df_onco.columns[2]]
    df_onco[cols_ffill_onco] = df_onco[cols_ffill_onco].ffill()
    df_onco = df_onco.dropna(subset=[df_onco.columns[4]]).reset_index(drop=True)

    df_recon = pd.read_excel(
        DADOS_DIR / "hospitais-habilitados-em-reconstrucao-mamaria.xlsx",
        header=0,
    )  # pyright: ignore[reportUnknownMemberType]
    df_recon.columns = df_recon.columns.str.strip()

    df_sinc = pd.read_excel(
        DADOS_DIR / "tratamento-sincronico.xlsx",
        header=1,
    )  # pyright: ignore[reportUnknownMemberType]
    df_sinc.columns = df_sinc.columns.str.strip()
    df_sinc = df_sinc[df_sinc[df_sinc.columns[1]].notna()].reset_index(drop=True)

    return df_onco, df_recon, df_sinc


def filtrar_mg(
    df_onco: pd.DataFrame,
    df_recon: pd.DataFrame,
    df_sinc: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    col_uf_onco = df_onco.columns[0]
    df_onco_mg = df_onco[df_onco[col_uf_onco].astype(str).str.strip() == "MG"].reset_index(drop=True)

    col_uf_recon = df_recon.columns[0]
    df_recon_mg = df_recon[df_recon[col_uf_recon].astype(str).str.strip() == "MG"].reset_index(drop=True)

    col_uf_sinc = df_sinc.columns[1]
    df_sinc_mg = df_sinc[df_sinc[col_uf_sinc].astype(str).str.strip() == "MG"].reset_index(drop=True)

    return df_onco_mg, df_recon_mg, df_sinc_mg


def gerar_csv_unificado(
    df_onco_mg: pd.DataFrame,
    df_recon_mg: pd.DataFrame,
    df_sinc_mg: pd.DataFrame,
) -> Path:
    df_unificado = pd.concat(
        {
            "Oncologia": df_onco_mg,
            "Reconstrução Mamária": df_recon_mg,
            "Tratamento Sincrônico": df_sinc_mg,
        },
        axis=0,
        sort=False,
    )
    df_unificado.index.names = ["TIPO", "ID_ORIGINAL"]

    caminho_csv = SAIDA_DIR / "hospitais_de_mg.csv"
    df_unificado.reset_index(level="TIPO").to_csv(caminho_csv, index=False, encoding="utf-8-sig")
    return caminho_csv


def main() -> None:
    df_onco, df_recon, df_sinc = carregar_dados()
    df_onco_mg, df_recon_mg, df_sinc_mg = filtrar_mg(df_onco, df_recon, df_sinc)
    caminho_csv = gerar_csv_unificado(df_onco_mg, df_recon_mg, df_sinc_mg)

    print(f"Pasta de entrada: {DADOS_DIR}")
    print(f"CSV salvo em: {caminho_csv}")
    print(
        "Linhas por tipo (MG): "
        f"Oncologia={len(df_onco_mg)}, "
        f"Reconstrução Mamária={len(df_recon_mg)}, "
        f"Tratamento Sincrônico={len(df_sinc_mg)}"
    )


if __name__ == "__main__":
    main()
