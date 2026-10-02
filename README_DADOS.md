# Mapeamento dos dados (CSV e XLSX)

Lista os arquivos de dados do projeto, organizados pelas etapas do KDD. Em cada tabela, **Variável** é o que o arquivo representa, **Nome da tabela** é o nome exato do arquivo e **Colunas** descreve o cabeçalho.

Convenções de colunas usadas nas etapas 2 e seguintes:

- `AAAA` é o ano de 4 dígitos. `AAAA_<faixa>` é a contagem (ou a população) da faixa etária no ano; as 8 faixas padrão são `0-9`, `10-19`, `20-29`, `30-39`, `40-49`, `50-59`, `60-69` e `70 OU MAIS`.
- `AAAA_TOTAL` é a soma das categorias do ano.
- Sufixo `_TAXA` é a taxa por 100 mil habitantes da coluna correspondente.

## 1. Limpeza e Integração (dados brutos)

Pasta `Limpeza e Integração/`. Os CSV são extraídos por scripts `main.py` (INCA, DATASUS) ou baixados (IBGE); os XLSX vêm do Ministério da Saúde e da SES-MG.

| Variável | Nome da tabela (arquivo) | Colunas |
|---|---|---|
| Casos por ano de diagnóstico, por município (uma tabela por ano de 1985 a 2023, exceto 1987) | `Casos/Ano Diagnóstico/Dados/AnoDiagnostico-AAAA.csv` | Cabeçalho de texto do tabulador do RHC/INCA, seguido de `Procedência` (formato `MG - <código IBGE> - <município>`), `Total`, uma coluna por ano de diagnóstico e `Sem informação` |
| Casos por escolaridade, por município (um arquivo por ano, 1985–2023, exceto 1987) | `Casos/Escolaridade/Dados/Escolaridade-AAAA.csv` | `Procedência`, `Total`, `Sem Informação`, `Nenhuma`, `Fundamental incompleto`, `Fundamental completo`, `Nivel medio`, `Nivel superior incompleto`, `Nivel superior completo` |
| Casos por faixa etária, por município (um arquivo por ano, 1985–2023, exceto 1987) | `Casos/Faixa Etária/Dados/Faixa-Etaria-AAAA.csv` | `Procedência`, `Total`, faixas de 5 anos (`00-04`, `05-09`, ..., `80-84`, `85+`) e `Sem Informação` |
| Casos por raça/cor, por município (um arquivo por ano, 1985–2023, exceto 1987) | `Casos/Raça-Cor/Dados/RacaCor-AAAA.csv` | `Procedência`, `Total`, `Branca`, `Preta`, `Parda`, `Amarela`, `Indígena`, `Sem Informação` |
| Mamografias por município e faixa etária (um arquivo por ano, 2013–2025) | `Mamografia/Dados/mamografia_AAAA.csv` | `Munic.da un.saúde` (código + nome), `Até 9 anos`, `Entre 10 a 14 anos`, ..., `Entre 75 a 79 anos`, `Acima de 79 anos`, `Ignorado`, `Total` |
| Mortalidade por câncer de mama, por município (um arquivo por município e ano, em `Mortalidade/Cidades Atendidas por Cada Regional/<Regional>/<Município>-MG/`) | `AAAA-<Município>-MG.csv` | Cabeçalho de texto do Mortalidade Web/INCA, seguido de `CID`, `Total` e uma coluna por faixa etária com óbito (ex.: `50 a 59`, `60 a 69`); a linha de dados é `C50 - MAMA` |
| Hospitais habilitados em oncologia | `Hospitais Habilitados/hospitais-habilitados-em-oncologia-abril-2025.xlsx` | `UF`, `MUNICÍPIO`, `MACRORREGIÃO DE SAÚDE`, `TOTAL DE HABILITAÇÕES`, `ESTABELECIMENTO`, `CNES`, `CÓDIGO`, `HABILITAÇÃO` |
| Hospitais habilitados em reconstrução mamária | `Hospitais Habilitados/hospitais-habilitados-em-reconstrucao-mamaria.xlsx` | `UF`, `IBGE`, `MUNICÍPIO`, `ESTABELECIMENTO`, `CNES`, `CNPJ`, `GESTÃO`, `TIPO DE HABILITAÇÃO (CÓDIGO DO CNES)`, `TIPO DE HABILITAÇÃO (Descrição)` |
| Hospitais habilitados em tratamento sincrônico | `Hospitais Habilitados/tratamento-sincronico.xlsx` | `TOTAL DE HABILITAÇÕES`, `UF`, `MUNICÍPIO`, `MACRORREGIÃO DE SAÚDE`, `ESTABELECIMENTO`, `CNES`, `CÓDIGO`, `HABILITAÇÃO` |
| Municípios e Regionais de Saúde de MG (aba `RegionalizaçãoMG2024`) | `Municípios/Relacao-de-municipios-por-vinculacao-administrativa-090.xlsx` | `Código IBGE`, `Código DATASUS/ MS`, `Município`, `Unidade Regional de Saúde` |
| População feminina por faixa etária, parte 1 (um arquivo por censo: 1970, 1980, 1991, 2000, 2010, 2022) | `População - Faixa Etária/1-AAAA.csv` | `Sigla`, `Código`, `Município`, população de mulheres de 0 a 4, 10 a 14, 15 a 19, 20 a 24, 25 a 29 e 30 a 39 anos |
| População feminina por faixa etária, parte 2 (mesmos censos) | `População - Faixa Etária/2-AAAA.csv` | `Sigla`, `Código`, `Município`, população de mulheres de 5 a 9, 40 a 49, 50 a 59, 60 a 69 e 70 anos ou mais |

## 2. Seleção e Transformação

Pasta `Seleção e Transformação/`. Tabelas tratadas por município e, depois, por Regional de Saúde.

### 2.1 Tabelas por município

| Variável | Nome da tabela (arquivo) | Colunas |
|---|---|---|
| Municípios e Regionais de Saúde | `Municípios/tabela_municipios_regionais.csv` | `CÓDIGO IBGE`, `MUNICÍPIO ORIGINAL`, `MUNICÍPIO NORMALIZADO`, `REGIONAL ORIGINAL`, `REGIONAL NORMALIZADA` |
| Casos por ano de diagnóstico | `Casos/tabela_casos_por_ano_de_diagnóstico.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_DIAGNOSTICO` (1985–2023), `ANO_SEM-INFORMAÇÃO`, `AAAA_TOTAL` |
| Casos por escolaridade | `Casos/tabela_casos_por_escolaridade.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<categoria>` (categorias: `SEM INFORMAÇÃO`, `NENHUMA`, `FUNDAMENTAL INCOMPLETO`, `FUNDAMENTAL COMPLETO`, `NÍVEL MÉDIO`, `NÍVEL SUPERIOR INCOMPLETO`, `NÍVEL SUPERIOR COMPLETO`), `AAAA_TOTAL` |
| Casos por faixa etária | `Casos/tabela_casos_por_faixa_etária.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<faixa>` (8 faixas), `AAAA_TOTAL` |
| Casos por raça e cor | `Casos/tabela_casos_por_raça_e_cor.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<categoria>` (`BRANCA`, `PRETA`, `PARDA`, `AMARELA`, `INDÍGENA`, `SEM INFORMAÇÃO`), `AAAA_TOTAL` |
| Hospitais habilitados | `Hospitais/tabela_hospitais_habilitados.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `TIPO` (`ONCOLOGIA`, `RECONSTRUÇÃO MAMÁRIA`, `TRATAMENTO SINCRÔNICO`), `2023_TOTAL` |
| Mamografias por faixa etária | `Mamografias/tabela_mamografias_por_faixa_etária.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<faixa>` (2013–2025), `AAAA_TOTAL` |
| Mortalidade por faixa etária | `Mortalidade/tabela_mortes_por_faixa_etária.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<faixa>` (1979–2024), `AAAA_TOTAL` |
| População feminina por faixa etária (anos censitários) | `População/tabela_populacao_faixa_etaria.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<faixa>` e `AAAA_TOTAL` para 1970, 1980, 1991, 2000, 2010 e 2022 |
| População feminina interpolada e extrapolada, por município | `População/Interpolação e Extrapolação/populacao_interpolacao_extrapolacao.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<faixa>` e `AAAA_TOTAL` para todos os anos de 1970 a 2025 |
| População feminina interpolada e extrapolada, por Regional | `População/Interpolação e Extrapolação/populacao_interpolacao_extrapolacao_por_regional.csv` | `REGIONAL DE SAÚDE`, `AAAA_<faixa>` e `AAAA_TOTAL` para 1970 a 2025 |

### 2.2 Taxas por Regional de Saúde

Pasta `Seleção e Transformação/População/Taxa/`. Cada arquivo tem uma linha por Regional; para cada coluna de valor há a quantidade somada e a coluna `_TAXA` ao lado.

| Variável | Nome da tabela (arquivo) | Colunas |
|---|---|---|
| Casos por ano de diagnóstico | `tabela_casos_por_ano_de_diagnóstico_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_DIAGNOSTICO`, `AAAA_DIAGNOSTICO_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (1985–2023) |
| Casos por escolaridade | `tabela_casos_por_escolaridade_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_<categoria>`, `AAAA_<categoria>_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (1998–2023) |
| Casos por faixa etária | `tabela_casos_por_faixa_etária_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_<faixa>`, `AAAA_<faixa>_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (1985–2023) |
| Casos por raça e cor | `tabela_casos_por_raça_e_cor_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_<categoria>`, `AAAA_<categoria>_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (1998–2023) |
| Mamografias por faixa etária | `tabela_mamografias_por_faixa_etária_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_<faixa>`, `AAAA_<faixa>_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (2013–2025) |
| Mortalidade por faixa etária | `tabela_mortes_por_faixa_etária_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_<faixa>`, `AAAA_<faixa>_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (1979–2024) |
| Hospitais habilitados | `tabela_hospitais_habilitados_taxa.csv` | `REGIONAL DE SAÚDE`, `TIPO` (inclui `TODOS`), `2023_TOTAL`, `2023_TOTAL_TAXA` |
| Agregado estadual por ano (todas as variáveis) | `tabela_regional_agregada_por_ano.csv` | `ANO` e, para cada variável, `<categoria>_<VARIÁVEL>` e `<categoria>_<VARIÁVEL>_TAXA`, com `VARIÁVEL` em `CASOS`, `CASOS_ESCOLARIDADE`, `CASOS_RACA_COR`, `MORTES`, `MAMOGRAFIAS` e `HOSPITAIS` |

## 3. Mineração de Dados

Esta etapa não grava CSV nem XLSX. O KMeans lê as cinco tabelas de taxa abaixo (etapa 2.2) e mantém os resultados apenas nas saídas do notebook `Mineração de Dados/KMEANS/kmeans.ipynb`.

| Variável | Nome da tabela (arquivo) | Colunas usadas |
|---|---|---|
| Casos por faixa etária | `tabela_casos_por_faixa_etária_taxa.csv` | colunas `AAAA_<faixa>_TAXA` |
| Casos por escolaridade | `tabela_casos_por_escolaridade_taxa.csv` | colunas `AAAA_<categoria>_TAXA` |
| Casos por raça e cor | `tabela_casos_por_raça_e_cor_taxa.csv` | colunas `AAAA_<categoria>_TAXA` |
| Mortalidade por faixa etária | `tabela_mortes_por_faixa_etária_taxa.csv` | colunas `AAAA_<faixa>_TAXA` |
| Mamografias por faixa etária | `tabela_mamografias_por_faixa_etária_taxa.csv` | colunas `AAAA_<faixa>_TAXA` |

## 4. Avaliação e Apresentação

Os notebooks de `Avaliação e Apresentação/` não geram CSV nem XLSX; produzem figuras (PNG, SVG e HTML) em `Gráficos/`. Eles leem as tabelas da etapa 2.2 e `Seleção e Transformação/Municípios/tabela_municipios_regionais.csv`:

| Variável | Nome da tabela (arquivo) | Colunas usadas |
|---|---|---|
| Casos, mortalidade e mamografias por Regional (heatmaps e mapas) | `tabela_casos_por_ano_de_diagnóstico_taxa.csv`, `tabela_mortes_por_faixa_etária_taxa.csv`, `tabela_mamografias_por_faixa_etária_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` |
| Hospitais habilitados por tipo (mapas) | `tabela_hospitais_habilitados_taxa.csv` | `REGIONAL DE SAÚDE`, `TIPO`, `2023_TOTAL` |
| Casos por categoria, agregado estadual (gráficos de linha) | `tabela_regional_agregada_por_ano.csv` | `ANO`, `<categoria>_CASOS`, `<categoria>_CASOS_ESCOLARIDADE`, `<categoria>_CASOS_RACA_COR` e as respectivas colunas `_TAXA` |
| Nomes das Regionais e municípios (mapas) | `tabela_municipios_regionais.csv` | `CÓDIGO IBGE`, `REGIONAL NORMALIZADA`, `REGIONAL ORIGINAL` |
