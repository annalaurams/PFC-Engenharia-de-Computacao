import pandas as pd

def calcular_estatisticas_populacao(caminho_arquivo):
    try:
        # 1. Carregamento dos dados
        df = pd.read_csv(caminho_arquivo)
        
        # 2. Definição das colunas de interesse (Anos de Censo - Faixa 30-39)
        colunas_censo = [
             '2022_30-39'
        ]
        
        # 3. Limpeza e Conversão
        # Garante que todas as colunas de anos sejam numéricas (float ou int)
        # errors='coerce' transforma textos inválidos em NaN, e fillna(0) transforma NaN em 0
        for col in colunas_censo:
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
        # 4. Seleção do DataFrame final para análise
        # Mantemos apenas o necessário: Municípios e os anos
        df_final = df[['MUNICÍPIOS'] + colunas_censo].copy()
        
        # 5. Cálculos de Soma
        # Soma vertical (Total do estado por ano)
        soma_por_ano = df_final[colunas_censo].sum()
        
        # Soma total (Acumulado de todos os anos selecionados)
        total_geral = soma_por_ano.sum()
        
        # 6. Exibição dos Resultados no Terminal
        print("="*50)
        print("RELATÓRIO DE POPULAÇÃO - MINAS GERAIS (30-39 ANOS)")
        print("="*50)
        print("Soma total por ano (Todos os municípios):")
        print(soma_por_ano.map('{:,.0f}'.format)) # Formata com separador de milhar
        print("-" * 50)
        print(f"TOTAL GERAL DO PERÍODO SELECIONADO: {total_geral:,.0f}")
        print("="*50)
        
        return df_final

    except FileNotFoundError:
        print("Erro: O arquivo não foi encontrado no caminho especificado.")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")

# --- Execução do Script ---
caminho = r'/home/anna/tcc/Tratamento/População - Faixa Etária/tabela_populacao_faixa_etaria.csv'
df_processado = calcular_estatisticas_populacao(caminho)

# Se quiser ver as primeiras linhas do resultado final:
if df_processado is not None:
    print("\nVisualização das primeiras linhas do DataFrame:")
    print(df_processado.head())