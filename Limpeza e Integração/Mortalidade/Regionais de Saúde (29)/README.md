# Mortalidade - Regionais de Saúde (29)

## Estrutura da pasta

```
Regionais de Saúde (29)/
├── main.py                       # extração cidade a cidade (uso interativo)
├── auditoria_csv_cidades.py      # audita CSVs faltantes por regional
└── Regionais - Cidades/
    └── <Cidade-UF>/                    # uma subpasta por cidade-sede de regional (28 cidades)
        ├── AAAA-<Cidade>-UF.csv        # um CSV por ano com mortes registradas
        └── gemini.py                   # apenas em Alfenas-MG/ (ver observação abaixo)
```

## O que esta pasta faz

Extrai do Atlas de Mortalidade por Câncer (INCA) o número de óbitos por câncer de mama (CID C50) em mulheres, por faixa etária, para a cidade-sede de cada uma das 28 regionais de saúde de Minas Gerais.

## Resumo das operações

`main.py` segue a mesma lógica de `Mortalidade/Cidades Atendidas por Cada Regional/main_extracao.py`: abre a consulta do Atlas de Mortalidade com Selenium, pede que o usuário configure manualmente os filtros na página e confirme no terminal, e então percorre um intervalo de anos (`ANO_INICIAL` a `ANO_FINAL`, editado por execução) selecionando um ano por vez, clicando em "OK" e depois no botão de gerar CSV, baixando o resultado e salvando em `Regionais - Cidades/<Cidade-UF>/<ano>-<Cidade>-<UF>.csv`. A cidade-alvo é definida manualmente no topo do script (variável `CIDADE`) e o script é reexecutado uma vez por cidade-sede.

`auditoria_csv_cidades.py` não extrai dados; ele varre `Regionais - Cidades/` para as 28 cidades-sede esperadas e verifica, para o período 1979-2024, quais anos não têm CSV salvo, reportando por cidade a lista de anos faltantes.

**Observação sobre `Regionais - Cidades/Alfenas-MG/gemini.py`**: é uma variação isolada do script de extração, presente apenas nessa subpasta. Usa um caminho de saída genérico (`/home/usuario/Documentos/novo/Código`) que não corresponde à estrutura deste repositório, o que indica ser um rascunho/experimento gerado com assistência de IA e não integrado ao fluxo de extração usado nas demais cidades.
