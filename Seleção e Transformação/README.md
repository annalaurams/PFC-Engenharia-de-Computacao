# Seleção e Transformação

Notebooks Jupyter que consolidam os dados brutos extraídos em `Limpeza e Integração` em tabelas por município, uma dimensão por domínio — e, no caso da população, também estimam valores para anos sem censo e calculam taxas por 100 mil habitantes.

## Estrutura da pasta

```
Seleção e Transformação/
├── Casos/
├── Hospitais/
├── Mamografias/
├── Mortalidade/
├── Municípios/
└── População/
```

## O que cada subpasta faz

- **Casos**: consolida casos de câncer de mama do RHC/INCA por município, com regional de saúde. Ver [Casos/README.md](Casos/README.md).
- **Hospitais**: filtra hospitais habilitados para MG e junta com código IBGE. Ver [Hospitais/README.md](Hospitais/README.md).
- **Mamografias**: consolida exames de mamografia por município, ano e faixa etária. Ver [Mamografias/README.md](Mamografias/README.md).
- **Mortalidade**: consolida óbitos por câncer de mama por município, ano e faixa etária. Ver [Mortalidade/README.md](Mortalidade/README.md).
- **Municípios**: junta a base territorial de municípios com a regional de saúde de cada um. Ver [Municípios/README.md](Munic%C3%ADpios/README.md).
- **População**: consolida população por município/ano censitário, estima população para os demais anos e calcula taxas por 100 mil habitantes para as demais variáveis. Ver [População/README.md](Popula%C3%A7%C3%A3o/README.md).

