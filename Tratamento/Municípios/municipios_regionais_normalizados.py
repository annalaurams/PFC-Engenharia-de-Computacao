from pathlib import Path
import unicodedata
import pandas as pd

PROJETO_DIR = Path(__file__).resolve().parents[2]
ARQUIVO_ENTRADA = PROJETO_DIR / "Variáveis" / "Municípios" / "Relacao-de-municipios-por-vinculacao-administrativa-090.xlsx"
ARQUIVO_SAIDA = Path(__file__).with_name("municipios_regionais_normalizados.csv")
NOME_ABA = "RegionalizaçãoMG2024"

def normalizar_texto(texto: str) -> str:
    texto = "" if pd.isna(texto) else str(texto).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return texto.lower()


def main() -> None:
    df = pd.read_excel(ARQUIVO_ENTRADA, sheet_name=NOME_ABA, header=3)  # pyright: ignore[reportUnknownMemberType]

    resultado = pd.DataFrame(
        {
            "codigo_ibge": df["Código IBGE"],
            "municipio_original": df["Município "].astype(str).str.strip(),
            "municipio_normalizado": df["Município "].map(normalizar_texto),
            "regional_original": df["Unidade Regional de Saúde"].astype(str).str.strip(),
            "regional_normalizada": df["Unidade Regional de Saúde"].map(normalizar_texto),
        }
    )

    resultado.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")
    print(f"CSV gerado em: {ARQUIVO_SAIDA}")
    print(f"Total de linhas: {len(resultado)}")


if __name__ == "__main__":
    main()
