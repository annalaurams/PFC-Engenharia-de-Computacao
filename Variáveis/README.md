# Variáveis de análise - Dados Brutos

## 📋 Estrutura de domínios

```
Variáveis/
├── Casos/                          # Registro Hospitalar de Câncer (INCA) - Web Scraper 
│   ├── Ano Diagnóstico/
│   │   ├── Código/
│   │   └── Dados/
│   ├── Escolaridade/
│   │   ├── Código/
│   │   └── Dados/
│   ├── Faixa Etária/
│   │   ├── Código/
│   │   └── Dados/
│   └── Raça-Cor/
│       ├── Código/
│       └── Dados/
│
├── Hospitais Habilitados/          # GOV -  Download direto
│
├── Mamografia/                     # DATASUS - Web Scraper 
│   └── Código/                    
│   └── Dados/
│
├── Mortalidade/                    # Atlas de Mortalidade (INCA) - Web Scraper 
│   └── Regionais de Saúde (29)/
│       └── [27 arquivos regionais com subpastas de municípios]
│
├── Municípios/                     # Base de referência territorial -  Download direto
│
├── População - Faixa Etária/       # Dados populacionais por grupo etário - Download direto
```

## 🔍 Domínios de dados

### 1) **Casos** (RHC/INCA)
- **Formato**: CSVs com dados de casos por município e segmentos
- **Período**: 1985-2023 
- **Origem**: Coleta processada por script
- **Segmentos**: Ano diagnóstico, escolaridade, faixa etária, raça-cor

### 2) **Hospitais Habilitados**
- **Formato**: Planilhas e CSVs administrativos
- **Período**: 2023
- **Origem**: Download direto de bases 

### 3) **Mamografia**
- **Formato**: CSVs anuais consolidados
- **Período**: 2013-2023
- **Origem**: Coleta processada por script

### 4) **Mortalidade**
- **Formato**: Arquivos de texto por regional e município
- **Período**: 1979-2024
- **Origem**: Coleta processada por script

### 5) **Municípios**
- **Formato**: Base de referência territorial (município, código IBGE, regional)
- **Período**: Administrativa (sem série temporal)
- **Origem**: Download direto de planilha oficial de regionalização
- 
### 6) **População por Faixa Etária**
- **Formato**: Pares de CSVs anuais (1-AAAA.csv e 2-AAAA.csv)
- **Período**: 1970, 1980, 1991, 2000, 2010, 2022
- **Origem**: Download direto de tabelas oficiais de população

## 🔄 Estratégias de aquisição

O projeto combina **duas abordagens**:

1. **Extração via script** — para fontes com consulta dinâmica (RHC/INCA, Atlas de Mortalidade, DATASUS)
2. **Download direto** — para planilhas e bases já consolidadas (hospitais, população, território)


