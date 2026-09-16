# Mineração de Dados

## Estrutura da pasta

```
Mineração de Dados/
├── DBSCAN/
│   ├── dbscan.ipynb                        # DBSCAN sobre o painel (Regional, Ano)
│   ├── utilitarios_agrupamentoManual.py    # montagem do painel, pré-processamento, estimativa de eps/min_samples
│   ├── graficos_agrupamentoManual.py       # visualização dos agrupamentos
│   ├── DBSCAN.md                           # detalhes da implementação
│   └── settings.json                       # configuração do Jupyter/Python para o VS Code
│
├── KMEANS/
│   ├── kmeans.ipynb                                # KMeans sobre o painel (Regional, Ano)
│   ├── utilitarios_agrupamento_kmeansManual.py     # montagem do painel, pré-processamento, escolha de k
│   ├── graficos_agrupamento_kmeansManual.py        # visualização dos agrupamentos
│   └── KMEANS.md                                   # detalhes da implementação
│
└── README.md
```

## Sobre esta etapa

Esta pasta corresponde à etapa de Mineração de Dados da metodologia KDD (Knowledge Discovery in Databases), aplicada ao estudo epidemiológico do câncer de mama em Minas Gerais (PFC II). Ela lê as taxas por 100 mil habitantes já calculadas em `Seleção e Transformação/População/Taxa` e aplica algoritmos de agrupamento (clustering) às Regionais de Saúde de MG. A etapa de análise exploratória e de apresentação dos resultados fica em `Avaliação e Apresentação/` (pasta irmã, fora de `Mineração de Dados/`).

## O que cada subpasta faz

- **DBSCAN** — agrupa pares (Regional de Saúde, Ano) por densidade, estimando `eps` pelo método de Monko & Kimura (2023, distância média aos k vizinhos com amostragem estratificada) e `MinPts` por busca em grade (eps fixo). Detalhes em [DBSCAN/DBSCAN.md](DBSCAN/DBSCAN.md).
- **KMEANS** — agrupa pares (Regional, Ano) escolhendo `k` pelo cotovelo da curva de inércia, reaproveitando as mesmas regras de pré-processamento (janela temporal, descarte de colunas/linhas, RobustScaler, PCA condicional) do DBSCAN, de forma independente. Detalhes em [KMEANS/KMEANS.md](KMEANS/KMEANS.md).

Cada notebook importa suas funções utilitárias do arquivo `.py` de mesmo prefixo na própria pasta (`sys.path.append(str(Path.cwd()))` + `from utilitarios_agrupamento(_kmeans)?Manual import ...`), que por sua vez lê os CSVs de taxa em `Seleção e Transformação/População/Taxa` (`PASTA_TAXA`).

## Fluxo geral

```
Seleção e Transformação / População / Taxa (taxas por 100 mil habitantes)
    ↓
Mineração de Dados / DBSCAN ou KMEANS (agrupamento das Regionais de Saúde)
    ↓
Avaliação e Apresentação (gráficos, mapas e análise exploratória)
```
