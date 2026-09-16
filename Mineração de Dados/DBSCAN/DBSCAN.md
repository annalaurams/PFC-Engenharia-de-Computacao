# DBSCAN — como funciona e como foi implementado

Este documento explica o algoritmo DBSCAN, como ele foi implementado neste projeto (`utilitarios_agrupamentoManual.py`, `graficos_agrupamentoManual.py`, `dbscan.ipynb`), quais decisões técnicas foram tomadas e por quê, e o que o algoritmo produz como resultado.

## 1. O que é o DBSCAN

DBSCAN (*Density-Based Spatial Clustering of Applications with Noise*) é um algoritmo de agrupamento **baseado em densidade**, proposto por Ester et al. (1996). Diferente do KMeans (que particiona o espaço em torno de centróides), o DBSCAN define um cluster como uma região do espaço onde os pontos estão suficientemente densos, separada de outras regiões por áreas de baixa densidade.

Dois parâmetros controlam essa noção de densidade:

- **`eps`**: o raio de vizinhança ao redor de cada ponto.
- **`min_samples`** (MinPts): o número mínimo de pontos que precisam existir dentro desse raio para que a região seja considerada densa.

A partir disso, cada ponto é classificado como:
- **ponto central**: tem pelo menos `min_samples` vizinhos dentro de `eps`;
- **ponto de borda**: está na vizinhança de um ponto central, mas não é central ele mesmo;
- **ruído** (rótulo `-1`): não é central nem está na vizinhança de nenhum ponto central — não pertence a nenhum cluster.

Isso dá ao DBSCAN duas propriedades que o KMeans não tem: (1) **não exige definir o número de clusters `k` de antemão** — o número de agrupamentos emerge da densidade dos dados; e (2) **tem uma noção explícita de ruído/outlier** — nem todo ponto precisa pertencer a um cluster, ao contrário do KMeans, que força cada ponto para o centróide mais próximo.

## 2. Unidade de agrupamento e formato dos dados de entrada

A unidade agrupada é o par **(Regional de Saúde, Ano)** — não o município, não a Regional isolada. Uma mesma Regional pode cair em clusters diferentes em anos diferentes; isso é interpretado como mudança de perfil epidemiológico ao longo do tempo, não como inconsistência.

### De onde vêm os dados

Os dados de entrada são os CSVs de **taxa por 100 mil habitantes** já calculados na etapa de Seleção e Transformação (`Seleção e Transformação/População/Taxa/*.csv`) — nunca valores absolutos, porque o agrupamento compara Regionais entre si e só faz sentido com uma variável já ajustada por população. Cinco blocos de taxa compõem o painel de entrada:

| Bloco | Prefixo da coluna | Categorias |
|---|---|---|
| Casos por Faixa Etária | `casos-faixa` | 0-9, 10-19, ..., 70 ou mais |
| Casos por Escolaridade | `casos-escolaridade` | Fundamental, Médio, Superior, Nenhuma, Sem Informação |
| Casos por Raça e Cor | `casos-raca-cor` | Branca, Preta, Parda, Amarela, Indígena, Sem Informação |
| Mortalidade | `mortalidade` | mesmas faixas etárias |
| Mamografia | `mamografia` | mesmas faixas etárias |

Hospitais Habilitados fica de fora porque só existe para um único ano (2023) — não cabe no formato painel (Regional x Ano).

### Etapa 1 — Leitura e reformatação (`montar_painel`, `ler_csv_taxa_em_painel`)

Cada CSV de taxa vem em formato **largo** (uma coluna `<ano>_<categoria>_TAXA` por combinação). `ler_csv_taxa_em_painel` faz `melt` (largo → longo) e depois `pivot_table` (longo → painel), produzindo uma tabela com índice `(REGIONAL DE SAÚDE, ANO)` e uma coluna por categoria, já prefixada pelo nome do bloco (ex.: `casos-faixa_70-ou-mais`) para não colidir com categorias de mesmo nome de outro bloco (ex.: "Sem Informação" existe tanto em Escolaridade quanto em Raça/Cor). Os cinco painéis são concatenados lado a lado (`pd.concat(..., axis=1, join="outer")`), resultando numa matriz de **1.316 pares Regional-Ano x 42 variáveis** (28 Regionais, todos os anos entre 1979-2023 em que pelo menos um bloco tem dado).

## 3. Fluxo de pré-processamento (etapas 2-3, antes do DBSCAN em si)

### Etapa 2 — Janela temporal, descarte de colunas, tratamento de nulos

1. **Janela comum** (`USAR_JANELA_COMUM`, `ANO_INICIAL_COMUM=2013`, `ANO_FINAL_COMUM=2023`): quando ligada, restringe o painel a um período em que todos os blocos têm cobertura razoável. No pipeline principal atual, `USAR_JANELA_COMUM=False` — usa-se o período completo de cada bloco, sem restringir ano.
2. **Descarte de categorias "sem informação" e "total"** (`descartar_colunas_sem_informacao_e_total`): essas colunas não são um perfil epidemiológico, são resíduo de preenchimento incompleto (sem informação) ou redundância (total = soma das demais).
3. **Descarte de colunas muito esparsas** (`descartar_colunas_com_muitos_nulos`, limiar 70%): remove atributos clinicamente quase inexistentes (ex.: mortalidade por câncer de mama em faixas etárias jovens) que, se mantidos, esvaziariam a base inteira no próximo passo.
4. **Descarte de linhas com qualquer valor ausente** (`tratar_nulos_sem_imputar`) — **nenhum valor é imputado**. Essa é uma decisão metodológica central do projeto: como o NaN nos CSVs de taxa é ambíguo (pode ser "zero eventos" ou "sem população válida para calcular a taxa"), preencher esse vazio por qualquer método (média, interpolação, zero) inventaria dado. A consequência é um descarte pesado: no pipeline principal (sem janela comum), 945 de 1.316 linhas (71,8%) são descartadas nessa etapa, sobrando **371 pares Regional-Ano x 22 variáveis**.

### Etapa 3 — Padronização (RobustScaler) e PCA condicional

- **RobustScaler** (mediana e IQR, não média e desvio padrão) é aplicado sempre, antes de qualquer outra coisa — protege contra outliers extremos (ex.: Belo Horizonte, com valores muito maiores que as demais Regionais) sem que eles distorçam a escala das variáveis.
- **PCA** é condicional (`USAR_PCA`): `None` decide sozinho pela razão nº de atributos / nº de linhas (aplica PCA se ultrapassar `RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA=0.10` — a "maldição da dimensionalidade": muitos atributos para poucas observações torna a distância euclidiana pouco informativa); `True` força PCA; `False` pula PCA inteiramente. No pipeline principal, `USAR_PCA=False` está fixado manualmente (razão real = 22/371 = 0,059 — já ficaria abaixo do limiar automático mesmo com `USAR_PCA=None`).
- Quando aplicado, o número de componentes é escolhido para atingir `VARIANCIA_EXPLICADA_ALVO=0.85` (85% da variância), limitado a `NUMERO_MAXIMO_DE_COMPONENTES=10`.

## 4. Estimativa de `eps` (Monko & Kimura, 2023)

`eps` não é escolhido à mão. O método (`estimar_eps_monko_kimura`) é:

1. Para cada ponto, calcula a **distância média aos `K_VIZINHOS_EPS=5` vizinhos mais próximos** (`distancia_media_aos_k_vizinhos`, via `sklearn.neighbors.NearestNeighbors`).
2. Ordena essa curva de forma crescente.
3. Faz **amostragem estratificada** (`amostragem_estratificada`): divide a curva em `QUANTIDADE_DE_ESTRATOS=10` faixas de mesma amplitude (não mesma contagem) e amostra até `AMOSTRAS_POR_ESTRATO=5` pontos de cada uma — reduz ruído do ajuste sem perder a variação ao longo de toda a curva.
4. Ajusta um **polinômio de grau `GRAU_POLINOMIO_EPS=3`** (`numpy.polyfit`) sobre a amostra.
5. Localiza o **joelho** da curva ajustada com a biblioteca `kneed` (`KneeLocator`, `curve="convex"`, `direction="increasing"`, sensibilidade `S=1.0`) — o ponto de maior curvatura, onde a distância aos vizinhos passa a crescer mais rápido (sinal de que se está saindo de uma região densa para uma esparsa).
6. `eps` = valor da curva original nesse índice.

Se o `kneed` não encontrar joelho, há um **fallback**: usa o ponto de maior curvatura discreta (segunda derivada numérica) como reserva, registrado em log.

## 5. Estimativa de `MinPts` (grid search)

Com `eps` já fixo, `buscar_min_samples` varre `MinPts` de `MIN_SAMPLES_MINIMO=3` até um teto derivado de `MULTIPLICADOR_MIN_SAMPLES_MAXIMO=4` × número de atributos (regra de bolso de Sander et al., 1998: MinPts ≈ 2× a dimensionalidade; aqui usa-se 4× para dar folga à busca — substitui o teto fixo "3 a 100" sugerido no Algoritmo 2 de Monko & Kimura, 2023, por um teto proporcional à dimensionalidade real dos dados do projeto), rodando o DBSCAN completo em cada candidato e escolhendo o `MinPts` de **maior silhueta sem ruído** (empate → menor `MinPts`). `MinPts` nunca fica abaixo de 3.

**Nota sobre fidelidade ao método citado**: o Algoritmo 2 de Monko & Kimura (2023) calcula a silhueta com `silhouette_score(features, labels)` sobre todos os pontos, ruído incluído. Este projeto adapta esse critério para excluir o ruído do cálculo da silhueta antes de escolher o `MinPts` (ver `resumir_agrupamento`) — o rótulo `-1` não representa um agrupamento de fato, e incluí-lo distorce a métrica (`silhouette_score` assume que todo rótulo é um cluster válido). É uma adaptação deliberada e documentada, não uma reprodução literal do Algoritmo 2 do artigo.

## 6. Execução do DBSCAN

`executar_dbscan` chama `sklearn.cluster.DBSCAN(eps, min_samples, metric="euclidean", algorithm="auto", n_jobs=-1)`. Com `algorithm="auto"`, o próprio scikit-learn escolhe a estrutura de busca de vizinhança (`kd_tree`, `ball_tree` ou `brute`) com base na métrica **e** na dimensionalidade dos dados — acima de ~15 atributos a biblioteca já prefere `brute`, porque árvores espaciais deixam de compensar em alta dimensão (curse of dimensionality). Uma escolha fixa feita à mão (sempre `kd_tree`, nunca `brute`) ignoraria esse critério.

## 7. Métricas e medidas estatísticas usadas

- **Distância euclidiana** (`METRICA_DISTANCIA="euclidean"`) — configurável para outras métricas do scikit-learn.
- **Silhueta** (`sklearn.metrics.silhouette_score`), em **duas versões**: sem ruído (pontos rotulados `-1` excluídos — é o critério real usado para escolher `MinPts`) e com ruído (ruído tratado como um cluster próprio — só reportada para comparação, nunca usada como critério, porque distorce a métrica: silhueta assume que todo rótulo é um agrupamento válido, e ruído representa ausência de agrupamento).
- **Variância explicada acumulada** do PCA, quando aplicado.
- **Pesos ("loadings") dos atributos no primeiro componente principal** (`pesos_das_variaveis_no_componente`) — interpreta o que o eixo PC1 representa (porte/volume da Regional vs. perfil epidemiológico distinto).

## 8. O que é configurável (e o que cada coisa afeta)

| Constante | Efeito |
|---|---|
| `USAR_JANELA_COMUM`, `ANO_INICIAL_COMUM`, `ANO_FINAL_COMUM` | período do painel — afeta quantas linhas sobrevivem ao dropna |
| `LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA` | quão esparsa uma coluna pode ser antes de ser descartada |
| `K_VIZINHOS_EPS`, `QUANTIDADE_DE_ESTRATOS`, `AMOSTRAS_POR_ESTRATO`, `GRAU_POLINOMIO_EPS`, `SENSIBILIDADE_JOELHO` | como `eps` é estimado |
| `MIN_SAMPLES_MINIMO`, `MULTIPLICADOR_MIN_SAMPLES_MAXIMO`, `MIN_SAMPLES_PASSO` | grade de busca de `MinPts` |
| `USAR_PCA`, `RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA`, `VARIANCIA_EXPLICADA_ALVO`, `NUMERO_MAXIMO_DE_COMPONENTES` | se e quanto reduzir dimensionalidade |
| `METRICA_DISTANCIA` | métrica de distância do DBSCAN e da estimativa de `eps` |
| `SEMENTE_ALEATORIA=42` | reprodutibilidade da amostragem estratificada e do PCA |

Nenhum desses valores é lido de fora do código (não há arquivo de configuração externo) — são constantes no topo de `utilitarios_agrupamentoManual.py`, editadas diretamente ali.

## 9. Bibliotecas usadas

`numpy`, `pandas` (manipulação de dados), `scikit-learn` (`DBSCAN`, `PCA`, `RobustScaler`, `NearestNeighbors`, `silhouette_score`), `kneed` (localização do joelho), `plotly` (visualizações, em `graficos_agrupamentoManual.py`).

## 10. O que o pipeline produz

- **`resumo_parametros`**: uma linha com todos os parâmetros e métricas usados na execução (eps, MinPts, nº de clusters, nº de ruído, silhueta) — rastreabilidade da configuração.
- **`atributos_usados`**: lista das variáveis que efetivamente entraram no DBSCAN (22 no pipeline principal atual, sem janela comum).
- **`resultado`** (`montar_tabela_pertencimento`): uma linha por par Regional-Ano com o `CLUSTER` atribuído.
- **`visao_agregada_regional_ano`**: pivot Regional × Ano → cluster, mostra em quais agrupamentos cada Regional caiu, ano a ano.
- **`resumo_por_cluster`**: uma linha por cluster (ruído incluído), com quantidade de pares, quantas Regionais distintas e a lista de membros.
- **Visualizações**: gráfico de variância explicada (quando há PCA), pesos do PC1, curva de k-distâncias com o joelho marcado, silhueta por MinPts, dispersão PC1×PC2 (geral e por ano), heatmap Regional×Ano colorido por cluster, distribuição de clusters por Regional e por Ano.

## 11. Resultado obtido e limitação observada

Com a configuração atual do pipeline principal (sem janela comum, sem PCA — `USAR_JANELA_COMUM=False`, `USAR_PCA=False`), o DBSCAN estima `eps=2,9709` (k=5, p=10, m=5, grau 3) e `MinPts=3`, e converge para **2 clusters** sobre 371 pares Regional-Ano x 22 atributos: 70 pares classificados como ruído (18,9%), silhueta sem ruído = 0,3727 (silhueta com ruído incluído = 0,2614, só reportada para comparação). Ou seja, nessa configuração o algoritmo separa dois perfis epidemiológicos distintos entre as Regionais, com separação razoável entre eles.

A configuração com `USAR_JANELA_COMUM=True` (janela 2013-2023, 114 pares x 32 atributos) é um regime bem mais restrito, com bem menos linhas — vale testá-la e registrar como comparação na monografia, já que o comportamento do DBSCAN (nº de clusters, ruído, silhueta) é sensível à combinação específica de janela temporal + dimensionalidade, não uma propriedade fixa dos dados.
