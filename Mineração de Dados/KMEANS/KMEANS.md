# KMeans — como funciona e como foi implementado

Este documento explica o algoritmo KMeans, como ele foi implementado neste projeto (`utilitarios_agrupamento_kmeansManual.py`, `graficos_agrupamento_kmeansManual.py`, `kmeans.ipynb`) e as decisões técnicas tomadas. O módulo é **autocontido**: não importa nada da pasta `DBSCAN/` — replica de propósito as mesmas regras de pré-processamento (montagem do painel, janela comum, tratamento de nulos sem imputar, RobustScaler + PCA condicional), para que os dois algoritmos possam ser configurados/editados de forma independente.

## 1. O que é o KMeans

KMeans é um algoritmo de agrupamento **particional baseado em centróides**. Dado um número `k` de clusters (escolhido antes de rodar o algoritmo), ele:

1. Inicializa `k` centróides;
2. Atribui cada ponto ao centróide mais próximo;
3. Recalcula cada centróide como a média dos pontos atribuídos a ele;
4. Repete os passos 2-3 até convergir.

O critério que o algoritmo minimiza é a **inércia** (WCSS — *Within-Cluster Sum of Squares*): a soma dos quadrados das distâncias de cada ponto ao centróide do seu cluster. Diferente do DBSCAN, o KMeans **sempre** atribui todo ponto a algum cluster — não existe "ruído"; e o número de clusters `k` **precisa** ser definido a priori (não emerge da densidade dos dados).

## 2. Unidade de agrupamento, dados de entrada e pré-processamento

A unidade agrupada é o par **(Regional de Saúde, Ano)** — a mesma unidade usada pelo DBSCAN. Este módulo é **autocontido** (não importa nada de `DBSCAN/`), mas replica de propósito, com o mesmo código, as mesmas regras de entrada e pré-processamento do DBSCAN: leitura dos 5 blocos de taxa (`montar_painel`/`ler_csv_taxa_em_painel`), janela temporal (`USAR_JANELA_COMUM`), descarte de colunas sem-informação/total e com muitos nulos, `dropna` sem imputação, e `RobustScaler` + PCA condicional. Essas etapas estão descritas em detalhe em [`DBSCAN.md`, Seções 2 e 3](../DBSCAN/DBSCAN.md) — não repetidas aqui porque o código e o resultado são idênticos: com `USAR_JANELA_COMUM=False` e `LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA=0.70` nos dois arquivos, a matriz final é **371 pares × 22 atributos** nos dois algoritmos, e `USAR_PCA=False` está fixado nos dois (razão atributos/linhas = 22/371 ≈ 0,059, já abaixo do limiar automático).

A partir daqui, a matriz de entrada do KMeans já passou por essas etapas. A única etapa que muda é a escolha do parâmetro central: `k`, no lugar do par `eps`/`MinPts` do DBSCAN (Seção 3, abaixo), seguida por `executar_kmeans` (`sklearn.cluster.KMeans`).

## 3. Escolha de `k` (cotovelo da curva de inércia)

`k` não é fixado à mão. `calcular_inercia_e_silhueta_por_k` roda o KMeans para cada `k` entre `K_MINIMO` e `K_MAXIMO` (=10), calculando inércia (sempre decrescente com `k`) e silhueta. `escolher_k_pelo_cotovelo` usa a mesma biblioteca `kneed` do DBSCAN (`KneeLocator`, agora `curve="convex"`, `direction="decreasing"` — a curva de inércia decresce, ao contrário da curva de k-distâncias do DBSCAN, que cresce) para localizar o cotovelo — o ponto a partir do qual aumentar `k` deixa de reduzir a inércia de forma significativa (método de Thorndike, 1953). Mesmo fallback do DBSCAN se o `kneed` não encontrar cotovelo (segunda derivada discreta).

`busca_em_grade_k` roda a mesma varredura com `ParameterGrid` como validação complementar, testando múltiplas sementes (`SEMENTES_DA_BUSCA = [42, 7, 123, 2024, 99]` por padrão) para checar a sensibilidade do resultado à inicialização dos centróides.

## 4. Execução do KMeans

`executar_kmeans` chama `sklearn.cluster.KMeans(n_clusters=k, random_state=SEMENTE_ALEATORIA, n_init=NUMERO_DE_INICIALIZACOES)`. `n_init=10`: o KMeans roda 10 vezes com inicializações de centróide diferentes e mantém o melhor resultado (menor inércia) — mitiga o problema de o algoritmo convergir para um mínimo local ruim dependendo da inicialização.

## 5. Métricas e medidas estatísticas usadas

- **Inércia (WCSS)** — critério principal de ajuste do próprio KMeans e base do método do cotovelo.
- **Silhueta** (`sklearn.metrics.silhouette_score`) — aqui em **uma única versão** (diferente do DBSCAN), já que não existe ruído a separar; usada como validação complementar ao cotovelo, nunca como critério isolado (o comentário no código é explícito: a inércia decrescente monotonicamente com `k` tornaria "maior silhueta" um critério enviesado para `k` pequeno).
- **Distância euclidiana** sobre a matriz padronizada (RobustScaler) — mesma métrica do DBSCAN.
- **Variância explicada acumulada** do PCA, quando aplicado.
- **Pesos ("loadings") do PC1** (`pesos_das_variaveis_no_componente`), mesma função reaproveitada em espírito do DBSCAN (implementação própria, mas idêntica).
- **Diagnóstico de tamanho de cluster** (`diagnostico_tamanho_dos_clusters`): identifica clusters com menos de `MINIMO_DE_ELEMENTOS_POR_CLUSTER=4` elementos — um aviso pós-hoc, sem efeito sobre o resultado, sinalizando que um cluster muito pequeno tende a ser um outlier isolado, não um perfil compartilhado.

## 6. O que é configurável (e o que cada coisa afeta)

| Constante | Efeito |
|---|---|
| `USAR_JANELA_COMUM`, `ANO_INICIAL_COMUM`, `ANO_FINAL_COMUM` | período do painel |
| `LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA` | esparsidade máxima de coluna aceita |
| `USAR_PCA`, `RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA`, `VARIANCIA_EXPLICADA_ALVO`, `NUMERO_MAXIMO_DE_COMPONENTES` | se e quanto reduzir dimensionalidade |
| `K_MINIMO`, `K_MAXIMO` | faixa de busca de `k` |
| `SENSIBILIDADE_COTOVELO` | sensibilidade do `KneeLocator` |
| `SEMENTES_DA_BUSCA`, `NUMERO_DE_INICIALIZACOES` | reprodutibilidade/estabilidade da inicialização do KMeans |
| `MINIMO_DE_ELEMENTOS_POR_CLUSTER` | só afeta o aviso de diagnóstico, não o resultado |

Assim como no DBSCAN, tudo são constantes no topo do arquivo `.py`, sem configuração externa.

## 7. Bibliotecas usadas

`numpy`, `pandas`, `scikit-learn` (`KMeans`, `PCA`, `RobustScaler`, `silhouette_score`, `ParameterGrid`), `kneed`, `plotly`.

## 8. O que o pipeline produz

`resumo_parametros` (k, inércia, silhueta, PCA, dimensões), `atributos_usados`, tabela de pertencimento por cluster, `visao_agregada_regional_ano` (pivot Regional×Ano→cluster) e heatmap correspondente, gráfico de cotovelo com `k` marcado, gráfico de silhueta por `k`, dispersão PC1×PC2 (geral e por ano), distribuição por Regional/Ano, gráfico de variância explicada e pesos (quando há PCA) — mesmo formato do DBSCAN, para comparação direta entre os dois algoritmos sobre a mesma matriz.

Nenhum resultado é gravado em disco — tudo fica só como saída de célula (mesma decisão do DBSCAN).

## 9. Resultado obtido

Com a configuração atual (sem janela comum, sem PCA — 371 pares × 22 atributos), o cotovelo escolhe `k=4`, inércia 3.864,83, silhueta 0,148 (baixa). Composição dos 4 clusters: cluster 0 com 69 pares (18 Regionais distintas), cluster 1 com 119 pares (27 Regionais), cluster 2 com 180 pares (23 Regionais) — mas **cluster 3 tem só 3 pares (2 Regionais)**, abaixo de `MINIMO_DE_ELEMENTOS_POR_CLUSTER=4`, sinalizado pelo próprio `diagnostico_tamanho_dos_clusters` como possível outlier isolado em vez de perfil compartilhado.

Uma silhueta de 0,148 indica clusters com sobreposição considerável — não uma separação nítida entre grupos. Isso é consistente com o que o DBSCAN também mostra nesta mesma matriz (ver `DBSCAN.md`, Seção 11) e vale ser reportado como achado metodológico na monografia, não apenas como número de tabela.
