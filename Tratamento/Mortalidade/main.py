# pyright: reportUnknownMemberType=false

import re
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd

PASTA_RAIZ = Path("/home/anna/tcc/Variáveis/Mortalidade/Cidades Atendidas por Cada Regional")
PASTA_SAIDA = Path("/home/anna/tcc/Tratamento/Mortalidade")
ARQUIVO_SAIDA = PASTA_SAIDA / "tabela_mortalidade_faixa_etaria.csv"
ARQUIVOS_MUNICIPIOS_CANDIDATOS = [
    Path("/home/anna/tcc/Tratamento/Municípios/municipios_regionais_normalizados.csv"),
    Path("/home/anna/tcc/Tratamento/Municípios/tabela_municipios_regionais.csv"),
]

ANOS = list(range(1979, 2025))
FAIXAS_ETARIAS = [
    "0-9",
    "10-19",
    "20-29",
    "30-39",
    "40-49",
    "50-59",
    "60-69",
    "70 ou mais",
]

# O texto do arquivo extraído indica se a consulta foi "em homens" ou "em mulheres".
# Para câncer de mama, normalmente queremos manter apenas "mulheres".
# Use None para não filtrar por sexo.
SEXO_DESEJADO: str | None = "mulheres"

PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

PADRAO_ANO_ARQUIVO = re.compile(r"^(19\d{2}|20\d{2})")
PADRAO_INTERVALO = re.compile(r"(\d{1,3})\s*(?:a|-|ate|até)\s*(\d{1,3})", re.IGNORECASE)
PADRAO_OU_MAIS = re.compile(r"^(\d{1,3})\s*(?:ou\s*mais|\+|e\s*mais|99\+)$", re.IGNORECASE)


def _faixa_final_por_idade_inicial(ini: int) -> str | None:
    """Mapeia idade inicial para a faixa final desejada (0-9, 10-19, ..., 70+)."""
    if ini < 0:
        return None
    if ini < 10:
        return "0-9"
    if ini < 20:
        return "10-19"
    if ini < 30:
        return "20-29"
    if ini < 40:
        return "30-39"
    if ini < 50:
        return "40-49"
    if ini < 60:
        return "50-59"
    if ini < 70:
        return "60-69"
    return "70 ou mais"


def normalizar_texto(texto: str) -> str:
    txt = str(texto).strip()
    txt = unicodedata.normalize("NFKD", txt)
    txt = "".join(ch for ch in txt if not unicodedata.combining(ch))
    txt = txt.lower()
    txt = txt.replace("_", " ").replace("–", "-").replace("—", "-")
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


def _parse_intervalo_idade(rotulo: str) -> tuple[int, int] | None:
    """Extrai (ini, fim) de um rótulo do site (ex: '00 a 04', '70 a 79', '80 ou mais')."""
    t = normalizar_texto(rotulo)

    # Colunas que não são faixas etárias — devem ser ignoradas
    IGNORAR = {
        "cid",
        "ci",
        "total",
        "ignorado",
        "ign",
        "obito",
        "óbito",
        "obitos",
        "óbitos",
        "subtotal",
        "sem informacao",
        "sem informação",
        "ign.",
        "ign",
    }
    if not t or t in IGNORAR:
        return None

    # Ignora qualquer coluna que comece com texto não-numérico
    # (ex: "C50 - MAMA", descrições, etc.)
    if not t[0].isdigit():
        return None

    # Padrão "X ou mais" / "X+" / "99+"
    m_mais = PADRAO_OU_MAIS.search(t)
    if m_mais:
        ini = int(m_mais.group(1))
        return (ini, 999)

    # Padrão intervalo: "X a Y", "X-Y", "X até Y"
    m_int = PADRAO_INTERVALO.search(t)
    if m_int:
        ini = int(m_int.group(1))
        fim = int(m_int.group(2))
        fim = 999 if fim >= 99 else fim
        return (ini, fim)

    # Número puro isolado (algumas tabelas usam apenas o início: "0", "5", "10", ...)
    if t.isdigit():
        idade = int(t)
        return (idade, idade)

    return None


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


def extrair_ano_do_arquivo(nome_arquivo: str) -> int | None:
    m = PADRAO_ANO_ARQUIVO.search(nome_arquivo)
    if not m:
        return None
    ano = int(m.group(1))
    return ano if ano in ANOS else None


def para_inteiro(valor) -> int | None:
    """Converte valor para inteiro, retorna None se inválido ou zero."""
    if valor is None:
        return None
    txt = str(valor).strip()
    if txt == "":
        return None
    txt = txt.replace(".", "").replace(",", "")
    try:
        if not txt.isdigit():
            return None
        n = int(txt)
        return n if n > 0 else None
    except (ValueError, TypeError):
        return None


def mapear_faixa_etaria(rotulo: str) -> str | None:
    """
    Converte rótulo de faixa etária do CSV (ex: '00 a 04', '80 ou mais')
    para a faixa desejada. Retorna None para colunas não-etárias
    (CID, Total, Ignorado, etc.).
    """
    intervalo = _parse_intervalo_idade(rotulo)
    if intervalo is None:
        return None

    ini, fim = intervalo
    if fim < ini:
        return None

    # Evita mapear intervalos muito amplos (ex: 0-99) para uma faixa só.
    # As tabelas do site normalmente são 0-4, 5-9, 10-14, 15-19, 20-29, 30-39, ...
    # A exceção é o "X ou mais".
    if fim != 999 and (fim - ini) > 10:
        return None

    faixa = _faixa_final_por_idade_inicial(int(ini))
    if faixa is None:
        return None

    # Sanidade: garante que a faixa final está dentro do padrão configurado
    if faixa not in set(FAIXAS_ETARIAS):
        return None
    return faixa


def ler_linhas_csv(csv_path: Path) -> list[str]:
    try:
        with open(csv_path, "r", encoding="latin-1", errors="replace") as f:
            return [ln.rstrip("\n") for ln in f]
    except Exception:
        with open(csv_path, "r", encoding="utf-8", errors="replace") as f:
            return [ln.rstrip("\n") for ln in f]


def detectar_sexo_arquivo(csv_path: Path) -> str | None:
    """Tenta detectar 'homens' ou 'mulheres' a partir do texto do arquivo."""
    linhas = ler_linhas_csv(csv_path)
    # Em geral a 1ª linha já traz "em homens" / "em mulheres"
    topo = " ".join(normalizar_texto(ln) for ln in linhas[:3] if ln.strip())
    if "em homens" in topo:
        return "homens"
    if "em mulheres" in topo:
        return "mulheres"
    return None


def _eh_linha_dados_csv(linha: str) -> bool:
    # precisa ter separador e pelo menos 2 campos
    if ";" not in linha:
        return False
    partes = split_csv_line(linha)
    return len(partes) >= 2 and any(p.strip() for p in partes[1:])


def _match_cid(linha: str, cid_preferido: str) -> bool:
    partes = split_csv_line(linha)
    if not partes:
        return False
    primeiro = normalizar_texto(partes[0])
    # aceita formatos tipo "C50 - MAMA" / "C50" / "c50"
    return bool(re.search(rf"\b{re.escape(cid_preferido.lower())}\b", primeiro))


def extrair_pares_cabecalho_valor(csv_path: Path, cid_preferido: str = "c50") -> list[tuple[str, str]]:
    """
    Retorna lista de (rotulo_coluna, valor) para as colunas de faixa etária,
    ignorando corretamente CID e Total independentemente de posição.

    Se o CSV tiver múltiplas linhas (ex.: vários CIDs), tenta escolher a linha do
    `cid_preferido` (padrão: C50).
    """
    linhas = ler_linhas_csv(csv_path)

    # Localiza a linha de cabeçalho (começa com "CID")
    idx_cab = None
    for i, linha in enumerate(linhas):
        if re.match(r"^\s*CID\s*;", linha, re.IGNORECASE):
            idx_cab = i
            break

    if idx_cab is None or idx_cab + 1 >= len(linhas):
        return []

    cabecalho = split_csv_line(linhas[idx_cab])

    # Seleciona a linha de dados: preferindo o CID desejado, senão a primeira válida
    candidatos = [ln for ln in linhas[idx_cab + 1 :] if _eh_linha_dados_csv(ln)]
    linha_valores = None
    for ln in candidatos:
        if _match_cid(ln, cid_preferido=cid_preferido):
            linha_valores = ln
            break
    if linha_valores is None:
        linha_valores = candidatos[0] if candidatos else None
    if linha_valores is None:
        return []

    valores = split_csv_line(linha_valores)

    # Emparelha cabeçalho com valores (ignora diferença de tamanho)
    pares = []
    for i, rotulo in enumerate(cabecalho):
        valor = valores[i] if i < len(valores) else ""
        pares.append((rotulo, valor))

    return pares


def consolidar_mortalidade(pasta_raiz: Path) -> pd.DataFrame:
    registros = []

    regionais = [p for p in pasta_raiz.iterdir() if p.is_dir()]
    for regional_dir in sorted(regionais):
        regional = regional_dir.name

        municipios = [p for p in regional_dir.iterdir() if p.is_dir()]
        for municipio_dir in sorted(municipios):
            municipio = municipio_dir.name
            registro: dict[str, object] = {
                "Município": municipio,
                "Regional de Saúde": regional,
            }

            arquivos_csv = sorted(municipio_dir.glob("*.csv"))
            for csv_path in arquivos_csv:
                if SEXO_DESEJADO is not None:
                    sexo_arquivo = detectar_sexo_arquivo(csv_path)
                    # Se não conseguir detectar, não filtra (para não perder dados por falha de OCR/encoding)
                    if sexo_arquivo is not None and sexo_arquivo != SEXO_DESEJADO:
                        continue

                ano = extrair_ano_do_arquivo(csv_path.name)
                if ano is None:
                    continue

                pares = extrair_pares_cabecalho_valor(csv_path, cid_preferido="c50")
                if not pares:
                    continue

                for rotulo, valor_raw in pares:
                    faixa = mapear_faixa_etaria(rotulo)
                    if faixa is None:
                        # Ignora CID, Total e colunas não-etárias
                        continue

                    valor = para_inteiro(valor_raw)
                    if valor is None:
                        continue

                    coluna = f"{ano}_{faixa}"
                    anterior = registro.get(coluna)
                    if anterior is None:
                        registro[coluna] = valor
                    else:
                        registro[coluna] = int(anterior) + valor  # type: ignore[arg-type]

            registros.append(registro)

    return pd.DataFrame(registros)


def organizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    colunas_ano_faixa = [f"{ano}_{faixa}" for ano in ANOS for faixa in FAIXAS_ETARIAS]
    colunas_total_ano = [f"Total_{ano}" for ano in ANOS]

    # Garante que todas as colunas existam (preenchidas com NaN onde não há dado)
    faltantes = [c for c in colunas_ano_faixa if c not in df.columns]
    if faltantes:
        df = pd.concat(
            [df, pd.DataFrame(np.nan, index=df.index, columns=faltantes)],
            axis=1,
        )

    # Converte colunas de contagem para Int64 (inteiro nullable do pandas)
    for col in colunas_ano_faixa:
        df[col] = pd.to_numeric(df[col], errors="coerce").astype("Int64")

    # Total geral
    df["Total"] = df[colunas_ano_faixa].sum(axis=1, min_count=1).astype("Int64")

    # Totais por ano
    for ano in ANOS:
        cols = [f"{ano}_{faixa}" for faixa in FAIXAS_ETARIAS]
        df[f"Total_{ano}"] = df[cols].sum(axis=1, min_count=1).astype("Int64")

    colunas_finais = ["Município", "Regional de Saúde"] + colunas_ano_faixa + ["Total"]
    extras = [c for c in df.columns if c not in {*colunas_finais, *colunas_total_ano}]
    colunas_finais.extend(extras)
    colunas_finais.extend(colunas_total_ano)

    df = df[colunas_finais].copy()
    df = df.sort_values(["Regional de Saúde", "Município"], na_position="last").reset_index(drop=True)
    return df


def carregar_mapa_codigos(arquivo_municipios: Path | None = None) -> dict[str, str]:
    if arquivo_municipios is None:
        arquivo_municipios = next(
            (p for p in ARQUIVOS_MUNICIPIOS_CANDIDATOS if p.exists()),
            None,
        )
    if arquivo_municipios is None or not arquivo_municipios.exists():
        candidatos = ", ".join(str(p) for p in ARQUIVOS_MUNICIPIOS_CANDIDATOS)
        raise FileNotFoundError(f"Arquivo de municípios não encontrado. Tentativas: {candidatos}")

    ref = pd.read_csv(arquivo_municipios, dtype={"codigo_ibge": "string"})
    colunas_necessarias = {"municipio_normalizado", "codigo_ibge"}
    faltantes = colunas_necessarias - set(ref.columns)
    if faltantes:
        raise ValueError(
            f"Arquivo de municípios sem colunas obrigatórias: {sorted(faltantes)}"
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
    codigos = chaves.map(mapa_codigos).astype("string")
    sem_correspondencia = (
        df.loc[codigos.isna(), "Município"].astype(str).dropna().sort_values().unique().tolist()
    )

    if sem_correspondencia:
        print(f"[AVISO] Municípios sem correspondência de código ({len(sem_correspondencia)}):")
        for municipio in sem_correspondencia:
            print(f"  - {municipio}")
    else:
        print("[OK] Todos os municípios tiveram código encontrado.")

    df = df.drop(columns=["CÓDIGO", "Código"], errors="ignore").copy()
    pos_municipio = list(df.columns).index("Município") + 1
    df.insert(pos_municipio, "Código", codigos)
    return df


def main() -> None:
    print(f"Pasta raiz: {PASTA_RAIZ}")
    print(f"Arquivo de saída: {ARQUIVO_SAIDA}")

    df = consolidar_mortalidade(PASTA_RAIZ)
    print("Dimensão após consolidação:", df.shape)

    df = organizar_colunas(df)

    df["Município"] = df["Município"].map(remover_sufixo_mg)
    mapa_codigos = carregar_mapa_codigos()
    df = adicionar_codigo_municipio(df, mapa_codigos=mapa_codigos)

    print("Dimensão final:", df.shape)
    print("Linhas (municípios):", len(df))
    print("Municípios únicos:", df["Município"].nunique())
    print("Regionais únicas:", df["Regional de Saúde"].nunique(dropna=True))
    print("Soma de Total:", df["Total"].sum(skipna=True))

    df = df.rename(columns={"Município": "Municípios"})
    df.to_csv(ARQUIVO_SAIDA, sep=",", index=False, encoding="utf-8")

    print(f"\nCSV criado: {ARQUIVO_SAIDA}")
    print(f"Dimensão exportada: {df.shape}")


if __name__ == "__main__":
    main()