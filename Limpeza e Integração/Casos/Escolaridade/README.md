# Casos - Escolaridade

## Estrutura da pasta

```
Escolaridade/
├── Código/
│   └── main.py   # script de extração
└── Dados/
    └── Escolaridade-AAAA.csv   # um CSV por ano
```

## O que esta pasta faz

Extrai do TabNet do Registro Hospitalar de Câncer (RHC/INCA) o número de casos de câncer de mama (CID C50) em mulheres, em Minas Gerais, cruzando procedência (linha) por nível de escolaridade (coluna), um arquivo por ano.

## Resumo das operações

`main.py` é uma cópia do script usado em `Casos/Ano Diagnóstico`, com a mesma sequência de navegação e preenchimento de formulário via Selenium/JavaScript, mudando apenas a dimensão selecionada na coluna do TabNet (Escolaridade em vez de Ano diagnóstico). Os mesmos filtros fixos se aplicam (sexo = Feminino, UF de procedência = MG, localização primária = C50). Para cada ano da lista, baixa o CSV gerado e salva em `Dados/` como `Escolaridade-<ano>.csv`.
