# Mortalidade - Cidades Atendidas por Cada Regional

## Estrutura da pasta

```
Cidades Atendidas por Cada Regional/
├── main.py                          # extração cidade a cidade 
└── <Regional>/                                # uma subpasta por Unidade Regional de Saúde (28 regionais)
    └── <Município-UF>/                        # uma subpasta por município atendido por aquela regional
        └── AAAA-<Município>-UF.csv            # um CSV por ano com mortes registradas
```

Cada uma das 28 regionais (Alfenas, Barbacena, Belo Horizonte, Coronel Fabriciano, Diamantina, Divinópolis, Governador Valadares, Itabira, Ituiutaba, Januária, Juiz de Fora, Leopoldina, Manhumirim, Montes Claros, Passos, Patos de Minas, Pedra Azul, Pirapora, Ponte Nova, Pouso Alegre, São João Del Rei, Sete Lagoas, Teófilo Otoni, Ubá, Uberaba, Uberlândia, Unaí, Varginha) tem uma subpasta com uma subpasta por município que ela atende, cada uma contendo os CSVs anuais de mortalidade daquele município.

## O que esta pasta faz

Extrai do Atlas de Mortalidade por Câncer (INCA) o número de óbitos por câncer de mama (CID C50) em mulheres, por faixa etária, para cada município de Minas Gerais, organizado pela regional de saúde que o atende.

## Resumo das operações

`main.py` abre com Selenium a consulta do Atlas de Mortalidade (`inca.gov.br/MortalidadeWeb`), aplica os filtros fixos (sexo feminino, localização primária C50-MAMA, nível de localidade = município, região = Sudeste, estado = MG, faixa etária completa) e seleciona a regional de saúde e o município configurados no topo do arquivo (variáveis `CIDADE` e `REGIONAL_SAUDE`, editadas manualmente antes de cada execução). Depois de o usuário confirmar os filtros na tela, o script percorre a lista de anos definida em `PERIODO`, seleciona o intervalo de um ano por vez, aciona os botões "OK" e "Gerar CSV" (com múltiplas estratégias de localização de botão e novas tentativas em caso de falha), aguarda o download e move o CSV para a subpasta `<Regional>/<Município-UF>/` com o nome `<ano>-<Município>-<UF>.csv`. O script trata casos de "sem resultado" e reinicia o navegador se a sessão cair.
