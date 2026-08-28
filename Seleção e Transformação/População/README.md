# Seleção e Transformação - População - Faixa Etária

## Estrutura da pasta

```
População - Faixa Etária/
├── populacao_tratamento.ipynb                     # consolida os censos do IBGE
├── interpolacao_extrapolação.ipynb                # estima população nos anos sem censo
├── calculo_taxa.ipynb                              # calcula taxas por 100 mil habitantes
├── tabela_populacao_faixa_etaria.csv               # população por município, ano censitário e faixa etária
├── populacao_interpolacao_extrapolacao.csv         # população estimada para todos os anos 1970-2025
├── casos_ano_diagnostico_taxa_por_100_mil.csv       # taxa de casos por ano de diagnóstico
├── casos_escolaridade_taxa_por_100_mil.csv          # taxa de casos por escolaridade
├── casos_faixa_etaria_taxa_por_100_mil.csv          # taxa de casos por faixa etária
├── casos_raca_cor_taxa_por_100_mil.csv              # taxa de casos por raça-cor
├── mortalidade_taxa_por_100_mil.csv                 # taxa de mortalidade
├── mamografia_taxa_por_100_mil.csv                  # taxa de exames de mamografia
├── hospitais_taxa_por_100_mil.csv                   # taxa de hospitais habilitados
└── hospitais_por_tipo_taxa_por_100_mil.csv          # taxa de hospitais habilitados, por tipo de habilitação
```

Esta é a única subpasta desta etapa com mais de um notebook: além de consolidar os dados brutos, ela também estima população para os anos sem censo e calcula as taxas por 100 mil habitantes usadas na etapa seguinte (Mineração de Dados).

## O que cada notebook faz

- **populacao_tratamento.ipynb**: consolida os censos do IBGE (1970, 1980, 1991, 2000, 2010, 2022) por município e faixa etária.
- **interpolacao_extrapolação.ipynb**: estima a população de cada município em todos os anos entre 1970 e 2025, incluindo os anos sem censo.
- **calculo_taxa.ipynb**: calcula, para cada variável do projeto (casos, mortalidade, mamografia, hospitais), a taxa por 100 mil habitantes usando a população estimada.

## Resumo das operações

`populacao_tratamento.ipynb` é a versão atualizada e documentada da lógica de `Tratamento/População - Faixa Etária/main.py` (ver [../README.md](../README.md) para a relação entre as duas pastas). Localiza os pares de arquivos `1-AAAA.csv`/`2-AAAA.csv` de cada ano censitário, une as duas partes, agrupa as colunas de população em faixas decenais e monta uma tabela wide com uma coluna por ano/faixa e uma coluna `TOTAL_<ano>` por ano censitário, com o código IBGE de cada município. Salva `tabela_populacao_faixa_etaria.csv`.

`interpolacao_extrapolação.ipynb` não tem equivalente em `Tratamento`. Parte de `tabela_populacao_faixa_etaria.csv` e usa o método geométrico discreto de interpolação/extrapolação populacional (razão de crescimento constante entre dois pontos conhecidos) para estimar a população total de cada município em todo ano entre 1970 e 2025: interpola entre censos consecutivos e extrapola para os anos posteriores ao último censo (2023-2025) a partir da taxa observada entre os dois últimos censos (2010 e 2022). Salva o resultado em `populacao_interpolacao_extrapolacao.csv`.

`calculo_taxa.ipynb` também não tem equivalente em `Tratamento`. Importa funções utilitárias de `Mineração de Dados - Avaliação e Apresentação/Análise Populacional/utilitarios_comuns.py` e as especificações de variáveis de `configuracao_variaveis.py` (mesma pasta) — este é o único ponto do projeto onde a etapa de Seleção e Transformação reaproveita código de fora dela mesma. Para cada variável tratada nas demais subpastas desta etapa (Casos, Mortalidade, Mamografia, Hospitais), calcula a taxa por 100 mil habitantes (valor absoluto dividido pela população do mesmo ano, multiplicado por 100.000, arredondado a 2 casas decimais), usando `populacao_interpolacao_extrapolacao.csv` como base populacional. Os CSVs de taxa gerados não ficam nesta pasta: são salvos diretamente em `Mineração de Dados - Avaliação e Apresentação/Análise Populacional`, de onde os notebooks de análise daquela etapa os leem. Os arquivos `*_taxa_por_100_mil.csv` presentes nesta pasta são cópias/versões geradas em execuções anteriores do notebook antes desse ajuste de caminho de saída.
