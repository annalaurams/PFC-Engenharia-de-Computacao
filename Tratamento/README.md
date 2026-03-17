# Tratamento - Processamento e Padronização das Variáveis

Esta pasta reúne as tabelas consolidadas e scripts de limpeza/transformação que convertem os dados de `Variáveis/` para um formato analítico consistente.

## Objetivo técnico

- Padronizar nomes de município/regional.
- Filtrar recortes de interesse (principalmente MG).
- Harmonizar estrutura temporal (ano + categoria/faixa).
- Consolidar múltiplas fontes em tabelas únicas por domínio.

## 1) Casos (`Tratamento/Casos`)

### Arquivos finais
- `resultado_ano_diagnostico_casos.csv`
- `resultado_escolaridade_casos.csv`
- `resultado_faixa_etaria_casos.csv`
- `resultado_raca_cor_casos.csv`
- `resultado_casos_unificado.csv`

### Tratamento aplicado
- Agregação por **município** e por dimensão analítica:
  - ano diagnóstico;
  - escolaridade;
  - faixa etária;
  - raça/cor.
- Transformação para formato de colunas temporais do tipo `ANO_CATEGORIA`.
- Unificação das quatro dimensões em um arquivo consolidado (`resultado_casos_unificado.csv`).

### Como o processamento é realizado
- O fluxo de montagem está no notebook `tabela_numero_de_casos.ipynb`.
- As saídas indicam pivotamento/merge de tabelas por município, preservando séries históricas de cada dimensão.

## 2) Hospitais (`Tratamento/Hospitais`)

### Scripts
- `hospitais_mg.py`
- `normalizar_reduzir_colunas.py`

### Arquivos finais
- `hospitais_de_mg.csv`
- `hospitais_de_mg_normalizado.csv`

### Tratamento aplicado
1. **Leitura de 3 planilhas** (oncologia, reconstrução mamária e tratamento sincrônico).
2. **Ajustes de estrutura**:
   - `strip()` em nomes de colunas;
   - preenchimento (`ffill`) de colunas hierárquicas na planilha de oncologia;
   - remoção de linhas vazias conforme colunas-chave.
3. **Filtro territorial**: manutenção apenas de registros de MG.
4. **Unificação vertical** das 3 bases com coluna de tipo (`TIPO`).
5. **Normalização final**:
   - remoção de colunas administrativas não essenciais;
   - normalização de `MUNICÍPIO` para minúsculas sem acento;
   - reorganização com município na primeira coluna.

## 3) Índices (`Tratamento/Índices`)

### Script
- `gerar_ifdm_mg_csvs.py`

### Arquivos finais
- `IFDM-Geral-MG.csv`
- `IFDM-Educacao-MG.csv`
- `IFDM-Saude-MG.csv`
- `IFDM-Emprego-Renda-MG.csv`
- `IFDM-Unificado-MG.csv`

### Tratamento aplicado
1. Leitura da planilha histórica IFDM (com fallback de caminho).
2. Filtro por `SIGLA_UF = MG`.
3. Renomeação `NOME_MUNIC -> Municípios`.
4. Normalização textual de municípios (minúsculas sem acento).
5. Reordenação de colunas (identificação + rankings + valores IFDM).
6. Geração de uma tabela ampla unificada (`IFDM-Unificado-MG.csv`) por merge dos quatro componentes:
   - chave: `Municípios` + `COD_MUNIC`;
   - colunas dos componentes recebem sufixo de índice (`[geral]`, `[educacao]`, `[saude]`, `[emprego_renda]`) para evitar colisão.

## 4) Mortalidade (`Tratamento/Mortalidade`)

### Script
- `tabela_mortalidade.py`

### Arquivo final
- `mortalidade_agrupada_ano_faixa_etaria.csv`

### Tratamento aplicado
1. Varredura da estrutura por **regional -> município -> arquivos CSV anuais**.
2. Leitura robusta de CSV (tentativa `latin-1`, fallback `utf-8`).
3. Extração do ano pelo nome do arquivo.
4. Interpretação e padronização de rótulos de faixa etária para blocos:
   - `0-9`, `10-19`, ..., `70-79`, `80 ou mais`.
5. Conversão numérica com tratamento de formato brasileiro (`.` milhar, `,` decimal).
6. Agregação em colunas `ANO_FAIXA` com soma quando necessário.
7. Inclusão de colunas faltantes para padronizar grade temporal.
8. Cálculo de `TOTAL_MORTES` por município.
9. Normalização de `Município` (minúsculas sem acento e remoção de sufixo `-mg`).

## 5) Municípios (`Tratamento/Municípios`)

### Script
- `municipios_regionais_normalizados.py`

### Arquivo final
- `municipios_regionais_normalizados.csv`

### Tratamento aplicado
1. Leitura da aba `RegionalizaçãoMG2024` da planilha de referência.
2. Seleção e reorganização de campos-chave:
   - `codigo_ibge`
   - `municipio_original` e `municipio_normalizado`
   - `regional_original` e `regional_normalizada`
3. Normalização textual (sem acento + minúsculas) para município e regional.

## 6) População - Faixa Etária (`Tratamento/População - Faixa Etária`)

### Script
- `populacao_faixa_etaria.py`

### Arquivo final
- `tabela_populacao_faixa_etaria.csv`

### Tratamento aplicado
1. Leitura de pares de arquivos por ano (`1-AAAA.csv` e `2-AAAA.csv`).
2. Limpeza de colunas (`strip`, remoção de `Unnamed`).
3. Merge interno por chaves (`Sigla`, `Código`, `Município`) para recompor faixas do ano.
4. Mapeamento das colunas de idade originais para faixas decenais padronizadas.
5. Criação de colunas `ANO_FAIXA` (ex.: `2010_40-49`).
6. Merge entre anos para formar série histórica única.
7. Conversão de faltantes para zero e cast para inteiro nas colunas numéricas.
8. Cálculo de `TOTAL_POPULACAO` por município.
9. Remoção de `Sigla` e `Código` na saída final e normalização do nome de município.

## Padrões de transformação usados no projeto

- Normalização textual com remoção de acentos e uso de minúsculas.
- Reorganização de colunas para priorizar identificadores territoriais no início.
- Uso de codificação UTF-8 (com BOM em parte das saídas) para compatibilidade com planilhas.
- Consolidação em formato tabular amplo para facilitar cruzamento com outras variáveis.

## Reprodutibilidade

A atualização das tabelas tratadas depende da atualização prévia dos insumos em `Variáveis/`.
Em seguida, os scripts de cada subpasta de `Tratamento/` podem ser executados de forma independente por domínio.