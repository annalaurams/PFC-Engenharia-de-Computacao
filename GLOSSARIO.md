# Glossário — Documentação e Entendimento

Dicionário de termos usados no trabalho: o que cada um significa e onde/como foi aplicado neste projeto especificamente (não só a definição genérica).

## Epidemiologia

Estudo da distribuição e dos determinantes de eventos de saúde (doenças, óbitos, agravos) em populações — não do indivíduo isolado, mas de como esses eventos se distribuem no tempo, no espaço e entre grupos, e por quê. A definição mais citada na área (Last, 1998) trata a epidemiologia como o estudo da frequência, distribuição e determinantes de eventos ligados à saúde em populações específicas, servindo de base para o controle e a prevenção.

**Como foi usado aqui:** é o enquadramento de todo o trabalho. Em vez de analisar uma paciente ou um município isoladamente, o projeto olha para a distribuição do câncer de mama (casos, óbitos, mamografias) entre as 28 Regionais de Saúde de Minas Gerais e ao longo do tempo (1979–2025, dependendo da variável) — é esse recorte populacional e espaço-temporal que torna o trabalho um estudo epidemiológico, não clínico.

Fontes: [SciELO (Morabia, 2013)](https://scielosp.org/pdf/csp/2013.v29n6/1059-1062/pt), [UCB (Pinto Júnior, 2018)](https://portalrevistas.ucb.br/index.php/rmsbr/article/download/9023/5732/42413).

## Acesso à saúde

Não tem definição única na literatura; os dois autores mais citados divergem no foco:

- **Donabedian (1973)** chama o conceito de "acessibilidade" e o define pelas características dos recursos de saúde que facilitam ou dificultam o uso pelos potenciais usuários, separando uma dimensão sócio-organizacional e uma geográfica (distância/tempo até o serviço).
- **Andersen** trata o acesso como resultado de três grupos de determinantes — predisposição individual, fatores capacitantes (renda, seguro, disponibilidade de serviço) e necessidade de saúde — e, com Aday (1974), defende que a prova do acesso está em quem efetivamente usa o serviço de que precisa, não só na existência dele.

**Como foi usado aqui:** é o fio condutor da interpretação dos mapas e taxas regionais. Quando o trabalho nota que uma Regional tem taxa de casos ou mamografia desproporcional ao seu volume populacional, ou que hospitais habilitados se concentram em poucas Regionais (mapa de Casos × Hospitais, `mapa_regional_valores_absolutos.ipynb`), a leitura é em termos de acesso geográfico (dimensão de Donabedian): mulheres de Regionais sem hospital habilitado ou com baixa cobertura de rastreamento têm, na prática, acesso mais difícil ao diagnóstico e tratamento, independente de sua necessidade de saúde ser a mesma.

Fontes: [SciELO (Revista de Saúde Pública, 2012)](https://scielosp.org/pdf/rpsp/2012.v31n3/260-268/pt), [Tempus/UnB (Iturri)](https://tempusactas.unb.br/index.php/tempus/article/download/1457/1301).

## Raça e cor (por que "e", não "/")

O IBGE classifica a população brasileira em cinco categorias — branca, preta, parda, amarela e indígena — desde o Censo de 1991, com base na autodeclaração (autoidentificação que combina traços fenotípicos e critérios históricos/sociais, não um dado biológico objetivo).

A expressão oficial do IBGE é **"cor ou raça"** (não "raça/cor" nem só "cor"), porque reconhece que "cor" e "raça" não são sinônimos nem se substituem: "cor" remete a uma categoria de classificação (fenotípica), enquanto "raça" carrega também um sentido social e histórico de pertencimento e discriminação; usar as duas conjugadas evita restringir a resposta do entrevistado a só uma dessas leituras.

**Como foi usado aqui:** a variável vem do RHC/INCA, que replica essa mesma classificação de 5 categorias para os casos de câncer de mama em MG (`Limpeza e Integração/Casos/Raça-Cor/Código/main.py`, campo `racaCor` do formulário de extração). Optei por manter a conjunção "e" (coerente com a nomenclatura do IBGE) em vez de abreviar como "raça/cor" no texto da monografia, para não sugerir que os dois termos são intercambiáveis.

Fontes: [IBGE — biblioteca](https://biblioteca.ibge.gov.br/visualizacao/livros/liv49891.pdf), [Agência IBGE](https://agenciadenoticias.ibge.gov.br/agencia-sala-de-imprensa/2013-agencia-de-noticias/releases/14057-asi-ibgedivulga-resultados-de-estudo-sobre-cor-ou-raca).

## (Dados/variáveis) demográficos

Dados que descrevem a composição da população segundo características como idade, sexo, escolaridade, raça/cor — em oposição a dados clínicos (diagnóstico, estadiamento) ou geográficos (localização).

**Como foi usado aqui:** é a categoria que agrupa as variáveis usadas para estratificar Casos e Mamografias além do total simples — faixa etária (0-9 a 70+), escolaridade e raça e cor, todas vindas do RHC/INCA e tratadas em `Seleção e Transformação/Casos/` e usadas tanto nas taxas por Regional (`calculo_taxa.ipynb`) quanto como atributos de entrada do K-means (`casos-faixa_*`, `casos-escolaridade_*`, `casos-raca-cor_*` em `utilitarios_agrupamento_kmeans.py`).

## Municípios limítrofes

Segundo o IBGE, município limítrofe é aquele que faz divisa geográfica (fronteira contígua) com outro município — um vizinho confinante, com fins estatísticos/geocientíficos, sem relação com qualquer validação legal ou administrativa.

**Como foi usado aqui:** no mapa coroplético por Regional de Saúde (`mapa_regional_valores_absolutos.ipynb`), municípios sem Regional cadastrada na malha geográfica recebem, apenas para fins de desenho do mapa (sem afetar nenhum total numérico das taxas), a Regional do município vizinho mais próximo — na prática, do município limítrofe mais próximo, calculado pela distância entre as geometrias já projetadas (`com_regional.geometry.distance(geometria)`).

Fonte: [IBGE — Municípios Limítrofes](https://www.ibge.gov.br/geociencias/organizacao-do-territorio/estrutura-territorial/42224-municipios-limitrofes.html).

# Metodologia — Esclarecimentos

## Interpolação/extrapolação geométrica — mecânica exata

A taxa geométrica ($r_g$) é calculada **uma vez por intervalo censitário** (ex.: 1970–1980) e reaproveitada para todo ano dentro dele. O que muda ano a ano **não é $P_{inicial}$** — ele fica fixo no valor do censo-âncora do intervalo (ex.: 1970) — e sim o **expoente** $t$ (tempo decorrido = ano − ano_inicial):

$$P(t) = P_{1970} \times (1 + r_g)^{t}, \quad t = \text{ano} - 1970$$

Não há encadeamento ano a ano (o resultado de 1971 não vira a base de 1972); todo ano do intervalo usa o mesmo $P_{inicial}$ e a mesma $r_g$, só o expoente muda. Implementado em `interpolar_geometrica`, `Seleção e Transformação/População/Interpolação e Extrapolação/interpolacao_extrapolacao.ipynb`.

## Verificação: interpolar o TOTAL direto ≠ somar as faixas já interpoladas

O total de um ano intermediário (ex.: 1971) é, por construção, a soma das 8 faixas etárias já interpoladas separadamente — não existe um "total original" de 1971 pra comparar. Adicionei uma célula em `interpolacao_extrapolacao.ipynb` que testa se essa escolha (interpolar por faixa e depois somar) dá resultado diferente de interpolar o TOTAL diretamente entre os dois censos, para cada ano intermediário de cada intervalo.

**Resultado real:** diferença absoluta média de 1,193%, máxima de 3,240%. As duas contas não são equivalentes — esperado, já que cada faixa etária cresce a uma taxa geométrica própria, e a soma de crescimentos distintos não é igual a um único crescimento aplicado ao total. É esse resultado que justifica interpolar por faixa etária (preserva a estrutura demográfica de cada município) em vez de interpolar só o total.

## Custo computacional do K-means

O gargalo do pipeline é o K-means (as etapas anteriores são só soma/razão, O(n)). Valores reais do projeto:

- $n = 256$ (pares Regional-Ano, matriz final)
- $d = 29$ (atributos/colunas finais)
- $k$ testado de 2 a 12 ($K_{min}..K_{max}$), escolhido $k=5$ pelo cotovelo
- $i \le 30$ (`max_iter`; nenhuma execução observada passou de 29 iterações)
- `n_init = 10` (sklearn reinicia o KMeans 10× com centróides diferentes e fica com o melhor resultado)

Complexidade de uma única chamada `KMeans(n_clusters=k)`: $O(n \cdot k \cdot i \cdot d)$; com `n_init`, multiplica por 10. A busca em grade (`busca_em_grade_k`) roda isso para 11 valores de $k$ × 5 sementes = 55 combinações, cada uma já com seu próprio `n_init=10` interno — custo total da ordem de $55 \times 10 \times n \cdot \bar{k} \cdot i \cdot d$.

## Onde proporção/frequência/média/desvio padrão são de fato usados no código

- **Proporção:** só como diagnóstico de qualidade de dado — `proporcao_nula` em `descartar_colunas_com_muitos_nulos` (K-means, decide quais colunas descartar pelo limiar de 5% de nulos) e nas células de diagnóstico do mesmo notebook. Não é usada como medida analítica/epidemiológica em nenhum outro lugar do código.
- **Frequência:** única ocorrência é `FREQUENCIA_ROTULO_LINHA_CATEGORICA`, parâmetro de espaçamento de rótulos no eixo X dos gráficos de linha (a cada quantos anos mostrar o marcador) — puramente visual, não é a "frequência" estatística que fundamenta a taxa.
- **Média/mediana:** aparecem em `mortalidade_tratamento.ipynb` e `mamografia_tratamento.ipynb` só como estatística descritiva de inspeção pós-processamento (sem uso posterior); e em `calcular_caracterizacao_por_cluster` (K-means) como `MEDIA_GERAL`/`MEDIA_CLUSTER` — essa sim é analítica, usada na caracterização dos clusters.
- **Desvio padrão:** só em dois lugares — a mesma inspeção descritiva de Mortalidade/Mamografia (`.std()`, sem uso posterior) e no cálculo do coeficiente de variação da inércia entre sementes (estabilidade do K-means) — única vez que média e desvio padrão são usados juntos como coeficiente de variação.
- **Importante:** a padronização do K-means (RobustScaler) usa **mediana e IQR**, não média/desvio padrão.

Então proporção e frequência, no texto da monografia, servem só como referencial teórico pra definir "taxa" — não aparecem como medidas calculadas/reportadas em nenhuma outra etapa da análise.

## Divisão dos valores nos mapas (legenda de cor e de bolha)

Não é um corte em intervalos numéricos iguais. É **por quantil** (`pd.qcut`, em `_classificar_em_faixas_por_quantil`, `Avaliação e Apresentação/utilitarios_graficos_populacionais.py`): corta os valores das 28 Regionais em `N_FAIXAS_COR = 5` (cor) ou `N_DEGRAUS_BOLHA = 5` (tamanho de bolha) grupos com a **mesma quantidade de Regionais em cada faixa**, não a mesma amplitude numérica — por isso os intervalos de cada faixa da legenda têm larguras diferentes entre si. Só se `qcut` falhar (poucos valores distintos, cortes duplicados) é que cai para `pd.cut` (intervalo igual). As cores vêm de amostrar a escala de cor em pontos igualmente espaçados (`pcolors.sample_colorscale`); o tamanho de cada bolha vem de `np.linspace` entre o tamanho mínimo e máximo configurado, nas mesmas 5 faixas por quantil.
