# Script utilitário: lista os municípios de uma Regional de Saúde e a
# população total de cada um num ano específico, usando a base já
# interpolada/extrapolada de população.
import pandas as pd
from pathlib import Path

PASTA_POPULACAO = Path("../População/Interpolação e Extrapolação")

# Regional e ano a consultar; ajuste aqui para checar outra combinação.
REGIONAL_ALVO = "passos"
ANO_ALVO = 2022

populacao = pd.read_csv(PASTA_POPULACAO / "populacao_interpolacao_extrapolacao.csv")

# Filtra só os municípios da Regional alvo (comparação normalizada: sem
# espaços nas bordas e em minúsculas, para não depender da grafia exata).
passos = populacao[
    populacao["REGIONAL DE SAÚDE"].str.strip().str.lower() == REGIONAL_ALVO
].copy()

# Nome da coluna de população total do ano alvo (padrão "<ANO>_TOTAL").
coluna_ano = f"{ANO_ALVO}_TOTAL"

# Imprime a população de cada município da Regional e o total somado.
print(f"Municípios da regional de Passos e população em {ANO_ALVO}:\n")
for _, linha in passos.iterrows():
    print(f"{linha['MUNICÍPIO']}: {linha[coluna_ano]:.0f}")

total = passos[coluna_ano].sum()
print(f"\nPopulação total da regional de Passos em {ANO_ALVO}: {total:.0f}")
