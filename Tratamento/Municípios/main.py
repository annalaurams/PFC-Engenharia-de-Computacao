from pathlib import Path
import unicodedata
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]

ENTRADA_MUNICIPIOS  = ROOT / "Variáveis" / "Municípios" / "Relacao-de-municipios-por-vinculacao-administrativa-090.xlsx"
ENTRADA_MORTALIDADE = ROOT / "Tratamento" / "Mortalidade" / "tabela_mortalidade_faixa_etaria.csv"
SAIDA = Path(__file__).with_name("tabela_municipios_regionais.csv")
ABA   = "RegionalizaçãoMG2024"

COL_MUNICIPIO_MORT = "Municípios"
COL_REGIONAL_MORT  = "Regional de Saúde"

CORRECOES_NOMES = {
    "brazopolis":        "brasopolis",
    "dona euzebia":      "dona eusebia",
    "sao tome das letras": "sao thome das letras",
}


# ________________________________________________________________________________
# Texto

def normalizar_texto(texto: str) -> str:
    texto = "" if pd.isna(texto) else str(texto).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto.lower()


# ________________________________________________________________________________
# Operações

def main() -> None:
    # Municípios do Excel
    df = pd.read_excel(ENTRADA_MUNICIPIOS, sheet_name=ABA, header=3)

    tabela = pd.DataFrame({
        "codigo_ibge":           df["Código IBGE"],
        "municipio_original":    df["Município "].astype(str).str.strip(),
        "municipio_normalizado": df["Município "].map(normalizar_texto),
    })

    # Corrige grafias divergentes antes do merge
    tabela["municipio_normalizado"] = tabela["municipio_normalizado"].replace(CORRECOES_NOMES)

    # Regionais do CSV de mortalidade (uma linha por município)
    mort = pd.read_csv(ENTRADA_MORTALIDADE, encoding="utf-8-sig")
    regionais = (
        mort[[COL_MUNICIPIO_MORT, COL_REGIONAL_MORT]]
        .drop_duplicates(subset=COL_MUNICIPIO_MORT)
        .assign(municipio_normalizado=lambda d: d[COL_MUNICIPIO_MORT].map(normalizar_texto))
        .rename(columns={COL_REGIONAL_MORT: "regional_original"})
        [["municipio_normalizado", "regional_original"]]
    )

    # Join pelo nome normalizado
    tabela = tabela.merge(regionais, on="municipio_normalizado", how="left")
    tabela["regional_normalizada"] = tabela["regional_original"].map(normalizar_texto)

    tabela.to_csv(SAIDA, index=False, encoding="utf-8-sig")
    print(f"CSV gerado em: {SAIDA}")
    print(f"Total de linhas: {len(tabela)}")

    sem_regional = tabela["regional_original"].isna().sum()
    if sem_regional:
        print(f"\n⚠️  {sem_regional} município(s) sem regional (ausentes na base de mortalidade):")
        print(tabela[tabela["regional_original"].isna()][["codigo_ibge", "municipio_original"]].to_string(index=False))


if __name__ == "__main__":
    main()