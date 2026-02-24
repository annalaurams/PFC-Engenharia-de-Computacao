# PFC I -  Extração de Dados

## Variáveis 1 - Atlas da Mortalidade por Câncer (INCA)

Este diretório contém dados de mortalidade por câncer feminino no estado de Minas Gerais, extraídos do Atlas da Mortalidade do INCA, cobrindo o período de **1979 a 2024**.

## 📂 Estrutura das Pastas

### 1. Regionais de Saúde (29)
Dados de mortalidade organizados por **29 regionais de saúde** de Minas Gerais.

**Conteúdo:**
- Arquivos CSV anuais (1979-2024) para cada regional
- Taxas de mortalidade por câncer feminino segmentadas por faixa etária
- Scripts de processamento (`main.py`, `auditoria_csv_cidades.py`)
- Documentação dos filtros aplicados (`Variáveis 1 - Filtro I.txt`)

**Regionais incluídas:** Alfenas, Barbacena, Belo Horizonte, Coronel Fabriciano, Diamantina, Divinópolis, Governador Valadares, Itabira, Ituiutaba, Januária, Juiz de Fora, Leopoldina, Manhumirim, Montes Claros, Passos, Patos de Minas, Pedra Azul, Pirapora, Ponte Nova, Pouso Alegre, São João Del Rei, Sete Lagoas, Teófilo Otoni, Ubá, Uberaba, Uberlândia, Unaí e Varginha.

### 2. Cidades Atendidas por Cada Regional
Dados de mortalidade organizados por municípios dentro de cada regional de saúde, ou seja, as cidades que uma determinada regional atende.

**Conteúdo:**
- Estrutura hierárquica: Regional → Município → Dados CSV
- Taxas de mortalidade por câncer feminino por faixa etária para cada município
- Cobertura de todas as cidades atendidas pelas 29 regionais de saúde
- Scripts de extração e auditoria (`main_extracao.py`, `auditoria_csv_cidades.py`)

### 3. Hospitais Habilitados
Informações sobre a infraestrutura hospitalar habilitada para tratamento oncológico em Minas Gerais.

**Conteúdo:**
- `hospitais-habilitados-em-oncologia-abril-2025.xlsx`: Lista de hospitais habilitados em oncologia
- `hospitais-habilitados-em-reconstrucao-mamaria.xlsx`: Hospitais credenciados para cirurgia de reconstrução mamária
- `tratamento-sincronico.xlsx`: Dados sobre tratamento síncrono

