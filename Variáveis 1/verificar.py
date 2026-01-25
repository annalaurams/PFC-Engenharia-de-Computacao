import os

# ================= CONFIGURAÇÕES =================
BASE_PATH = "/home/usuario/Documentos/PFC I/Código"
ANO_INICIAL = 1979
ANO_FINAL = 2024

CIDADES = [
    "Alfenas-MG",
    "Barbacena-MG",
    "Belo Horizonte-MG",
    "Coronel Fabriciano-MG",
    "Diamantina-MG",
    "Divinópolis-MG",
    "Governador Valadares-MG",
    "Itabira-MG",
    "Ituiutaba-MG",
    "Januária-MG",
    "Juiz de Fora-MG",
    "Leopoldina-MG",
    "Manhumirim-MG",
    "Montes Claros-MG",
    "Passos-MG",
    "Patos de Minas-MG",
    "Pedra Azul-MG",
    "Pirapora-MG",
    "Ponte Nova-MG",
    "Pouso Alegre-MG",
    "São João Del Rei-MG",
    "Sete Lagoas-MG",
    "Teófilo Otoni-MG",
    "Ubá-MG",
    "Uberaba-MG",
    "Uberlândia-MG",
    "Unaí-MG",
    "Varginha-MG",
]

# ================= LÓGICA =================
def verificar_cidade(cidade):
    pasta = os.path.join(BASE_PATH, cidade)

    if not os.path.isdir(pasta):
        return ["PASTA NÃO EXISTE"]

    arquivos = set(os.listdir(pasta))
    anos_faltando = []

    for ano in range(ANO_INICIAL, ANO_FINAL + 1):
        nome_esperado = f"{ano}-{cidade}.csv"
        if nome_esperado not in arquivos:
            anos_faltando.append(ano)

    return anos_faltando


def main():
    print("\n" + "=" * 80)
    print("📊 RELATÓRIO DE CSVs FALTANTES POR CIDADE".center(80))
    print(f"Período analisado: {ANO_INICIAL} → {ANO_FINAL}".center(80))
    print("=" * 80 + "\n")

    total_cidades_com_problema = 0

    for cidade in CIDADES:
        faltantes = verificar_cidade(cidade)

        if faltantes:
            total_cidades_com_problema += 1
            print(f"📍 Cidade: {cidade}")
            print("-" * 80)

            if faltantes == ["PASTA NÃO EXISTE"]:
                print("❌ ERRO: Pasta da cidade não encontrada.\n")
            else:
                print(f"⚠️ Total de anos sem CSV: {len(faltantes)}")
                print("📅 Anos faltantes:")
                
                # quebra de linha a cada 10 anos para ficar legível
                for i in range(0, len(faltantes), 10):
                    bloco = ", ".join(map(str, faltantes[i:i+10]))
                    print(f"   - {bloco}")
                
                print()

    if total_cidades_com_problema == 0:
        print("✅ Todas as cidades possuem todos os CSVs do período analisado.")
    else:
        print("=" * 80)
        print(f"⚠️ Total de cidades com pendências: {total_cidades_com_problema}")
        print("=" * 80)


if __name__ == "__main__":
    main()
