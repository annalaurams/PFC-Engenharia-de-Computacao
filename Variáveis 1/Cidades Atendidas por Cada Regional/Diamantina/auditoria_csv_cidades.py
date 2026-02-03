import os
import unicodedata

BASE_PATH = "/home/anna/Documentos/PFC I/Variáveis 1/Cidades Atendidas por Cada Regional/Diamantina"

CIDADES_ESPERADAS = [
    "Alvorada de Minas-MG",
    "Araçuaí-MG",
    "Aricanduva-MG",
    "Berilo-MG",
    "Capelinha-MG",
    "Carbonita-MG",
    "Chapada do Norte-MG",
    "Coluna-MG",
    "Congonhas do Norte-MG",
    "Coronel Murta-MG",
    "Couto de Magalhães de Minas-MG",
    "Datas-MG",
    "Diamantina-MG",
    "Felício dos Santos-MG",
    "São Gonçalo do Rio Preto-MG",
    "Francisco Badaró-MG",
    "Gouveia-MG",
    "Itamarandiba-MG",
    "Jenipapo de Minas-MG",
    "José Gonçalves de Minas-MG",
    "Leme do Prado-MG",
    "Materlândia-MG",
    "Minas Novas-MG",
    "Presidente Kubitschek-MG",
    "Rio Vermelho-MG",
    "Sabinópolis-MG",
    "Santo Antônio do Itambé-MG",
    "Senador Modestino Gonçalves-MG",
    "Serra Azul de Minas-MG",
    "Serro-MG",
    "Turmalina-MG",
    "Veredinha-MG",
    "Virgem da Lapa-MG"
]

def normalizar_nome(nome):
    nome = nome.replace("-MG", "")
    nome = unicodedata.normalize("NFKD", nome)
    nome = "".join(c for c in nome if not unicodedata.combining(c))
    return nome.lower().strip()

def verificar_pastas_faltantes():
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO DE PASTAS - Regional de Coronel Fabriciano".center(80))
    print("=" * 80 + "\n")

    if not os.path.isdir(BASE_PATH):
        print(f"ERRO: O caminho '{BASE_PATH}' não existe!")
        return

    pastas_existentes = [
        item for item in os.listdir(BASE_PATH)
        if os.path.isdir(os.path.join(BASE_PATH, item))
    ]

    pastas_normalizadas = {
        normalizar_nome(pasta) for pasta in pastas_existentes
    }

    cidades_faltantes = []
    for cidade in CIDADES_ESPERADAS:
        if normalizar_nome(cidade) not in pastas_normalizadas:
            cidades_faltantes.append(cidade)

    print(f"Total de cidades esperadas: {len(CIDADES_ESPERADAS)}")
    print(f"Total de pastas encontradas: {len(pastas_existentes)}")
    print(f"Total de cidades faltantes: {len(cidades_faltantes)}\n")

    if cidades_faltantes:
        print("-" * 80)
        print("CIDADES SEM PASTA:")
        print("-" * 80)
        for cidade in sorted(cidades_faltantes):
            print(f"   ✗ {cidade}")
    else:
        print("✓ Todas as cidades esperadas possuem pasta correspondente!")

    print("=" * 80)


if __name__ == "__main__":
    verificar_pastas_faltantes()
