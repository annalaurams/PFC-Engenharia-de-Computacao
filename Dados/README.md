# Dados

Dados de consulta usados no projeto sobre câncer de mama em Minas Gerais, organizados por Regional de Saúde (PFC, Engenharia de Computação). Estão publicados aqui os arquivos de cada etapa, do dado bruto extraído das fontes públicas até as tabelas prontas para análise.

O código de extração, tratamento, agrupamento (K-means) e os gráficos ficam nas outras branches do repositório (`pfc` e `pfcII`). Esta branch guarda somente os dados.

## Estrutura

```
Dados/
├── Dados brutos/            # arquivos como foram extraídos ou baixados, um por variável
│   ├── Casos/               # Ano Diagnóstico, Escolaridade, Faixa Etária, Raça-Cor
│   ├── Hospitais Habilitados/
│   ├── Mamografia/
│   ├── Mortalidade/         # <Regional>/<Município>-MG/AAAA-<Município>-MG.csv
│   ├── Municípios/
│   └── População - Faixa Etária/
└── Dados estruturados/      # tabelas únicas por variável, já tratadas
    ├── Tratados/            # municípios, Regionais e variáveis unificados em uma tabela
    ├── Interpolados/        # população por faixa etária de 1970 a 2025
    └── Taxas/               # valores por Regional e taxas por 100 mil habitantes
```

Cada pasta tem seu próprio README, com o nome de cada arquivo e a descrição das colunas:

- [Dados brutos/README.md](Dados%20brutos/README.md)
- [Dados estruturados/README.md](Dados%20estruturados/README.md)

## Fontes

| Variável | Fonte |
|---|---|
| Casos de câncer de mama (ano de diagnóstico, escolaridade, faixa etária, raça/cor) | Registros Hospitalares de Câncer (RHC), INCA, via TabNet |
| Mamografias | TabNet DATASUS (SISCAN) |
| Mortalidade por câncer de mama | Atlas de Mortalidade por Câncer, INCA |
| Hospitais habilitados em oncologia, reconstrução mamária e tratamento sincrônico | Ministério da Saúde |
| Municípios e Regionais de Saúde | Secretaria de Estado de Saúde de Minas Gerais (SES-MG) |
| População feminina por faixa etária | IBGE (censos de 1970, 1980, 1991, 2000, 2010 e 2022) |

As consultas de casos, mamografias e mortalidade foram restritas a câncer de mama (CID C50) em mulheres, em municípios de Minas Gerais.

## Convenções

- `AAAA` é o ano com 4 dígitos. `AAAA_<faixa>` é a contagem (ou a população) da faixa etária naquele ano.
- As 8 faixas etárias padrão são `0-9`, `10-19`, `20-29`, `30-39`, `40-49`, `50-59`, `60-69` e `70 OU MAIS`.
- `AAAA_TOTAL` é a soma das categorias do ano.
- O sufixo `_TAXA` é a taxa por 100 mil habitantes da coluna correspondente.
- A unidade de análise é o município nos dados brutos e tratados, e a Regional de Saúde nas taxas.
