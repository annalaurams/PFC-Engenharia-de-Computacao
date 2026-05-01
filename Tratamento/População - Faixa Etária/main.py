from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
ENTRADA = ROOT / "Variáveis" / "População - Faixa Etária"
SAIDA = Path(__file__).with_name("tabela_populacao_faixa_etaria.csv")
MUNICIPIOS = ROOT / "Tratamento" / "Municípios" / "tabela_municipios_regionais.csv"

CHAVES = ["Sigla", "Código", "Município"]
FAIXAS = [
    "0 a 9",
    "10 a 19",
    "20 a 29",
    "30 a 39",
    "40 a 49",
    "50 a 59",
    "60 a 69",
    "70 anos ou mais",
]

FAIXA_SAIDA = {
    "0 a 9": "0-9",
    "10 a 19": "10-19",
    "20 a 29": "20-29",
    "30 a 39": "30-39",
    "40 a 49": "40-49",
    "50 a 59": "50-59",
    "60 a 69": "60-69",
    "70 anos ou mais": "70 ou mais",
}


# ________________________________________________________________________________
# Texto

def normalizar_texto(texto: str) -> str:
    texto = "" if pd.isna(texto) else str(texto).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(caractere for caractere in texto if not unicodedata.combining(caractere))
    return texto.lower()


def normalizar_chave_municipio(texto: str) -> str:
    chave = normalizar_texto(texto)
    chave = chave.replace("-", " ").replace("'", " ")
    chave = re.sub(r"\s+", " ", chave).strip()
    aliases = {
        "dona eusebia": "dona euzebia",
        "sao thome das letras": "sao tome das letras",
        "brasopolis": "brazopolis",
    }
    return aliases.get(chave, chave)


# ________________________________________________________________________________
# Arquivos

def carregar_mapa_codigos(arquivo_municipios: Path = MUNICIPIOS) -> dict[str, str]:
    if not arquivo_municipios.exists():
        raise FileNotFoundError(f"Arquivo de municípios não encontrado: {arquivo_municipios}")

    df_ref = pd.read_csv(arquivo_municipios, dtype={"codigo_ibge": "string"})
    colunas_necessarias = {"municipio_normalizado", "codigo_ibge"}
    faltantes = colunas_necessarias - set(df_ref.columns)
    if faltantes:
        raise ValueError(
            "Arquivo de municípios sem colunas obrigatórias: "
            f"{sorted(faltantes)}"
        )

    df_ref = df_ref.dropna(subset=["municipio_normalizado", "codigo_ibge"]).copy()
    df_ref["municipio_normalizado"] = (
        df_ref["municipio_normalizado"].astype(str).map(normalizar_chave_municipio)
    )
    df_ref["codigo_ibge"] = df_ref["codigo_ibge"].astype(str).str.strip()
    df_ref = df_ref.drop_duplicates(subset=["municipio_normalizado"], keep="first")

    return dict(zip(df_ref["municipio_normalizado"], df_ref["codigo_ibge"]))


def adicionar_coluna_codigo(df: pd.DataFrame, mapa_codigos: dict[str, str]) -> pd.DataFrame:
    if "Município" not in df.columns:
        raise ValueError("DataFrame sem a coluna obrigatória 'Município'.")

    chaves = df["Município"].astype(str).map(normalizar_chave_municipio)
    codigos = chaves.map(mapa_codigos)

    sem_correspondencia = (
        df.loc[codigos.isna(), "Município"].astype(str).dropna().sort_values().unique().tolist()
    )

    if sem_correspondencia:
        print(f"[AVISO] Municípios sem correspondência de código ({len(sem_correspondencia)}):")
        for municipio in sem_correspondencia:
            print(f"  - {municipio}")
    else:
        print("[OK] Todos os municípios tiveram código encontrado.")

    df = df.drop(columns=["CÓDIGO"], errors="ignore").copy()
    pos_municipio = list(df.columns).index("Município") + 1
    df.insert(pos_municipio, "CÓDIGO", codigos)
    return df


# ________________________________________________________________________________
# Tratamento


def limpar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df.columns = [str(coluna).strip() for coluna in df.columns]
    return df.loc[:, ~df.columns.str.match(r"^Unnamed")].copy()

def ler_arquivo_csv(caminho: Path) -> pd.DataFrame:
    return limpar_colunas(pd.read_csv(caminho, sep=";", encoding="utf-8"))

def extrair_ano_e_parte(caminho: Path) -> tuple[int, int]:
    match = re.fullmatch(r"([12])-(\d{4})\.csv", caminho.name)
    if not match:
        raise ValueError(f"Nome de arquivo inesperado: {caminho.name}")
    parte = int(match.group(1))
    ano = int(match.group(2))
    return ano, parte


# ________________________________________________________________________________
# Criação de colunas

def faixa_decenal(nome_coluna: str) -> str | None:
    intervalo = re.search(r"pessoas (\d+) a (\d+) anos", nome_coluna)
    if intervalo:
        inicio = int(intervalo.group(1))
        inicio_decada = (inicio // 10) * 10
        fim_decada = inicio_decada + 9
        return f"{inicio_decada} a {fim_decada}"

    if re.search(r"pessoas 70 anos ou mais", nome_coluna):
        return "70 anos ou mais"

    return None

def nome_coluna_saida(ano: int, faixa: str) -> str:
    return f"{ano}_{FAIXA_SAIDA[faixa]}"

def montar_tabela_ano(ano: int, arquivos_do_ano: dict[int, Path]) -> pd.DataFrame:
    faltando = {1, 2} - set(arquivos_do_ano)
    if faltando:
        raise ValueError(f"Faltam arquivos do ano {ano}: {sorted(faltando)}")

    df_1 = ler_arquivo_csv(arquivos_do_ano[1])
    df_2 = ler_arquivo_csv(arquivos_do_ano[2])

    colunas_parte2 = [col for col in df_2.columns if col not in CHAVES]
    combinado = df_1.merge(df_2[CHAVES + colunas_parte2], on=CHAVES, how="inner")

    resultado_ano = combinado[CHAVES].copy()
    for faixa in FAIXAS:
        resultado_ano[faixa] = 0

    colunas_populacao = [col for col in combinado.columns if col not in CHAVES]
    for coluna in colunas_populacao:
        faixa = faixa_decenal(coluna)
        if faixa is None:
            continue

        resultado_ano[faixa] = (
            resultado_ano[faixa]
            + pd.to_numeric(combinado[coluna], errors="coerce").fillna(0)
        )

    resultado_ano = resultado_ano.rename(
        columns={faixa: nome_coluna_saida(ano, faixa) for faixa in FAIXAS}
    )
    return resultado_ano


# ________________________________________________________________________________
# Operações


def main() -> None:
    arquivos = sorted(ENTRADA.glob("*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo CSV encontrado em: {ENTRADA}")

    arquivos_por_ano: dict[int, dict[int, Path]] = {}
    for arquivo in arquivos:
        ano, parte = extrair_ano_e_parte(arquivo)
        arquivos_por_ano.setdefault(ano, {})[parte] = arquivo

    tabelas_por_ano = [
        montar_tabela_ano(ano, arquivos_por_ano[ano])
        for ano in sorted(arquivos_por_ano)
    ]

    tabela_final = tabelas_por_ano[0].copy()
    for tabela_ano in tabelas_por_ano[1:]:
        colunas_novas = [col for col in tabela_ano.columns if col not in CHAVES]
        tabela_final = tabela_final.merge(
            tabela_ano[CHAVES + colunas_novas],
            on=CHAVES,
            how="outer",
        )

    ordem_colunas = CHAVES + [
        nome_coluna_saida(ano, faixa)
        for ano in sorted(arquivos_por_ano)
        for faixa in FAIXAS
    ]

    tabela_final = tabela_final[ordem_colunas].sort_values("Município").reset_index(drop=True)
    for coluna in tabela_final.columns:
        if coluna not in CHAVES:
            tabela_final[coluna] = tabela_final[coluna].fillna(0).astype(int)

    anos_ordenados = sorted(arquivos_por_ano)
    for ano in anos_ordenados:
        colunas_faixas_ano = [nome_coluna_saida(ano, faixa) for faixa in FAIXAS]
        coluna_total_ano = f"TOTAL_{ano}"
        tabela_final[coluna_total_ano] = tabela_final[colunas_faixas_ano].sum(axis=1).astype(int)

    faixas_todas = [nome_coluna_saida(ano, faixa) for ano in anos_ordenados for faixa in FAIXAS]
    totais_ano = [f"TOTAL_{ano}" for ano in anos_ordenados]
    colunas_com_totais_ano: list[str] = list(CHAVES) + faixas_todas + totais_ano

    tabela_final = tabela_final[colunas_com_totais_ano]

    tabela_final = tabela_final.drop(columns=["Sigla", "Código"])
    tabela_final["Município"] = tabela_final["Município"].map(normalizar_texto)
    mapa_codigos = carregar_mapa_codigos()

    tabela_final = adicionar_coluna_codigo(tabela_final, mapa_codigos=mapa_codigos)
    if "CÓDIGO" in tabela_final.columns:
        tabela_final["CÓDIGO"] = tabela_final["CÓDIGO"].astype(str).str.replace(r"\.0$", "", regex=True)
        tabela_final = tabela_final.rename(columns={"CÓDIGO": "CÓDIGO IBGE"})
    tabela_final = tabela_final.rename(columns={"Município": "MUNICÍPIOS"})

    tabela_final.to_csv(SAIDA, index=False, encoding="utf-8-sig")
    print(f"Pasta de entrada: {ENTRADA}")
    print(f"CSV gerado em: {SAIDA}")
    print(f"Total de linhas: {len(tabela_final)}")


if __name__ == "__main__":
    main()