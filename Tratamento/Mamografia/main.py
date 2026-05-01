import re
import unicodedata
from pathlib import Path

import pandas as pd

ROOT = Path("/home/anna/tcc/Tratamento/Mamografia")
ENTRADA = Path("/home/anna/tcc/Variáveis/Mamografia/Dados")
OUTPUT = ROOT / "tabela_mamografia.csv"
MUNICIPIOS = Path("/home/anna/tcc/Tratamento/Municípios/tabela_municipios_regionais.csv")


FAIXAS: list[tuple[str, list[str]]] = [
    ("0-9", ["ate 9"]),
    ("10-19", ["entre 10 a 14", "entre 15 a 19"]),
    ("20-29", ["entre 20 a 24", "entre 25 a 29"]),
    ("30-39", ["entre 30 a 34", "entre 35 a 39"]),
    ("40-49", ["entre 40 a 44", "entre 45 a 49"]),
    ("50-59", ["entre 50 a 54", "entre 55 a 59"]),
    ("60-69", ["entre 60 a 64", "entre 65 a 69"]),
    ("70+", ["entre 70 a 74", "entre 75 a 79", "acima de 79"]),
]


# ________________________________________________________________________________
# Texto


def remover_acentos(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", texto)
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def normalizar_municipio(valor: object) -> object:
    if not isinstance(valor, str):
        return valor

    texto = remover_acentos(valor).lower().strip()
    texto = re.sub(r"[^0-9a-z]+", " ", texto)
    return " ".join(texto.split())


def normalizar_coluna(texto: str) -> str:
    texto = normalizar_municipio(texto)
    return "" if not isinstance(texto, str) else texto


def extrair_ano_do_nome_arquivo(path: Path) -> int:
    m = re.search(r"(19|20)\d{2}", path.stem)
    if not m:
        raise ValueError(f"Ano não encontrado no nome do arquivo: {path.name}")
    return int(m.group(0))


def extrair_codigo_municipio(valor: object) -> tuple[str | None, str | None]:
    if not isinstance(valor, str):
        return None, None

    texto = valor.strip().strip("\ufeff")
    m = re.match(r"\s*(\d{1,7})\s+(.*)$", texto)
    if not m:
        return None, None

    codigo = m.group(1)
    municipio = m.group(2)
    return codigo, municipio



# ________________________________________________________________________________
# Tratamento

def carregar_por_ano(arquivo: Path) -> pd.DataFrame:
    ano = extrair_ano_do_nome_arquivo(arquivo)
    tabela = pd.read_csv(
        arquivo,
        sep=";",
        encoding="latin1",
        dtype=str,
    )
    tabela.columns = tabela.columns.str.strip()

    coluna_municipio = tabela.columns[0]
    extraido = tabela[coluna_municipio].map(extrair_codigo_municipio)
    tabela[["codigo", "municipio_raw"]] = pd.DataFrame(extraido.tolist(), index=tabela.index)
    tabela = tabela.dropna(subset=["codigo", "municipio_raw"]).copy()

    tabela["codigo"] = tabela["codigo"].astype(str).str.strip().str.zfill(7)

    tabela["municipios"] = tabela["municipio_raw"].map(normalizar_municipio)
    tabela = tabela.drop(columns=["municipio_raw"])

    mapa_colunas: dict[str, str] = {normalizar_coluna(c): c for c in tabela.columns}

    saida = tabela[["codigo", "municipios"]].copy()

    for faixa, padroes in FAIXAS:
        colunas_origem: list[str] = []
        for p in padroes:
            for chave_norm, col_original in mapa_colunas.items():
                if p in chave_norm:
                    colunas_origem.append(col_original)

        colunas_origem = sorted(set(colunas_origem))
        if not colunas_origem:
            saida[faixa] = 0
            continue

        valores = (
            tabela[colunas_origem]
            .apply(lambda s: pd.to_numeric(s, errors="coerce"), axis=0)
            .fillna(0)
            .sum(axis=1)
        )
        saida[faixa] = valores.astype(int)

    colunas_faixas = [f for f, _ in FAIXAS]
    saida = (
        saida.groupby(["codigo", "municipios"], as_index=False)[colunas_faixas]
        .sum()
        .reset_index(drop=True)
    )

    saida = saida.rename(columns={c: f"{ano}_{c}" for c in colunas_faixas})
    return saida



# ________________________________________________________________________________
# Criação de colunas

def gerar_tabela() -> pd.DataFrame:
    arquivos = sorted(ENTRADA.glob("mamografia_*.csv"))
    if not arquivos:
        raise FileNotFoundError(f"Nenhum arquivo encontrado em {ENTRADA}")

    tabela: pd.DataFrame | None = None
    for arquivo in arquivos:
        df_ano = carregar_por_ano(arquivo)
        if tabela is None:
            tabela = df_ano
            continue

        tabela = tabela.merge(df_ano, on=["codigo"], how="outer", suffixes=("", "_dup"))

        if "municipios_dup" in tabela.columns:
            tabela["municipios"] = tabela["municipios"].fillna(tabela["municipios_dup"])
            tabela = tabela.drop(columns=["municipios_dup"])

    assert tabela is not None

    ordem_faixas = [f for f, _ in FAIXAS]
    anos = sorted({int(c.split("_")[0]) for c in tabela.columns if re.match(r"^(19|20)\d{2}_", str(c))})

    colunas_ano = [
        f"{ano}_{faixa}"
        for ano in anos
        for faixa in ordem_faixas
        if f"{ano}_{faixa}" in tabela.columns
    ]
    tabela = tabela[["municipios", "codigo"] + colunas_ano]

    if colunas_ano:
        tabela[colunas_ano] = (
            tabela[colunas_ano]
            .apply(lambda s: pd.to_numeric(s, errors="coerce"), axis=0)
            .fillna(0)
            .astype(int)
        )

    totais: dict[str, pd.Series] = {}
    colunas_total_ano: list[str] = []
    for ano in anos:
        cols = [f"{ano}_{faixa}" for faixa in ordem_faixas if f"{ano}_{faixa}" in tabela.columns]
        if not cols:
            continue
        col_total = f"total_{ano}"
        totais[col_total] = tabela[cols].sum(axis=1).astype(int)
        colunas_total_ano.append(col_total)

    if colunas_total_ano:
        totais["total"] = pd.concat([totais[c] for c in colunas_total_ano], axis=1).sum(axis=1).astype(int)
    else:
        totais["total"] = pd.Series(0, index=tabela.index, dtype=int)

    tabela = pd.concat([tabela, pd.DataFrame(totais)], axis=1)

    colunas_ordenadas: list[str] = ["municipios", "codigo"]
    for ano in anos:
        cols = [f"{ano}_{faixa}" for faixa in ordem_faixas if f"{ano}_{faixa}" in tabela.columns]
        colunas_ordenadas.extend(cols)
        col_total = f"total_{ano}"
        if col_total in tabela.columns:
            colunas_ordenadas.append(col_total)
    colunas_ordenadas.append("total")
    tabela = tabela[colunas_ordenadas]

    tabela = tabela.sort_values(["codigo"]).reset_index(drop=True)

    try:
        df_mun = pd.read_csv(MUNICIPIOS, dtype=str)
        if "municipio_normalizado" in df_mun.columns:
            mapa = df_mun.set_index("municipio_normalizado")["codigo_ibge"].to_dict()
            tabela["codigo_ibge_mapeado"] = tabela["municipios"].map(mapa)

            tabela["codigo"] = tabela["codigo_ibge_mapeado"].fillna(tabela["codigo"])

            mask_short = tabela["codigo"].notna() & (tabela["codigo"].str.len() < 7)
            if mask_short.any():
                cods = df_mun["codigo_ibge"].astype(str)

                def expand_codigo(c):
                    if not isinstance(c, str) or len(c) >= 7:
                        return c
                    matches = cods[cods.str.endswith(c)]
                    if len(matches) == 1:
                        return matches.iloc[0]
                    return c

                tabela.loc[mask_short, "codigo"] = tabela.loc[mask_short, "codigo"].map(expand_codigo)

            tabela = tabela.drop(columns=[c for c in ["codigo_ibge_mapeado"] if c in tabela.columns])
    except FileNotFoundError:
        pass

    tabela = tabela.rename(columns={"municipios": "Municípios", "codigo": "Código"})
    return tabela



# ________________________________________________________________________________
# Operações

def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    df = gerar_tabela()
    df.to_csv(OUTPUT, index=False, encoding="utf-8-sig")
    print(f"Arquivo gerado: {OUTPUT} (linhas={len(df)}, colunas={len(df.columns)})")


if __name__ == "__main__":
    main()
