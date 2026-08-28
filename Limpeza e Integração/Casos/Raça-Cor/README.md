# Casos - Raça-Cor

## Estrutura da pasta

```
Raça-Cor/
├── Código/
│   └── main_extracao.py   # script de extração via Selenium
└── Dados/
    └── RacaCor-AAAA.csv   # um CSV por ano
```

## O que esta pasta faz

Extrai do TabNet do Registro Hospitalar de Câncer (RHC/INCA) o número de casos de câncer de mama (CID C50) em mulheres, em Minas Gerais, cruzando procedência (linha) por raça-cor (coluna), um arquivo por ano.

## Resumo das operações

`main_extracao.py` segue a mesma estrutura dos demais scripts de `Casos` (navegação e preenchimento do formulário do TabNet via Selenium/JavaScript), selecionando Raça-Cor como dimensão da coluna. Os filtros fixos (sexo = Feminino, UF de procedência = MG, localização primária = C50) e a lista de anos são os mesmos usados nos outros scripts de `Casos`. Cada CSV baixado é salvo em `Dados/` como `RacaCor-<ano>.csv`.
