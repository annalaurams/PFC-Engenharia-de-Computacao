# Resultados - Análises e Evidências

Esta pasta reúne os notebooks Jupyter para exploração, cruzamento e análise das tabelas consolidadas geradas em [Tratamento/](../Tratamento/README.md).

## 🎯 Objetivo

Usar as tabelas padronizadas para:
- Avaliar padrões temporais e territoriais de câncer de mama em Minas Gerais
- Integrar variáveis de múltiplos domínios (casos, mortalidade, mamografia, hospitais, socioeconômico)
- Gerar evidências para discussão na monografia

## 📓 Notebooks disponíveis

```
Resultados/
├── casos.ipynb                      # Análise de incidência de casos por dimensão
├── mamografia.ipynb                 # Análise de mamografia e rastreamento
├── mortalidade.ipynb                # Análise de mortalidade e taxas
├── hospitais_habilitados.ipynb       # Distribuição e cobertura de hospitais
├── municípios.ipynb                 # Análise territorial e regional
└── README.md
```

### Descrição dos notebooks

| Notebook | Foco | Dados principais |
|----------|------|-----------------|
| **casos.ipynb** | Incidência por ano, escolaridade, faixa etária, raça-cor | Tabela de incidência (Tratamento/) |
| **mamografia.ipynb** | Cobertura, tendência temporal de mamografias | Tabela de mamografia (Tratamento/) |
| **mortalidade.ipynb** | Taxas, distribuição por faixa etária, evolução temporal | Tabela de mortalidade (Tratamento/) |
| **hospitais_habilitados.ipynb** | Distribuição geográfica, cobertura regional | Tabela de hospitais (Tratamento/) |
| **municípios.ipynb** | Análise territorial, agregação por regional | Tabela de municípios (Tratamento/) |

## ▶️ Como executar

### Verificar pré-requisitos

```bash
# 1. Confirme que as bases em Tratamento/ estão atualizadas
ls Tratamento/*/tabela_*.csv

# 2. Instale dependências (se não fez ainda)
uv sync
```

### Abrir e executar notebooks

#### Com Jupyter Notebook (terminal)

```bash
jupyter notebook Resultados/
```

Depois acesse `http://localhost:8888` no navegador e selecione um notebook.

#### Com VS Code

```bash
code Resultados/
```

Abra um `.ipynb` e execute as células com `Shift + Enter`.

#### Com Jupyter Lab

```bash
jupyter lab Resultados/
```

### Executar célula por célula

- **VS Code**: Clique em "Run" acima de cada célula ou `Shift + Enter`
- **Jupyter Notebook/Lab**: Selecione célula e `Ctrl + Enter` (execute) ou `Shift + Enter` (execute e próxima)

### Executar notebook inteiro

```bash
# Com nbconvert (gera HTML)
jupyter nbconvert --to html --execute Resultados/casos.ipynb

# Ou com papermill (executa em background)
papermill Resultados/casos.ipynb output.ipynb
```

## 📌 Boas práticas

1. **Ordem de execução recomendada**:
   - Comece com `casos.ipynb` (understand incidence)
   - Depois `mamografia.ipynb` (screening coverage)
   - Então `mortalidade.ipynb` (outcomes)
   - Explore `hospitais_habilitados.ipynb` (capacity)
   - Finalize com `municípios.ipynb` (territorial synthesis)

2. **Antes de abrir um notebook**:
   - Confirme que Tratamento/ foi executado recentemente
   - Verifique nomes de colunas na documentação de cada domínio
   - Tenha em mente o período temporal (ex: mamografia: 2013-2025)

3. **Durante a análise**:
   - Valide consistência de totais entre agregações
   - Cruze municípios com a base de referência em Tratamento/Municípios/
   - Anote anomalias ou valores faltantes para revisão em Variáveis/

4. **Saídas esperadas**:
   - Gráficos e tabelas para discussão
   - Validação de hipóteses
   - Insumos textuais para a monografia

## 🔗 Fluxo integrado

```
Variáveis/ (dados brutos)
    ↓
Tratamento/ (processa e padroniza)
    ↓
Resultados/ (analisa e cruza) ← VOCÊ ESTÁ AQUI
    ↓
Monografia/ (incorpora evidências)
```

## ⚠️ Troubleshooting

**Erro: "FileNotFoundError: tabela_*.csv"**
- Execute novamente os scripts em Tratamento/

**Erro: "ModuleNotFoundError: pandas, geopandas, etc"**
- Execute `uv sync` na raiz do projeto

**Notebook lento ao renderizar gráficos Plotly**
- Reduza volume de dados com filtros temporais ou regionais
- Use `plotly.graph_objects` em vez de `plotly.express` para performance

## Saídas esperadas

- Tabelas e visões analíticas para apoiar o texto da monografia.
- Validação de consistência entre domínios, como município, ano e faixas ou categorias.
- Evidências para discussão dos fatores associados.