import os

BASE_PATH = "/home/anna/Documentos/PFC I/Variáveis 1/Cidades Atendidas por Cada Regional/Belo Horizonte"

CIDADES_ESPERADAS = [
    "Belo Horizonte",
    "Belo Vale",
    "Betim",
    "Bonfim",
    "Brumadinho",
    "Caeté",
    "Conceição do Mato Dentro",
    "Confins",
    "Contagem",
    "Crucilândia",
    "Esmeraldas",
    "Florestal",
    "Ibirité",
    "Igarapé",
    "Itabirito",
    "Jaboticatubas",
    "Nova União",
    "Juatuba",
    "Lagoa Santa",
    "Mariana",
    "Mário Campos",
    "Mateus Leme",
    "Matozinhos",
    "Moeda",
    "Nova Lima",
    "Ouro Preto",
    "Pedro Leopoldo",
    "Piedade dos Gerais",
    "Raposos",
    "Ribeirão das Neves",
    "Rio Acima",
    "Rio Manso",
    "Sabará",
    "Santa Luzia",
    "Santana do Riacho",
    "São Joaquim de Bicas",
    "São José da Lapa",
    "Sarzedo",
    "Taquaraçu de Minas",
    "Vespasiano",
]


def verificar_pastas_faltantes():
    print("\n" + "=" * 80)
    print("VERIFICAÇÃO DE PASTAS - Regional de Alfenas".center(80))
    print("=" * 80 + "\n")

    if not os.path.isdir(BASE_PATH):
        print(f"ERRO: O caminho '{BASE_PATH}' não existe!")
        return

    # Listar todas as pastas existentes
    pastas_existentes = [
        item for item in os.listdir(BASE_PATH)
        if os.path.isdir(os.path.join(BASE_PATH, item))
    ]

    # Normalizar nomes para comparação (remover sufixo -MG se houver)
    pastas_normalizadas = set()
    for pasta in pastas_existentes:
        nome_limpo = pasta.replace("-MG", "").strip()
        pastas_normalizadas.add(nome_limpo)

    # Verificar quais cidades estão faltando
    cidades_faltantes = []
    for cidade in CIDADES_ESPERADAS:
        if cidade not in pastas_normalizadas:
            cidades_faltantes.append(cidade)

    # Exibir resultados
    print(f"Total de cidades esperadas: {len(CIDADES_ESPERADAS)}")
    print(f"Total de pastas encontradas: {len(pastas_existentes)}")
    print(f"Total de cidades faltantes: {len(cidades_faltantes)}\n")

    if cidades_faltantes:
        print("-" * 80)
        print("CIDADES SEM PASTA:")
        print("-" * 80)
        for cidade in sorted(cidades_faltantes):
            print(f"   ✗ {cidade}")
        print()
    else:
        print("✓ Todas as cidades esperadas possuem pasta correspondente!")

    print("=" * 80)


if __name__ == "__main__":
    verificar_pastas_faltantes()