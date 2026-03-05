import subprocess
import sys
import os
from pathlib import Path

def executar(script, descricao):
    print("\n" + "=" * 80)
    print(f"  {descricao}")
    print("=" * 80)
    
    resultado = subprocess.run([sys.executable, script], capture_output=False)
    
    if resultado.returncode != 0:
        print(f" Erro ao executar {script}")
        return False
    
    return True

def main():
    pasta_saidas = Path("/home/anna/Documentos/PFC I/Variáveis 1/Saídas")
    pasta_saidas.mkdir(exist_ok=True)
    
    print("\n" + " " * 40)
    print("ANÁLISE COMPLETA DE CIDADES POR REGIONAL")
    print(" " * 40)
    
    scripts = [
        ("cidades.py", "1. Gerando lista de cidades por regional"),
        ("normalizar_csv.py", "2. Normalizando nomes das cidades"),
        ("listar_problemas.py", "3. Identificando problemas (duplicatas e erros)")
    ]
    
    for script, descricao in scripts:
        if not executar(script, descricao):
            print("\nProcesso interrompido devido a erro.")
            sys.exit(1)
    
    print("\n" + "=" * 80)
    print("\nANÁLISE COMPLETA CONCLUÍDA!")
    print("=" * 80)
    print("\n📁 Arquivos gerados na pasta 'Saídas':")
    print("   • cidades_por_regional.csv - Lista original de todas as cidades")
    print("   • cidades_por_regional_normalizado.csv - Lista normalizada")
    print("   • PROBLEMAS_ENCONTRADOS.csv - Problemas identificados")
    print("\n Verifique o arquivo PROBLEMAS_ENCONTRADOS.csv para ver se ainda há erros.")
    print("=" * 80 + "\n")

if __name__ == "__main__":
    main()
