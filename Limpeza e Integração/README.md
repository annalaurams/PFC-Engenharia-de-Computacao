# Limpeza e Integração

Primeira etapa do KDD deste projeto: extração e coleta dos dados brutos, de fontes públicas heterogêneas, para as próximas etapas (Seleção e Transformação, Tratamento, Mineração de Dados).

## Estrutura da pasta

```
Limpeza e Integração/
├── Casos/                         
│   ├── Ano Diagnóstico/
│   ├── Escolaridade/
│   ├── Faixa Etária/
│   └── Raça-Cor/
├── Hospitais Habilitados/         
├── Mamografia/                     
├── Mortalidade/                    
│   ├── Cidades Atendidas por Cada Regional/
│   └── Regionais de Saúde (29)/
├── Municípios/                     
├── População - Faixa Etária/      
```

## Resumo das operações

O projeto combina duas estratégias de aquisição de dados:

1. **Extração via script (Selenium)** — para fontes que exigem preencher formulários e consultas dinâmicas: Casos (TabNet RHC/INCA), Mamografia (TabNet DATASUS/SISCAN) e Mortalidade (Atlas de Mortalidade INCA). Cada script abre um navegador Chrome controlado, preenche os filtros da consulta (sempre restritos a câncer de mama, CID C50, em mulheres), aciona a geração do resultado e baixa o CSV gerado, salvando-o em uma pasta `Dados/` (ou equivalente) dentro do domínio correspondente.
2. **Download direto** — para bases já consolidadas em planilha: Hospitais Habilitados, Municípios e População - Faixa Etária, baixados prontos de fontes públicas (Ministério da Saúde, SES-MG e IBGE) e usados sem alteração nesta etapa.



## Domínios de dados

## Domínios de dados

| Domínio | Formato | Período | Fonte | Extração |
|---|---|---|---|---|
| [Casos](Casos/README.md) | CSV, um por ano e por segmento | 1985-2023 | RHC | Extração via script (RHC/INCA) |
| [Hospitais Habilitados](Hospitais%20Habilitados/README.md) | XLSX | 2025 | GOV | Download direto (Ministério da Saúde) |
| [Mamografia](Mamografia/README.md) | CSV, um por ano | 2013-2025 | DATASUS | Extração via script (DATASUS/SISCAN) |
| [Mortalidade](Mortalidade/README.md) | CSV, um por ano e por município | 1979-2024 | INCA | Extração via script (Atlas de Mortalidade INCA) |
| [Municípios](Munic%C3%ADpios/README.md) | XLSX | 2023 (ajuste 2024) | GOV | Download direto (SES-MG) |
| [População - Faixa Etária](Popula%C3%A7%C3%A3o%20-%20Faixa%20Et%C3%A1ria/README.md) | CSV, dois por ano | 1970, 1980, 1991, 2000, 2010, 2022 | IBGE | Download direto (IBGE) |