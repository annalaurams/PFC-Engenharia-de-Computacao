# Mortalidade

## Estrutura da pasta

```
Mortalidade/
├── Cidades Atendidas por Cada Regional/   # mortalidade por município, agrupada por regional
└── Regionais de Saúde (29)/               # mortalidade apenas nas 28 cidades-sede de regional
```

## O que cada subpasta faz

- **Cidades Atendidas por Cada Regional**: extrai a mortalidade por câncer de mama de todos os municípios de MG, organizados pela regional de saúde que os atende. Ver [Cidades Atendidas por Cada Regional/README.md](Cidades%20Atendidas%20por%20Cada%20Regional/README.md).
- **Regionais de Saúde (29)**: extrai a mortalidade por câncer de mama apenas das cidades-sede de cada regional de saúde (não dos demais municípios atendidos por elas). Ver [Regionais de Saúde (29)/README.md](Regionais%20de%20Sa%C3%BAde%20%2829%29/README.md).

O nome da pasta ("29") não corresponde à contagem real encontrada nos dados: tanto `Cidades Atendidas por Cada Regional/` quanto `Regionais - Cidades/` têm 28 regionais/cidades-sede, não 29.

## Resumo das operações

Ambas as subpastas extraem dados do Atlas de Mortalidade por Câncer do INCA via Selenium, filtrando sempre por câncer de mama (CID C50) em mulheres. A diferença é o escopo: "Regionais de Saúde (29)" cobre só a cidade-sede de cada regional, enquanto "Cidades Atendidas por Cada Regional" cobre todos os municípios atendidos por cada regional — um superconjunto que inclui as cidades-sede. Os scripts de extração das duas subpastas são variações do mesmo padrão: configuração manual da cidade/regional-alvo no topo do arquivo, confirmação do usuário no terminal, e laço sobre os anos disponíveis (1979-2024) baixando um CSV por ano.
