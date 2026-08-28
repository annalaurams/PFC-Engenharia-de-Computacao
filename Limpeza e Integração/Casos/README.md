# Casos

## Estrutura da pasta

```
Casos/
├── Ano Diagnóstico/   
├── Escolaridade/       
├── Faixa Etária/       
└── Raça-Cor/           
```

## O que cada subpasta faz

- **Ano Diagnóstico**: número de casos de câncer de mama por ano de diagnóstico. Ver [Ano Diagnóstico/README.md](Ano%20Diagn%C3%B3stico/README.md).
- **Escolaridade**: número de casos de câncer de mama por nível de escolaridade da paciente. Ver [Escolaridade/README.md](Escolaridade/README.md).
- **Faixa Etária**: número de casos de câncer de mama por faixa etária da paciente. Ver [Faixa Etária/README.md](Faixa%20Et%C3%A1ria/README.md).
- **Raça-Cor**: número de casos de câncer de mama por raça-cor da paciente. Ver [Raça-Cor/README.md](Ra%C3%A7a-Cor/README.md).

## Resumo das operações

As quatro subpastas extraem dados do mesmo sistema, o TabNet do Registro Hospitalar de Câncer (RHC/INCA), filtrando sempre por câncer de mama (CID C50), sexo feminino e UF de procedência = MG. Cada subpasta usa um script de extração próprio (`Código/main_extracao.py`), praticamente idêntico entre si, mudando apenas a dimensão selecionada na coluna da consulta (ano diagnóstico, escolaridade, faixa etária ou raça-cor). Cada script percorre os anos disponíveis (1985-2023, com exceções de anos sem dados), baixa um CSV por ano via Selenium e salva em `Dados/`.
