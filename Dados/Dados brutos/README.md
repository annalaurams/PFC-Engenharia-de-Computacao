# Dados brutos

Arquivos CSV e XLSX como foram extraídos ou baixados das fontes públicas, sem nenhuma alteração. Há uma pasta por variável.

## Estrutura

```
Dados brutos/
├── Casos/
│   ├── Ano Diagnóstico/        # AnoDiagnostico-AAAA.csv
│   ├── Escolaridade/           # Escolaridade-AAAA.csv
│   ├── Faixa Etária/           # Faixa-Etaria-AAAA.csv
│   └── Raça-Cor/               # RacaCor-AAAA.csv
├── Hospitais Habilitados/      # 3 planilhas XLSX
├── Mamografia/                 # mamografia_AAAA.csv
├── Mortalidade/                # <Regional>/<Município>-MG/AAAA-<Município>-MG.csv
├── Municípios/                 # 1 planilha XLSX
└── População - Faixa Etária/   # 1-AAAA.csv e 2-AAAA.csv
```

## Arquivos

| Variável | Nome do arquivo | Quantidade | Colunas |
|---|---|---|---|
| Casos por ano de diagnóstico, por município | `Casos/Ano Diagnóstico/AnoDiagnostico-AAAA.csv` | 38 (1985 a 2023, exceto 1987) | Cabeçalho de texto do RHC/INCA, seguido de `Procedência` (formato `MG - <código IBGE> - <município>`), `Total`, uma coluna por ano de diagnóstico e `Sem informação` |
| Casos por escolaridade, por município | `Casos/Escolaridade/Escolaridade-AAAA.csv` | 38 (1985 a 2023, exceto 1987) | `Procedência`, `Total`, `Sem Informação`, `Nenhuma`, `Fundamental incompleto`, `Fundamental completo`, `Nivel medio`, `Nivel superior incompleto`, `Nivel superior completo` |
| Casos por faixa etária, por município | `Casos/Faixa Etária/Faixa-Etaria-AAAA.csv` | 38 (1985 a 2023, exceto 1987) | `Procedência`, `Total`, faixas de 5 anos (`00-04`, `05-09`, ..., `80-84`, `85+`) e `Sem Informação` |
| Casos por raça/cor, por município | `Casos/Raça-Cor/RacaCor-AAAA.csv` | 38 (1985 a 2023, exceto 1987) | `Procedência`, `Total`, `Branca`, `Preta`, `Parda`, `Amarela`, `Indígena`, `Sem Informação` |
| Mamografias por município e faixa etária | `Mamografia/mamografia_AAAA.csv` | 13 (2013 a 2025) | `Munic.da un.saúde` (código + nome), `Até 9 anos`, `Entre 10 a 14 anos`, ..., `Entre 75 a 79 anos`, `Acima de 79 anos`, `Ignorado`, `Total` |
| Mortalidade por câncer de mama, por município | `Mortalidade/<Regional>/<Município>-MG/AAAA-<Município>-MG.csv` | 11.767 (um por município e ano com registro, 1979 a 2024) | Cabeçalho de texto do Atlas de Mortalidade/INCA, seguido de `CID`, `Total` e uma coluna por faixa etária com óbito (ex.: `50 a 59`, `60 a 69`); a linha de dados é `C50 - MAMA` |
| Hospitais habilitados em oncologia | `Hospitais Habilitados/hospitais-habilitados-em-oncologia-abril-2025.xlsx` | 1 | `UF`, `MUNICÍPIO`, `MACRORREGIÃO DE SAÚDE`, `TOTAL DE HABILITAÇÕES`, `ESTABELECIMENTO`, `CNES`, `CÓDIGO`, `HABILITAÇÃO` |
| Hospitais habilitados em reconstrução mamária | `Hospitais Habilitados/hospitais-habilitados-em-reconstrucao-mamaria.xlsx` | 1 | `UF`, `IBGE`, `MUNICÍPIO`, `ESTABELECIMENTO`, `CNES`, `CNPJ`, `GESTÃO`, `TIPO DE HABILITAÇÃO (CÓDIGO DO CNES)`, `TIPO DE HABILITAÇÃO (Descrição)` |
| Hospitais habilitados em tratamento sincrônico | `Hospitais Habilitados/tratamento-sincronico.xlsx` | 1 | `TOTAL DE HABILITAÇÕES`, `UF`, `MUNICÍPIO`, `MACRORREGIÃO DE SAÚDE`, `ESTABELECIMENTO`, `CNES`, `CÓDIGO`, `HABILITAÇÃO` |
| Municípios e Regionais de Saúde de MG | `Municípios/Relacao-de-municipios-por-vinculacao-administrativa-090.xlsx` (aba `RegionalizaçãoMG2024`) | 1 | `Código IBGE`, `Código DATASUS/ MS`, `Município`, `Unidade Regional de Saúde` |
| População feminina por faixa etária, parte 1 | `População - Faixa Etária/1-AAAA.csv` | 6 (censos de 1970, 1980, 1991, 2000, 2010 e 2022) | `Sigla`, `Código`, `Município`, população de mulheres de 0 a 4, 10 a 14, 15 a 19, 20 a 24, 25 a 29 e 30 a 39 anos |
| População feminina por faixa etária, parte 2 | `População - Faixa Etária/2-AAAA.csv` | 6 (mesmos censos) | `Sigla`, `Código`, `Município`, população de mulheres de 5 a 9, 40 a 49, 50 a 59, 60 a 69 e 70 anos ou mais |

## Observações

- Não há arquivo de casos para 1987.
- Os arquivos são CSV com separador `;` e codificação ISO-8859-1 (Latin-1). Para ler com pandas, use `encoding="latin-1"` e `sep=";"`.
- Os arquivos de casos e de mortalidade começam com linhas de texto geradas pela própria fonte (título da consulta), antes da tabela; os de casos têm 3 linhas de título e os de mortalidade, 1 linha de título e uma em branco. Os de mamografia começam direto no cabeçalho de colunas.
- Na mortalidade, existe um arquivo por município e por ano com óbito registrado. Município e ano sem arquivo não tiveram registro. A pasta de cada Regional agrupa os municípios que ela atende (28 Regionais, 853 municípios).
