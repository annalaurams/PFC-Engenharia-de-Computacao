from pathlib import Path
import unicodedata
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ENTRADA = ROOT / "Variáveis" / "Municípios" / "Relacao-de-municipios-por-vinculacao-administrativa-090.xlsx"
SAIDA = Path(__file__).with_name("tabela_municipios_regionais.csv")
ABA = "RegionalizaçãoMG2024"

# ________________________________________________________________________________
# Texto

def normalizar_texto(texto: str) -> str:
    texto = "" if pd.isna(texto) else str(texto).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return texto.lower()


# ________________________________________________________________________________
# Operações

def main() -> None:
    df = pd.read_excel(ENTRADA, sheet_name=ABA, header=3)

    tabela = pd.DataFrame(
        {
            "codigo_ibge": df["Código IBGE"],
            "municipio_original": df["Município "].astype(str).str.strip(),
            "municipio_normalizado": df["Município "].map(normalizar_texto),
            "regional_original": df["Unidade Regional de Saúde"].astype(str).str.strip(),
            "regional_normalizada": df["Unidade Regional de Saúde"].map(normalizar_texto),
        }
    )

    tabela.to_csv(SAIDA, index=False, encoding="utf-8-sig")
    print(f"CSV gerado em: {SAIDA}")
    print(f"Total de linhas: {len(tabela)}")


if __name__ == "__main__":
    main()
