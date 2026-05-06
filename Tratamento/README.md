# Tratamento - Processamento e Padronização

## 📊 Estrutura de domínios e saídas

```
Tratamento/
├── Casos/
│   ├── main.py
│   ├── incidencia_ano_diagnostico.csv
│   ├── incidencia_escolaridade.csv
│   ├── incidencia_faixa_etaria.csv
│   ├── incidencia_raca_cor.csv
│   └── tabela_incidencia.csv
│
├── Hospitais/
│   ├── main.py
│   ├── filtro_hospitais_mg.csv
│   └── tabela_hospitais_habilitados.csv
│
├── Mamografia/
│   ├── main.py
│   └── tabela_mamografia.csv
│
├── Mortalidade/
│   ├── main.py
│   └── tabela_mortalidade_faixa_etaria.csv
│
├── Municípios/
│   ├── main.py
│   └── tabela_municipios_regionais.csv
│
├── População - Faixa Etária/
│   ├── main.py
│   └── tabela_populacao_faixa_etaria.csv
```

## 📋 Etapas por domínio

### 1) **Casos**
Processa dados do Registro Hospitalar de Câncer (RHC/INCA).

**Saídas**:
- `incidencia_ano_diagnostico.csv` — casos por ano de diagnóstico
- `incidencia_escolaridade.csv` — casos por nível de escolaridade
- `incidencia_faixa_etaria.csv` — casos por faixa etária
- `incidencia_raca_cor.csv` — casos por raça-cor
- `tabela_incidencia.csv` — unificação de todas as dimensões


### 2) **Hospitais**
Consolida bases de habilitação de estabelecimentos de saúde.

**Saídas**:
- `filtro_hospitais_mg.csv` — hospitais brutos para MG
- `tabela_hospitais_habilitados.csv` — unificação e padronização de colunas

### 3) **Mamografia**
Consolida dados de mamografia por ano e faixa etária.

**Saídas**:
- `tabela_mamografia.csv` — série unificada 2013-2025

### 4) **Mortalidade**
Processa dados do Atlas de Mortalidade (INCA).

**Saídas**:
- `tabela_mortalidade_faixa_etaria.csv` — mortes por faixa etária e ano

### 5) **Municípios**
Cria base de referência territorial.

**Saídas**:
- `tabela_municipios_regionais.csv` — município, código IBGE, regional

### 6) **População - Faixa Etária**
Consolida dados populacionais por grupo etário.

**Saídas**:
- `tabela_populacao_faixa_etaria.csv` — população por faixa e ano

- **Normalização textual**: minúsculas, sem acentos para chaves de município
- **Estrutura temporal**: colunas ANO_CATEGORIA (ex: 2022_BRANCO, 2023_PRETA)
- **Formato retangular**: amplo (many columns) para facilitar cruzamentos
- **Compatibilidade**: saídas prontas para uso em planilhas e Jupyter

