# Decisões, Critérios e Metodologias — Pontos Prováveis de Banca

Documento de defesa: cada decisão de projeto com o critério exato, a justificativa e uma resposta pronta para a pergunta que a banca provavelmente vai fazer. Organizado pelas etapas do KDD.

---

## 1. Coleta (Limpeza e Integração)

### 1.1 Casos e Mortalidade usam "origem do paciente"; Mamografia usa "local do exame" — assimetria geográfica

- **Casos (RHC-INCA):** tabulado por `LINHA_ID = "12"  # Procedência` — município de **procedência do paciente** (`Limpeza e Integração/Casos/*/Código/main.py`).
- **Mortalidade (Mortalidade Web/INCA):** `TIPO_COLUNA_ID = "2"  # Município` — por convenção do sistema (SIM/DATASUS), mortalidade é tabulada pelo município de **residência** do falecido, não de ocorrência do óbito. **Confirmar esse detalhe na documentação do Mortalidade Web antes da defesa** — é uma afirmação sobre convenção de terceiros, não algo que o código decide.
- **Mamografia (SISCAN/TABNET):** `FILTRO_LINHA = "Munic.da un.saúde"` — município da **unidade de saúde onde o exame foi realizado**, não de residência da paciente.

**Por que isso importa:** Casos e Mortalidade medem onde a paciente mora; Mamografia mede onde o exame foi feito. Uma Regional com hospital/clínica de referência pode "importar" exames de regiões vizinhas, inflando sua taxa de mamografia sem que isso reflita a cobertura real de rastreamento da sua própria população residente.

**Pergunta provável:** *"Por que você não ajustou a Mamografia por município de residência, pra ficar comparável com Casos e Mortalidade?"*
**Resposta:** O SISCAN/TABNET não oferece essa quebra por residência nesse tabulador; só por município da unidade de saúde. Essa limitação é reconhecida explicitamente na análise do mapa/heatmap de Mamografia (Passos, por ex., como possível polo que absorve demanda de regiões vizinhas) em vez de ser tratada como se as duas bases fossem diretamente equivalentes.

### 1.2 Casos é por ano de diagnóstico, não por ano de notificação

`COLUNA_ID = "22"  # ano de diagnóstico` — a série é organizada pela data em que o câncer foi diagnosticado, não pela data em que o registro entrou na base (notificação pode ser anos depois do diagnóstico). Isso explica por que anos recentes podem estar sujeitos a *under-reporting* temporário (casos diagnosticados mas ainda não notificados ao RHC) — relevante para qualquer leitura de "queda" nos últimos anos da série.

### 1.3 Lacuna de 1987 no script de Casos por Ano de Diagnóstico (corrigida)

A lista `ANOS` em `Limpeza e Integração/Casos/Ano Diagnóstico/Código/main.py` pulava de 1988 para 1986, sem 1987 — mas o CSV final (`tabela_casos_por_ano_de_diagnóstico.csv`) já tinha a coluna `1987_TOTAL` com dados reais (soma = 11 casos, 836 municípios com valor), de uma extração anterior não refletida na lista. 1987 foi adicionado de volta a `ANOS`; o script volta a ser reprodutível fim a fim.

### 1.4 Cobertura temporal desigual por sistema de origem

- Casos: 1985–2023 (RHC-INCA)
- Mortalidade: 1979–2024 (SIM/Mortalidade Web)
- Mamografia: 2013–2025 (SISCAN — sistema mais recente)
- Hospitais Habilitados: só 2023 (retrato único, sem série histórica no CNES/fonte usada)
- Casos por Escolaridade/Raça e Cor: 1998–2023 (campos só começam a ser preenchidos de forma consistente no RHC a partir de 1998)

**Pergunta provável:** *"Por que os períodos são diferentes entre variáveis?"*
**Resposta:** cada variável vem de um sistema de informação diferente, com seu próprio início de coleta nacional/estadual — não é escolha do projeto, é limite da fonte. O projeto não força um período comum entre si (cada notebook de taxa usa o período próprio da sua variável); só o K-means impõe uma janela comum (2014–2023, ver seção 4).

### 1.5 Mortalidade: lista de anos não contígua

`PERIODO` em `Limpeza e Integração/Mortalidade/Cidades Atendidas por Cada Regional/main.py` tem lacunas (ex.: salta 1981→1984, 1990→1993) — reflete anos em que o Mortalidade Web não tem dado municipal disponível para consulta, não uma escolha arbitrária do projeto.

---

## 2. Seleção e Transformação — População e Taxas

### 2.1 Interpolação/extrapolação geométrica, por faixa etária (não linear, não pelo total)

- **Método geométrico** (`P(t) = P_0 (1+r)^t`), não linear — justificativa: crescimento populacional tipicamente aproxima progressão geométrica/exponencial em intervalos curtos/médios, é o método padrão do IBGE para estimativas intercensitárias.
- **Por faixa etária separadamente, depois somado** — não interpolando o total direto. Verificação feita (`interpolacao_extrapolacao.ipynb`): interpolar o total direto diverge da soma das faixas em média 1,19% (máx. 3,24%) — confirma que as duas contas não são equivalentes e que interpolar por faixa preserva a estrutura demográfica de cada município (ex.: envelhecimento não é uniforme entre faixas).
- **Extrapolação (2023–2025)** usa a taxa geométrica só dos **dois últimos censos** (2010, 2022), não de todo o histórico — captura a dinâmica populacional mais recente, mas é sensível a qualquer irregularidade entre esses dois censos específicos (ex.: o de 2022 teve atraso/problemas de coleta conhecidos, pós-pandemia).

**Pergunta provável:** *"Por que só os dois últimos censos pra extrapolar, e não uma regressão com todos?"*
**Resposta:** é o método padrão de estimativas intercensitárias (IBGE também usa essa lógica); usar todo o histórico assumiria que a taxa de crescimento é constante ao longo de 50+ anos, o que não é realista (transição demográfica muda a taxa de década pra década).

### 2.2 Limiar de população válida: `POPULACAO_MINIMA_VALIDA = 1`

População ausente (NaN) ou menor que 1 habitante é tratada como inválida. Tanto a população quanto a quantidade do evento daquele par específico (município, ano, [faixa]) são descartadas da soma — nunca só uma das duas (ver 2.3).

**Pergunta provável:** *"Por que não excluir toda a linha do município, só porque faltou um ano?"*
**Resposta:** o descarte é por célula (ano/faixa específico), não por município inteiro — os demais anos/faixas do mesmo município com dado válido continuam no estudo. Excluir o município inteiro desperdiçaria dado válido disponível.

### 2.3 Exclusão em par (evento + população), nunca uma sem a outra

Manter o evento sem a população correspondente infla artificialmente a taxa (denominador ausente tratado como erro, não como zero). Essa regra é aplicada **antes** da soma por Regional de Saúde.

### 2.4 Município sem Regional cadastrada é descartado por inteiro, antes de qualquer checagem de população

Ocorre em `calcular_taxa_por_regional` (`dropna(subset=[COLUNA_REGIONAL])`), executado antes do loop de validação de população — é uma ordem de operações deliberada: sem Regional, o registro não tem onde ser somado, então sai primeiro. Hoje esse caso não ocorre mais em nenhuma variável (0 registros, confirmado no log de `calculo_taxa.ipynb`) — era 6 registros em Mamografia antes de uma correção anterior no enriquecimento de Código IBGE/Regional.

### 2.5 Denominador da taxa: faixa etária quando existe, população total nos demais casos

`coluna_populacao_correspondente` decide isso coluna a coluna: se o nome da coluna bate com uma das 8 faixas etárias padrão, usa a população daquela faixa; senão (Escolaridade, Raça e Cor, TOTAL), usa a população total da Regional naquele ano. Hospitais usa população total de 2023 fixo (retrato único).

**Pergunta provável:** *"Por que Escolaridade e Raça/Cor não têm denominador próprio (população por nível de escolaridade, por raça/cor)?"*
**Resposta:** a base de população (IBGE, interpolada) não tem a população de MG estratificada por escolaridade nem por raça/cor ano a ano — só por faixa etária. Não é escolha, é limite da fonte de denominador disponível.

### 2.6 Agregação sempre em duas etapas: por município primeiro, por Regional depois

A soma por Regional de Saúde é a soma das quantidades (numerador) e das populações (denominador) de cada município já individualmente validado — a taxa final é a razão das somas regionais, **não** a média das taxas municipais já calculadas (evita o erro clássico de "média de taxas" distorcer o resultado por municípios pequenos).

### 2.7 Multiplicador da taxa: por 100.000 habitantes (`MULTIPLICADOR_TAXA = 100_000`)

Padrão em epidemiologia para eventos de baixa frequência (câncer, óbitos) — torna a taxa legível (ex.: 45,48 em vez de 0,0004548).

---

## 3. Variáveis categóricas (Escolaridade, Raça e Cor)

### 3.1 Colunas "DIAGNOSTICO" e "TOTAL" duplicadas são descartadas no agregado estadual

"DIAGNOSTICO" em Casos é idêntico a TOTAL na própria fonte (conferido, sempre o mesmo valor) — mantido só TOTAL. As 3 quebras categóricas de Casos (Faixa Etária, Escolaridade, Raça/Cor) têm cada uma seu próprio "TOTAL" que é redundante com a fonte "Casos" dedicada (a soma real) — descartado para não duplicar coluna no CSV agregado por ano.

### 3.2 "Sem informação" é mantida como categoria própria (não imputada, não descartada da base de Casos)

Escolaridade e Raça/Cor têm uma categoria "SEM INFORMAÇÃO" própria no RHC — tratada como categoria legítima (pode refletir campo não preenchido no prontuário), não como dado ausente a imputar. É descartada só na entrada do K-means (ver 4.3), não na tabela de taxas.

---

## 4. Mineração de Dados — K-means

### 4.1 RobustScaler em vez de StandardScaler

Usa mediana e IQR (não média e desvio padrão) para padronizar — robusto a outliers, que são esperados nos dados (ex.: Belo Horizonte tem volume absoluto muito acima das demais Regionais em quase toda variável). StandardScaler (média/desvio padrão) seria distorcido por esses poucos valores extremos.

### 4.2 PCA calculado mas desligado (`USAR_PCA = False`)

Critério para decidir se seria necessário: razão atributos/linhas (`RAZAO_MAXIMA_ATRIBUTOS_POR_LINHA = 0.10`). No caso final (29 atributos / 256 linhas = 0,113), ficou perto do limiar mas o código força `False` explicitamente (não é a decisão automática que decidiu, foi fixada). Estrutura para PCA (`VARIANCIA_EXPLICADA_ALVO = 0.85`, até 10 componentes) está implementada e pode ser religada trocando a flag.

**Pergunta provável:** *"Por que não usar PCA, já que a razão tá perto do limiar?"*
**Resposta:** PCA comprometeria a interpretabilidade da caracterização por cluster (seção 4.6) — os "componentes principais" não têm leitura direta como "taxa de mamografia na faixa 40-49"; manter as variáveis originais permite caracterizar cada cluster em termos que a banca e a área de saúde reconhecem diretamente.

### 4.3 Limiar de 5% de nulos por coluna (`LIMIAR_MAXIMO_DE_NULOS_POR_COLUNA = 0.05`)

Aplicado por **coluna** (variável), não por linha — uma coluna com mais de 5% de ausência na janela 2014–2023 é descartada por completo antes de qualquer imputação. O descarte de linha com nulo residual é uma etapa **separada e posterior** (dropna, sem imputar — ver 4.4).

**Pergunta provável:** *"Por que 5% e não 10% ou 1%?"*
**Resposta:** é um limiar de bom senso adotado para equilibrar dois riscos — um limiar muito alto manteria colunas quase todas vazias (ex.: `mortalidade_0-9`, 100% nula, ou `mortalidade_10-19`, ~99,3% nula) distorcendo a padronização; um limiar muito baixo descartaria colunas com ausência pontual e não estrutural. Não há um teste estatístico formal escolhendo 5% — é um valor de corte prático, documentado explicitamente para que o resultado seja reprodutível, dado que as colunas acima do limiar correspondem a eventos genuinamente raros (contagens de 0 a 6 por ano em todo o estado), não a falha de coleta.

### 4.4 Linhas com nulo residual são descartadas, não imputadas

`tratar_nulos_sem_imputar` — 24 de 280 linhas (8,6%) descartadas na janela 2014–2023, todas por nulos em `mortalidade_*` (contagens raras por faixa etária) ou, num caso (Teófilo Otoni, 2015), mamografia ausente.

**Pergunta provável:** *"Por que não imputar (média, mediana, KNN) em vez de descartar linha?"*
**Resposta:** imputar um valor de contagem rara (ex.: mortes na faixa 40-49) criaria um dado sintético que o K-means trataria como real, distorcendo a distância ao centróide sem nenhuma base empírica — para uma série já esparsa, imputação introduziria mais ruído do que a perda de 8,6% das linhas.

### 4.5 Janela temporal comum do K-means: 2014–2023

Não é o período completo de nenhuma variável — é definido pela cobertura mínima da Mamografia: em 2013, só 3 das 28 Regionais têm qualquer registro (e nenhuma nas faixas etárias mais jovens), tornando 2013 inutilizável como linha de um painel multivariado. 2023 é o ano final porque é o último ano com Casos disponível (RHC-INCA até 2023).

### 4.6 K escolhido pelo cotovelo (`KneeLocator`), não pela silhueta

`CALCULAR_SILHUETA = False` por padrão — a silhueta está implementada mas desligada; o critério efetivamente usado é só a curva de inércia (WCSS) com o pacote `kneed`, `S=1.0` (sensibilidade padrão). $k=5$ escolhido.

**Pergunta provável:** *"Por que não validar k=5 também pela silhueta?"*
**Resposta:** a função de cálculo de silhueta está implementada e pode ser ativada (`CALCULAR_SILHUETA = True`); a escolha de manter o cotovelo como critério principal foi por ser o método mais estabelecido na literatura de K-means pra esse tipo de problema exploratório, mas nada impede reportar a silhueta como validação adicional — vale considerar adicionar esse número ao texto se a banca perguntar.

### 4.7 Faixa de k testada: 2 a 12, heurística $\sqrt{N/2}$

$\sqrt{256/2} = \sqrt{128} \approx 11{,}3$ — arredondado para $K_{máximo}=12$. $K_{mínimo}=2$ é o menor valor que ainda configura um agrupamento (1 cluster não particiona nada).

### 4.8 Estabilidade: busca em grade com 5 sementes, não só `random_state=42`

`SEMENTES_DA_BUSCA = [0, 10, 30, 42, 66]` — testa se o resultado do cotovelo/inércia é sensível à inicialização aleatória do K-means. Coeficiente de variação da inércia para k=5 entre as 5 sementes: 0,07% — evidência de que o resultado não depende da sorte da inicialização. `n_init=10` dentro de cada chamada já mitiga isso também (sklearn reinicia 10× e pega o melhor).

### 4.9 `max_iter = 30` (não o default 300 do sklearn)

Ajustado depois de observar que nenhuma das 55+1 execuções (busca em grade + modelo final) passou de 29 iterações até convergir — o teto de 300 nunca restringiu nada; 30 documenta o comportamento real observado sem comprometer a convergência.

### 4.10 Caracterização de cluster: diferença padronizada por IQR, não por desvio padrão, sem teste de significância

`DP_{c,v} = (média do cluster − média geral) / IQR geral` — usa o mesmo IQR do RobustScaler (consistência com a escala em que o K-means calculou as distâncias), não o desvio padrão. Não há ANOVA/Tukey comparando clusters: seria circular, porque o K-means já maximiza a diferença entre grupos exatamente nessas variáveis (Everitt et al., 2011, citado no próprio notebook) — qualquer teste de significância post-hoc tenderia a "confirmar" diferenças que o próprio algoritmo foi desenhado para produzir.

**Pergunta provável:** *"Como você sabe que as diferenças entre clusters são estatisticamente significativas?"*
**Resposta:** não é essa a pergunta que a caracterização responde — ela descreve o que diferencia um cluster do perfil médio geral (uma leitura descritiva/exploratória), não testa uma hipótese confirmatória. Um teste de significância aqui seria metodologicamente circular (ver acima), por isso foi deliberadamente omitido, com a justificativa citada no próprio notebook.

### 4.11 Top 15 variáveis discriminantes por cluster (`NUMERO_DE_VARIAVEIS_DISCRIMINANTES = 15`)

De 29 atributos totais, só as 15 de maior `|DP|` por cluster entram na descrição textual/gráfica — corte prático para não listar as ~29 variáveis de cada cluster no texto, mantendo as metade mais relevante de cada um.

### 4.12 Hospitais Habilitados: TIPO="TODOS" nunca usado como entrada, só como soma de referência

`calcular_com_total_por_tipo` gera uma linha "TODOS" por Regional (soma dos 3 tipos de habilitação) só para exibição; o K-means e os gráficos filtram `TIPO != "TODOS"` antes de somar — se não filtrassem, cada hospital seria contado em dobro (uma vez pelo tipo específico, outra em "TODOS").

---

## 5. Avaliação e Apresentação — Mapas e Gráficos

### 5.1 Legenda dos mapas (cor e bolha): por quantil, não por intervalo igual

`pd.qcut` com `N_FAIXAS_COR = 5` / `N_DEGRAUS_BOLHA = 5` — cada faixa da legenda tem a mesma **quantidade de Regionais**, não a mesma amplitude numérica; por isso os intervalos de cada faixa têm larguras diferentes entre si. Cai para `pd.cut` (intervalo igual) só se `qcut` falhar por poucos valores distintos.

**Pergunta provável:** *"Por que quantil e não intervalo igual (ex.: dividir o range em 5 partes iguais)?"*
**Resposta:** com só 28 Regionais e distribuições com outlier forte (Belo Horizonte sempre no topo em volume absoluto), um corte por intervalo igual deixaria quase todas as Regionais numa única faixa de cor e BH isolada nas faixas mais altas — por quantil, a legenda distribui as Regionais de forma mais equilibrada entre as faixas, o que é mais legível visualmente, ao custo de intervalos numéricos desiguais.

### 5.2 Municípios sem Regional cadastrada na malha: atribuídos à Regional do vizinho mais próximo (só geometria)

No mapa coroplético, municípios sem Regional (ex.: inconsistência de código IBGE na malha do `geobr`) recebem a Regional do município limítrofe mais próximo (distância euclidiana entre geometrias projetadas), **só para o desenho do mapa** — nenhum total numérico das taxas é afetado por essa atribuição (ela não entra em `calculo_taxa.ipynb`, só no notebook de mapas).

### 5.3 Valores absolutos acumulados nos mapas, não taxas

Os mapas de valor absoluto (`mapa_regional_valores_absolutos.ipynb`) somam a quantidade bruta de todo o período disponível de cada variável, sem ajuste por população — complementares aos mapas/heatmaps de taxa, não substitutos. O texto de cada mapa inclui a ressalva de que são valores "não ajustados ainda pela população" precisamente para não serem lidos como medida comparável entre Regionais de tamanho populacional muito diferente.

### 5.4 Heatmap Regional × Ano começa em 2013, mesmo sabendo da escassez de Mamografia nesse ano

Decisão deliberada de deixar visível a escassez (3 de 28 Regionais com dado) em vez de recortar a visualização a partir de 2014 como no K-means — o heatmap tem outro propósito (mostrar a evolução completa disponível, inclusive onde ela é ruim), diferente do K-means (que precisa de uma matriz completa, sem furos, pra calcular distância).

### 5.5 Raça e cor: "e", não "/", seguindo a nomenclatura do IBGE

Ver `GLOSSARIO.md` — escolha terminológica deliberada, não trivial, para não sugerir que "cor" e "raça" são sinônimos.

---

## 6. Pontos sem justificativa documentada no código (atenção redobrada na defesa)

- **Convenção exata do Mortalidade Web** (município de residência vs. ocorrência do óbito) não está confirmada em comentário de código — vale checar a documentação oficial do sistema antes da defesa, pois é uma afirmação sobre fonte externa.
- **Limiar de 5% de nulos** (seção 4.3) e **$k=2..12$** (seção 4.7) são escolhas práticas/heurísticas, não resultado de um teste estatístico formal — documentado aqui como tal, para não serem apresentados como se tivessem uma prova matemática única por trás.
