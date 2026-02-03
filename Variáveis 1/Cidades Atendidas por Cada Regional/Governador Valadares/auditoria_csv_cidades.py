import os
import unicodedata

BASE_PATH = "/home/anna/Documentos/PFC I/Variáveis 1/Cidades Atendidas por Cada Regional/Governador Valadares"

CIDADES_ESPERADAS = [
    "Água Boa-MG",
    "Aimorés-MG",
    "Alpercata-MG",
    "Alvarenga-MG",
    "Cantagalo-MG",
    "Capitão Andrade-MG",
    "Central de Minas-MG",
    "Conselheiro Pena-MG",
    "Coroaci-MG",
    "Cuparaque-MG",
    "Divino das Laranjeiras-MG",
    "Divinolândia de Minas-MG",
    "Engenheiro Caldas-MG",
    "Fernandes Tourinho-MG",
    "Frei Inocêncio-MG",
    "Frei Lagonegro-MG",
    "Galiléia-MG",
    "Goiabeira-MG",
    "Gonzaga-MG",
    "Governador Valadares-MG",
    "Itabirinha-MG",
    "Itanhomi-MG",
    "Itueta-MG",
    "Jampruca-MG",
    "José Raydan-MG",
    "Mantena-MG",
    "Marilac-MG",
    "Mendes Pimentel-MG",
    "Nacip Raydan-MG",
    "Nova Belém-MG",
    "Paulistas-MG",
    "Peçanha-MG",
    "Resplendor-MG",
    "Santa Efigênia de Minas-MG",
    "Santa Maria do Suaçuí-MG",
    "Santa Rita do Itueto-MG",
    "São Félix de Minas-MG",
    "São Geraldo da Piedade-MG",
    "São Geraldo do Baixio-MG",
    "São João do Manteninha-MG",
    "São João Evangelista-MG",
    "São José da Safira-MG",
    "São José do Jacuri-MG",
    "São Pedro do Suaçuí-MG",
    "São Sebastião do Maranhão-MG",
    "Sardoá-MG",
    "Sobrália-MG",
    "Tarumirim-MG",
    "Tumiritinga-MG",
    "Mathias Lobato-MG"
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
