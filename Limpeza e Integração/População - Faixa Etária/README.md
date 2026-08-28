# População - Faixa Etária

## Estrutura da pasta

```
População - Faixa Etária/
├── 1-1970.csv   # população feminina por faixa etária (grupo 1) - censo/contagem 1970
├── 1-1980.csv   # idem, 1980
├── 1-1991.csv   # idem, 1991
├── 1-2000.csv   # idem, 2000
├── 1-2010.csv   # idem, 2010
├── 1-2022.csv   # idem, 2022
├── 2-1970.csv   # população feminina por faixa etária (grupo 2) - censo/contagem 1970
├── 2-1980.csv   # idem, 1980
├── 2-1991.csv   # idem, 1991
├── 2-2000.csv   # idem, 2000
├── 2-2010.csv   # idem, 2010
└── 2-2022.csv   # idem, 2022
```

Os arquivos são planilhas em CSV baixadas diretamente do IBGE (Censos/Contagens Populacionais), sem processamento adicional.

## O que esta pasta faz

Fornece a população feminina de Minas Gerais por município e faixa etária, nos anos censitários 1970, 1980, 1991, 2000, 2010 e 2022. É a base de referência usada para calcular taxas de incidência e mortalidade por câncer de mama (número de casos ou óbitos por habitante) nas etapas seguintes do projeto.

## Resumo do conteúdo dos arquivos

Cada ano censitário é coberto por dois arquivos, identificados pelo prefixo `1-` e `2-`, que juntos formam o total das faixas etárias do IBGE dividido em duas planilhas (provavelmente por limite de colunas na exportação da fonte):

- **Arquivos `1-<ano>.csv`**: faixas de 0 a 4, 10 a 14, 15 a 19, 20 a 24, 25 a 29 e 30 a 39 anos.
- **Arquivos `2-<ano>.csv`**: faixas de 5 a 9, 40 a 49, 50 a 59, 60 a 69 e 70 anos ou mais.

Em ambos os casos, cada linha corresponde a um município de Minas Gerais, identificado por Sigla (UF), Código (IBGE) e Município, seguido pela contagem de mulheres em cada faixa etária para o ano em questão. Os dados cobrem os 853 municípios mineiros em todos os seis anos.
