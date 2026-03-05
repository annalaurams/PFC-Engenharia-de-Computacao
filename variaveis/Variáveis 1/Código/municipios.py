import json
import gzip
import re
import unicodedata
from pathlib import Path
from typing import Iterable
from urllib.request import urlopen


URL_MUNICIPIOS_MG = "https://servicodados.ibge.gov.br/api/v1/localidades/estados/MG/municipios"
ARQUIVO_SAIDA = Path("/home/anna/tcc/variaveis/Variáveis 1/Saídas/municipios_oficiais_mg_normalizado.txt")


def remover_acentos(texto: str) -> str:
	nfkd = unicodedata.normalize("NFKD", texto)
	return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar_cidade(cidade: str) -> str:
	cidade = cidade.strip()
	cidade = re.sub(r"\s+", " ", cidade)
	cidade = remover_acentos(cidade)
	cidade = cidade.lower()
	return cidade.strip()


def obter_municipios_oficiais_mg() -> list[str]:
	with urlopen(URL_MUNICIPIOS_MG) as resposta:
		conteudo = resposta.read()

	if conteudo[:2] == b"\x1f\x8b":
		conteudo = gzip.decompress(conteudo)

	dados = json.loads(conteudo.decode("utf-8"))
	return [item["nome"] for item in dados]


def gerar_arquivo_saida(nomes_municipios: Iterable[str]) -> int:
	nomes_normalizados = sorted({normalizar_cidade(nome) for nome in nomes_municipios})
	total = len(nomes_normalizados)

	ARQUIVO_SAIDA.parent.mkdir(parents=True, exist_ok=True)
	with open(ARQUIVO_SAIDA, "w", encoding="utf-8") as arquivo:
		for nome in nomes_normalizados:
			arquivo.write(f"{nome}\n")
		arquivo.write(f"\ntotal: {total}\n")

	return total


def main():
	print("=" * 80)
	print("GERANDO LISTA OFICIAL DE MUNICÍPIOS DE MG")
	print("=" * 80)

	nomes_municipios = obter_municipios_oficiais_mg()
	total = gerar_arquivo_saida(nomes_municipios)

	print(f"\nArquivo gerado: {ARQUIVO_SAIDA}")
	print(f"Total de municípios oficiais de MG: {total}")
	print("=" * 80)


if __name__ == "__main__":
	main()
