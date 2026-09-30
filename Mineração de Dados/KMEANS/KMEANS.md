# KMeans — como funciona e como foi implementado

Este documento descreve o algoritmo KMeans e a implementação usada no projeto: [utilitarios_agrupamento_kmeans.py](utilitarios_agrupamento_kmeans.py) (painel, pré-processamento, escolha de `k`, caracterização), [graficos_agrupamento_kmeans.py](graficos_agrupamento_kmeans.py) (gráficos) e [kmeans.ipynb](kmeans.ipynb) (execução e resultados).

## 1. O que é o KMeans

Algoritmo de agrupamento particional baseado em centróides. Dado `k`, ele inicializa `k` centróides, atribui cada ponto ao centróide mais próximo, recalcula cada centróide como a média dos seus pontos e repete até convergir. O critério minimizado é a **inércia** (WCSS): a soma dos quadrados das distâncias de cada ponto ao centróide do seu cluster. Todo ponto pertence a algum cluster (não há "ruído") e `k` precisa ser definido antes da execução.

## 2. Unidade de agrupamento e pré-processamento

A unidade agrupada é o par **(Regional de Saúde, Ano)**. As etapas, todas em `utilitarios_agrupamento_kmeans.py`:

1. `montar_painel` lê os 5 CSVs de taxa (casos por faixa etária, escolaridade e raça/cor, mortalidade e mamografia) e monta a matriz (Regional, Ano) x variável.
2. Janela comum 2014–2023 (`USAR_JANELA_COMUM`). O início da mamografia foi ajustado para 2014 (`ano_inicial_override` em `_bloco`), porque em 2013 só 3 das 28 Regionais têm registro.
3. Descarte das colunas "sem informação" e "total" e das colunas com mais de 5% de nulos (`LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA`).
4. `tratar_nulos_sem_imputar` descarta as linhas com valor ausente; nenhum valor é imputado.
5. `padronizar_e_reduzir` aplica o `RobustScaler` (mediana e IQR).

A matriz final tem **256 pares x 29 atributos**.

## 3. Etapas testadas e não usadas no resultado final

O código das duas abordagens abaixo foi mantido, mas elas estão desligadas:

- **PCA** (`USAR_PCA = False`): `padronizar_e_reduzir`, `preparar_projecao_2d`, `pesos_das_variaveis_no_componente` e os gráficos `grafico_variancia_explicada`, `grafico_pesos_da_componente` e de dispersão PC1 x PC2.
- **Silhueta** (`CALCULAR_SILHUETA = False`): o cálculo em `calcular_inercia_e_silhueta_por_k`, `busca_em_grade_k` e `resumir_agrupamento_kmeans`, além de `grafico_silhueta_por_k`. As colunas de silhueta ficam `NaN`.

## 4. Escolha de `k` (cotovelo da curva de inércia)

`calcular_inercia_e_silhueta_por_k` roda o KMeans para cada `k` de `K_MINIMO` (2) a `K_MAXIMO` (12). `escolher_k_pelo_cotovelo` usa o `KneeLocator` da biblioteca `kneed` (`curve="convex"`, `direction="decreasing"`); se não houver cotovelo, usa a maior curvatura discreta (segunda derivada).

`busca_em_grade_k` repete a varredura para cada combinação de `k` e semente (`SEMENTES_DA_BUSCA = [0, 10, 30, 42, 66]`), para verificar a sensibilidade à inicialização.

## 5. Execução e caracterização

- `executar_kmeans` roda `sklearn.cluster.KMeans(n_clusters=k, random_state=42, n_init=10)`; os clusters são numerados a partir de 1.
- `diagnostico_tamanho_dos_clusters` avisa sobre clusters com menos de 4 elementos.
- `calcular_caracterizacao_por_cluster` compara a média de cada variável no cluster com a média geral, em unidades de IQR geral, sem teste de significância (seria circular, pois o KMeans já maximiza essa diferença).
- `calcular_parcelas_distancia_ao_centroide` decompõe a distância² de cada par ao centróide em uma parcela por variável; a soma de todas as parcelas é a inércia final.

## 6. Constantes configuráveis

| Constante | Efeito |
|---|---|
| `USAR_JANELA_COMUM`, `ANO_INICIAL_COMUM`, `ANO_FINAL_COMUM` | período do painel |
| `LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA` | proporção máxima de nulos por coluna |
| `USAR_PCA`, `RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA`, `VARIANCIA_EXPLICADA_ALVO`, `NUMERO_MAXIMO_DE_COMPONENTES` | PCA (desligado) |
| `CALCULAR_SILHUETA` | silhueta (desligada) |
| `K_MINIMO`, `K_MAXIMO`, `SENSIBILIDADE_COTOVELO` | busca de `k` |
| `SEMENTE_ALEATORIA`, `SEMENTES_DA_BUSCA`, `NUMERO_DE_INICIALIZACOES` | inicialização do KMeans |
| `MINIMO_DE_ELEMENTOS_POR_CLUSTER` | só o aviso de diagnóstico |
| `NUMERO_DE_VARIAVEIS_DISCRIMINANTES` | variáveis exibidas por cluster |

Todas ficam no topo do arquivo `.py`.

## 7. Bibliotecas

`numpy`, `pandas`, `scikit-learn`, `kneed`, `plotly`.

## 8. Resultado obtido

O cotovelo escolhe `k = 5` (inércia 3.736,87). Os clusters têm 41, 60, 59, 92 e 4 pares (10, 12, 17, 20 e 1 Regionais distintas). O cluster de 4 pares, de uma única Regional, está no limite do aviso de tamanho mínimo e deve ser lido como candidato a caso atípico. O notebook não grava resultados em disco; tudo fica como saída de célula. A metodologia completa está em [RELATORIO_METODOLOGIA_KMEANS.md](RELATORIO_METODOLOGIA_KMEANS.md).
