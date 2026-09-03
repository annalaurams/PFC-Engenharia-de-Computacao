import pandas as pd
from pathlib import Path

PASTA_POPULACAO = Path("../População/Interpolação e Extrapolação")

REGIONAL_ALVO = "passos"
ANO_ALVO = 2022

populacao = pd.read_csv(PASTA_POPULACAO / "populacao_interpolacao_extrapolacao.csv")

passos = populacao[
    populacao["REGIONAL DE SAÚDE"].str.strip().str.lower() == REGIONAL_ALVO
].copy()

coluna_ano = f"{ANO_ALVO}_TOTAL"

print(f"Municípios da regional de Passos e população em {ANO_ALVO}:\n")
for _, linha in passos.iterrows():
    print(f"{linha['MUNICÍPIO']}: {linha[coluna_ano]:.0f}")

total = passos[coluna_ano].sum()
print(f"\nPopulação total da regional de Passos em {ANO_ALVO}: {total:.0f}")
