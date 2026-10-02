# Dados do Câncer de Mama em Minas Gerais por Regional de Saúde

Este repositório disponibiliza, para consulta pública, os dados usados no Projeto Final de Curso (PFC) de Engenharia de Computação sobre o câncer de mama em Minas Gerais, organizados por Regional de Saúde.

Esta branch guarda **somente os dados**: os arquivos como foram extraídos das fontes públicas e as tabelas já tratadas a partir deles. O código e as análises não estão aqui.

## Estrutura das pastas

```
.
└── Dados/
    ├── Dados brutos/            # arquivos extraídos ou baixados, sem alteração, um por variável
    │   ├── Casos/               # Ano Diagnóstico, Escolaridade, Faixa Etária, Raça-Cor
    │   ├── Hospitais Habilitados/
    │   ├── Mamografia/
    │   ├── Mortalidade/         # <Regional>/<Município>-MG/
    │   ├── Municípios/
    │   └── População - Faixa Etária/
    └── Dados estruturados/      # tabelas únicas por variável, já tratadas
        ├── Tratados/            # dados brutos unificados, por município
        ├── Interpolados/        # população por faixa etária de 1970 a 2025
        └── Taxas/               # valores e taxas por 100 mil habitantes, por Regional
```

## O que cada pasta contém

- **Dados brutos**: os arquivos CSV e XLSX originais das fontes (INCA, DATASUS, Ministério da Saúde, SES-MG e IBGE), separados por variável. Detalhes em [Dados/Dados brutos/README.md](Dados/Dados%20brutos/README.md).
- **Dados estruturados**: as tabelas resultantes do tratamento, da interpolação da população e do cálculo das taxas. Detalhes em [Dados/Dados estruturados/README.md](Dados/Dados%20estruturados/README.md).

A descrição geral dos dados, as fontes e as convenções de colunas estão em [Dados/README.md](Dados/README.md).

## Autoria

Anna Laura Moura Santana, Engenharia de Computação.
