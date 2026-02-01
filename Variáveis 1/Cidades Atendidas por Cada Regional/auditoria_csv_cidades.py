import os
import unicodedata

BASE_PATH = "/home/anna/Documentos/PFC I/Variáveis 1/Cidades Atendidas por Cada Regional/Coronel Fabriciano"

CIDADES_ESPERADAS = [
    "Açucena-MG",
    "Antônio Dias-MG",
    "Belo Oriente-MG",
    "Bom Jesus do Galho-MG",
    "Braúnas-MG",
    "Bugre-MG",
    "Caratinga-MG",
    "Coronel Fabriciano-MG",
    "Córrego Novo-MG",
    "Dionísio-MG",
    "Dom Cavati-MG",
    "Entre Folhas-MG",
    "Iapu-MG",
    "Imbé de Minas-MG",
    "Inhapim-MG",
    "Ipaba-MG",
    "Ipatinga-MG",
    "Jaguaraçu-MG",
    "Joanésia-MG",
    "Marliéria-MG",
    "Mesquita-MG",
    "Naque-MG",
    "Periquito-MG",
    "Piedade de Caratinga-MG",
    "Pingo-d'Água-MG",
    "Santa Bárbara do Leste-MG",
    "Santana do Paraíso-MG",
    "Santa Rita de Minas-MG",
    "São Domingos das Dores-MG",
    "São João do Oriente-MG",
    "São Sebastião do Anta-MG",
    "Timóteo-MG",
    "Ubaporanga-MG",
    "Vargem Alegre-MG",
    "Vermelho Novo-MG"
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
