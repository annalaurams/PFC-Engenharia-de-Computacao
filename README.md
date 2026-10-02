# TCC - Análise Epidemiológica Computacional do Câncer de Mama em Minas Gerais

Projeto de Conclusão de Curso (Engenharia de Computação) que aplica a metodologia KDD (Knowledge Discovery in Databases) a dados públicos de câncer de mama em Minas Gerais, indo da coleta dos dados brutos até a análise exploratória e populacional dos municípios do estado.


## Estrutura de pastas

```
tcc/
├── Limpeza e Integração/                   # 1. Dados brutos (scripts de extração INCA/DATASUS, planilhas, IBGE)
├── Seleção e Transformação/                # 2. Notebooks de tratamento, população (interpolação) e taxas por 100 mil hab.
├── Mineração de Dados/                     # 3. KMeans sobre os pares (Regional de Saúde, Ano)
│   └── KMEANS/
├── Avaliação e Apresentação/               # 4. Gráficos, mapas e análise exploratória
├── src/tcc/                                # Pacote Python do projeto
├── README_DADOS.md                         # Mapeamento dos arquivos CSV/XLSX por etapa do KDD
├── pyproject.toml                          # Dependências e configuração
├── uv.lock                                 # Lock de dependências
└── .python-version                         # Versão do Python usada pelo uv
```

Os dados de cada etapa estão descritos em [README_DADOS.md](README_DADOS.md).

## Fluxo

1. **Limpeza e Integração**: cada pasta tem um `main.py` (Selenium) que baixa os CSV de casos (RHC/INCA), mamografias (SISCAN/DATASUS) e mortalidade (Mortalidade Web/INCA); hospitais habilitados, municípios e população (IBGE) ficam como planilhas e CSV.
2. **Seleção e Transformação**: notebooks `*_tratamento.ipynb` geram uma tabela por variável; `interpolacao_extrapolacao.ipynb` estima a população de 1970 a 2025; `calculo_taxa.ipynb` calcula as taxas por Regional (módulo comum: `utilitarios_comuns.py`).
3. **Mineração de Dados**: `kmeans.ipynb` agrupa as Regionais por ano, com `k` escolhido pelo cotovelo da inércia. PCA e silhueta estão implementados, mas desligados.
4. **Avaliação e Apresentação**: notebooks de heatmap, mapas coropléticos e gráficos de linha, com funções em `utilitarios_graficos_populacionais.py` e estilo em `configuracao_layout_graficos.py`.

## Tecnologias

### Linguagem

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)

### Dados e análise

![Pandas](https://img.shields.io/badge/Pandas-150458?style=for-the-badge&logo=pandas&logoColor=white)
![OpenPyXL](https://img.shields.io/badge/OpenPyXL-2F6B9A?style=for-the-badge&logo=python&logoColor=white)
![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)
![nbformat](https://img.shields.io/badge/nbformat-3776AB?style=for-the-badge&logo=python&logoColor=white)

### Geoespacial

![GeoPandas](https://img.shields.io/badge/GeoPandas-139C5A?style=for-the-badge&logo=python&logoColor=white)
![GeoBR](https://img.shields.io/badge/GeoBR-139C5A?style=for-the-badge&logo=python&logoColor=white)
![PySAL](https://img.shields.io/badge/PySAL-3776AB?style=for-the-badge&logo=python&logoColor=white)
![SPOpt](https://img.shields.io/badge/SPOpt-3776AB?style=for-the-badge&logo=python&logoColor=white)

### Visualização

![Matplotlib](https://img.shields.io/badge/Matplotlib-11557C?style=for-the-badge&logo=python&logoColor=white)
![Plotly](https://img.shields.io/badge/Plotly-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)
![Kaleido](https://img.shields.io/badge/Kaleido-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)

### Mineração de dados

![Scikit-Learn](https://img.shields.io/badge/Scikit--Learn-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)
![Kneed](https://img.shields.io/badge/Kneed-3776AB?style=for-the-badge&logo=python&logoColor=white)

### Extração de dados

![Selenium](https://img.shields.io/badge/Selenium-43B02A?style=for-the-badge&logo=selenium&logoColor=white)
![WebDriver Manager](https://img.shields.io/badge/WebDriver--Manager-43B02A?style=for-the-badge&logo=selenium&logoColor=white)


### Desenvolvimento

![Jupyter](https://img.shields.io/badge/Jupyter-F37626?style=for-the-badge&logo=jupyter&logoColor=white)
![Pyright](https://img.shields.io/badge/Pyright-3776AB?style=for-the-badge&logo=python&logoColor=white)

## Como executar o projeto

### Pré-requisitos

Antes de executar o projeto, é necessário ter o **Python 3.12+** e o **uv** instalados.

#### 1. Python 3.12+

> O projeto utiliza **Python 3.12 ou superior**. O `uv` também pode instalar automaticamente a versão especificada no arquivo `.python-version`, caso ela não esteja disponível no sistema.

Baixe o Python pelo site oficial:  https://www.python.org/downloads/ 


#### 2. uv

> O `uv` é um gerenciador de projetos e pacotes Python desenvolvido pela Astral.

Baixe o uv pelo site oficial: https://docs.astral.sh/uv/getting-started/installation/


Após instalar o Python e o `uv`, confirme que ambos estão disponíveis no terminal:

```bash
python --version
uv --version
```

Se o comando `python` não estiver disponível no Linux/macOS, utilize:

```bash
python3 --version
```


### Instalar as dependências

```bash
uv sync
```

Isso cria o ambiente virtual do projeto e instala todas as dependências fixadas em `uv.lock`.

### Rodar os notebooks

```bash
uv run jupyter notebook
```

Em seguida, abra o notebook desejado dentro de `Limpeza e Integração/`, `Seleção e Transformação/`, `Mineração de Dados/` ou `Avaliação e Apresentação/`.

### Rodar um script Python específico

```bash
uv run python "Limpeza e Integração/Casos/Ano Diagnóstico/Código/main.py"
```
