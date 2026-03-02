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

### 4. Código
Scripts Python para análise e validação da estrutura de dados das regionais e municípios.

**Scripts principais:**
- **`cidades.py`** - Extrai lista de todas as cidades por regional das pastas
- **`normalizar_csv.py`** - Normaliza nomes das cidades (remove acentos, minúsculas, sem "-MG")
- **`listar_problemas.py`** - Identifica duplicatas e erros de nomenclatura
- **`verificar_tudo.py`** - Script mestre que executa toda a análise

**Uso:** Execute `python3 verificar_tudo.py` dentro da pasta Código para gerar todos os relatórios na pasta `Saídas/`.

**Saídas geradas:**
- `cidades_por_regional.csv` - Lista completa de cidades por regional
- `cidades_por_regional_normalizado.csv` - Lista normalizada
- `PROBLEMAS_ENCONTRADOS.csv` - Problemas identificados (duplicatas, erros de digitação)

