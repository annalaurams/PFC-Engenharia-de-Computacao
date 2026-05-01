from __future__ import annotations

import argparse
import re
import unicodedata
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

import pandas as pd


@dataclass(frozen=True)
class Config:
	base: Path
	out: Path


# ________________________________________________________________________________
# Texto


def normalize_text(value: str) -> str:
	text = str(value).strip().lower()
	text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("utf-8")
	text = re.sub(r"\s+", " ", text)
	return text


def clean_col(col: str) -> str:
	col = str(col).replace("\ufeff", "").replace('"', "").strip()
	col = unicodedata.normalize("NFKD", col).encode("ascii", "ignore").decode("utf-8")
	col = re.sub(r"\s+", " ", col).strip()
	return col


def parse_municipio_codigo(procedencia: str) -> tuple[str | None, int | None]:
	text = str(procedencia).replace('"', "").strip()
	match = re.match(r"^MG\s*-\s*(\d{7})\s*-\s*(.+)$", text, flags=re.IGNORECASE)
	if not match:
		return None, None
	codigo = int(match.group(1))
	municipio = normalize_text(match.group(2))
	return municipio, codigo


# ________________________________________________________________________________
# Arquivos

def read_raw_table(file_path: Path) -> pd.DataFrame:
	content = file_path.read_text(encoding="latin1", errors="ignore").splitlines()
	header_idx = None
	for idx, line in enumerate(content):
		if ";" in line and "proced" in normalize_text(line):
			header_idx = idx
			break
	if header_idx is None:
		raise ValueError(f"Cabecalho nao encontrado em: {file_path}")

	table_text = "\n".join(content[header_idx:])
	df = pd.read_csv(StringIO(table_text), sep=";", engine="python", encoding="latin1")
	df.columns = [clean_col(c) for c in df.columns]

	unnamed = [c for c in df.columns if clean_col(c) == ""]
	if unnamed:
		df = df.drop(columns=unnamed)

	col_proc = df.columns[0]
	parsed = df[col_proc].apply(parse_municipio_codigo)
	df["MUNICIPIOS"] = parsed.map(lambda x: x[0])
	df["CODIGO"] = parsed.map(lambda x: x[1])
	df = df[df["CODIGO"].notna()].copy()
	df["CODIGO"] = df["CODIGO"].astype("Int64")
	df["MUNICIPIOS"] = df["MUNICIPIOS"].astype(str)

	return df


def numeric_columns(df: pd.DataFrame, skip: set[str]) -> list[str]:
	cols: list[str] = []
	for col in df.columns:
		if col in skip:
			continue
		low = normalize_text(col)
		if low in {"total", ""}:
			continue
		cols.append(col)
	return cols


# ________________________________________________________________________________
# Tratamento

def aggregate_ano_diagnostico(raw_files: list[Path]) -> pd.DataFrame:
	frames: list[pd.DataFrame] = []
	for file_path in raw_files:
		df = read_raw_table(file_path)
		cols = numeric_columns(df, {df.columns[0], "MUNICIPIOS", "CODIGO"})
		rename_map = {}
		for col in cols:
			norm = clean_col(col)
			if normalize_text(norm) == "sem informacao":
				rename_map[col] = "Sem Informacao"
			else:
				rename_map[col] = norm
		current = df[["MUNICIPIOS", "CODIGO", *cols]].rename(columns=rename_map)
		frames.append(current)

	long_df = pd.concat(frames, ignore_index=True)
	value_cols = [c for c in long_df.columns if c not in {"MUNICIPIOS", "CODIGO"}]
	for col in value_cols:
		long_df[col] = pd.to_numeric(long_df[col], errors="coerce")

	agg = long_df.groupby(["MUNICIPIOS", "CODIGO"], as_index=False)[value_cols].sum(min_count=1)

	ano_cols = sorted([c for c in value_cols if re.fullmatch(r"\d{4}", str(c))], key=lambda x: int(x))
	tail_cols = [c for c in value_cols if c not in ano_cols]
	ordered = ["MUNICIPIOS", "CODIGO", *ano_cols, *sorted(tail_cols)]
	return agg[ordered].rename(columns={"MUNICIPIOS": "MUNICÍPIOS", "CODIGO": "CÓDIGO"})


def extract_year(file_name: str) -> int:
	match = re.search(r"(19\d{2}|20\d{2})", file_name)
	if not match:
		raise ValueError(f"Ano nao encontrado no nome do arquivo: {file_name}")
	return int(match.group(1))


def normalize_categoria_escolaridade(col: str) -> str:
	normalized = clean_col(col)
	if normalize_text(normalized) == "sem informacao":
		return "Sem Informacao"
	return normalized


def normalize_categoria_raca(col: str) -> str:
	normalized = clean_col(col)
	if normalize_text(normalized) == "sem informacao":
		return "Sem Informacao"
	return normalized


FAIXA_TARGET = [
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


# ________________________________________________________________________________
# Criação de colunas

def map_faixa(col: str) -> str | None:
	c = normalize_text(col).replace(" ", "")
	if c in {"00-04", "0-4", "05-09", "5-9"}:
		return "0-9"
	if c in {"10-14", "15-19"}:
		return "10-19"
	if c in {"20-24", "25-29"}:
		return "20-29"
	if c in {"30-34", "35-39"}:
		return "30-39"
	if c in {"40-44", "45-49"}:
		return "40-49"
	if c in {"50-54", "55-59"}:
		return "50-59"
	if c in {"60-64", "65-69"}:
		return "60-69"
	if c in {"70-74", "75-79"}:
		return "70-79"
	if c in {"80-84", "85+", "85-89", "90+"}:
		return "80 ou mais"
	return None


def aggregate_wide_by_year(
	raw_files: list[Path],
	category_mapper,
	*,
	faixa_mode: bool = False,
) -> pd.DataFrame:
	result: pd.DataFrame | None = None

	for file_path in sorted(raw_files):
		year = extract_year(file_path.name)
		df = read_raw_table(file_path)
		cols = numeric_columns(df, {df.columns[0], "MUNICIPIOS", "CODIGO"})

		work = df[["MUNICIPIOS", "CODIGO", *cols]].copy()
		for col in cols:
			work[col] = pd.to_numeric(work[col], errors="coerce")

		if faixa_mode:
			grouped_cols: dict[str, list[str]] = {k: [] for k in FAIXA_TARGET}
			for col in cols:
				mapped = map_faixa(col)
				if mapped is not None:
					grouped_cols[mapped].append(col)

			current = work[["MUNICIPIOS", "CODIGO"]].copy()
			for target in FAIXA_TARGET:
				src = grouped_cols[target]
				if src:
					current[f"{year}_{target}"] = work[src].sum(axis=1, min_count=1)
				else:
					current[f"{year}_{target}"] = pd.NA
		else:
			renamed = {}
			for col in cols:
				cat = category_mapper(col)
				renamed[col] = f"{year}_{cat}"
			current = work[["MUNICIPIOS", "CODIGO", *cols]].rename(columns=renamed)

		if result is None:
			result = current
		else:
			result = result.merge(current, on=["MUNICIPIOS", "CODIGO"], how="outer")

	if result is None:
		raise ValueError("Nenhum arquivo processado.")

	return result.rename(columns={"MUNICIPIOS": "MUNICÍPIOS", "CODIGO": "CÓDIGO"})


def build_tabela_incidencia(
	ano_diag: pd.DataFrame,
	escolaridade: pd.DataFrame,
	faixa_etaria: pd.DataFrame,
	raca_cor: pd.DataFrame,
) -> pd.DataFrame:
	out = ano_diag.merge(escolaridade, on=["MUNICÍPIOS", "CÓDIGO"], how="outer")
	out = out.merge(faixa_etaria, on=["MUNICÍPIOS", "CÓDIGO"], how="outer")
	out = out.merge(raca_cor, on=["MUNICÍPIOS", "CÓDIGO"], how="outer")
	return out


# ________________________________________________________________________________
# Operações

def sorted_files(path: Path, pattern: str) -> list[Path]:
	files = list(path.glob(pattern))
	return sorted(files, key=lambda p: extract_year(p.name))


def run(config: Config) -> None:
	base = config.base
	out = config.out
	out.mkdir(parents=True, exist_ok=True)

	# Extração: criação dos CSVs individuais
	files_ano = sorted_files(base / "Ano Diagnóstico" / "Dados", "AnoDiagnostico-*.csv")
	files_esc = sorted_files(base / "Escolaridade" / "Dados", "Escolaridade-*.csv")
	files_faixa = sorted_files(base / "Faixa Etária" / "Dados", "Faixa-Etaria-*.csv")
	files_raca = sorted_files(base / "Raça-Cor" / "Dados", "RacaCor-*.csv")

	if not files_ano or not files_esc or not files_faixa or not files_raca:
		raise FileNotFoundError("Arquivos de entrada nao encontrados em uma ou mais pastas de Casos.")

	# Tratamento: cada parte separada
	ano_diag = aggregate_ano_diagnostico(files_ano)
	esc = aggregate_wide_by_year(files_esc, normalize_categoria_escolaridade)
	faixa = aggregate_wide_by_year(files_faixa, lambda c: c, faixa_mode=True)
	raca = aggregate_wide_by_year(files_raca, normalize_categoria_raca)

	# Tratamento: união das tabelas
	tabela = build_tabela_incidencia(ano_diag, esc, faixa, raca)

	ano_diag.to_csv(out / "incidencia _ano_diagnostico.csv", index=False)
	esc.to_csv(out / "incidencia _escolaridade.csv", index=False)
	faixa.to_csv(out / "incidencia _faixa_etaria.csv", index=False)
	raca.to_csv(out / "incidencia _raca_cor.csv", index=False)
	tabela.to_csv(out / "tabela_incidencia _.csv", index=False)

	print("Arquivos gerados com sucesso:")
	print(out / "incidencia _ano_diagnostico.csv")
	print(out / "incidencia _escolaridade.csv")
	print(out / "incidencia _faixa_etaria.csv")
	print(out / "incidencia _raca_cor.csv")
	print(out / "tabela_incidencia _.csv")


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(description="Gera tabelas de tratamento para variavel Casos.")
	parser.add_argument(
		"--base-variaveis",
		type=Path,
		default=Path("/home/anna/tcc/Variáveis/Casos"),
		help="Pasta base com os dados brutos de Casos.",
	)
	parser.add_argument(
		"--out-dir",
		type=Path,
		default=Path("/home/anna/tcc/Tratamento/Casos"),
		help="Pasta de saida dos CSVs tratados.",
	)
	return parser.parse_args()


if __name__ == "__main__":
	args = parse_args()
	run(Config(base=args.base_variaveis, out=args.out_dir))
