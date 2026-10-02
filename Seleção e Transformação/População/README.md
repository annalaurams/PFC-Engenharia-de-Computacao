# Seleção e Transformação - População

## Estrutura da pasta

```
População/
├── populacao_tratamento.ipynb                            # consolida os censos do IBGE
├── utilitarios_comuns.py                                 # funções utilitárias compartilhadas (usadas por esta pasta e por Avaliação e Apresentação)
├── tabela_populacao_faixa_etaria.csv                      # população por município, ano censitário e faixa etária
│
├── Interpolação e Extrapolação/
│   ├── interpolacao_extrapolacao.ipynb                          # estima população nos anos sem censo
│   ├── populacao_interpolacao_extrapolacao.csv                  # população estimada para todos os anos 1970-2025, por município
│   └── populacao_interpolacao_extrapolacao_por_regional.csv     # idem, agregada por regional de saúde
│
└── Taxa/
    ├── calculo_taxa.ipynb                              # calcula taxas por 100 mil habitantes
    ├── tabela_casos_por_ano_de_diagnóstico_taxa.csv    # taxa de casos por ano de diagnóstico
    ├── tabela_casos_por_escolaridade_taxa.csv          # taxa de casos por escolaridade
    ├── tabela_casos_por_faixa_etária_taxa.csv          # taxa de casos por faixa etária
    ├── tabela_casos_por_raça_e_cor_taxa.csv            # taxa de casos por raça-cor
    ├── tabela_mortes_por_faixa_etária_taxa.csv         # taxa de mortalidade
    ├── tabela_mamografias_por_faixa_etária_taxa.csv    # taxa de exames de mamografia
    ├── tabela_hospitais_habilitados_taxa.csv           # taxa de hospitais habilitados
    └── tabela_regional_agregada_por_ano.csv            # taxas agregadas por regional de saúde e ano
```

Esta é a única subpasta desta etapa com mais de um notebook: além de consolidar os dados brutos, ela também estima população para os anos sem censo e calcula as taxas por 100 mil habitantes usadas na etapa seguinte (Mineração de Dados).

## O que cada notebook faz

- **populacao_tratamento.ipynb**: consolida os censos do IBGE (1970, 1980, 1991, 2000, 2010, 2022) por município e faixa etária.
- **Interpolação e Extrapolação/interpolacao_extrapolacao.ipynb**: estima a população de cada município (e, agregada, de cada regional) em todos os anos entre 1970 e 2025, incluindo os anos sem censo.
- **Taxa/calculo_taxa.ipynb**: calcula, para cada variável do projeto (casos, mortalidade, mamografia, hospitais), a taxa por 100 mil habitantes usando a população estimada.

## Resumo das operações

`populacao_tratamento.ipynb` localiza os pares de arquivos `1-AAAA.csv`/`2-AAAA.csv` de cada ano censitário (em `Limpeza e Integração/População - Faixa Etária`), une as duas partes, agrupa as colunas de população em faixas decenais e monta uma tabela wide com uma coluna por ano/faixa e uma coluna `TOTAL_<ano>` por ano censitário, com o código IBGE de cada município. Salva `tabela_populacao_faixa_etaria.csv`.

`Interpolação e Extrapolação/interpolacao_extrapolacao.ipynb` parte de `tabela_populacao_faixa_etaria.csv` e usa o método geométrico discreto de interpolação/extrapolação populacional (razão de crescimento constante entre dois pontos conhecidos) para estimar a população total de cada município em todo ano entre 1970 e 2025: interpola entre censos consecutivos e extrapola para os anos posteriores ao último censo (2023-2025) a partir da taxa observada entre os dois últimos censos (2010 e 2022). Salva o resultado por município em `populacao_interpolacao_extrapolacao.csv` e a versão agregada por regional em `populacao_interpolacao_extrapolacao_por_regional.csv`.

`Taxa/calculo_taxa.ipynb` importa funções utilitárias de `utilitarios_comuns.py` (na raiz desta pasta, `População/`). O mesmo arquivo também é importado pelos notebooks de `Avaliação e Apresentação/` (via `Avaliação e Apresentação/caminho_utilitarios.py`, que resolve o caminho até esta pasta) e diretamente pelos dois pipelines de `Mineração de Dados/` (`DBSCAN/utilitarios_agrupamentoManual.py` e `KMEANS/utilitarios_agrupamento_kmeansManual.py`, cada um localizando esta pasta a partir da própria posição no repositório) — é o único ponto do projeto onde código de baixo nível é reaproveitado entre as etapas de Seleção e Transformação, Mineração de Dados e Avaliação e Apresentação. Para cada variável tratada nas demais subpastas desta etapa (Casos, Mortalidade, Mamografia, Hospitais), calcula a taxa por 100 mil habitantes (valor absoluto dividido pela população do mesmo ano, multiplicado por 100.000, arredondado a 2 casas decimais), usando `populacao_interpolacao_extrapolacao.csv` como base populacional. Os CSVs de taxa gerados são salvos em `Taxa/`, de onde os notebooks de `Mineração de Dados/` (DBSCAN, KMeans) e de `Avaliação e Apresentação/` os leem.
