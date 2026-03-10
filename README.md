# PFC I - Extração de Dados

Este repositório organiza bases e scripts de extração/tratamento para o TCC, com foco em dados oncológicos de Minas Gerais.

## Estrutura principal (`variaveis/`)

### 1) Casos
Dados do Registro Hospitalar de Câncer (RHC/INCA), filtrados para:
- Localização primária: **C50 (mama)**
- UF de procedência: **MG**
- Sexo: **Feminino**

Subpastas:
- **Ano Diagnóstico**: distribuição dos casos por ano de diagnóstico.
- **Escolaridade**: distribuição dos casos por escolaridade.
- **Faixa Etária**: distribuição dos casos por faixa etária.
- **Raça-Cor**: distribuição dos casos por raça/cor.

Cada subpasta possui:
- `Código/`: script de automação (`main_extracao.py`) com Selenium.
- `Dados/`: arquivos CSV por ano (anos disponíveis no portal do INCA).

### 2) Hospitais Habilitados
Bases em planilhas sobre oferta assistencial oncológica em MG.

Conteúdo:
- `hospitais-habilitados-em-oncologia-abril-2025.xlsx`: hospitais habilitados em oncologia.
- `hospitais-habilitados-em-reconstrucao-mamaria.xlsx`: serviços habilitados para reconstrução mamária.
- `tratamento-sincronico.xlsx`: informações de tratamento síncrono.

Estrutura:
- `Código/`: notebook para filtro e preparação dos arquivos.
- `Dados/`: planilhas brutas e/ou tratadas.

### 3) Mortalidade
Dados do Atlas de Mortalidade por Câncer (INCA), organizados em dois níveis:
- **Regionais de Saúde (29)**: séries por regional.
- **Cidades Atendidas por Cada Regional**: séries por município dentro de cada regional.

Estrutura:
- `Código/`
	- `Filtros/`: notebook de consulta por cidade/regional.
	- `Tratamento/`: notebook de apoio para organização das cidades por regional.
- `Dados/`
	- `Regionais de Saúde (29)/`: scripts de extração/auditoria, filtros e pastas por regional.
	- `Cidades Atendidas por Cada Regional/`: scripts de extração/auditoria e pastas por município.

### 4) População
Bases de população para apoio a análises e indicadores.

Conteúdo:
- `Faixa Etária/`: arquivos por grupos etários em anos de referência (ex.: 1970, 1980, 1991, 2000, 2010, 2022).
- `Residente/`: população residente total em anos de referência.

### 5) Índices IFDM
Bases do Índice FIRJAN de Desenvolvimento Municipal (IFDM), com recorte exclusivo para Minas Gerais (`SIGLA_UF = MG`) e série histórica de 2013 a 2023.

Estrutura:
- `Código/`
	- `gerar_ifdm_mg_csvs.py`: script que lê a planilha histórica e exporta os CSVs filtrados para MG.
- `Dados/`
	- `IFDM-Geral-MG.csv`: indicador IFDM geral por município de MG.
	- `IFDM-Educacao-MG.csv`: componente de educação por município de MG.
	- `IFDM-Saude-MG.csv`: componente de saúde por município de MG.
	- `IFDM-Emprego-Renda-MG.csv`: componente de emprego e renda por município de MG.

