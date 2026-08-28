# Mamografia

## Estrutura da pasta

```
Mamografia/
├── Código/
│   └── main.py   # script de extração via Selenium + requests
└── Dados/
    └── mamografia_AAAA.csv   # um CSV por ano (2013-2025)
```

## O que esta pasta faz

Extrai do TabNet do DATASUS (SISCAN) o número de exames de mamografia realizados por município de Minas Gerais e faixa etária, um arquivo por ano.

## Resumo das operações

`Código/main.py` abre com Selenium a consulta de mamografia do SISCAN em `tabnet.datasus.gov.br`, seleciona nos filtros da página "Munic.da un.saúde" (linha), "Faixa etária" (coluna), "Exames" (conteúdo) e o ano desejado, além de sexo feminino e "todas as categorias" nos filtros adicionais quando disponíveis. Depois de clicar em "Mostra", troca para a janela de resultado, localiza o link "Salva como CSV" e baixa o arquivo reaproveitando os cookies da sessão do navegador via `requests` (em vez do download nativo do Chrome), salvando o resultado em `Dados/mamografia_<ano>.csv`. O script aceita argumentos de linha de comando para escolher os anos, rodar sem interface gráfica (`--headless`) e customizar diretórios de download/saída; por padrão cobre do ano atual até 2013.
