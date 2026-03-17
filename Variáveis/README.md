# Variáveis - Dicionário das Bases de Entrada

Esta pasta concentra as bases utilizadas no projeto antes do processamento final. As variáveis estão organizadas por tema e podem ter origem em:

- **extração automatizada por script** (ex.: Selenium/rotinas de coleta);
- **download direto de tabelas/planilhas oficiais**.

## Escopo comum

- Recorte temático principal: câncer de mama feminino.
- Recorte territorial principal: Minas Gerais (MG).
- Unidade geográfica predominante: município (quando disponível na fonte).

## 1) Casos

### O que representa
Distribuições de casos do Registro Hospitalar de Câncer (RHC/INCA), com filtros de interesse do estudo (C50, sexo feminino, procedência MG), separadas por diferentes dimensões.

### Série temporal
- Arquivos anuais disponíveis em geral de **1985 a 2023** (a depender da disponibilidade do portal para cada dimensão).

### Características relevantes
- **Fonte**: INCA (RHC).
- **Granularidade**: município + categoria (ano diagnóstico, escolaridade, faixa etária, raça/cor).
- **Aquisição**: predominantemente via **scripts de extração** em `Casos/*/Código/main_extracao.py`.
- **Saída de entrada**: CSVs anuais em `Casos/*/Dados/`.

Subgrupos:
- **Ano Diagnóstico**: distribuição por ano de diagnóstico.
- **Escolaridade**: distribuição por categorias educacionais.
- **Faixa Etária**: distribuição por grupos etários.
- **Raça-Cor**: distribuição por categorias de raça/cor.

## 2) Hospitais Habilitados

### O que representa
Oferta de serviços habilitados relacionados à oncologia (incluindo reconstrução mamária e tratamento sincrônico).

### Série temporal
- Base **pontual/snapshot** (ex.: abril/2025 para uma das planilhas).

### Características relevantes
- **Fonte**: planilhas administrativas de saúde.
- **Granularidade**: estabelecimento de saúde.
- **Aquisição**: **download direto** de arquivos XLSX.
- **Conteúdo**: inclui campos administrativos (CNPJ/CNES/códigos), localização e tipo de habilitação.

## 3) Índices IFDM (por vezes referenciado como “FDN”)

### O que representa
Indicadores do Índice FIRJAN de Desenvolvimento Municipal (IFDM) e seus componentes para municípios de MG.

### Série temporal
- **2013 a 2023**.

### Características relevantes
- **Fonte**: FIRJAN (série histórica do IFDM).
- **Granularidade**: município (com código municipal).
- **Aquisição**: base principal por **download direto** de planilha histórica.
- **Componentes incluídos**:
  - IFDM Geral
  - IFDM Educação
  - IFDM Saúde
  - IFDM Emprego e Renda
- **Campos típicos**: ranking estadual, ranking nacional/geral e valor do índice por ano.

## 4) Mortalidade

### O que representa
Óbitos por câncer, organizados por regional de saúde e por município vinculado a cada regional.

### Série temporal
- Cobertura histórica ampla, com uso no projeto de **1979 a 2024** na etapa de consolidação.

### Características relevantes
- **Fonte**: Atlas de Mortalidade por Câncer (INCA).
- **Granularidade**: município e regional (com detalhamento por faixa etária, conforme arquivo).
- **Aquisição**: majoritariamente via **scripts de extração/auditoria** nas subpastas de mortalidade.
- **Estrutura de entrada**:
  - `Mortalidade/Regionais de Saúde (29)/`
  - `Mortalidade/Cidades Atendidas por Cada Regional/`

## 5) Municípios

### O que representa
Relação de municípios e vinculação administrativa por regional de saúde.

### Série temporal
- Base de referência administrativa (não necessariamente anual).

### Características relevantes
- **Fonte**: planilha oficial de regionalização (XLSX).
- **Granularidade**: município com código IBGE e regional.
- **Aquisição**: **download direto** da planilha.
- **Uso no projeto**: chave de apoio para padronização territorial e cruzamentos.

## 6) População - Faixa Etária

### O que representa
População municipal por grupos etários, usada para contextualização e indicadores.

### Série temporal
- Anos de referência disponíveis: **1970, 1980, 1991, 2000, 2010, 2022**.

### Características relevantes
- **Fonte**: tabelas oficiais de população.
- **Granularidade**: município + faixa etária.
- **Aquisição**: **download direto** dos CSVs.
- **Formato de entrada**: pares de arquivos por ano (`1-AAAA.csv` e `2-AAAA.csv`) para completar o conjunto de faixas.

## Observação sobre origem dos dados

Neste projeto coexistem duas estratégias de aquisição:

1. **Extração via script**: usada principalmente em fontes com interface de consulta/exportação dinâmica (ex.: RHC e Atlas).
2. **Download direto de tabelas**: usada em bases disponibilizadas em planilhas/CSV oficiais (ex.: IFDM, hospitais e população).

Essa distinção é importante para reprodutibilidade e atualização periódica das bases.