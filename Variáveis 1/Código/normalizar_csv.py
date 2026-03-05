import csv
import unicodedata
import re

def remover_acentos(texto):
  
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])

def normalizar_cidade(cidade):

    # Remove espaços extras
    cidade = cidade.strip()
    
    # Remove o -MG do final
    cidade = re.sub(r'\s*-\s*MG\s*$', '', cidade, flags=re.IGNORECASE)
    
    # Remove acentos
    cidade = remover_acentos(cidade)
    
    # Converte para minúsculas
    cidade = cidade.lower()
    
    # Remove espaços extras
    cidade = re.sub(r'\s+', ' ', cidade)
    cidade = cidade.strip()
    
    return cidade

def normalizar_csv(arquivo_entrada, arquivo_saida):

    with open(arquivo_entrada, 'r', encoding='utf-8') as f_in:
        reader = csv.DictReader(f_in)
        
        with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f_out:
            writer = csv.writer(f_out)
            writer.writerow(['Regional', 'Cidade'])
            
            for row in reader:
                regional = row['Regional']
                cidade = row['Cidade']
                cidade_normalizada = normalizar_cidade(cidade)
                
                writer.writerow([regional, cidade_normalizada])
    
    print(f"Arquivo normalizado gerado: {arquivo_saida}")

def main():
    arquivo_entrada = "/home/anna/Documentos/PFC I/Variáveis 1/Saídas/cidades_por_regional.csv"
    arquivo_saida = "/home/anna/Documentos/PFC I/Variáveis 1/Saídas/cidades_por_regional_normalizado.csv"
    
    print("=" * 80)
    print("Normalizando arquivo CSV")
    print("=" * 80)
    print("\nConvertendo para: minúsculas, sem acentos, sem -MG\n")
    
    normalizar_csv(arquivo_entrada, arquivo_saida)
    
    print("\n" + "=" * 80)
    print("Processo concluído!")
    print("=" * 80)

if __name__ == "__main__":
    main()
