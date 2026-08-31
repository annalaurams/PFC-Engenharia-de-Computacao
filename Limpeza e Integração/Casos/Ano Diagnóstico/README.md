# Casos - Ano Diagnóstico

## Estrutura da pasta

```
Ano Diagnóstico/
├── Código/
│   └── main.py   # script de extração 
└── Dados/
    └── AnoDiagnostico-AAAA.csv   # um CSV por ano (1985-2023)
```

## O que esta pasta faz

Extrai do TabNet do Registro Hospitalar de Câncer (RHC/INCA) o número de casos de câncer de mama (CID C50) em mulheres, em Minas Gerais, cruzando procedência (linha) por ano de diagnóstico (coluna), um arquivo por ano.

## Resumo das operações

`main.py` abre o TabNet do RHC (irhc.inca.gov.br) com Selenium/Chrome headless-capaz, navega até o formulário de consulta, e para cada ano da lista (1985-2023, excluindo os anos sem dados disponíveis) preenche os filtros via JavaScript injetado (linha = Procedência, coluna = Ano diagnóstico, sexo = Feminino, UF de procedência = MG, localização primária = C50), clica em "Mostra" para gerar a tabela, baixa o CSV resultante e move para `Dados/` com o nome `AnoDiagnostico-<ano>.csv`. Se algum ano falha, o script tenta voltar ao formulário e segue para o próximo ano em vez de interromper a extração inteira.
