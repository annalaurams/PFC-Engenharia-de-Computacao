# pyright: reportUnknownMemberType=false

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

PASTA_RAIZ = Path("/home/anna/tcc/Variáveis/Mortalidade/Cidades Atendidas por Cada Regional")
PASTA_SAIDA = Path("/home/anna/tcc/Tratamento/Mortalidade")
ARQUIVO_SAIDA = PASTA_SAIDA / "mortalidade_agrupada_ano_faixa_etaria.csv"
ARQUIVO_MUNICIPIOS = Path(
    "/home/anna/tcc/Tratamento/Municípios/municipios_regionais_normalizados.csv"
)

ANOS = list(range(1979, 2025))
FAIXAS_ETARIAS = [
    "0-9",
    "10-19",
    "20-29",
    "30-39",
    "40-49",
    "50-59",
    "60-69",
    "70-79",
    "80 ou mais",
]

PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

PADRAO_ANO_ARQUIVO = re.compile(r"^(19\d{2}|20\d{2})")
PADRAO_INTERVALO = re.compile(r"(\d{1,2})\s*(?:a|-|ate|até)\s*(\d{1,2})", re.IGNORECASE)


def normalizar_texto(texto: str) -> str:
    txt = str(texto).strip()
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
    txt = txt.lower()
    txt = txt.replace("_", " ").replace("–", "-").replace("—", "-")
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def remover_sufixo_mg(texto: str) -> str:
    txt = normalizar_texto(texto)
    txt = re.sub(r"\s*-\s*mg$", "", txt)
    txt = re.sub(r"\s+mg$", "", txt)
    return txt.strip()


def normalizar_chave_municipio(texto: str) -> str:
    txt = remover_sufixo_mg(texto)
    txt = txt.replace("-", " ").replace("'", " ")
    txt = re.sub(r"\s+", " ", txt).strip()
    aliases = {
        "dona eusebia": "dona euzebia",
        "sao thome das letras": "sao tome das letras",
        "brasopolis": "brazopolis",
    }
    return aliases.get(txt, txt)


def split_csv_line(linha: str) -> list[str]:
    partes = [c.strip() for c in str(linha).split(";")]
    while partes and partes[-1] == "":
        partes.pop()
    return partes


def extrair_ano_do_arquivo(nome_arquivo: str):
    m = PADRAO_ANO_ARQUIVO.search(nome_arquivo)
    if not m:
        return None
    ano = int(m.group(1))
    return ano if ano in ANOS else None

def para_numero(valor):
    if valor is None:
        return np.nan
    txt = str(valor).strip()
    if txt == "":
        return np.nan
    txt = txt.replace(".", "").replace(",", ".")
    return pd.to_numeric(txt, errors="coerce")


def mapear_faixa_etaria(rotulo: str):
    t = normalizar_texto(rotulo)
    if not t or t in {"cid", "ci", "total"}:
        return None

    if "80" in t and ("mais" in t or "+" in t):
        return "80 ou mais"

    m = PADRAO_INTERVALO.search(t)
    if m:
        ini = int(m.group(1))
        fim = int(m.group(2))

        if ini >= 80 or fim >= 80:
            return "80 ou mais"

        if ini < 0:
            return None

        if ini <= 79:
            base = (ini // 10) * 10
            if base <= 70:
                return f"{base}-{base + 9}"

    if t.isdigit():
        idade = int(t)
        if idade >= 80:
            return "80 ou mais"
        base = (idade // 10) * 10
        if base <= 70:
            return f"{base}-{base + 9}"

    return None


def ler_linhas_csv(csv_path: Path):
    try:
        with open(csv_path, "r", encoding="latin-1", errors="replace") as f:
            return [ln.rstrip("\n") for ln in f]
    except Exception:
        with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
            return [ln.rstrip("\n") for ln in f]


def extrair_header_valores_csv(csv_path: Path):
    linhas = ler_linhas_csv(csv_path)

    if len(linhas) >= 4:
        cabecalho = split_csv_line(linhas[2])
        valores = split_csv_line(linhas[3])
    else:
        cabecalho, valores = [], []

    if not cabecalho or not valores or ";" not in linhas[2] if len(linhas) > 2 else True:
        idx_cabecalho = None
        for i, linha in enumerate(linhas):
            if linha.strip().startswith("CID;"):
                idx_cabecalho = i
                break

        if idx_cabecalho is None or idx_cabecalho + 1 >= len(linhas):
            return [], []

        cabecalho = split_csv_line(linhas[idx_cabecalho])
        valores = split_csv_line(linhas[idx_cabecalho + 1])

    cabecalho = cabecalho[1:] if len(cabecalho) > 1 else []
    valores = valores[1:] if len(valores) > 1 else []

    return cabecalho, valores

def consolidar_mortalidade(pasta_raiz: Path) -> pd.DataFrame:
    registros = []

    regionais = [p for p in pasta_raiz.iterdir() if p.is_dir()]
    for regional_dir in sorted(regionais):
        regional = regional_dir.name

        municipios = [p for p in regional_dir.iterdir() if p.is_dir()]
        for municipio_dir in sorted(municipios):
            municipio = municipio_dir.name
            registro = {
                "Município": municipio,
                "Regional de Saúde": regional,
            }

            arquivos_csv = sorted(municipio_dir.glob("*.csv"))
            for csv_path in arquivos_csv:
                ano = extrair_ano_do_arquivo(csv_path.name)
                if ano is None:
                    continue

                cabecalho, valores = extrair_header_valores_csv(csv_path)
                if not cabecalho or not valores:
                    continue

                for i, rotulo_faixa in enumerate(cabecalho):
                    faixa = mapear_faixa_etaria(rotulo_faixa)
                    if faixa is None:
                        continue

                    valor = para_numero(valores[i] if i < len(valores) else None)
                    if pd.isna(valor):
                        continue

                    coluna = f"{ano}_{faixa}"
                    valor_anterior = registro.get(coluna, np.nan)
                    if pd.isna(valor_anterior):
                        registro[coluna] = float(valor)
                    else:
                        registro[coluna] = float(valor_anterior) + float(valor)

            registros.append(registro)

    return pd.DataFrame(registros)

def organizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    colunas_ano_faixa = [f"{ano}_{faixa}" for ano in ANOS for faixa in FAIXAS_ETARIAS]

    faltantes = [c for c in colunas_ano_faixa if c not in df.columns]
    if faltantes:
        df = pd.concat(
            [df, pd.DataFrame(np.nan, index=df.index, columns=faltantes)],
            axis=1,
        )

    df["TOTAL_MORTES"] = df[colunas_ano_faixa].sum(axis=1, min_count=1)

    colunas_finais = ["Município", "Regional de Saúde"] + colunas_ano_faixa + ["TOTAL_MORTES"]
    extras = [c for c in df.columns if c not in colunas_finais]
    colunas_finais.extend(extras)

    df = df[colunas_finais].copy()
    df = df.sort_values(["Regional de Saúde", "Município"], na_position="last").reset_index(drop=True)
    return df


def carregar_mapa_codigos(arquivo_municipios: Path = ARQUIVO_MUNICIPIOS) -> dict[str, str]:
    if not arquivo_municipios.exists():
        raise FileNotFoundError(
            f"Arquivo de municípios não encontrado: {arquivo_municipios}"
        )

    ref = pd.read_csv(arquivo_municipios, dtype={"codigo_ibge": "string"})
    colunas_necessarias = {"municipio_normalizado", "codigo_ibge"}
    faltantes = colunas_necessarias - set(ref.columns)
    if faltantes:
        raise ValueError(
            "Arquivo de municípios sem colunas obrigatórias: "
            f"{sorted(faltantes)}"
        )

    ref = ref.dropna(subset=["municipio_normalizado", "codigo_ibge"]).copy()
    ref["municipio_normalizado"] = (
        ref["municipio_normalizado"].astype(str).map(normalizar_chave_municipio)
    )
    ref["codigo_ibge"] = ref["codigo_ibge"].astype(str).str.strip()
    ref = ref.drop_duplicates(subset=["municipio_normalizado"], keep="first")
    return dict(zip(ref["municipio_normalizado"], ref["codigo_ibge"]))


def adicionar_codigo_municipio(df: pd.DataFrame, mapa_codigos: dict[str, str]) -> pd.DataFrame:
    if "Município" not in df.columns:
        raise ValueError("DataFrame não possui a coluna obrigatória 'Município'.")

    chaves = df["Município"].astype(str).map(normalizar_chave_municipio)
    codigos = chaves.map(mapa_codigos)
    sem_correspondencia = (
        df.loc[codigos.isna(), "Município"].astype(str).dropna().sort_values().unique().tolist()
    )

    if sem_correspondencia:
        print(
            "[AVISO] Municípios sem correspondência de código "
            f"({len(sem_correspondencia)}):"
        )
        for municipio in sem_correspondencia:
            print(f"  - {municipio}")
    else:
        print("[OK] Todos os municípios tiveram código encontrado.")

    df = df.drop(columns=["CÓDIGO"], errors="ignore").copy()
    pos_municipio = list(df.columns).index("Município") + 1
    df.insert(pos_municipio, "CÓDIGO", codigos)
    return df


def main() -> None:
    print(f"Pasta raiz: {PASTA_RAIZ}")
    print(f"Arquivo de saída: {ARQUIVO_SAIDA}")

    df = consolidar_mortalidade(PASTA_RAIZ)
    print("Dimensão após consolidação:", df.shape)

    df = organizar_colunas(df)

    # Município: minúsculas sem acento e sem sufixo "-mg"
    df["Município"] = df["Município"].map(remover_sufixo_mg)
    mapa_codigos = carregar_mapa_codigos()
    df = adicionar_codigo_municipio(df, mapa_codigos=mapa_codigos)

    print("Dimensão final:", df.shape)
    print("Linhas (municípios):", len(df))
    print("Municípios únicos:", df["Município"].nunique())
    print("Regionais únicas:", df["Regional de Saúde"].nunique(dropna=True))
    print("Soma de TOTAL_MORTES:", df["TOTAL_MORTES"].sum(skipna=True))

    df = df.rename(columns={"Município": "MUNICÌPIO"})

    df.to_csv(ARQUIVO_SAIDA, sep=",", index=False, encoding="utf-8")

    print(f"\nCSV criado: {ARQUIVO_SAIDA}")
    print(f"Dimensão exportada: {df.shape}")


if __name__ == "__main__":
    main()
