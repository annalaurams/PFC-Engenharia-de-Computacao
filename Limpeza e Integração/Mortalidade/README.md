# Mortalidade

## Estrutura da pasta

```
Mortalidade/
├── Cidades Atendidas por Cada Regional/   # mortalidade por município, agrupada por regional
```

## O que cada subpasta faz

- **Cidades Atendidas por Cada Regional**: extrai a mortalidade por câncer de mama de todos os municípios de MG, organizados pela regional de saúde que os atende. Ver [Cidades Atendidas por Cada Regional/README.md](Cidades%20Atendidas%20por%20Cada%20Regional/README.md).


## Resumo das operações

Ambas as subpastas extraem dados do Atlas de Mortalidade por Câncer do INCA via Selenium, filtrando sempre por câncer de mama (CID C50) em mulheres. "Cidades Atendidas por Cada Regional" cobre todos os municípios atendidos por cada regional, um conjunto que inclui as cidades-sede. O script de extração contém a configuração manual da cidade/regional-alvo no topo do arquivo, confirmação do usuário no terminal, e laço sobre os anos disponíveis (1979-2024) baixando um CSV por ano.
