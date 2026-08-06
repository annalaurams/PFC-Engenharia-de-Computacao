# Análise Populacional

## Objetivo desta parte

Os dados de Casos, Mortalidade, Mamografia e Hospitais Habilitados só
existem como **números absolutos** (ex.: "42 casos em Uberlândia em
2015"). Números absolutos não podem ser comparados diretamente entre
municípios ou entre anos, porque municípios maiores naturalmente têm
mais casos só por terem mais gente — não porque o problema seja mais
grave lá.

Esta pasta resolve dois problemas para permitir essa comparação:

1. **A população de Minas Gerais só é contada de 6 em 6 anos (censo
   do IBGE: 1970, 1980, 1991, 2000, 2010, 2022)**, mas os dados de
   saúde existem ano a ano desde 1970 até hoje. É preciso estimar a
   população nos anos entre censos (**interpolação**) e depois de
   2022 (**extrapolação**), para cada um dos 853 municípios de MG.
2. **Com a população estimada ano a ano, calcular a taxa por 100 mil
   habitantes** de cada variável (Casos, Mortalidade, Mamografia,
   Hospitais), o que torna os números comparáveis entre municípios de
   tamanhos diferentes e entre anos diferentes — e gerar os gráficos
   finais usados na análise.

## Resultado geral da saída

- Uma série populacional completa (1970–2025) para os 853 municípios
  de MG, por dois métodos diferentes (linear e geométrico), com
  validação do erro de cada método.
- Um CSV de **taxa por 100 mil habitantes** para cada variável de
  saúde (Casos, Mortalidade, Mamografia, Hospitais, e as versões por
  categoria: escolaridade, raça/cor, faixa etária).
- Um conjunto de gráficos (pasta `Figuras/`) mostrando a evolução das
  taxas ao longo do tempo, a comparação entre Regionais de Saúde, e a
  composição por categoria — prontos para uso na apresentação/TCC.

O método **geométrico** é o adotado como resultado final (é o que
alimenta os notebooks de cálculo de taxa e gráfico); o método linear
existe como comparação/validação alternativa.

---

## Como os arquivos se encaixam (ordem de execução)

```
1. interpolacao_extrapolacao_geometrica.ipynb   ─┐
   interpolacao_extrapolacao_linear.ipynb        ├─► gera as séries de população
                                                  │   (populacao_interpolacao_extrapolacao_*.csv)
2. erro_populacional_geometrico.ipynb            │
   erro_populacional_linear.ipynb                ┘─► valida se as séries do passo 1 são confiáveis

3. calculo_taxas_por_variavel_corrigido.ipynb    ──► usa a população do passo 1 para calcular
                                                      a taxa por 100 mil de cada variável
                                                      (*_taxa_por_100_mil.csv)

4. grafico_taxa_por_ano_corrigido.ipynb          ──► usa os CSVs de taxa do passo 3 para
   grafico_taxa_por_regional_corrigido.ipynb         gerar os gráficos finais (pasta Figuras/)
```

`utilitarios_populacional.py` não é executado diretamente — é uma
"caixa de ferramentas" com funções e constantes usadas por todos os
notebooks acima, para não repetir código.

---

## Descrição de cada arquivo

### Notebooks — Estimativa de População

**`interpolacao_extrapolacao_geometrica.ipynb`**
Estima a população de cada município de MG, ano a ano, de 1970 a 2025,
usando o **método geométrico** (crescimento percentual composto,
"juros compostos" aplicado à população). Faz três coisas:
- **Interpolação**: preenche os anos *entre* dois censos (ex.: 1971 a
  1979, entre os censos de 1970 e 1980), assumindo taxa de crescimento
  constante entre os dois pontos conhecidos.
- **Extrapolação**: estima os anos *depois* do último censo (2023 a
  2025), usando crescimento exponencial contínuo a partir da taxa
  observada entre os dois últimos censos.
- Arredonda sempre para cima (`np.ceil`), para nunca subestimar a
  população, e confere que os anos de censo originais batem com os
  valores interpolados (checagem de sanidade).
- **Saída**: `populacao_interpolacao_extrapolacao_geometrica.csv`.

**`interpolacao_extrapolacao_linear.ipynb`**
Mesma ideia acima, mas usando o **método aritmético/linear**
(crescimento por uma quantidade fixa de pessoas por ano, "reta" em vez
de "curva"). Serve de comparação com o método geométrico — também
compara as três formas de calcular taxa de crescimento (aritmética,
geométrica, exponencial) lado a lado.
- **Saída**: `populacao_interpolacao_extrapolacao_linear.csv`.

### Notebooks — Validação da Estimativa

**`erro_populacional_geometrico.ipynb`**
Testa a qualidade do método geométrico: esconde um censo conhecido,
estima a população nesse ano usando os censos vizinhos, e compara a
estimativa com o valor real — calculando o **Erro Percentual (EP)**.
Gera gráficos da curva populacional do estado, do erro percentual ao
longo do tempo, e da população por Regional de Saúde. Também calcula
o EP **anualizado** (erro dividido pelo tempo decorrido no teste), para
comparar de forma justa testes com janelas de tempo diferentes entre
censos.

**`erro_populacional_linear.ipynb`**
Mesma validação, mas para o método aritmético/linear.

### Notebooks — Cálculo de Taxa e Gráficos

**`calculo_taxas_por_variavel_corrigido.ipynb`**
Pega a população estimada (geométrica) e cruza com cada variável de
saúde para calcular:
$$\text{Taxa} = \frac{\text{Quantidade do evento}}{\text{População}} \times 100.000$$
Processa Casos, Mortalidade, Mamografia, Hospitais (incluindo a versão
"por tipo" de hospital) e as variáveis categóricas de Casos
(escolaridade, raça/cor, faixa etária). Não gera gráfico — só produz
os CSVs de taxa usados nos dois notebooks de gráfico a seguir.

**`grafico_taxa_por_ano_corrigido.ipynb`**
Gera os gráficos de evolução **ano a ano** para Minas Gerais inteiro:
barras (valor absoluto) + linha (taxa por 100 mil) no mesmo gráfico,
com dois eixos Y. Para Hospitais (que só tem dado de 2023), usa o tipo
de hospital no eixo X em vez do ano. Também gera os gráficos de barras
empilhadas de composição (faixa etária/raça-cor/escolaridade) por ano.

**`grafico_taxa_por_regional_corrigido.ipynb`**
Mesma ideia, mas agrupando os municípios pelas suas **Regionais de
Saúde** (em vez de por ano) e somando todo o período disponível —
mostra quais regiões do estado têm a maior/menor taxa. Também tem a
versão de Hospitais por tipo × regional e os gráficos empilhados de
composição por regional.

### Módulo compartilhado

**`utilitarios_populacional.py`**
Não é um notebook — é um arquivo Python com as funções e constantes
reaproveitadas por todos os notebooks acima: nomes de coluna
padronizados, normalização do Código IBGE, fórmulas dos métodos
geométrico/exponencial/aritmético, cálculo de erro percentual, e o
"kit" de gráficos (`montar_grafico_barra_linha`,
`montar_grafico_empilhado`, `salvar_figura`) — assim o layout dos
gráficos fica idêntico em todos os notebooks, e cada um só precisa
informar os dados/título/cores.

### Dados de entrada

**`populacao_interpolacao_extrapolacao_geometrica.csv`**
População estimada (método geométrico) de cada município de MG,
ano a ano, 1970–2025. Gerado por `interpolacao_extrapolacao_geometrica.ipynb`
e usado como base para o cálculo de todas as taxas.

**`populacao_interpolacao_extrapolacao_linear.csv`**
Mesma coisa, pelo método linear — usado só para comparação/validação,
não entra no cálculo das taxas oficiais.

### Dados de saída — Taxas por 100 mil habitantes

Todos gerados por `calculo_taxas_por_variavel_corrigido.ipynb`, com
uma linha por município × ano (ou por município × categoria, nos
categóricos):

| Arquivo | Conteúdo |
|---|---|
| `casos_taxa_por_100_mil.csv` | Taxa de incidência de câncer de mama, por município e ano |
| `mortalidade_taxa_por_100_mil.csv` | Taxa de mortalidade por câncer de mama, por município e ano |
| `mamografia_taxa_por_100_mil.csv` | Taxa de mamografias realizadas, por município e ano |
| `hospitais_taxa_por_100_mil.csv` | Taxa de hospitais habilitados (2023), por município |
| `hospitais_por_tipo_taxa_por_100_mil.csv` | Igual ao acima, mas sem somar os tipos de hospital (Oncologia, Reconstrução Mamária, Tratamento Sincrônico) |
| `casos_escolaridade_taxa_por_100_mil.csv` | Taxa de casos por município, aberta por nível de escolaridade |
| `casos_raca_cor_taxa_por_100_mil.csv` | Taxa de casos por município, aberta por raça/cor |
| `casos_faixa_etaria_taxa_por_100_mil.csv` | Taxa de casos por município, aberta por faixa etária |

### Pasta `Figuras/`

Contém os gráficos finais gerados pelos dois notebooks de gráfico, em
dois formatos: `.html` (interativo, abre no navegador) e `.png`
(imagem estática, para inserir no TCC/apresentação).

- `taxa_<variável>_por_ano.*` — evolução ano a ano em Minas Gerais
  (Casos, Mortalidade, Mamografia, Hospitais por tipo).
- `taxa_<variável>_por_regional.*` — comparação entre Regionais de
  Saúde, somando todo o período (Casos, Mortalidade, Mamografia,
  Hospitais, Hospitais por tipo).
- `empilhado_<categoria>_por_ano.*` e `empilhado_<categoria>_por_regional.*`
  — composição percentual dos casos por faixa etária, raça/cor e
  escolaridade, ao longo dos anos ou por regional.
