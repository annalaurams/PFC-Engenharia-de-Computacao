# Tratamento - Processamento e Padronização

['MUNICÍPIOS', 'CÓDIGO', '1970_0-9', '1970_10-19', '1970_20-29', '1970_30-39', '1970_40-49', '1970_50-59', '1970_60-69', '1970_70 ou mais', '1980_0-9', '1980_10-19', '1980_20-29', '1980_30-39', '1980_40-49', '1980_50-59', '1980_60-69', '1980_70 ou mais', '1991_0-9', '1991_10-19', '1991_20-29', '1991_30-39', '1991_40-49', '1991_50-59', '1991_60-69', '1991_70 ou mais', '2000_0-9', '2000_10-19', '2000_20-29', '2000_30-39', '2000_40-49', '2000_50-59', '2000_60-69', '2000_70 ou mais', '2010_0-9', '2010_10-19', '2010_20-29', '2010_30-39', '2010_40-49', '2010_50-59', '2010_60-69', '2010_70 ou mais', '2022_0-9', '2022_10-19', '2022_20-29', '2022_30-39', '2022_40-49', '2022_50-59', '2022_60-69', '2022_70 ou mais', 'TOTAL_POPULACAO']

Esta pasta concentra os scripts que transformam as bases brutas de [Variáveis/](../Variáveis/README.md) em tabelas analíticas consolidadas e padronizadas.

## 🎯 Objetivo

- Filtrar dados para Minas Gerais
- Padronizar nomes de municípios, regionais e chaves territoriais
- Harmonizar séries temporais (anos, categorias, faixas)
- Consolidar saídas em formato pronto para análise

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
├── Índices/
│   ├── tabela_ifdm_mg.py
│   ├── IFDM-Educacao-MG.csv
│   ├── IFDM-Emprego-Renda-MG.csv
│   ├── IFDM-Geral-MG.csv
│   ├── IFDM-Saude-MG.csv
│   └── tabela_IFDM.csv
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
│   ├── A.py
│   ├── main.py
│   └── tabela_populacao_faixa_etaria.csv
│
└── Socioeconômico/
    ├── main_10296_renda.py
    ├── main_raca_cor.py
    ├── tabela_raca_cor.csv
    └── tabela_renda.csv
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

**Operações**: Agregação por município, pivot por ano/categoria, consolidação

### 2) **Hospitais**
Consolida bases de habilitação de estabelecimentos de saúde.

**Saídas**:
- `filtro_hospitais_mg.csv` — hospitais brutos para MG
- `tabela_hospitais_habilitados.csv` — normalizado e consistente

**Operações**: Filtragem para MG, limpeza estrutural, normalização de município

### 3) **Índices** (IFDM)
Processa índices de desenvolvimento municipal da FIRJAN.

**Saídas**:
- `IFDM-Geral-MG.csv`, `IFDM-Educacao-MG.csv`, `IFDM-Saude-MG.csv`, `IFDM-Emprego-Renda-MG.csv`
- `tabela_IFDM.csv` — merge dos 4 componentes

**Operações**: Filtro de MG, padronização de município, reorganização de colunas

### 4) **Mamografia**
Consolida dados de mamogragia por ano.

**Saídas**:
- `tabela_mamografia.csv` — série unificada 2013-2025

**Operações**: Leitura de anuários, padronização, consolidação temporal

### 5) **Mortalidade**
Processa dados do Atlas de Mortalidade (INCA).

**Saídas**:
- `tabela_mortalidade_faixa_etaria.csv` — mortes por faixa etária e ano

**Operações**: Varredura regional → municipal, tratamento de encoding, agregação, cálculo de totais

### 6) **Municípios**
Cria base de referência territorial.

**Saídas**:
- `tabela_municipios_regionais.csv` — município, código IBGE, regional

**Operações**: Seleção de campos, padronização textual

### 7) **População - Faixa Etária**
Consolida dados populacionais por grupo etário.

**Saídas**:
- `tabela_populacao_faixa_etaria.csv` — população por faixa e ano

**Operações**: Merge de pares anuais, mapeamento de idades, consolidação temporal

### 8) **Socioeconômico**
Processa indicadores de renda e raça-cor.

**Saídas**:
- `tabela_renda.csv` — renda por município
- `tabela_raca_cor.csv` — raça-cor por município

**Operações**: Padronização, consolidação

## ▶️ Como executar

### Executar um domínio específico

```bash
python Tratamento/Casos/main.py
python Tratamento/Hospitais/main.py
python Tratamento/Mamografia/main.py
```

### Executar todos em sequência

```bash
cd Tratamento

for dir in Casos Hospitais Índices Mamografia Mortalidade Municípios "População - Faixa Etária" Socioeconômico; do
  echo "Processando $dir..."
  python "$dir/main.py" && echo "✓ $dir concluído" || echo "✗ Erro em $dir"
done
```

### Com uv

```bash
uv run python Tratamento/Casos/main.py
```

## 📌 Padrões adotados

- **Normalização textual**: minúsculas, sem acentos para chaves de município
- **Estrutura temporal**: colunas ANO_CATEGORIA (ex: 2022_BRANCO, 2023_PRETA)
- **Formato retangular**: amplo (many columns) para facilitar cruzamentos
- **Compatibilidade**: saídas prontas para uso em planilhas e Jupyter

## ✅ Checklist antes de análise

- [ ] Todas as bases em Variáveis/ foram atualizadas?
- [ ] Scripts executados com sucesso?
- [ ] Saídas geradas em cada subpasta?
- [ ] Pronto para consumo em [Resultados/](../Resultados/README.md)