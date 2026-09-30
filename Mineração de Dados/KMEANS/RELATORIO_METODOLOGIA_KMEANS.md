# Metodologia — Agrupamento por KMeans

> Nota de escopo: o KMeans deste projeto tem, na intenção do trabalho, uma variante *painel* (linha = par Regional-Ano) e uma variante *trajetória* (linha = Regional inteira, colunas = categoria × ano). Apenas a variante **painel** está implementada e executada no repositório (`Mineração de Dados/KMEANS/`); não há código, notebook ou branch correspondente à variante trajetória. Este relatório documenta exclusivamente a variante painel, com números extraídos da execução real do pipeline.

## 1. Matriz de entrada

A matriz é construída a partir de cinco blocos de indicadores em taxa por 100 mil habitantes — Casos por Faixa Etária, Casos por Escolaridade, Casos por Raça e Cor, Mortalidade (por faixa etária) e Mamografias (por faixa etária) —, cada um lido de um CSV largo (`<ano>_<categoria>_TAXA` como coluna) e reformatado para o formato longo-para-painel: índice `(REGIONAL DE SAÚDE, ANO)`, uma coluna por categoria, prefixada pelo nome do bloco (ex.: `casos-faixa_60-69`, `mortalidade_70-ou-mais`). Os cinco painéis são unidos por `outer join` no índice comum.

Nessa etapa bruta, cada **linha** é um par (Regional de Saúde, Ano) e cada **coluna** é uma categoria de um dos cinco blocos, em taxa por 100 mil habitantes. O painel bruto resultante tem **1.316 linhas × 42 colunas**, cobrindo 28 Regionais de Saúde e o intervalo **1979–2025** (união das coberturas declaradas dos cinco blocos, que não coincidem entre si — mortalidade vai de 1979 a 2024, mamografia só começa em 2013).

Depois do descarte de colunas e linhas (Seção 2), a matriz que efetivamente alimenta o KMeans tem **371 linhas × 22 colunas**, cobrindo as 28 Regionais e o intervalo **2000–2023**. Um trecho real (Regional de Saúde de Alfenas, quatro anos, quatro das 22 colunas):

| ANO | casos-faixa_60-69 | casos-escolaridade_nenhuma | casos-raca-cor_branca | mortalidade_70-ou-mais |
|---|---|---|---|---|
| 2003 | 82,33 | 0,94 | 3,76 | 99,07 |
| 2005 | 155,58 | 1,42 | 14,64 | 81,61 |
| 2007 | 160,24 | 1,42 | 16,55 | 87,69 |
| 2008 | 149,13 | 2,36 | 35,44 | 127,54 |

## 2. Critérios, regras e restrições

**Variáveis incluídas:** apenas colunas de **taxa** (por 100 mil habitantes), nunca o valor absoluto — o agrupamento compara Regionais de tamanhos populacionais muito diferentes entre si, e a taxa é o que torna essa comparação válida.

**Variáveis excluídas por definição:** as categorias `sem informação` e `total` de cada bloco (7 colunas) — a primeira por não ser um perfil epidemiológico e sim uma lacuna de registro, a segunda por ser redundante com a soma das demais categorias do mesmo bloco.

**Variáveis excluídas por esparsidade:** colunas com mais de 70% de valores nulos (limiar `LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA=0,70`) — 13 colunas, entre elas todas as faixas etárias de mamografia exceto uma e três faixas de mortalidade (`mortalidade_0-9`, `10-19`, `20-29`), que têm cobertura temporal curta demais dentro do período em análise.

**Tratamento de nulos:** nenhum valor é imputado. Nos CSVs de taxa, uma célula fica em branco quando a soma bruta da categoria-ano-Regional é nula em todos os municípios da Regional — ambiguidade proposital entre "zero eventos" e "sem população válida para calcular", que não pode ser resolvida por imputação sem inventar um número. Por isso, toda linha com pelo menos um valor ausente é descartada (`dropna`), o que remove **945 das 1.316 linhas (71,8%)**. Essa perda não é aleatória: decorre da falta de sobreposição temporal entre as cinco fontes (ex.: mamografia só cobre 2013–2025), não de um problema de qualidade de dado pontual — o descarte listwise é defensável aqui precisamente porque a alternativa (imputar taxas para décadas em que a fonte simplesmente não existe) fabricaria dado, mas o volume de perda deve ser reportado como limitação explícita, não tratado como um detalhe de limpeza.

**Restrição imposta pelo método:** o KMeans opera sobre distância euclidiana, que não é definida na presença de `NaN` — daí a exigência de matriz completamente numérica e sem nulos antes do agrupamento.

## 3. Padronização

O código usa `RobustScaler`, não o z-score clássico (média/desvio-padrão): a padronização é centrada na mediana e escalada pelo intervalo interquartil (IQR).

$$x' = \frac{x - \mathrm{med}(x)}{\mathrm{IQR}(x)}, \qquad \mathrm{IQR}(x) = Q_3(x) - Q_1(x)$$

onde $x$ é o valor original de um atributo, $\mathrm{med}(x)$ é a mediana da coluna, $Q_1(x)$ e $Q_3(x)$ são o primeiro e o terceiro quartil, e $x'$ é o valor padronizado.

A padronização é obrigatória aqui porque o KMeans mede distância euclidiana diretamente sobre os valores dos atributos — sem ela, uma variável de maior magnitude numérica (ex.: `casos-faixa_60-69`, tipicamente na casa das centenas) dominaria a distância sobre uma variável de magnitude menor (ex.: `casos-raca-cor_amarela`, tipicamente abaixo de 1), independentemente de qual delas é mais informativa. A escolha por mediana/IQR em vez de média/desvio-padrão é deliberada: taxas por 100 mil habitantes calculadas sobre Regionais de população pequena produzem valores extremos ocasionais, e a mediana/IQR é robusta a esses outliers, enquanto a média e o desvio-padrão seriam distorcidos por eles.

**Exemplo numérico real** — Regional de Alfenas, ano 2008, coluna `casos-faixa_60-69`:
- valor bruto: $x = 149{,}13$
- mediana da coluna: $\mathrm{med}(x) = 150{,}23$
- IQR da coluna: $\mathrm{IQR}(x) = 79{,}685$
- valor padronizado: $x' = \dfrac{149{,}13 - 150{,}23}{79{,}685} = -0{,}0138$

## 4. O algoritmo

O KMeans particiona as $n$ observações em $k$ clusters $C_1, \dots, C_k$, cada um representado por um centróide $\mu_i$ (a média dos pontos do cluster), minimizando a soma dos quadrados intra-cluster (WCSS — *Within-Cluster Sum of Squares*, também chamada inércia):

$$J = \sum_{i=1}^{k} \sum_{x \in C_i} \lVert x - \mu_i \rVert^2$$

onde $x$ é um ponto (aqui, um par Regional-Ano na matriz padronizada), $C_i$ é o conjunto de pontos atribuídos ao cluster $i$, $\mu_i$ é o centróide do cluster $i$, e $\lVert \cdot \rVert$ é a distância euclidiana.

A otimização é feita por um laço iterativo (algoritmo de Lloyd): a cada iteração, cada ponto é atribuído ao centróide mais próximo (passo de atribuição), e cada centróide é recalculado como a média dos pontos que lhe foram atribuídos (passo de atualização); o laço repete até que as atribuições não mudem mais ou até um número máximo de iterações. $k$ não emerge dos dados — precisa ser definido antes de rodar o algoritmo (Seção 5), e todo ponto é atribuído a algum cluster (não há noção de ruído, diferente de algoritmos baseados em densidade).

## 5. Definição de k e busca de parâmetros

**Método do cotovelo:** a inércia $J$ decresce monotonicamente com $k$; o cotovelo é o ponto a partir do qual aumentar $k$ deixa de reduzir $J$ de forma proporcional (Thorndike, 1953). É localizado algoritmicamente pela biblioteca `kneed` (`KneeLocator`, `curve="convex"`, `direction="decreasing"`, sensibilidade $S=1{,}0$), não por inspeção visual.

**Coeficiente de silhueta**, para um ponto $i$:

$$s(i) = \frac{b(i) - a(i)}{\max\{a(i), b(i)\}}$$

onde $a(i)$ é a distância média de $i$ aos demais pontos do seu próprio cluster (coesão), e $b(i)$ é a distância média de $i$ aos pontos do cluster vizinho mais próximo (separação). $s(i) \in [-1, 1]$; valores próximos de 1 indicam boa separação, próximos de 0 indicam sobreposição entre clusters, e negativos indicam possível má atribuição. O valor reportado é a média de $s(i)$ sobre todos os pontos.

Os dois critérios são usados em conjunto porque medem propriedades diferentes e complementares: o cotovelo favorece compacidade (baseia-se só na inércia, que decresce sempre) e a silhueta favorece separação — usar só a silhueta como critério isolado seria enviesado para $k$ pequeno, já que $k=2$ tende a maximizá-la artificialmente sem necessariamente ser a partição mais informativa.

**Grade de parâmetros efetivamente testada:** $k \in \{2, 3, \dots, 15\}$ (14 valores) cruzado com 5 sementes de inicialização ($\{42, 7, 123, 2024, 99\}$), totalizando 70 ajustes de KMeans (`n_init=10` cada). Isso não é uma busca supervisionada — não há rótulo de referência para validar contra — mas uma varredura de sensibilidade: cada combinação $(k, \text{semente})$ é avaliada pelos mesmos critérios internos (inércia, silhueta), e o objetivo é checar se o resultado depende da inicialização dos centróides, não escolher $k$ por um critério externo.

Curva de inércia e silhueta por $k$ (semente 42, `n_init=10`):

| k | Inércia | Silhueta |
|---|---|---|
| 2 | 4.410,32 | 0,8403 |
| 3 | 3.262,57 | 0,2382 |
| 4 | 2.849,67 | 0,1997 |
| **5** | **2.609,25** | **0,2112** |
| 6 | 2.401,84 | 0,2135 |
| 7 | 2.241,73 | 0,2205 |
| 8 | 2.104,48 | 0,1584 |
| 9 | 1.993,79 | 0,1847 |
| 10 | 1.907,55 | 0,1442 |
| 11 | 1.812,76 | 0,1618 |
| 12 | 1.748,86 | 0,1376 |
| 13 | 1.680,43 | 0,1583 |
| 14 | 1.613,07 | 0,1474 |
| 15 | 1.570,98 | 0,1456 |

Estabilidade de cada $k$ ao variar a semente de inicialização (média e desvio-padrão sobre as 5 sementes, apenas os valores relevantes ao redor do cotovelo):

| k | Inércia (média ± dp) | Silhueta (média ± dp) |
|---|---|---|
| 4 | 2.849,70 ± 0,07 | 0,1989 ± 0,0007 |
| **5** | **2.609,72 ± 1,25** | **0,2126 ± 0,0035** |
| 6 | 2.404,58 ± 6,22 | 0,2137 ± 0,0016 |

**Configuração vencedora e critério:** $k=5$, pelo método do cotovelo (posição 3 de 14 na curva de inércia). Isso **não** coincide com o $k$ de maior silhueta — $k=2$ tem silhueta 0,84, muito acima de qualquer outro valor — e esse não é um empate a ser escondido: $k=2$ maximiza a silhueta precisamente pelo viés estrutural descrito acima (poucos clusters tendem a ser mais "separados" por definição), não porque seja a partição mais informativa sobre o painel Regional-Ano. O cotovelo foi fixado como critério principal desde o desenho do pipeline exatamente para não ser capturado por esse viés; a silhueta entra como validação complementar do $k$ já escolhido, não como critério de decisão. A variação de $k=5$ ao redor do cotovelo ($k=4$ a $k=6$) mostra uma curva relativamente suave, sem um joelho abrupto — outro sinal, reportável como achado metodológico, de que os grupos não são nitidamente separados no espaço de atributos. A busca em grade confirma que, para $k=5$, o resultado é estável entre sementes (desvio-padrão da inércia de ~0,05% da média; da silhueta, ~1,6% da média).

## 6. Configuração final

Parâmetros de `sklearn.cluster.KMeans` para o modelo que gerou o resultado reportado na monografia:

| Parâmetro | Valor | Efeito |
|---|---|---|
| `n_clusters` | 5 | Número de clusters, determinado pelo cotovelo (Seção 5) |
| `init` | `k-means++` (padrão) | Inicialização dos centróides por amostragem probabilística que privilegia pontos afastados entre si — reduz a chance de convergência para um mínimo local ruim, em vez de centróides iniciais puramente aleatórios |
| `n_init` | 10 | O algoritmo roda 10 vezes com inicializações distintas de centróide e mantém a execução de menor inércia — mitiga a dependência do resultado à inicialização |
| `max_iter` | 300 (padrão) | Número máximo de iterações do laço de atribuição/atualização por execução |
| `tol` | 1e-4 (padrão) | Variação mínima de inércia entre iterações para considerar convergência |
| `random_state` | 42 | Fixa a semente do gerador aleatório usado por `k-means++` e na escolha entre as `n_init` execuções |
| `algorithm` | `lloyd` (padrão) | Variante do laço de atribuição/atualização (Lloyd clássico) |

A reprodutibilidade é garantida pela combinação de `random_state` fixo, `n_init` explícito (em vez do valor `auto` do scikit-learn) e um pipeline de pré-processamento determinístico (mesmos CSVs de entrada, mesmas regras de descarte, mesma padronização) — rodar o notebook novamente sobre os mesmos dados de entrada produz exatamente os mesmos rótulos de cluster.

## 7. Ferramentas

Do **scikit-learn**: `RobustScaler` para a padronização (Seção 3); `PCA` para reduzir os 22 atributos padronizados a 9 componentes antes do agrupamento (86,8% da variância acumulada) — decisão justificada não pela razão atributos/linhas (0,059, abaixo do limiar que dispararia o PCA automaticamente), mas pela correlação entre variáveis do mesmo bloco categórico: entre as 22 variáveis, 2,1% dos pares têm $|r| > 0{,}7$ (ex.: `casos-faixa_40-49` × `casos-faixa_50-59`, $r=0{,}795$), o suficiente para distorcer a distância euclidiana ao contar a mesma informação subjacente mais de uma vez; `KMeans` para o agrupamento em si (Seção 4); `silhouette_score` para a métrica de validação (Seção 5); `ParameterGrid` para enumerar a grade $(k, \text{semente})$ da busca de sensibilidade. Da biblioteca `kneed`, `KneeLocator` para localizar o cotovelo algoritmicamente.

Do **Plotly**: `graph_objects.Scatter` para as curvas de inércia e de silhueta por $k$, com o $k$ escolhido marcado; `graph_objects.Scatter` também para a dispersão dos pares Regional-Ano projetados em PC1×PC2 (geral e em grade por ano, com eixos fixos entre painéis); `graph_objects.Heatmap` para a visão Regional×Ano colorida por cluster; `express.bar` para a distribuição de clusters por Regional e por Ano, e para o gráfico de barras horizontais que compara, lado a lado, a diferença percentual das variáveis mais discriminantes de cada cluster em relação à média geral da base (Seção 8).

## 8. Investigação dos agrupamentos

A dispersão em PC1×PC2 e o heatmap Regional×Ano mostram *quando* e *onde* cada cluster aparece, mas não *o quê* ele representa: como o KMeans roda sobre a matriz padronizada e reduzida por PCA, seus valores não são diretamente interpretáveis em unidade epidemiológica.

A leitura de cada cluster é feita reatribuindo os rótulos de cluster às linhas da matriz **original** (taxas por 100 mil habitantes, antes de qualquer padronização) e comparando, para cada uma das 22 variáveis, a média dentro do cluster com a média geral da base inteira (todas as 371 linhas, sem agrupar), via diferença percentual. Dentro de cada cluster, as variáveis são ordenadas pela maior diferença percentual absoluta — as primeiras da lista são as que mais afastam aquele cluster do perfil médio geral, isto é, as que o "definem". Esse procedimento independe de quais colunas sobraram na matriz final (não há nome de variável fixado no código), e é aplicado uniformemente aos cinco clusters.

Complementarmente, os pesos ("loadings") de PC1 são inspecionados para identificar quais variáveis originais dominam a direção de maior variância da base, e a tabela de composição por Regional-Ano (cruzando cluster com Regional e Ano) permite checar se um cluster está concentrado em poucas Regionais/anos ou distribuído de forma ampla — é assim que o cluster com apenas 3 pares e 2 Regionais distintas foi identificado como candidato a outlier isolado (abaixo do mínimo de 4 elementos configurado), a ser tratado com cautela na interpretação em vez de reportado como um perfil regional compartilhado.

---

## (a) O que foi removido ou corrigido no código, e por quê

1. **`SEMENTES_DA_BUSCA` continha uma única semente (`[42]`)** — `busca_em_grade_k` cruza `k` com as sementes fornecidas via `ParameterGrid`; com uma só semente, essa etapa recalculava exatamente os mesmos 14 valores de `calcular_inercia_e_silhueta_por_k`, sem nenhuma informação nova, apesar de o próprio docstring da função afirmar que ela testa "sensibilidade do resultado à inicialização dos centróides". Confirmado por execução: `tabela_da_busca` era numericamente idêntica a `tabela_k`. Corrigido para `[42, 7, 123, 2024, 99]` — agora a validação é real (Seção 5) e o resultado (k=5) se confirma estável entre sementes.
2. **`KMEANS.md` estava desatualizado**: citava `K_MAXIMO=10` (o código já usa 15), e a Seção 9 reportava um resultado antigo (`k=4`, inércia 3.864,83, composição de clusters diferente da atual) que não corresponde ao pipeline nem ao notebook em execução. Atualizado com os números confirmados pela reexecução (`k=5`, inércia 2.609,25, silhueta 0,211).
3. **Célula do notebook que exibia `tabela_da_busca.head(20)`** — com a correção do item 1, a grade passou de 14 para 70 combinações; `head(20)` passaria a esconder a maior parte da validação sem aviso. Substituída por uma tabela agregada (média e desvio-padrão de inércia/silhueta por `k` entre as sementes), que é o que de fato importa reportar (estabilidade), em vez de truncar uma tabela de 70 linhas arbitrariamente.

**Avaliado e mantido, sem alteração de código** (registrado aqui para rastreabilidade):
- `RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA` não influencia a decisão de aplicar PCA na configuração atual, porque `USAR_PCA=True` está forçado (o critério automático só é usado quando `USAR_PCA=None`). Não é código morto — é um ramo alternativo válido, só não exercitado pela configuração vigente — por isso não foi removido; a justificativa real de por que o PCA é usado está na Seção 7 (correlação entre variáveis, não na razão atributos/linhas).
- `USAR_JANELA_COMUM=False` deixa `calcular_janela_comum`/`restringir_a_janela_comum` sem execução no caminho oficial atual, pelo mesmo motivo (alternância de configuração, não código morto).
- O parâmetro `usar_robust_scaler` de `montar_resumo_parametros_kmeans` é sempre chamado com `True` (não há ramo do pipeline que rode sem `RobustScaler`) — flexibilidade não utilizada, mas inofensiva; não alterado por não afetar resultado nem legibilidade de forma relevante.
- A perda de 71,8% das linhas no `dropna` (Seção 2) não foi "corrigida" por imputação: a literatura consultada desaconselha *listwise deletion* para perdas desse porte quando o mecanismo não é MCAR, mas aqui a alternativa (imputar taxas para décadas em que a fonte de dado simplesmente não cobre) fabricaria valor, o que é pior. A decisão correta identificada foi reportar o percentual e a causa estrutural explicitamente (o que o código já loga e este relatório reproduz), não trocar de método.

## (b) Fontes consultadas na Etapa 2

**Padronização e escala em KMeans:**
- [The impact of neglecting feature scaling in k-means clustering](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC11623793/) — PMC
- [Standardization and Its Effects on K-Means Clustering Algorithm](https://www.researchgate.net/publication/288044597_Standardization_and_Its_Effects_on_K-Means_Clustering_Algorithm) — ResearchGate
- [Applying a hierarchical clustering on principal components approach to identify different patterns of the SARS-CoV-2 epidemic across Italian regions](https://www.nature.com/articles/s41598-021-86703-3) — Scientific Reports (Nature)

**Método do cotovelo e silhueta combinados:**
- [Elbow Method vs Silhouette Co-efficient in Determining the Number of Clusters](https://adria708.medium.com/elbow-method-vs-silhouette-co-efficient-in-determining-the-number-of-clusters-33baff2fbeee)
- [Means Clustering Using Elbow and Silhouette Method](https://www.atlantis-press.com/article/125939938.pdf) — Atlantis Press

**KMeans aplicado a indicadores regionais de saúde:**
- [Clustering Portuguese municipalities based on population health indicators](https://pmc.ncbi.nlm.nih.gov/articles/PMC11518220/) — PMC
- [Cluster Analysis Methods to Support Population Health Improvement Among US Counties](https://pubmed.ncbi.nlm.nih.gov/38985976/) — PubMed
- [K-Means Cluster Analysis](https://www.publichealth.columbia.edu/research/population-health-methods/k-means-cluster-analysis) — Columbia University Mailman School of Public Health
- [Comparison of US County-Level Public Health Performance Rankings With County Cluster and National Rankings](https://pmc.ncbi.nlm.nih.gov/articles/PMC6324334/) — PMC

**Papel do PCA (redução antes do agrupamento vs. só visualização):**
- [K-means Clustering and Principal Component Analysis in 10 Minutes](https://towardsdatascience.com/k-means-clustering-and-principal-component-analysis-in-10-minutes-2c5b69c36b6b/) — Towards Data Science
- [How to Combine PCA & K-Means Clustering in Python](https://365datascience.com/tutorials/python-tutorials/pca-k-means/) — 365 Data Science

**Busca de hiperparâmetros em agrupamento não supervisionado:**
- [Clustering: How to Find Hyperparameters using Inertia](https://towardsdatascience.com/clustering-how-to-find-hyperparameters-using-inertia-b0343c6fe819/) — Towards Data Science
- [Grid search without cross-validation for unsupervised clustering (issue #6154)](https://github.com/scikit-learn/scikit-learn/issues/6154) — scikit-learn

**Tratamento de nulos (listwise deletion vs. imputação):**
- [Empirical Comparison of Imputation Methods for Multivariate Missing Data in Public Health](https://pmc.ncbi.nlm.nih.gov/articles/PMC9864541/) — PMC
- [A Note on Listwise Deletion versus Multiple Imputation](https://www.cambridge.org/core/journals/political-analysis/article/note-on-listwise-deletion-versus-multiple-imputation/39DE56539189423F6C985B3B9EBF7E56) — Political Analysis (Cambridge)
- [Missing Data and Multiple Imputation](https://www.publichealth.columbia.edu/research/population-health-methods/missing-data-and-multiple-imputation) — Columbia University Mailman School of Public Health

**Taxa vs. valor absoluto em análise regional de pequenas áreas:**
- [Using Disease-Cluster and Small-Area Analyses to Study Environmental Justice](https://www.ncbi.nlm.nih.gov/books/NBK100858/) — NCBI Bookshelf
- [Spatial Epidemiology: Current Approaches and Future Challenges](https://www.ncbi.nlm.nih.gov/pmc/articles/PMC1247193/) — PMC

**Correlação entre variáveis e distorção de distância no KMeans:**
- [Cluster Analysis Gets Complicated](https://www.greenbook.org/marketing-research/cluster-analysis) — Greenbook.org
