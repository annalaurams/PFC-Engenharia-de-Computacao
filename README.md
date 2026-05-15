# Projeto Final de Curso (PFC) I 
## Uma Abordagem Computacional Para Análise Epidemiológica do Câncer de Mama em Minas Gerais

O projeto consolida informações de múltiplas fontes públicas desde a extração, pré processamento e análise, seguindo a metodologia da Descoberta de Conhecimento em Bases de Dados (do inglês, KDD).

## Sobre o projeto

Este PFC organiza dados demográficos, socioeconômicos e de infraestrutura em uma base para estudar câncer de mama em MG e validar abordagem metodológica proposta.

**Tema**: câncer de mama feminino | **Território**: Minas Gerais | **Unidade**: município 

## 📁 Estrutura do repositório

```
PFC-I/
├── Variáveis/              # Extração
│   ├── Casos/
│   ├── ├── Ano Diagnóstico
│   ├── ├── Faixa Etária
│   ├── ├── Escolaridade
│   ├── ├── Raça e Cor
│   ├── Hospitais Habilitados/
│   ├── Mamografia/
│   ├── Mortalidade/
│   ├── Municípios/
│   ├── População - Faixa Etária/
│   └── README.md
│
├── Tratamento/             # Pré Processamento
│   ├── Casos/
│   ├── ├── Ano Diagnóstico
│   ├── ├── Faixa Etária
│   ├── ├── Escolaridade
│   ├── ├── Raça e Cor
│   ├── Hospitais Habilitados/
│   ├── Mamografia/
│   ├── Mortalidade/
│   ├── Municípios/
│   ├── População - Faixa Etária/
│   └── README.md
│
├── Resultados/             # Resultados da Análise Exploratória dos Dados
│   ├── casos.ipynb
│   ├── mamografia.ipynb
│   ├── mortalidade.ipynb
│   ├── hospitais_habilitados.ipynb
│   ├── municípios.ipynb
│   └── README.md
│
├── src/tcc/                # Pacote Python do projeto
├── pyproject.toml          # Dependências e configuração
└── README.md
```
## 🔗 Fluxo

```
Variáveis/ (dados brutos)
    ↓
Tratamento/ (dados estruturados)
    ↓
Resultados/ (conhecimento)
```

## 📚 Documentação

- [Variáveis/README.md](Variáveis/README.md) — Extração e obtenção dos dados brutos
- [Tratamento/README.md](Tratamento/README.md) — Pré processamento e obtenção dos dados estruturados
- [Resultados/README.md](Resultados/README.md) — Resultados da Análise Exploratória dos Dados

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
```

### Processar os dados (Tratamento/)

```bash
# Executar um script específico
python3 Tratamento/Casos/main.py
```

### Análise em Jupyter (Resultados/)

```bash
# Abrir e executar notebooks
jupyter notebook Resultados/
```


