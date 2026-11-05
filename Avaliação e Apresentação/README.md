# Avaliação e Apresentação

## Estrutura da pasta

```
Avaliação e Apresentação/
├── caminho_utilitarios.py                            # resolve o caminho até utilitarios_comuns.py (Seleção e Transformação/População)
├── configuracao_layout_graficos.py                   # estilo e paleta compartilhados dos gráficos
├── utilitarios_graficos_populacionais.py             # funções de mapas, heatmaps e gráficos de linha
├── conferir.ipynb                                    # notebook avulso de conferência manual
├── heatmap_regional_por_ano.ipynb                    # heatmap Regional x Ano
├── linha_multiplos_paineis_casos_categoricos.ipynb   # gráficos de linha por categoria (escolaridade, raça/cor, faixa etária)
├── linha_populacao_interpolacao_extrapolacao.ipynb   # gráfico de linha da população interpolada/extrapolada
└── mapa_regional_valores_absolutos.ipynb             # mapas coropléticos por Regional de Saúde
```

## Sobre esta etapa

Última etapa do KDD do projeto. Lê as tabelas de taxa (`Seleção e Transformação/População/Taxa`) e a população interpolada/extrapolada (`Seleção e Transformação/População/Interpolação e Extrapolação`) para produzir mapas, heatmaps e gráficos de linha usados na análise exploratória e na monografia. Os notebooks não geram CSV nem XLSX; as figuras (PNG, SVG, HTML) produzidas em cada execução não são versionadas no repositório.

`caminho_utilitarios.py` resolve o caminho até `utilitarios_comuns.py` (em `Seleção e Transformação/População`), reaproveitado aqui para manter a mesma definição de faixas etárias e constantes usada nas etapas anteriores. `configuracao_layout_graficos.py` centraliza cores, fontes e demais parâmetros visuais comuns a todos os gráficos. `utilitarios_graficos_populacionais.py` reúne as funções de montagem de mapas coropléticos, heatmaps e gráficos de linha usadas pelos notebooks desta pasta.

`conferir.ipynb` é um notebook avulso de conferência manual pontual (não faz parte do fluxo de geração de gráficos).

## Fluxo geral

```
Seleção e Transformação / População / Taxa (taxas por 100 mil habitantes)
Seleção e Transformação / População / Interpolação e Extrapolação (população estimada)
    ↓
Avaliação e Apresentação (mapas, heatmaps e gráficos de linha)
```
