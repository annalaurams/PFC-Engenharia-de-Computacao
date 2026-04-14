# Variáveis - Dados de Entrada

Esta pasta reúne as bases de entrada coletadas de fontes públicas, anteriores à etapa de processamento. Os arquivos estão organizados por domínio temático para facilitar atualização, rastreabilidade e reprocessamento.

## 📋 Estrutura de domínios

```
Variáveis/
├── Casos/                          # Registro Hospitalar de Câncer (INCA)
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
├── Hospitais Habilitados/          # Bases de estabelecimentos de saúde
│
├── Índices IFDM/                   # Índices de Desenvolvimento Municipal (FIRJAN)
│
├── Mamografia/                     # Mamografias por ano
│   └── Dados/
│       ├── mamografia_2013.csv
│       ├── mamografia_2014.csv
│       └── ...
│
├── Mortalidade/                    # Atlas de Mortalidade (INCA)
│   └── Regionais de Saúde (29)/
│       └── [27 arquivos regionais com subpastas de municípios]
│
├── Municípios/                     # Base de referência territorial
│
├── População - Faixa Etária/       # Dados populacionais por grupo etário
│   ├── 1-1970.csv
│   ├── 1-1980.csv
│   └── ...
│
└── Socioeconômica/                 # Indicadores de renda e raça-cor
    ├── tabela_10296_renda.csv
    └── tabela_raca_cor.csv
```

## 🔍 Domínios de dados

### 1) **Casos** (RHC/INCA)
- **Formato**: CSVs com dados de casos por município e dimensão
- **Período**: 1985-2023 (conforme disponibilidade por categoria)
- **Origem**: Registro Hospitalar de Câncer — extração via script de consulta ao INCA
- **Dimensões**: Ano diagnóstico, escolaridade, faixa etária, raça-cor

### 2) **Hospitais Habilitados**
- **Formato**: Planilhas e CSVs administrativos
- **Período**: Base pontual (data de publicação)
- **Origem**: Download direto de bases administrativas oficiais do ministério

### 3) **Índices IFDM** (Índice Firjam de Desenvolvimento Municipal)
- **Formato**: CSV municipal com 4 índices
- **Período**: 2013-2023
- **Origem**: Série histórica oficial da FIRJAN
- **Componentes**: Geral, Educação, Saúde, Emprego & Renda

### 4) **Mamografia**
- **Formato**: CSVs anuais consolidados
- **Período**: 2013-2025
- **Origem**: Coleta e armazenamento em Dados/, processados por script

### 5) **Mortalidade**
- **Formato**: Arquivos de texto por regional e município
- **Período**: Histórico amplo (uso em projeto: 1979-2024)
- **Origem**: Atlas de Mortalidade (INCA) — extração via script com tratamento de encoding

### 6) **Municípios**
- **Formato**: Base de referência territorial (município, código IBGE, regional)
- **Período**: Administrativa (sem série temporal)
- **Origem**: Download direto de planilha oficial de regionalização

### 7) **População por Faixa Etária**
- **Formato**: Pares de CSVs anuais (1-AAAA.csv e 2-AAAA.csv)
- **Período**: 1970, 1980, 1991, 2000, 2010, 2022
- **Origem**: Download direto de tabelas oficiais de população

### 8) **Socioeconômica**
- **Formato**: CSVs consolidados
- **Período**: Conforme disponibilidade de fontes originais
- **Origem**: Download direto de indicadores de renda e raça-cor

## 🔄 Estratégias de aquisição

O projeto combina **duas abordagens**:

1. **Extração via script** — para fontes com consulta dinâmica (RHC/INCA, Atlas de Mortalidade)
2. **Download direto** — para planilhas e bases já consolidadas (IFDM, hospitais, população, socioeconômico)

## ✅ Próximo passo

Após atualizar bases em Variáveis/, execute os scripts correspondentes em [Tratamento/README.md](../Tratamento/README.md) para consolidar e padronizar os dados.