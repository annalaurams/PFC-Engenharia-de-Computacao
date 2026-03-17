# PFC I - Base Integrada para Análise Oncológica em Minas Gerais

Este repositório organiza a coleta, o armazenamento e o tratamento de dados usados no TCC, com foco em câncer de mama feminino em Minas Gerais. O objetivo é consolidar variáveis demográficas, assistenciais e socioeconômicas em tabelas padronizadas por município e série temporal.

## Visão geral do projeto

- **Tema**: análise de casos oncológicos e fatores associados em MG.
- **Unidade geográfica principal**: município.
- **Integração de fontes**: INCA (RHC/Atlas), FIRJAN (IFDM), bases administrativas de saúde e planilhas oficiais.
- **Produto final**: tabelas tratadas em `Tratamento/` prontas para análise estatística, visualização e cruzamentos.

## Organização das pastas

- **`Variáveis/`**: camada de dados de entrada (brutos ou semibrutos), incluindo scripts de extração quando aplicável.
- **`Tratamento/`**: camada de preparação e padronização (filtro MG, normalização de municípios, agregações por ano/faixa/categoria e unificações).
- **`Dashboard/`**: artefatos de visualização e exploração.
- **`src/`**: estrutura de pacote Python do projeto.

## Fluxo de dados (alto nível)

1. **Aquisição**
   - Parte dos dados é obtida por **extração automatizada via script** (ex.: RHC/INCA, Atlas de Mortalidade).
   - Parte é obtida por **download direto de planilhas/tabelas oficiais** (ex.: IFDM FIRJAN, hospitais habilitados, população).
2. **Armazenamento em `Variáveis/`**
   - Organização por domínio temático (Casos, Mortalidade, IFDM, População, etc.).
3. **Processamento em `Tratamento/`**
   - Filtros de escopo (MG), padronização textual, harmonização de colunas e construção de tabelas consolidadas.
4. **Consumo analítico**
   - Uso das tabelas finais para análise no TCC e materiais de apoio (notebooks/dashboard).

## Documentação detalhada

- Detalhamento completo das variáveis: `Variáveis/README.md`
- Detalhamento técnico dos tratamentos: `Tratamento/README.md`

