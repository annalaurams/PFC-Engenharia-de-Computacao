import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path("/home/anna/tcc/Tratamento/Hospitais")
ENTRADA = Path("/home/anna/tcc/Variáveis/Hospitais Habilitados")
SAIDA = ROOT / "tabela_hospitais_habilitados.csv"
MUNICIPIOS = [
    Path("/home/anna/tcc/Tratamento/Municípios/tabela_municipios_regionais.csv"),
    Path("/home/anna/tcc/Tratamento/Municípios/municipios_regionais_normalizados.csv"),
]

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


# ________________________________________________________________________________
# Texto

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


# ________________________________________________________________________________
# Arquivos

def carregar_dados() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df_onco = pd.read_excel(
        ENTRADA / "hospitais-habilitados-em-oncologia-abril-2025.xlsx",
        header=1,
    )
    df_onco.columns = df_onco.columns.str.strip()
    colunas_onco = [df_onco.columns[0], df_onco.columns[1], df_onco.columns[2]]
    df_onco[colunas_onco] = df_onco[colunas_onco].ffill()
    df_onco = df_onco.dropna(subset=[df_onco.columns[4]]).reset_index(drop=True)

    df_recon = pd.read_excel(
        ENTRADA / "hospitais-habilitados-em-reconstrucao-mamaria.xlsx",
        header=0,
    )
    df_recon.columns = df_recon.columns.str.strip()

    df_sinc = pd.read_excel(
        ENTRADA / "tratamento-sincronico.xlsx",
        header=1,
    )
    df_sinc.columns = df_sinc.columns.str.strip()
    df_sinc = df_sinc[df_sinc[df_sinc.columns[1]].notna()].reset_index(drop=True)

    return df_onco, df_recon, df_sinc


def carregar_mapa_codigo_municipio() -> dict[str, int]:
    arquivo = next((p for p in MUNICIPIOS if p.exists()), None)
    if arquivo is None:
        candidatos = ", ".join(str(p) for p in MUNICIPIOS)
        raise FileNotFoundError(f"Nenhum arquivo de municípios encontrado. Tentativas: {candidatos}")

    df = pd.read_csv(arquivo, encoding="utf-8-sig")
    obrigatorias = {"codigo_ibge", "municipio_normalizado"}
    faltando = obrigatorias - set(df.columns)
    if faltando:
        raise ValueError(f"Arquivo de municípios sem colunas obrigatórias: {sorted(faltando)}")

    df["municipio_chave"] = df["municipio_normalizado"].map(normalizar_chave_municipio)
    df = df.dropna(subset=["municipio_chave", "codigo_ibge"])

    return dict(
        zip(
            df["municipio_chave"].astype(str),
            df["codigo_ibge"].astype(int),
            strict=False,
        )
    )


# ________________________________________________________________________________
# Tratamento

def filtrar_mg(
    df_onco: pd.DataFrame,
    df_recon: pd.DataFrame,
    df_sinc: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    col_onco = df_onco.columns[0]
    col_recon = df_recon.columns[0]
    col_sinc = df_sinc.columns[1]

    df_onco_mg = df_onco[df_onco[col_onco].astype(str).str.strip() == "MG"].reset_index(drop=True)
    df_recon_mg = df_recon[df_recon[col_recon].astype(str).str.strip() == "MG"].reset_index(drop=True)
    df_sinc_mg = df_sinc[df_sinc[col_sinc].astype(str).str.strip() == "MG"].reset_index(drop=True)

    return df_onco_mg, df_recon_mg, df_sinc_mg


def unir_tabelas(
    df_onco_mg: pd.DataFrame,
    df_recon_mg: pd.DataFrame,
    df_sinc_mg: pd.DataFrame,
) -> pd.DataFrame:
    tabela = pd.concat(
        {
            "Oncologia": df_onco_mg,
            "Reconstrução Mamária": df_recon_mg,
            "Tratamento Sincrônico": df_sinc_mg,
        },
        axis=0,
        sort=False,
    )
    tabela.index.names = ["TIPO", "ID_ORIGINAL"]
    return tabela.reset_index(level="TIPO")


# ________________________________________________________________________________
# Criação de colunas

def gerar_tabela_habilitados(tabela: pd.DataFrame) -> pd.DataFrame:
    if "MUNICÍPIO" in tabela.columns:
        coluna_municipio = "MUNICÍPIO"
    elif "MUNICÍPIOS" in tabela.columns:
        coluna_municipio = "MUNICÍPIOS"
    else:
        raise ValueError("Coluna de município não encontrada na tabela de hospitais.")

    mapa_codigo = carregar_mapa_codigo_municipio()
    df = tabela.copy()

    colunas_existentes = [c for c in COLUNAS_REMOVER if c in df.columns]
    df = df.drop(columns=colunas_existentes)

    df[coluna_municipio] = df[coluna_municipio].map(normalizar_municipio)
    df["municipio_chave"] = df[coluna_municipio].map(normalizar_chave_municipio)
    df["CÓDIGO"] = df["municipio_chave"].map(mapa_codigo)

    sem_codigo = sorted(
        {
            str(municipio)
            for municipio in df.loc[df["CÓDIGO"].isna(), coluna_municipio].dropna().unique().tolist()
        }
    )

    if sem_codigo:
        print("Municípios sem correspondência de código:")
        for municipio in sem_codigo:
            print(f"- {municipio}")
    else:
        print("Todos os municípios tiveram código encontrado.")

    df["CÓDIGO"] = pd.to_numeric(df["CÓDIGO"], errors="coerce").astype("Int64")
    df = df.drop(columns=["municipio_chave"])

    if coluna_municipio != "MUNICÍPIOS":
        df = df.rename(columns={coluna_municipio: "MUNICÍPIOS"})

    cols = ["MUNICÍPIOS", "CÓDIGO"] + [c for c in df.columns if c not in {"MUNICÍPIOS", "CÓDIGO"}]
    df = df[cols]
    return df


# ________________________________________________________________________________
# Operações

def main() -> None:
    df_onco, df_recon, df_sinc = carregar_dados()
    df_onco_mg, df_recon_mg, df_sinc_mg = filtrar_mg(df_onco, df_recon, df_sinc)
    tabela = unir_tabelas(df_onco_mg, df_recon_mg, df_sinc_mg)
    df_tabela = gerar_tabela_habilitados(tabela)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    df_tabela.to_csv(SAIDA, index=False, encoding="utf-8-sig")

    print(f"Pasta de entrada: {ENTRADA}")
    print(f"Tabela final salva em: {SAIDA}")
    print(
        "Linhas por tipo (MG): "
        f"Oncologia={len(df_onco_mg)}, "
        f"Reconstrução Mamária={len(df_recon_mg)}, "
        f"Tratamento Sincrônico={len(df_sinc_mg)}"
    )
    print(f"Total de linhas da tabela final: {len(df_tabela)}")


if __name__ == "__main__":
    main()
