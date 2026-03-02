import os
import unicodedata

BASE_PATH = "/home/anna/tcc/variaveis/Variáveis 1/Cidades Atendidas por Cada Regional/Varginha"

CIDADES_ESPERADAS = [
    "Aiuruoca-MG",
    "Alagoa-MG",
    "Baependi-MG",
    "Boa Esperança-MG",
    "Cambuquira-MG",
    "Campanha-MG",
    "Carmo da Cachoeira-MG",
    "Carmo de Minas-MG",
    "Carrancas-MG",
    "Carvalhos-MG",
    "Caxambu-MG",
    "Conceição do Rio Verde-MG",
    "Coqueiral-MG",
    "Cordislândia-MG",
    "Cristina-MG",
    "Cruzília-MG",
    "Dom Viçoso-MG",
    "Elói Mendes-MG",
    "Ijaci-MG",
    "Ilicínea-MG",
    "Ingaí-MG",
    "Itamonte-MG",
    "Itanhandu-MG",
    "Itumirim-MG",
    "Itutinga-MG",
    "Jesuânia-MG",
    "Lambari-MG",
    "Lavras-MG",
    "Luminárias-MG",
    "Monsenhor Paulo-MG",
    "Nepomuceno-MG",
    "Olímpio Noronha-MG",
    "Passa Quatro-MG",
    "Perdões-MG",
    "Pouso Alto-MG",
    "Ribeirão Vermelho-MG",
    "Santana da Vargem-MG",
    "São Bento Abade-MG",
    "São Lourenço-MG",
    "São Sebastião do Rio Verde-MG",
    "São Thomé das Letras-MG",
    "Seritinga-MG",
    "Serranos-MG",
    "Soledade de Minas-MG",
    "Três Corações-MG",
    "Três Pontas-MG",
    "Varginha-MG",
    "Virgínia-MG",
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
