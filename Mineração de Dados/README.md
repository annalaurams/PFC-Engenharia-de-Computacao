# Mineração de Dados

## Estrutura da pasta

```
Mineração de Dados/
├── KMEANS/
│   ├── kmeans.ipynb                              # KMeans sobre o painel (Regional, Ano)
│   ├── utilitarios_agrupamento_kmeans.py         # painel, pré-processamento, escolha de k, caracterização
│   ├── graficos_agrupamento_kmeans.py            # gráficos dos agrupamentos
│   └── KMEANS.md                                 # detalhes da implementação
│
└── README.md
```

## Sobre esta etapa

Corresponde à etapa de Mineração de Dados do KDD. Lê as taxas por 100 mil habitantes calculadas em `Seleção e Transformação/População/Taxa` (`PASTA_TAXA`) e agrupa os pares (Regional de Saúde, Ano) com o **KMeans**, escolhendo `k` pelo cotovelo da curva de inércia. Detalhes em [KMEANS/KMEANS.md](KMEANS/KMEANS.md).

O notebook importa as funções do `.py` da mesma pasta (`sys.path.append(str(Path.cwd()))`). O PCA e a silhueta estão implementados, mas desligados no resultado final (`USAR_PCA = False`, `CALCULAR_SILHUETA = False`).

## Fluxo geral

```
Seleção e Transformação / População / Taxa (taxas por 100 mil habitantes)
    ↓
Mineração de Dados / KMEANS (agrupamento dos pares Regional-Ano)
    ↓
Avaliação e Apresentação (gráficos, mapas e análise exploratória)
```
