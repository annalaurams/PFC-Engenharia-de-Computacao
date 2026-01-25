import os
import pandas as pd

def tratar_csv_para_tabela_real(caminho_entrada):
    print(f"\n[*] Processando arquivo: {caminho_entrada}")

    if not os.path.exists(caminho_entrada):
        print(f"[X] Erro: Arquivo '{caminho_entrada}' não encontrado.")
        return

    try:
        # 1. Ler o arquivo bruto
        with open(caminho_entrada, 'r', encoding='latin-1') as f:
            linhas = [linha.strip() for linha in f if ";" in linha]

        if not linhas:
            print("[X] Nenhuma linha com ';' encontrada.")
            return

        # 2. Quebra manual por ponto e vírgula
        dados = [linha.split(";") for linha in linhas]

        # 3. Normaliza o número de colunas
        max_colunas = max(len(linha) for linha in dados)
        dados_normalizados = [
            linha + [""] * (max_colunas - len(linha))
            for linha in dados
        ]

        # 4. Cria DataFrame SEM inferência automática
        df = pd.DataFrame(dados_normalizados)

        # 5. Remove colunas totalmente vazias
        df = df.dropna(axis=1, how="all")

        # 6. PRINT NO TERMINAL
        print("\n" + "=" * 40)
        print(" VISUALIZAÇÃO DO CSV TRATADO ")
        print("=" * 40)
        print(df.to_string(index=False, header=False))
        print("=" * 40 + "\n")

        # 7. Salva CSV final corretamente separado por ;
        nome_saida = caminho_entrada.replace(".csv", "_FINAL.csv")
        df.to_csv(nome_saida, sep=";", index=False, header=False, encoding="utf-8-sig")

        print(f"[✓] Arquivo tratado gerado com sucesso: {nome_saida}")

    except Exception as e:
        print(f"[X] Erro crítico: {e}")

if __name__ == "__main__":
    arquivo_teste = "1982-Alfenas-MG.csv"
    tratar_csv_para_tabela_real(arquivo_teste)
