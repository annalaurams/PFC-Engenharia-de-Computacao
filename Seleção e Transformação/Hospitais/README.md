# Seleção e Transformação - Hospitais

## Estrutura da pasta

```
Hospitais/
├── hospitais_tratamento.ipynb          # notebook de tratamento
└── tabela_hospitais_habilitados.csv    # hospitais de MG, com código IBGE do município
```

## O que esta pasta faz

Filtra as planilhas nacionais de hospitais habilitados (extraídas em `Limpeza e Integração/Hospitais Habilitados`) para os estabelecimentos de Minas Gerais e junta com o código IBGE do município.

## Resumo das operações

`hospitais_tratamento.ipynb` é a versão atualizada e documentada da lógica de `Tratamento/Hospitais/main.py` (ver [../README.md](../README.md) para a relação entre as duas pastas). Lê as três planilhas de origem (oncologia, reconstrução mamária, tratamento sincrônico), filtra cada uma para `UF == "MG"`, une as três com uma coluna `TIPO` indicando a origem de cada linha, remove colunas administrativas irrelevantes e adiciona o código IBGE via join com a tabela de municípios, normalizando nomes para casar as duas fontes. O resultado é salvo em `tabela_hospitais_habilitados.csv`, seguido de uma seção de inspeção (nulos, amostra) que não existe no script equivalente.
