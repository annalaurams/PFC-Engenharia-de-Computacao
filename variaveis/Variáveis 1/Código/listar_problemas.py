import csv
from collections import Counter
import unicodedata
import re

def remover_acentos(texto):
    nfkd = unicodedata.normalize('NFKD', texto)
    return ''.join([c for c in nfkd if not unicodedata.combining(c)])

def normalizar_cidade(cidade):
    cidade = cidade.strip()
    cidade = re.sub(r'\s*-\s*MG\s*$', '', cidade, flags=re.IGNORECASE)
    cidade = remover_acentos(cidade)
    cidade = cidade.lower()
    cidade = re.sub(r'\s+', ' ', cidade)
    return cidade.strip()

arquivo_original = "/home/anna/tcc/variaveis/Variáveis 1/Saídas/cidades_por_regional.csv"
arquivo_saida = "/home/anna/tcc/variaveis/Variáveis 1/Saídas/PROBLEMAS_ENCONTRADOS.csv"

registros = []
with open(arquivo_original, 'r', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        regional = row['Regional']
        cidade_original = row['Cidade']
        cidade_norm = normalizar_cidade(cidade_original)
        registros.append((regional, cidade_original, cidade_norm))

# Contar ocorrências normalizadas por regional
contador = Counter((reg, cnorm) for reg, _, cnorm in registros)

problemas = []

# 1. Duplicatas (mesma cidade normalizada, mesma regional, aparece mais de 1x)
for (regional, cidade_norm), count in contador.items():
    if count > 1:

        nomes = [orig for reg, orig, cn in registros if reg == regional and cn == cidade_norm]
        problemas.append({
            'tipo': 'DUPLICATA',
            'regional': regional,
            'cidade_norm': cidade_norm,
            'nomes_originais': nomes,
            'count': count,
            'obs': f'Mesma cidade aparece {count} vezes com nomes diferentes'
        })

# 2. Cidades com nomes muito similares na mesma regional (distância <= 2)
from collections import defaultdict
cidades_por_regional = defaultdict(list)
for regional, cidade_orig, cidade_norm in registros:
    cidades_por_regional[regional].append((cidade_orig, cidade_norm))

def calcular_distancia(s1, s2):
    """Distância de Levenshtein simples"""
    if len(s1) < len(s2):
        return calcular_distancia(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    linha_anterior = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        linha_atual = [i + 1]
        for j, c2 in enumerate(s2):
            linha_atual.append(min(
                linha_anterior[j + 1] + 1,  # deletar
                linha_atual[j] + 1,  # inserir
                linha_anterior[j] + (c1 != c2)  # substituir
            ))
        linha_anterior = linha_atual
    return linha_anterior[-1]

pares_ja_adicionados = set()

for regional, cidades in cidades_por_regional.items():
    cidades_norm_unicas = list(set(cn for _, cn in cidades))
    
    for i, c1 in enumerate(cidades_norm_unicas):
        for c2 in cidades_norm_unicas[i+1:]:
            dist = calcular_distancia(c1, c2)
            
            # Se distância <= 2 e não muito diferentes em tamanho
            if dist <= 2 and abs(len(c1) - len(c2)) <= 3:
                nomes1 = [orig for orig, cn in cidades if cn == c1]
                nomes2 = [orig for orig, cn in cidades if cn == c2]
                
                # Criar chave única para evitar duplicatas
                chave = (regional, tuple(sorted([c1, c2])))
                if chave not in pares_ja_adicionados:
                    pares_ja_adicionados.add(chave)
                    problemas.append({
                        'tipo': 'SIMILAR',
                        'regional': regional,
                        'cidade_norm': f'{c1} / {c2}',
                        'nomes_originais': nomes1 + nomes2,
                        'count': len(nomes1) + len(nomes2),
                        'obs': f'Nomes similares (distância: {dist}), provável erro de digitação'
                    })

with open(arquivo_saida, 'w', newline='', encoding='utf-8') as f:
    writer =csv.writer(f)
    writer.writerow(['Tipo', 'Regional', 'Nome da Pasta (Original)', 'Cidade Normalizada', 'Descrição do Problema'])
    
    for p in problemas:
        for nome_orig in p['nomes_originais']:
            writer.writerow([
                p['tipo'],
                p['regional'],
                nome_orig,
                p['cidade_norm'],
                p['obs']
            ])

print("=" * 100)
print("PROBLEMAS ENCONTRADOS NAS PASTAS")
print("=" * 100)
print(f"\nTotal de registros: {len(registros)}")
print(f"Problemas identificados: {len(problemas)}")
print("\n")

for idx, p in enumerate(problemas, 1):
    print(f"{idx}. [{p['tipo']}] Regional: {p['regional']}")
    print(f"   Cidade(s) normalizada(s): {p['cidade_norm']}")
    print(f"   Pastas encontradas:")
    for nome in p['nomes_originais']:
        print(f"      📁 {nome}")
    print(f"  {p['obs']}")
    print()

print(f"Relatório salvo em: {arquivo_saida}")
print("=" * 100)
