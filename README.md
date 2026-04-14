# PFC I - Base Integrada para Análise Oncológica em Minas Gerais

Base de dados integrada para análise de câncer de mama feminino em Minas Gerais. O projeto consolida informações de múltiplas fontes públicas com padronização territorial e temporal, permitindo análises estatísticas, cruzamentos entre variáveis e geração de evidências.

## Sobre o projeto

Este TCC organiza dados demográficos, assistenciais, territoriais e socioeconômicos em uma base analítica consistente para estudar câncer de mama em MG.

**Tema**: câncer de mama feminino | **Território**: Minas Gerais | **Unidade**: município | **Período**: histórico (1985-2025)

## 📁 Estrutura do repositório

```
PFC-I/
├── Variáveis/              # Dados brutos e semibrutos por domínio
│   ├── Casos/
│   ├── Hospitais Habilitados/
│   ├── Índices IFDM/
│   ├── Mamografia/
│   ├── Mortalidade/
│   ├── Municípios/
│   ├── População - Faixa Etária/
│   ├── Socioeconômica/
│   └── README.md
│
├── Tratamento/             # Scripts e saídas processadas
│   ├── Casos/
│   ├── Hospitais/
│   ├── Índices/
│   ├── Mamografia/
│   ├── Mortalidade/
│   ├── Municípios/
│   ├── População - Faixa Etária/
│   ├── Socioeconômico/
│   └── README.md
│
├── Resultados/             # Análises e notebooks
│   ├── casos.ipynb
│   ├── mamografia.ipynb
│   ├── mortalidade.ipynb
│   ├── hospitais_habilitados.ipynb
│   ├── municípios.ipynb
│   ├── mortalidade.ipynb
│   └── README.md
│
├── src/tcc/                # Pacote Python do projeto
├── pyproject.toml          # Dependências e configuração
└── README.md
```

## 🔄 Fluxo de trabalho

1. **Variáveis/** → Dados brutos coletados de fontes públicas (INCA, FIRJAN, bases administrativas)
2. **Tratamento/** → Limpeza, padronização territorial e consolidação em tabelas analíticas
3. **Resultados/** → Exploração, cruzamentos e análise das bases tratadas

## 📚 Documentação

- [Variáveis/README.md](Variáveis/README.md) — Origens dos dados e estrutura de aquisição
- [Tratamento/README.md](Tratamento/README.md) — Processamento e como rodar os scripts
- [Resultados/README.md](Resultados/README.md) — Notebooks de análise

## 🛠️ Tecnologias e dependências

**Python 3.12+** com as seguintes bibliotecas:

| Categoria | Pacotes |
|-----------|---------|
| **Dados** | `pandas>=3.0.0`, `openpyxl>=3.1.5` |
| **Geoespacial** | `geopandas>=1.1.0`, `geobr>=0.2.2` |
| **Visualização** | `matplotlib>=3.10.8`, `seaborn>=0.13.2`, `plotly>=5.24.0`, `plotly-express>=0.4.1` |
| **Web scraping** | `selenium>=4.40.0`, `webdriver-manager>=4.0.0` |
| **Dev/Jupyter** | `ipykernel>=7.2.0`, `pyright>=1.1.408` |

**Gerenciador**: [`uv`](https://docs.astral.sh/uv/) — gerenciador de pacotes Python rápido e confiável.

## ▶️ Como executar o projeto

### Instalação de dependências

```bash
# Com uv instalado
uv sync

# Ou com pip tradicional
pip install -e .
```

### Processar os dados (Tratamento/)

```bash
# Executar um script específico
python Tratamento/Casos/main.py

# Ou executar todos em sequência
cd Tratamento
for dir in Casos Hospitais Índices Mamografia Mortalidade Municípios "População - Faixa Etária" Socioeconômico; do
  python "$dir/main.py" && echo "✓ $dir"
done
```

### Análise em Jupyter (Resultados/)

```bash
# Abrir e executar notebooks
jupyter notebook Resultados/

# Ou usar VS Code
code Resultados/
```

## 📌 Notas importantes

- Sempre execute **Tratamento/** após atualizar **Variáveis/**
- Verifique a consistência de nomes de municípios antes de novos cruzamentos
- Os notebooks em **Resultados/** consomem tabelas processadas em **Tratamento/**

