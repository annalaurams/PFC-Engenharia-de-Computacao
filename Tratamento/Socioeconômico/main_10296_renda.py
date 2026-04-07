# pyright: reportUnknownMemberType=false

import re
import unicodedata
from pathlib import Path

import pandas as pd

ARQUIVO_ENTRADA = Path("/home/anna/tcc/Variáveis/Socioeconômica/tabela_10296_renda.csv")
ARQUIVO_MUNICIPIOS = Path("/home/anna/tcc/Tratamento/Municípios/tabela_municipios_regionais.csv")

PASTA_SAIDA = Path("/home/anna/tcc/Tratamento/Socioeconômico")
ARQUIVO_SAIDA = PASTA_SAIDA / "tabela_10296_renda.csv"


ORDEM_CATEGORIAS = [
    "Até 1/4 de salário mínimo",
    "Mais de 1/4 a 1/2 salário mínimo",
    "Mais de 1/2 a 1 salário mínimo",
    "Mais de 1 a 2 salários mínimos",
    "Mais de 2 a 3 salários mínimos",
    "Mais de 3 a 5 salários mínimos",
    "Mais de 5 a 10 salários mínimos",
    "Mais de 10 a 15 salários mínimos",
    "Mais de 15 a 20 salários mínimos",
    "Mais de 20 salários mínimos",
    "Sem rendimento",
    "Total",
]


def remover_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def normalizar_municipio(valor: object) -> object:
    if not isinstance(valor, str):
        return valor

    txt = valor.strip()
    # remove sufixos tipo "(MG)" e variações
    txt = re.sub(r"\s*\(\s*mg\s*\)\s*$", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\s*-\s*mg\s*$", "", txt, flags=re.IGNORECASE)
    txt = re.sub(r"\s+mg\s*$", "", txt, flags=re.IGNORECASE)

    txt = remover_acentos(txt).lower()
    # sem pontuação
    txt = re.sub(r"[^0-9a-z]+", " ", txt)
    txt = " ".join(txt.split())

    aliases = {
        "barao do monte alto": "barao de monte alto",
    }
    return aliases.get(txt, txt)


def extrair_ano_do_arquivo(path: Path) -> int | None:
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            primeiras = "\n".join([next(f) for _ in range(15)])
    except StopIteration:
        return None
    except Exception:
        return None

    anos = re.findall(r"\b(19\d{2}|20\d{2})\b", primeiras)
    return int(anos[-1]) if anos else None


def carregar_mapa_codigo_ibge() -> dict[str, int]:
    if not ARQUIVO_MUNICIPIOS.exists():
        raise FileNotFoundError(f"Arquivo de municípios não encontrado: {ARQUIVO_MUNICIPIOS}")

    ref = pd.read_csv(ARQUIVO_MUNICIPIOS, encoding="utf-8")
    obrig = {"codigo_ibge", "municipio_normalizado"}
    falt = obrig - set(ref.columns)
    if falt:
        raise ValueError(f"Arquivo de municípios sem colunas obrigatórias: {sorted(falt)}")

    ref = ref.dropna(subset=["codigo_ibge", "municipio_normalizado"]).copy()
    ref["municipio_normalizado"] = ref["municipio_normalizado"].astype(str).map(normalizar_municipio)
    ref["codigo_ibge"] = pd.to_numeric(ref["codigo_ibge"], errors="coerce")
    ref = ref.dropna(subset=["codigo_ibge", "municipio_normalizado"])

    ref = ref.drop_duplicates(subset=["municipio_normalizado"], keep="first")
    return dict(zip(ref["municipio_normalizado"].astype(str), ref["codigo_ibge"].astype(int), strict=False))


def para_numero(valor: object) -> float:
    if valor is None:
        return 0.0
    txt = str(valor).strip()
    if txt in {"", "-"}:
        return 0.0
    # valores vêm como inteiros em string
    txt = txt.replace(".", "").replace(",", ".")
    return float(pd.to_numeric(txt, errors="coerce") or 0)


def ler_base() -> pd.DataFrame:
    if not ARQUIVO_ENTRADA.exists():
        raise FileNotFoundError(f"Arquivo de entrada não encontrado: {ARQUIVO_ENTRADA}")

    # O arquivo possui linhas iniciais de descrição; os dados começam após a linha com dimensões.
    df = pd.read_csv(
        ARQUIVO_ENTRADA,
        sep=";",
        header=None,
        skiprows=6,
        encoding="utf-8",
        quotechar='"',
        dtype=str,
        engine="python",
    )

    # Esperado: 4 colunas (UF/Mun, Classe, Total, Mulheres). Mantém a 1a medida (Total).
    if df.shape[1] < 3:
        raise ValueError("Formato inesperado: menos de 3 colunas após pular cabeçalho")

    df = df.iloc[:, :4].copy() if df.shape[1] >= 4 else df.iloc[:, :3].copy()
    df.columns = ["uf_municipio", "classe", "valor_total", "valor_alt"][: df.shape[1]]

    df = df.dropna(subset=["uf_municipio", "classe"]).copy()
    df["uf_municipio"] = df["uf_municipio"].astype(str).str.strip()
    df["classe"] = df["classe"].astype(str).str.strip()

    # Remove linha agregada do estado.
    df = df[df["uf_municipio"].str.lower() != "minas gerais"].copy()

    # Mantém apenas municípios (no arquivo, vêm como "Nome (MG)").
    df = df[
        df["uf_municipio"].str.contains(r"\(\s*mg\s*\)\s*$", case=False, regex=True, na=False)
    ].copy()

    df["Municípios"] = df["uf_municipio"].map(normalizar_municipio)
    df["valor"] = df["valor_total"].map(para_numero)

    return df[["Municípios", "classe", "valor"]]


def gerar_tabela() -> pd.DataFrame:
    ano = extrair_ano_do_arquivo(ARQUIVO_ENTRADA)
    df = ler_base()

    tabela = (
        df.pivot_table(
            index="Municípios",
            columns="classe",
            values="valor",
            aggfunc="sum",
            fill_value=0,
        )
        .reset_index()
    )

    # Adiciona código IBGE
    mapa_codigos = carregar_mapa_codigo_ibge()
    tabela["Código"] = tabela["Municípios"].map(mapa_codigos)

    sem = (
        tabela.loc[tabela["Código"].isna(), "Municípios"]
        .dropna()
        .astype(str)
        .sort_values()
        .unique()
        .tolist()
    )
    if sem:
        print(f"[AVISO] Municípios sem código IBGE ({len(sem)}):")
        for m in sem[:50]:
            print(f"  - {m}")
        if len(sem) > 50:
            print("  ...")

    tabela["Código"] = pd.to_numeric(tabela["Código"], errors="coerce").astype("Int64")
    if ano is not None:
        tabela.insert(2, "Ano", int(ano))

    # Garante que contagens fiquem como inteiros.
    colunas_valor = [c for c in tabela.columns if c not in {"Municípios", "Código", "Ano"}]
    if colunas_valor:
        tabela[colunas_valor] = (
            tabela[colunas_valor]
            .apply(lambda s: pd.to_numeric(s, errors="coerce"), axis=0)
            .fillna(0)
            .astype(int)
        )

    # Ordena categorias
    colunas_categorias = [c for c in tabela.columns if c not in {"Municípios", "Código", "Ano"}]
    ordenadas = [c for c in ORDEM_CATEGORIAS if c in colunas_categorias]
    extras = sorted([c for c in colunas_categorias if c not in set(ordenadas)])
    colunas_final = ["Municípios", "Código"] + (["Ano"] if "Ano" in tabela.columns else []) + ordenadas + extras
    tabela = tabela[colunas_final]

    tabela = tabela.sort_values(["Código", "Municípios"], na_position="last").reset_index(drop=True)
    return tabela


def main() -> None:
    PASTA_SAIDA.mkdir(parents=True, exist_ok=True)
    tabela = gerar_tabela()
    tabela.to_csv(ARQUIVO_SAIDA, index=False, encoding="utf-8-sig")
    print(f"CSV criado: {ARQUIVO_SAIDA} (linhas={len(tabela)}, colunas={len(tabela.columns)})")


if __name__ == "__main__":
    main()
