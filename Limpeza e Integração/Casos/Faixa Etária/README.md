# Casos - Faixa Etária

## Estrutura da pasta

```
Faixa Etária/
├── Código/
│   └── main.py   # script de extração
└── Dados/
    └── Faixa-Etaria-AAAA.csv   # um CSV por ano
```

## O que esta pasta faz

Extrai do TabNet do Registro Hospitalar de Câncer (RHC/INCA) o número de casos de câncer de mama (CID C50) em mulheres, em Minas Gerais, cruzando procedência (linha) por faixa etária (coluna), um arquivo por ano.

## Resumo das operações

`main.py` segue a mesma estrutura dos demais scripts de `Casos` (navegação e preenchimento do formulário do TabNet via Selenium/JavaScript), selecionando Faixa Etária como dimensão da coluna. Os filtros fixos (sexo = Feminino, UF de procedência = MG, localização primária = C50) e a lista de anos são os mesmos. O script define como pasta de saída um caminho de `Downloads` fora do repositório (`~/Downloads/INCA_Mama_MG`), diferente dos demais scripts da pasta `Casos`, que gravam direto em `Dados/` — os arquivos hoje presentes em `Dados/` foram movidos para lá manualmente ou por execução com o caminho ajustado. Cada CSV baixado é salvo como `Faixa-Etaria-<ano>.csv`.
