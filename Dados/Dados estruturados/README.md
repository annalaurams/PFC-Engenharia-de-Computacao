# Dados estruturados

Tabelas únicas por variável, geradas a partir dos [dados brutos](../Dados%20brutos/README.md). Em cada uma, os arquivos anuais e por município foram unificados em um só CSV, com colunas padronizadas, com o código IBGE e a Regional de Saúde de cada município.

São três subpastas, que correspondem às etapas de processamento:

```
Dados estruturados/
├── Tratados/       # dados brutos unificados e padronizados, por município
│   ├── Casos/
│   ├── Hospitais/
│   ├── Mamografias/
│   ├── Mortalidade/
│   ├── Municípios/
│   └── População/
├── Interpolados/   # população por faixa etária de 1970 a 2025, por município e por Regional
└── Taxas/          # valores somados por Regional e taxas por 100 mil habitantes
```

Todos os arquivos são CSV com separador `,` e codificação UTF-8. Nomes de municípios e Regionais aparecem em minúsculas e sem acento nas colunas `MUNICÍPIO` e `REGIONAL DE SAÚDE`, exceto na tabela de municípios, que traz também os nomes originais.

Células vazias indicam ausência de registro para aquele município (ou Regional) e ano; elas não representam zero.

## Convenções de colunas

- `AAAA` é o ano com 4 dígitos. `AAAA_<faixa>` é a contagem (ou a população) da faixa etária naquele ano.
- As 8 faixas etárias padrão são `0-9`, `10-19`, `20-29`, `30-39`, `40-49`, `50-59`, `60-69` e `70 OU MAIS`.
- `AAAA_TOTAL` é a soma das categorias do ano.
- O sufixo `_TAXA` é a taxa por 100 mil habitantes da coluna correspondente.

## Tratados (por município)

| Variável | Nome do arquivo | Colunas |
|---|---|---|
| Municípios e Regionais de Saúde | `Municípios/tabela_municipios_regionais.csv` | `CÓDIGO IBGE`, `MUNICÍPIO ORIGINAL`, `MUNICÍPIO NORMALIZADO`, `REGIONAL ORIGINAL`, `REGIONAL NORMALIZADA` |
| Casos por ano de diagnóstico | `Casos/tabela_casos_por_ano_de_diagnóstico.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_DIAGNOSTICO` (1985–2023), `ANO_SEM-INFORMAÇÃO`, `AAAA_TOTAL` |
| Casos por escolaridade | `Casos/tabela_casos_por_escolaridade.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<categoria>` (`SEM INFORMAÇÃO`, `NENHUMA`, `FUNDAMENTAL INCOMPLETO`, `FUNDAMENTAL COMPLETO`, `NÍVEL MÉDIO`, `NÍVEL SUPERIOR INCOMPLETO`, `NÍVEL SUPERIOR COMPLETO`), `AAAA_TOTAL` |
| Casos por faixa etária | `Casos/tabela_casos_por_faixa_etária.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<faixa>` (8 faixas), `AAAA_TOTAL` |
| Casos por raça e cor | `Casos/tabela_casos_por_raça_e_cor.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<categoria>` (`BRANCA`, `PRETA`, `PARDA`, `AMARELA`, `INDÍGENA`, `SEM INFORMAÇÃO`), `AAAA_TOTAL` |
| Hospitais habilitados | `Hospitais/tabela_hospitais_habilitados.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `TIPO` (`ONCOLOGIA`, `RECONSTRUÇÃO MAMÁRIA`, `TRATAMENTO SINCRÔNICO`), `2023_TOTAL` |
| Mamografias por faixa etária | `Mamografias/tabela_mamografias_por_faixa_etária.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<faixa>` (2013–2025), `AAAA_TOTAL` |
| Mortalidade por faixa etária | `Mortalidade/tabela_mortes_por_faixa_etária.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<faixa>` (1979–2024), `AAAA_TOTAL` |
| População feminina por faixa etária (anos censitários) | `População/tabela_populacao_faixa_etaria.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<faixa>` e `AAAA_TOTAL` para 1970, 1980, 1991, 2000, 2010 e 2022 |

## Interpolados (população por ano)

A população feminina de cada faixa etária foi estimada para todos os anos de 1970 a 2025 pelo método geométrico: interpolação entre dois censos consecutivos e extrapolação para 2023–2025 com a taxa do último intervalo censitário (2010–2022). O total de cada ano é a soma das 8 faixas.

| Variável | Nome do arquivo | Colunas |
|---|---|---|
| População feminina por município | `populacao_interpolacao_extrapolacao.csv` | `MUNICÍPIO`, `CÓDIGO IBGE`, `REGIONAL DE SAÚDE`, `AAAA_<faixa>` e `AAAA_TOTAL` para todos os anos de 1970 a 2025 |
| População feminina por Regional | `populacao_interpolacao_extrapolacao_por_regional.csv` | `REGIONAL DE SAÚDE`, `AAAA_<faixa>` e `AAAA_TOTAL` para 1970 a 2025 |

## Taxas (por Regional de Saúde)

Cada arquivo tem uma linha por Regional. Para cada coluna de valor há a quantidade somada e, ao lado, a coluna `_TAXA` (valor por 100 mil habitantes, calculado com a população feminina estimada da Regional naquele ano, ver `Interpolados/`).

| Variável | Nome do arquivo | Colunas |
|---|---|---|
| Casos por ano de diagnóstico | `tabela_casos_por_ano_de_diagnóstico_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_DIAGNOSTICO`, `AAAA_DIAGNOSTICO_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (1985–2023) |
| Casos por escolaridade | `tabela_casos_por_escolaridade_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_<categoria>`, `AAAA_<categoria>_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (1998–2023) |
| Casos por faixa etária | `tabela_casos_por_faixa_etária_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_<faixa>`, `AAAA_<faixa>_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (1985–2023) |
| Casos por raça e cor | `tabela_casos_por_raça_e_cor_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_<categoria>`, `AAAA_<categoria>_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (1998–2023) |
| Mamografias por faixa etária | `tabela_mamografias_por_faixa_etária_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_<faixa>`, `AAAA_<faixa>_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (2013–2025) |
| Mortalidade por faixa etária | `tabela_mortes_por_faixa_etária_taxa.csv` | `REGIONAL DE SAÚDE`, `AAAA_<faixa>`, `AAAA_<faixa>_TAXA`, `AAAA_TOTAL`, `AAAA_TOTAL_TAXA` (1979–2024) |
| Hospitais habilitados | `tabela_hospitais_habilitados_taxa.csv` | `REGIONAL DE SAÚDE`, `TIPO` (inclui `TODOS`), `2023_TOTAL`, `2023_TOTAL_TAXA` |
| Agregado estadual por ano (todas as variáveis) | `tabela_regional_agregada_por_ano.csv` | `ANO` e, para cada variável, `<categoria>_<VARIÁVEL>` e `<categoria>_<VARIÁVEL>_TAXA`, com `VARIÁVEL` em `CASOS`, `CASOS_ESCOLARIDADE`, `CASOS_RACA_COR`, `MORTES`, `MAMOGRAFIAS` e `HOSPITAIS` |
