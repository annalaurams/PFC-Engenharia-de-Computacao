from pathlib import Path
import unicodedata

import pandas as pd

# ________________________________________________________________________________
# Configuração

PASTA = Path("/home/anna/tcc/Tratamento/Mortalidade")
MORTALIDADE = PASTA / "tabela_mortalidade_faixa_etaria.csv"
MUNICIPIOS = Path("/home/anna/tcc/Tratamento/Municípios/tabela_municipios_regionais.csv")
SAIDA = PASTA / "cidades_faltantes_na_mortalidade.csv"

# ________________________________________________________________________________
# Funções

def normalizar_texto(texto: str) -> str:
    texto = str(texto).strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.replace("_", " ")
    texto = texto.replace("-", " ")
    texto = " ".join(texto.split())
    return texto


def carregar_mortalidade() -> pd.DataFrame:
    tabela = pd.read_csv(MORTALIDADE, dtype=str, encoding="utf-8", sep=",")
    if "Municípios" not in tabela.columns:
        raise ValueError("A tabela de mortalidade não tem a coluna 'Municípios'.")
    tabela = tabela.copy()
    tabela["municipio_normalizado"] = tabela["Municípios"].apply(normalizar_texto)
    tabela = tabela[tabela["municipio_normalizado"] != "total"]
    return tabela


def carregar_municipios() -> pd.DataFrame:
    tabela = pd.read_csv(MUNICIPIOS, dtype=str, encoding="utf-8", sep=",")
    colunas_necessarias = {
        "codigo_ibge",
        "municipio_original",
        "municipio_normalizado",
        "regional_original",
        "regional_normalizada",
    }
    faltando = colunas_necessarias.difference(tabela.columns)
    if faltando:
        raise ValueError(f"A tabela de municípios está sem as colunas: {sorted(faltando)}")
    tabela = tabela.copy()
    tabela["municipio_normalizado_limpo"] = tabela["municipio_normalizado"].apply(normalizar_texto)
    return tabela


def encontrar_cidades_faltantes() -> pd.DataFrame:
    mortalidade = carregar_mortalidade()
    municipios = carregar_municipios()

    cidades_mortalidade = set(mortalidade["municipio_normalizado"].dropna())
    faltantes = municipios[~municipios["municipio_normalizado_limpo"].isin(cidades_mortalidade)].copy()

    faltantes = faltantes[
        [
            "codigo_ibge",
            "municipio_original",
            "municipio_normalizado",
            "regional_original",
            "regional_normalizada",
        ]
    ]
    faltantes = faltantes.sort_values(["regional_original", "municipio_original"], kind="stable")
    return faltantes


def main() -> int:
    municipios = carregar_municipios()
    faltantes = encontrar_cidades_faltantes()
    faltantes.to_csv(SAIDA, index=False, encoding="utf-8-sig")

    total_municipios = len(municipios)
    total_faltantes = len(faltantes)

    print("=" * 80)
    print("AUDITORIA DE MUNICÍPIOS NA MORTALIDADE".center(80))
    print("=" * 80)
    print(f"Total de municípios na tabela de referência : {total_municipios}")
    print(f"Total que não aparecem na mortalidade       : {total_faltantes}")
    print(f"Arquivo salvo em: {SAIDA}")

    if total_faltantes:
        print("\nCidades faltantes:")
        for _, linha in faltantes.iterrows():
            print(f"- {linha['municipio_original']} ({linha['regional_original']})")
    else:
        print("\nTodas as cidades da tabela de municípios aparecem na mortalidade.")

    print("=" * 80)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())