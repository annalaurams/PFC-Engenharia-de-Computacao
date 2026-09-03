# Mineração de Dados

## Estrutura da pasta

```
Mineração de Dados/
├── DBSCAN/
│   ├── dbscan_regionaisManual.ipynb        # DBSCAN sobre o painel (Regional, Ano)
│   ├── diagnostico_parametrosManual.ipynb  # investigação de por que o DBSCAN colapsa em 1 cluster + ruído
│   ├── utilitarios_agrupamentoManual.py    # montagem do painel, pré-processamento, estimativa de eps/min_samples
│   ├── graficos_agrupamentoManual.py       # visualização dos agrupamentos
│   └── settings.json                       # configuração do Jupyter/Python para o VS Code
│
├── KMEANS/
│   └── KMeans/
│       ├── kmeans_painel_regional_ano.ipynb        # KMeans sobre o painel (Regional, Ano)
│       ├── kmeans_regional_trajetoria.ipynb        # KMeans sobre a trajetória completa por Regional (28 linhas)
│       ├── utilitarios_agrupamento_kmeansManual.py # montagem do painel/trajetória, pré-processamento, escolha de K
│       └── graficos_agrupamento_kmeansManual.py    # visualização dos agrupamentos
│
└── README.md
```

## Sobre esta etapa

Esta pasta corresponde à etapa de Mineração de Dados da metodologia KDD (Knowledge Discovery in Databases), aplicada ao estudo epidemiológico do câncer de mama em Minas Gerais (PFC II). Ela lê as taxas por 100 mil habitantes já calculadas em `Seleção e Transformação/População/Taxa` e aplica algoritmos de agrupamento (clustering) às Regionais de Saúde de MG. A etapa de análise exploratória e de apresentação dos resultados fica em `Avaliação e Apresentação/` (pasta irmã, fora de `Mineração de Dados/`).

## O que cada subpasta faz

- **DBSCAN** — agrupa pares (Regional de Saúde, Ano) por densidade, estimando `eps` pelo método de Monko & Kimura (2023, distância média aos k vizinhos com amostragem estratificada) e `min_samples` a partir dos dados. `diagnostico_parametrosManual.ipynb` investiga cenários alternativos de parâmetros sem alterar a lógica de `utilitarios_agrupamentoManual.py`.
- **KMEANS/KMeans** — agrupa tanto pares (Regional, Ano) (`kmeans_painel_regional_ano.ipynb`) quanto a trajetória completa de cada Regional como uma única linha (`kmeans_regional_trajetoria.ipynb`), reaproveitando as mesmas regras de decisão (pré-processamento, PCA opcional) do DBSCAN.

Cada notebook importa suas funções utilitárias do arquivo `.py` de mesmo prefixo na própria pasta (`sys.path.append(str(Path.cwd()))` + `from utilitarios_agrupamento(_kmeans)?Manual import ...`), que por sua vez lê os CSVs de taxa em `Seleção e Transformação/População/Taxa` (`PASTA_TAXA`).

## Fluxo geral

```
Seleção e Transformação / População / Taxa (taxas por 100 mil habitantes)
    ↓
Mineração de Dados / DBSCAN ou KMEANS (agrupamento das Regionais de Saúde)
    ↓
Avaliação e Apresentação (gráficos, mapas e análise exploratória)
```
