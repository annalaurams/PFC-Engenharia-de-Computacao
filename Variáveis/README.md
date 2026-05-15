# Variáveis de análise - Dados Brutos

## 📋 Estrutura

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
│   └── Regionais de Saúde (28)/
│     │── Município/
│
├── Municípios/                     # Base de referência territorial -  Download direto
│
├── População - Faixa Etária/       # População - Download direto
```

## 🔍 Domínios de dados

### 1) **Casos** (RHC)
- **Formato**: CSVs com dados de casos por segmentos
- **Período**: 1985-2023 
- **Origem**: Coleta processada por script  - web scraping
- **Segmentos**: Ano diagnóstico, escolaridade, faixa etária, raça-cor

### 2) **Hospitais Habilitados**
- **Formato**: XSLS administrativos de Hospitais em Oncologia, Reconstrução Mamária e Tratamento Sincrônico
- **Período**: 2023
- **Origem**: Download direto de bases 

### 3) **Mamografia**
- **Formato**: CSVs com dados da quantidade de exame por faixa etária
- **Período**: 2013-2025
- **Origem**: Coleta processada por script - web scraping

### 4) **Mortalidade**
- **Formato**: CSVs do número de mortes por faixa etária
- **Período**: 1979-2024
- **Origem**: Coleta processada por script - web scraping

### 5) **Municípios**
- **Formato**: XSLS (município, código IBGE)
- **Período**: 2023
- **Origem**: Download direto de planilha 
- 
### 6) **População por Faixa Etária**
- **Formato**: CSVs anuais (1-AAAA.csv e 2-AAAA.csv)
- **Período**: 1970, 1980, 1991, 2000, 2010, 2022
- **Origem**: Download direto de tabelas 

## 🔄 Estratégias de aquisição

O projeto combina **duas abordagens**:

1. **Extração via script** — para fontes com consulta dinâmica
2. **Download direto** — para planilhas e bases já consolidadas 


