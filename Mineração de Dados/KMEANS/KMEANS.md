# KMeans — como funciona e como foi implementado

Este documento explica o algoritmo KMeans, como ele foi implementado neste projeto (`utilitarios_agrupamento_kmeansManual.py`, `graficos_agrupamento_kmeansManual.py`, `kmeans_painel_regional_ano.ipynb`, `kmeans_regional_trajetoria.ipynb`), as decisões técnicas tomadas e o que cada uma das duas análises produz. O módulo é **autocontido**: não importa nada da pasta `DBSCAN/` — replica de propósito as mesmas regras de pré-processamento (montagem do painel, janela comum, tratamento de nulos sem imputar, RobustScaler + PCA condicional), para que os dois algoritmos possam ser configurados/editados de forma independente.

## 1. O que é o KMeans

KMeans é um algoritmo de agrupamento **particional baseado em centróides**. Dado um número `k` de clusters (escolhido antes de rodar o algoritmo), ele:

1. Inicializa `k` centróides;
2. Atribui cada ponto ao centróide mais próximo;
3. Recalcula cada centróide como a média dos pontos atribuídos a ele;
4. Repete os passos 2-3 até convergir.

O critério que o algoritmo minimiza é a **inércia** (WCSS — *Within-Cluster Sum of Squares*): a soma dos quadrados das distâncias de cada ponto ao centróide do seu cluster. Diferente do DBSCAN, o KMeans **sempre** atribui todo ponto a algum cluster — não existe "ruído"; e o número de clusters `k` **precisa** ser definido a priori (não emerge da densidade dos dados).

## 2. Duas unidades de agrupamento, duas análises

O projeto usa o KMeans em **dois notebooks com unidades de agrupamento diferentes**:

| Notebook | Unidade agrupada | Nº de linhas |
|---|---|---|
| `kmeans_painel_regional_ano.ipynb` | par **(Regional de Saúde, Ano)** | 114 (mesma matriz do DBSCAN) |
| `kmeans_regional_trajetoria.ipynb` | **Regional de Saúde inteira** (série temporal completa como uma linha) | 28 → 14 após descarte |

O notebook "painel" é diretamente comparável ao DBSCAN (mesma matriz de entrada, mesmo pré-processamento). O notebook "trajetória" muda a estrutura dos dados: em vez de cada (Regional, Ano) ser uma linha, cada **Regional inteira** é uma linha, e cada combinação (categoria, ano) vira uma **coluna própria** — o tempo não é resumido em média/tendência, a série completa é preservada como estrutura larga.

## 3. Formato dos dados de entrada

Igual ao DBSCAN: os cinco blocos de **taxa por 100 mil habitantes** (`Seleção e Transformação/População/Taxa/*.csv`) — Casos por Faixa Etária, Casos por Escolaridade, Casos por Raça e Cor, Mortalidade, Mamografia — nunca valor absoluto. `montar_painel`/`ler_csv_taxa_em_painel` fazem a mesma reformatação largo → painel (melt + pivot_table), com o mesmo esquema de prefixo por bloco (`casos-faixa_`, `mortalidade_`, etc.) para não colidir categorias homônimas entre blocos.

## 4. Pipeline do notebook "painel" (idêntico ao DBSCAN até a etapa 4)

1. `montar_painel` → matriz 1.316 × 42.
2. Janela comum 2013-2023 → 308 pares.
3. Descarte de colunas sem-informação/total, colunas com >70% de nulos, linhas com qualquer nulo (sem imputação) → **114 pares × 32 atributos**.
4. `RobustScaler` sempre; PCA condicional (`USAR_PCA=False` fixado no notebook, mesma lógica do DBSCAN).
5. **Escolha de `k`** (única etapa que substitui eps/MinPts do DBSCAN — ver Seção 6).
6. `executar_kmeans` (`sklearn.cluster.KMeans`).

## 5. Pipeline do notebook "trajetória" (ajustes específicos)

Com 28 Regionais e potencialmente centenas de colunas (categoria × ano), o regime é `p >> n` (muito mais atributos que observações) — isso muda duas decisões em relação ao painel:

1. **`USAR_JANELA_COMUM=True` é obrigatório na prática** (reduz nº de anos → nº de colunas) — sem isso o número de colunas explode.
2. **`CONVERTER_EM_PROPORCAO=True`** (`converter_blocos_em_proporcao`): cada bloco de colunas é convertido em proporção dentro do bloco, linha a linha (ex.: proporção de casos em cada faixa etária, não a taxa bruta) — evita que o porte da Regional domine a distância euclidiana. Aplicado **antes** do colapso em trajetória, para a proporção ser calculada dentro de cada (bloco, Regional, Ano), não misturando anos diferentes. Como as proporções de um bloco somam 1, a última categoria de cada bloco é combinação linear das demais — redundância que o PCA absorve, mas que importa se alguém for interpretar os pesos das variáveis diretamente.
3. **`colapsar_painel_em_trajetoria`**: `painel.unstack(ANO)` — cada linha vira uma Regional, cada coluna vira `<categoria>_<ano>`. No caso real do projeto: **28 Regionais × 385 variáveis** — um alerta de log dispara porque 385 variáveis para 28 observações deixa o número máximo de componentes principais com informação em apenas 27.
4. **Descarte por coluna primeiro, depois por linha** (`relatorio_de_ausentes` + `MAXIMO_DE_AUSENTES_PARA_DESCARTAR=0.20`): como cada linha é uma Regional inteira, descartar uma linha é muito mais caro que no painel (perde-se a Regional inteira da análise, não só um ano dela). Por isso o corte é: (a) descarta colunas com ≥20% de ausência, (b) só depois descarta as linhas (Regionais) que ainda restarem com algum nulo — o log registra explicitamente qual Regional saiu. No caso real: 50 colunas descartadas, e ainda assim **14 das 28 Regionais são descartadas** (barbacena, diamantina, itabira, ituiutaba, januária, manhumirim, passos, pedra azul, pirapora, ponte nova, são joão del rei, sete lagoas, teófilo otoni, unaí) — sobra **14 Regionais × 333 variáveis**.
5. `descartar_colunas_constantes`: remove colunas com um único valor (variância zero quebra a padronização por IQR quando o IQR é zero).
6. **PCA obrigatório** (`usar_pca=True` fixado, não condicional como no painel): com razão atributos/linhas = 23,8, PCA é sempre necessário. Reduz para 9 componentes, 88% da variância acumulada.

## 6. Escolha de `k` (cotovelo da curva de inércia)

`k` não é fixado à mão. `calcular_inercia_e_silhueta_por_k` roda o KMeans para cada `k` entre `K_MINIMO` e `K_MAXIMO`, calculando inércia (sempre decrescente com `k`) e silhueta. `escolher_k_pelo_cotovelo` usa a mesma biblioteca `kneed` do DBSCAN (`KneeLocator`, agora `curve="convex"`, `direction="decreasing"` — a curva de inércia decresce, ao contrário da curva de k-distâncias do DBSCAN, que cresce) para localizar o cotovelo — o ponto a partir do qual aumentar `k` deixa de reduzir a inércia de forma significativa (método de Thorndike, 1953). Mesmo fallback do DBSCAN se o `kneed` não encontrar cotovelo (segunda derivada discreta).

`busca_em_grade_k` roda a mesma varredura com `ParameterGrid` como validação complementar (permite testar múltiplas sementes, `SEMENTES_DA_BUSCA`, embora só uma esteja configurada por padrão).

**Diferença entre os dois notebooks**: no painel, `K_MAXIMO=10`; na trajetória, `K_MAXIMO=8`, ajustado por comentário no código ("com poucas Regionais sobreviventes, `k` é também, na prática, o tamanho mínimo médio de cluster").

## 7. Execução do KMeans

`executar_kmeans` chama `sklearn.cluster.KMeans(n_clusters=k, random_state=SEMENTE_ALEATORIA, n_init=NUMERO_DE_INICIALIZACOES)`. `n_init=10`: o KMeans roda 10 vezes com inicializações de centróide diferentes e mantém o melhor resultado (menor inércia) — mitiga o problema de o algoritmo convergir para um mínimo local ruim dependendo da inicialização.

## 8. Métricas e medidas estatísticas usadas

- **Inércia (WCSS)** — critério principal de ajuste do próprio KMeans e base do método do cotovelo.
- **Silhueta** (`sklearn.metrics.silhouette_score`) — aqui em **uma única versão** (diferente do DBSCAN), já que não existe ruído a separar; usada como validação complementar ao cotovelo, nunca como critério isolado (o comentário no código é explícito: a inércia decrescente monotonicamente com `k` tornaria "maior silhueta" um critério enviesado para `k` pequeno).
- **Distância euclidiana** sobre a matriz padronizada (RobustScaler) — mesma métrica do DBSCAN.
- **Variância explicada acumulada** do PCA, quando aplicado.
- **Pesos ("loadings") do PC1** (`pesos_das_variaveis_no_componente`), mesma função reaproveitada em espírito do DBSCAN (implementação própria, mas idêntica).
- **Diagnóstico de tamanho de cluster** (`diagnostico_tamanho_dos_clusters`): identifica clusters com menos de `MINIMO_DE_ELEMENTOS_POR_CLUSTER` (painel: 4; trajetória: 3) elementos — um aviso pós-hoc, sem efeito sobre o resultado, sinalizando que um cluster muito pequeno tende a ser um outlier isolado, não um perfil compartilhado.

## 9. O que é configurável (e o que cada coisa afeta)

| Constante | Efeito |
|---|---|
| `USAR_JANELA_COMUM`, `ANO_INICIAL_COMUM`, `ANO_FINAL_COMUM` | período do painel |
| `LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA` | esparsidade máxima de coluna aceita (painel) |
| `MAXIMO_DE_AUSENTES_PARA_DESCARTAR` | esparsidade máxima de coluna aceita (trajetória, só nesse notebook) |
| `CONVERTER_EM_PROPORCAO` | se cada bloco vira proporção antes do colapso em trajetória (só na trajetória) |
| `USAR_PCA`, `RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA`, `VARIANCIA_EXPLICADA_ALVO`, `NUMERO_MAXIMO_DE_COMPONENTES` | se e quanto reduzir dimensionalidade |
| `K_MINIMO`, `K_MAXIMO` | faixa de busca de `k` |
| `SENSIBILIDADE_COTOVELO` | sensibilidade do `KneeLocator` |
| `SEMENTES_DA_BUSCA`, `NUMERO_DE_INICIALIZACOES` | reprodutibilidade/estabilidade da inicialização do KMeans |
| `MINIMO_DE_ELEMENTOS_POR_CLUSTER` | só afeta o aviso de diagnóstico, não o resultado |

Assim como no DBSCAN, tudo são constantes no topo do arquivo `.py`, sem configuração externa.

## 10. Bibliotecas usadas

`numpy`, `pandas`, `scikit-learn` (`KMeans`, `PCA`, `RobustScaler`, `silhouette_score`, `ParameterGrid`), `kneed`, `plotly` (incluindo `go.Scatterpolar` para o gráfico de perfil dos clusters).

## 11. O que cada pipeline produz

Comum aos dois notebooks: `resumo_parametros` (k, inércia, silhueta, PCA, dimensões), `atributos_usados`, tabela de pertencimento por cluster, gráfico de cotovelo com `k` marcado, gráfico de silhueta por `k`, dispersão PC1×PC2, gráfico de variância explicada e pesos (quando há PCA).

Específico do **painel**: `visao_agregada_regional_ano` (pivot Regional×Ano→cluster) e heatmap correspondente, dispersão por ano, distribuição por Regional/Ano — mesmo formato do DBSCAN, para comparação direta entre os dois algoritmos sobre a mesma matriz.

Específico da **trajetória**: `grafico_perfil_dos_clusters` — radar chart (`Scatterpolar`) com o perfil médio (em desvios-padrão robustos) de cada cluster nos 12 atributos de maior variância entre clusters, mostrando o que diferencia cada agrupamento (não apenas onde cada ponto caiu na projeção 2D); e `diagnostico_por_regional`, que lista as Regionais de cada cluster nominalmente.

Nenhum dos dois notebooks grava resultado em disco — tudo fica só como saída de célula (mesma decisão do DBSCAN).

## 12. Resultados obtidos e limitações observadas

**Painel (114 pares × 32 atributos)**: cotovelo escolhe `k=5`, inércia 1.954,5, silhueta 0,134 (baixa). Da composição dos 5 clusters: cluster 0 tem 55 pares, cluster 1 tem 26, cluster 2 tem 30 — mas **cluster 3 tem 1 único par** (`leopoldina, 2020`) e **cluster 4 tem 2** (`passos, 2021` e `passos, 2023`). Ou seja, 2 dos 5 clusters são efetivamente outliers isolados sendo tratados como agrupamento, não perfis compartilhados — o próprio código já sinaliza isso via `diagnostico_tamanho_dos_clusters`.

**Trajetória (14 Regionais × 333 variáveis, PCA a 9 componentes)**: cotovelo (via fallback de segunda derivada, o `kneed` não achou cotovelo nítido) escolhe `k=6` para 14 observações, inércia 1.145,4, silhueta 0,134. Composição: **5 dos 6 clusters têm 1 ou 2 Regionais** (alfenas sozinha; coronel fabriciano sozinha; leopoldina sozinha; patos de minas sozinha; governador valadares + montes claros) — só o cluster 1 tem um grupo real (8 Regionais: belo horizonte, divinópolis, juiz de fora, pouso alegre, ubá, uberaba, uberlândia, varginha). Com metade das Regionais descartadas por dados ausentes e a maioria dos clusters restantes sendo essencialmente uma Regional isolada, este resultado é frágil — o próprio pipeline já emite o aviso "sobraram pouquíssimas regionais... qualquer agrupamento encontrado é frágil" quando `matriz.shape[0] < 10` (não chegou a disparar aqui, mas 14 está perto do limite).

Em ambos os casos, silhuetas em torno de 0,13 indicam clusters com sobreposição considerável — não uma separação nítida entre grupos. Isso é consistente com o que o DBSCAN também mostrou (tendência a colapsar em poucos agrupamentos "reais" mais ruído/outliers) e vale ser reportado como achado metodológico na monografia, não apenas como número de tabela.
