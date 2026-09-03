# TCC - Análise Epidemiológica Computacional do Câncer de Mama em Minas Gerais

Projeto de Conclusão de Curso (Engenharia de Computação) que aplica a metodologia KDD (Knowledge Discovery in Databases) a dados públicos de câncer de mama em Minas Gerais, indo da coleta dos dados brutos até a análise exploratória e populacional dos municípios do estado.


## Estrutura de pastas

```
tcc/
├── Limpeza e Integração/                   # 1. Coleta dos dados brutos
├── Seleção e Transformação/                # 2. Tratamento dos dados
├── Mineração de Dados/                     # 3. Algoritmos de agrupamento (DBSCAN, KMeans)
├── Avaliação e Apresentação/               # 4. Análise exploratória dos dados brutos e populacionais
├── src/tcc/                                       # Pacote Python do projeto
├── pyproject.toml                                 # Dependências e configuração
├── uv.lock                                        # Lock de dependências
└── .python-version                                # Versão do Python usada pelo uv
```

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
![DBSCAN](https://img.shields.io/badge/DBSCAN-3776AB?style=for-the-badge&logo=python&logoColor=white)
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
