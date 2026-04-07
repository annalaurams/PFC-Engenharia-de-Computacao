# pyright: reportUnknownMemberType=false

import unicodedata
from pathlib import Path

import pandas as pd

DADOS_DIR = Path("/home/anna/tcc/Variáveis/Hospitais Habilitados")
SAIDA_DIR = Path("/home/anna/tcc/Tratamento/Hospitais")
ARQUIVOS_MUNICIPIOS_CANDIDATOS = [
    Path("/home/anna/tcc/Tratamento/Municípios/tabela_municipios_regionais.csv"),
    Path("/home/anna/tcc/Tratamento/Municípios/municipios_regionais_normalizados.csv"),
]
SAIDA_DIR.mkdir(parents=True, exist_ok=True)

SAIDA_FILTRO = SAIDA_DIR / "filtro_hospitais_mg.csv"
SAIDA_TABELA = SAIDA_DIR / "tabela_hospitais_habilitados.csv"

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


def carregar_dados() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    df_onco = pd.read_excel(
        DADOS_DIR / "hospitais-habilitados-em-oncologia-abril-2025.xlsx",
        header=1,
    )  
    df_onco.columns = df_onco.columns.str.strip()
    cols_ffill_onco = [df_onco.columns[0], df_onco.columns[1], df_onco.columns[2]]
    df_onco[cols_ffill_onco] = df_onco[cols_ffill_onco].ffill()
    df_onco = df_onco.dropna(subset=[df_onco.columns[4]]).reset_index(drop=True)

    df_recon = pd.read_excel(
        DADOS_DIR / "hospitais-habilitados-em-reconstrucao-mamaria.xlsx",
        header=0,
    )  
    df_recon.columns = df_recon.columns.str.strip()

    df_sinc = pd.read_excel(
        DADOS_DIR / "tratamento-sincronico.xlsx",
        header=1,
    )  
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


def gerar_tabela_filtro(
    df_onco_mg: pd.DataFrame,
    df_recon_mg: pd.DataFrame,
    df_sinc_mg: pd.DataFrame,
) -> pd.DataFrame:
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

    df_filtro = df_unificado.reset_index(level="TIPO")
    df_filtro.to_csv(SAIDA_FILTRO, index=False, encoding="utf-8-sig")
    return df_filtro


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
    arquivo_municipios = next(
        (p for p in ARQUIVOS_MUNICIPIOS_CANDIDATOS if p.exists()),
        None,
    )
    if arquivo_municipios is None:
        candidatos = ", ".join(str(p) for p in ARQUIVOS_MUNICIPIOS_CANDIDATOS)
        raise FileNotFoundError(f"Nenhum arquivo de municípios encontrado. Tentativas: {candidatos}")

    df_municipios = pd.read_csv(arquivo_municipios, encoding="utf-8-sig")

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


def gerar_tabela_habilitados(df_filtro: pd.DataFrame) -> pd.DataFrame:
    coluna_municipio = None
    if "MUNICÍPIO" in df_filtro.columns:
        coluna_municipio = "MUNICÍPIO"
    elif "MUNICÍPIOS" in df_filtro.columns:
        coluna_municipio = "MUNICÍPIOS"
    else:
        raise ValueError(
            "Coluna obrigatória de município não encontrada no filtro de hospitais. "
            "Esperado: 'MUNICÍPIO' ou 'MUNICÍPIOS'."
        )

    mapa_codigo = carregar_mapa_codigo_municipio()
    df = df_filtro.copy()

    colunas_existentes = [c for c in COLUNAS_REMOVER if c in df.columns]
    df = df.drop(columns=colunas_existentes)

    df[coluna_municipio] = df[coluna_municipio].map(normalizar_municipio)
    df["municipio_chave"] = df[coluna_municipio].map(normalizar_chave_municipio)
    df["CÓDIGO"] = df["municipio_chave"].map(mapa_codigo)

    municipios_sem_codigo = sorted(
        {
            str(municipio)
            for municipio in df.loc[df["CÓDIGO"].isna(), coluna_municipio].dropna().unique().tolist()
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

    if coluna_municipio != "MUNICÍPIOS":
        df = df.rename(columns={coluna_municipio: "MUNICÍPIOS"})

    cols = ["MUNICÍPIOS", "CÓDIGO"] + [
        c for c in df.columns if c not in {"MUNICÍPIOS", "CÓDIGO"}
    ]
    df = df[cols]

    df.to_csv(SAIDA_TABELA, index=False, encoding="utf-8-sig")
    return df


def main() -> None:
    df_onco, df_recon, df_sinc = carregar_dados()
    df_onco_mg, df_recon_mg, df_sinc_mg = filtrar_mg(df_onco, df_recon, df_sinc)
    df_filtro = gerar_tabela_filtro(df_onco_mg, df_recon_mg, df_sinc_mg)
    df_tabela = gerar_tabela_habilitados(df_filtro)

    print(f"Pasta de entrada: {DADOS_DIR}")
    print(f"CSV de filtro salvo em: {SAIDA_FILTRO}")
    print(f"Tabela final salva em: {SAIDA_TABELA}")
    print(
        "Linhas por tipo (MG): "
        f"Oncologia={len(df_onco_mg)}, "
        f"Reconstrução Mamária={len(df_recon_mg)}, "
        f"Tratamento Sincrônico={len(df_sinc_mg)}"
    )
    print(f"Total de linhas da tabela final: {len(df_tabela)}")


if __name__ == "__main__":
    main()
