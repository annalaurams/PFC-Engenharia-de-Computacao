import os
from pathlib import Path
import csv

def listar_cidades_por_regional(caminho_base):

    dados = []
    caminho = Path(caminho_base)
    
    # Percorre todas as pastas no diretório base
    for item in sorted(caminho.iterdir()):
        # Verifica se é uma pasta (ignora arquivos .py, .txt, etc)
        if item.is_dir():
            regional = item.name
            print(f"Processando regional: {regional}")
            
            # Percorre as subpastas (cidades) dentro de cada regional
            for cidade_pasta in sorted(item.iterdir()):
                if cidade_pasta.is_dir():
                    cidade = cidade_pasta.name
                    dados.append((regional, cidade))
                    print(f"  - {cidade}")
    
    return dados

def gerar_arquivo_saida(dados, arquivo_saida):

    with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['Regional', 'Cidade'])  # Cabeçalho
        writer.writerows(dados)
    
    print(f"\nArquivo gerado com sucesso: {arquivo_saida}")
    print(f"Total de registros: {len(dados)}")

def main():
    caminho_base = "/home/anna/tcc/variaveis/Variáveis 1/Cidades Atendidas por Cada Regional"
    
    pasta_saidas = Path("/home/anna/tcc/variaveis/Variáveis 1/Saídas")
    pasta_saidas.mkdir(exist_ok=True)
    
    arquivo_saida = "/home/anna/tcc/variaveis/Variáveis 1/Saídas/cidades_por_regional.csv"
    
    print("=" * 60)
    print("Listando cidades por regional")
    print("=" * 60)
    
    dados = listar_cidades_por_regional(caminho_base)
    
    gerar_arquivo_saida(dados, arquivo_saida)
    
    print("=" * 60)
    print("Processo concluído!")
    print("=" * 60)

if __name__ == "__main__":
    main()
