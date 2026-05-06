# Projeto Final de Curso I
## APLICAÇÃO DE TÉCNICAS COMPUTACIONAIS E MINERAÇÃO DE DADOS EM SAÚDE PÚBLICA: Uma análise epidemiológica do câncer de mama em Minas Gerais 

Este trabalho investiga como variáveis socioeconônomicas, demográficas e de acesso a saúde relacionadas ao câncer de mama se distribuem nos municípios de MG e quais delas exercem maior influência sobre a
incidência da doença.

## Sobre o projeto

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
├── Resultados/             # Resultados da Análise Exploratória
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
## 🔗 Fluxo integrado

```
Variáveis/ (dados brutos)
    ↓
Tratamento/ (processa e padroniza)
    ↓
Resultados/ (analisa e cruza)
    ↓
Monografia/ (incorpora evidências)
```

## 📚 Documentação

- [Variáveis/README.md](Variáveis/README.md) — Extração e obtenção dos dados brutos
- [Tratamento/README.md](Tratamento/README.md) — Pré processamento e obtenção dos dados estruturados
- [Resultados/README.md](Resultados/README.md) — Resultados da Análise Exploratória

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


