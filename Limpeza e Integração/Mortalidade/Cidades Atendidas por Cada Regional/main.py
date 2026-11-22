# Extrai do Mortalidade Web (INCA) os óbitos por câncer de mama (C50) de uma cidade, um CSV por ano.

import glob
import os
import shutil
import time

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import ElementClickInterceptedException, TimeoutException

# Configuração

CIDADE = "Unaí"
REGIONAL_SAUDE = "Unaí"
UF = "MG"

PERIODO = [
    1981, 1984, 1987, 1988, 1989, 1990, 1993, 1994, 1996, 1997,
    1998, 2001, 2002, 2004, 2005, 2006, 2007, 2008, 2009, 2010,
    2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020,
    2021, 2022, 2023, 2024,
]

PASTA_DOWNLOADS = "/home/anna/Downloads"
PASTA_BASE_PROJETO = "/home/anna/tcc/Limpeza e Integração/Mortalidade/Cidades Atendidas por Cada Regional"
PASTA_DESTINO_CIDADE = os.path.join(PASTA_BASE_PROJETO, f"{CIDADE}-{UF}")
os.makedirs(PASTA_DESTINO_CIDADE, exist_ok=True)

URL = "https://www.inca.gov.br/MortalidadeWeb/pages/Modelo10/consultar.xhtml"
MAX_TENTATIVAS = 3

# Filtros da consulta (Mortalidade Web - INCA)
SEXO_ID = "2"              # Feminino
LOCALIZACAO_PRIMARIA_TEXTO = "C50 - MAMA"
NIVEL_LOCALIDADE_ID = "5"  # Município
REGIAO_ID = "3"            # Sudeste
ESTADO_ID = "17"           # Minas Gerais
TIPO_LINHA_ID = "2"        # Linha do tabulador = Ano do óbito
TIPO_COLUNA_ID = "2"       # Coluna do tabulador = Município
FAIXA_ETARIA_INICIAL = "0"
FAIXA_ETARIA_FINAL = "999"  # sem limite superior (todas as idades)

# Utilidades

def log_status(ano, mensagem, tipo="INFO"):
    """Imprime uma linha de log colorida no terminal, identificando o ano e o tipo de evento (INFO/OK/ERRO/AVISO)."""
    cores = {"INFO": "34", "OK": "32", "ERRO": "31", "AVISO": "33"}
    print(f"\033[{cores.get(tipo, '37')}m[{tipo}] Ano {ano} | {mensagem}\033[0m")


def iniciar_driver():
    """Abre o Chrome controlado pelo Selenium, configurado para salvar downloads em PASTA_DOWNLOADS e permanecer aberto (`detach`) após o script terminar."""
    opcoes = webdriver.ChromeOptions()
    preferencias = {
        "download.default_directory": PASTA_DOWNLOADS,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    opcoes.add_experimental_option("prefs", preferencias)
    opcoes.add_experimental_option("detach", True)
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=opcoes
    )


def driver_esta_ativo(driver):
    """Verifica se a sessão do navegador ainda responde (usado para detectar queda de conexão e decidir se precisa reiniciar o driver)."""
    try:
        _ = driver.current_url
        return True
    except Exception:
        return False


def limpar_downloads_temp():
    """Remove CSVs de execuções anteriores da pasta de downloads, para não confundir com o próximo arquivo baixado."""
    for arquivo in glob.glob(os.path.join(PASTA_DOWNLOADS, "ModeloTabulador_*.csv")):
        try:
            os.remove(arquivo)
        except Exception:
            pass


def selecionar_por_nome(driver, nome, valor_ou_texto, por="value", tempo_limite=15):
    """Seleciona uma opção num <select> localizado pelo atributo `name`, por valor ou por texto visível."""
    espera = WebDriverWait(driver, tempo_limite)
    elemento = espera.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f'select[name="{nome}"]'))
    )
    seletor = Select(elemento)
    if por == "value":
        seletor.select_by_value(valor_ou_texto)
    else:
        seletor.select_by_visible_text(valor_ou_texto)


def selecionar_por_id(driver, id_elemento, valor_ou_texto, por="value", tempo_limite=15):
    """Seleciona uma opção num <select> localizado pelo `id`, por valor ou por texto visível."""
    espera = WebDriverWait(driver, tempo_limite)
    elemento = espera.until(
        EC.presence_of_element_located((By.ID, id_elemento))
    )
    seletor = Select(elemento)
    if por == "value":
        seletor.select_by_value(valor_ou_texto)
    else:
        seletor.select_by_visible_text(valor_ou_texto)


def aguardar_ajax(driver, tempo_limite=10):
    """Espera a página terminar de carregar e o indicador de loading (AJAX do site) desaparecer."""
    try:
        WebDriverWait(driver, tempo_limite).until(
            lambda d: d.execute_script(
                "return document.readyState === 'complete'"
            )
        )
        WebDriverWait(driver, tempo_limite).until(
            lambda d: all(
                not el.is_displayed()
                for el in d.find_elements(By.CSS_SELECTOR, "img.loading")
            )
        )
    except Exception:
        pass


def aguardar_resultado_ou_erro(driver, tempo_limite=40):
    """Espera até que o painel de resultado seja preenchido ou apareça a mensagem de campos obrigatórios vazios."""
    def condicao(d):
        try:
            painel = d.find_element(By.ID, "panelResultado")
            if painel.text.strip():
                return True
        except Exception:
            pass
        try:
            msg = d.find_element(By.ID, "formModeloTabulador:msgCamposVazios")
            if msg.text.strip():
                return True
        except Exception:
            pass
        return False

    try:
        WebDriverWait(driver, tempo_limite).until(condicao)
    except TimeoutException:
        pass


def verificar_erro_campos_obrigatorios(driver):
    """Detecta se o site mostrou o aviso de erro de validação (campo obrigatório não preenchido)."""
    try:
        elemento = driver.find_element(By.ID, "formModeloTabulador:msgCamposVazios")
        texto = elemento.text
        if "Atenção! Corrija estes erros" in texto or (
            "campo" in texto.lower() and "obrigatório" in texto.lower()
        ):
            return True
    except Exception:
        pass
    return False


def verificar_sem_resultado(driver):
    """Detecta se o site informou que a consulta não retornou dados para o ano/filtro atual."""
    try:
        elemento = driver.find_element(By.ID, "panelResultado")
        texto = elemento.text
        if "Esta consulta retornou sem resultado" in texto or "retornou sem resultado" in texto:
            return True
    except Exception:
        pass
    return False


def aplicar_filtros(driver, espera):
    """Preenche, na página do tabulador, todos os filtros fixos da consulta (sexo, câncer de mama, localidade, município, layout linha/coluna, faixa etária). Chamada uma vez no início e sempre que a sessão precisa ser reconfigurada após um erro."""
    try:
        # Sexo feminino
        selecionar_por_id(driver, "formModeloTabulador:comboSexo", SEXO_ID)
        time.sleep(2)

        # Localização primária do tumor: C50 - MAMA
        espera.until(
            EC.element_to_be_clickable((By.XPATH, f"//li[contains(text(),'{LOCALIZACAO_PRIMARIA_TEXTO}')]"))
        ).click()
        time.sleep(1)

        driver.find_element(By.CLASS_NAME, "ui-picklist-button-add").click()
        time.sleep(2)

        # Nível de localidade = Município, dentro da região/estado/regional de saúde configurados
        selecionar_por_id(driver, "formModeloTabulador:nivelLocalidade", NIVEL_LOCALIDADE_ID)
        time.sleep(3)

        selecionar_por_id(driver, "formModeloTabulador:regiao", REGIAO_ID)
        time.sleep(3)

        selecionar_por_id(driver, "formModeloTabulador:estado", ESTADO_ID)
        time.sleep(3)

        selecionar_por_id(driver, "formModeloTabulador:regionalSaude", REGIONAL_SAUDE, por="text")
        time.sleep(4)

        # Busca o município exato (nome + UF) na lista de localidades da regional selecionada
        espera.until(EC.presence_of_element_located((By.ID, "formModeloTabulador:localidades")))
        select_municipio = Select(driver.find_element(By.ID, "formModeloTabulador:localidades"))

        municipio_encontrado = False
        for opcao in select_municipio.options:
            if CIDADE in opcao.text and f"- {UF}" in opcao.text:
                select_municipio.select_by_visible_text(opcao.text)
                municipio_encontrado = True
                break

        if not municipio_encontrado:
            print(f"\n[ERRO] Município '{CIDADE}' não encontrado na lista!")
            return False

        time.sleep(2)

        driver.find_element(By.ID, "formModeloTabulador:add").click()
        time.sleep(3)

        # Layout do tabulador: linha = Ano do óbito, coluna = Município
        selecionar_por_nome(driver, "formModeloTabulador:j_idt155", TIPO_LINHA_ID)
        time.sleep(1)
        aguardar_ajax(driver)
        time.sleep(2)

        selecionar_por_id(driver, "formModeloTabulador:opcaoColuna", TIPO_COLUNA_ID)
        aguardar_ajax(driver, tempo_limite=15)
        time.sleep(3)

        # Faixa etária sem limite (todas as idades)
        try:
            selecionar_por_id(driver, "formModeloTabulador:idadeFaixaIni", FAIXA_ETARIA_INICIAL)
        except Exception:
            pass

        try:
            selecionar_por_id(driver, "formModeloTabulador:idadeFaixaFim", FAIXA_ETARIA_FINAL)
        except Exception:
            pass

        time.sleep(1)

        print("\n" + "=" * 80)
        print("Filtros aplicados com sucesso!".center(80))
        print("=" * 80)
        return True

    except Exception as erro:
        print(f"\n[ERRO] Falha ao aplicar filtros: {erro}")
        return False

# Processamento e download

def clicar_ok_com_retry(driver, espera, max_tentativas=5):
    """Clica no botão 'OK' da consulta, tentando várias estratégias de seletor (o site muda o markup entre carregamentos) e repetindo em caso de falha."""
    estrategias = [
        lambda: driver.find_element(
            By.XPATH,
            "//img[contains(@src,'bt_ok.gif')]/.."
        ),
        lambda: driver.find_element(
            By.XPATH,
            "//a[contains(@id,'formModeloTabulador')]//img[contains(@src,'bt_ok.gif')]/.."
        ),
        lambda: driver.find_element(
            By.CSS_SELECTOR,
            "a.ui-commandlink[id*='formModeloTabulador']"
        ),
        lambda: driver.find_element(
            By.XPATH,
            "//a[contains(@onclick,'panelResultado')]"
        ),
    ]

    for tentativa in range(max_tentativas):
        for estrategia in estrategias:
            try:
                botao = estrategia()
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", botao
                )
                time.sleep(0.5)
                try:
                    botao.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", botao)
                return True
            except Exception:
                continue

        if tentativa < max_tentativas - 1:
            time.sleep(3)

    return False


def clicar_gerar_csv_com_retry(driver, espera, max_tentativas=5):
    """Clica no botão 'Gerar CSV' do resultado, tentando várias estratégias de seletor e repetindo em caso de falha."""
    estrategias = [
        lambda: driver.find_element(By.ID, "formModeloTabuladorLinks:j_idt424"),
        lambda: driver.find_element(
            By.XPATH,
            "//button[contains(@id,'formModeloTabuladorLinks')]"
            "//span[contains(text(),'Gerar CSV')]/.."
        ),
        lambda: driver.find_element(
            By.CSS_SELECTOR,
            "button.ui-button[id*='formModeloTabuladorLinks']"
        ),
        lambda: driver.find_element(
            By.XPATH,
            "//span[contains(text(),'Gerar CSV')]/.."
        ),
    ]

    for tentativa in range(max_tentativas):
        for estrategia in estrategias:
            try:
                botao = estrategia()
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", botao
                )
                time.sleep(0.5)
                try:
                    botao.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", botao)
                return True
            except Exception:
                continue

        if tentativa < max_tentativas - 1:
            time.sleep(3)

    return False

# Execução principal

def executar():
    """Laço principal: aplica os filtros uma vez e, para cada ano em PERIODO, consulta e baixa o CSV de óbitos,
    reiniciando o driver ou reconfigurando os filtros quando a sessão cai ou a consulta falha repetidamente."""
    driver = iniciar_driver()
    espera = WebDriverWait(driver, 60)
    driver.get(URL)

    print("\033[1;36m" + "=" * 80)
    print(f"CIDADE: {CIDADE}-{UF} | REGIONAL: {REGIONAL_SAUDE}".center(80))
    print(f"ANOS A EXTRAIR: {PERIODO}".center(80))
    print(f"TOTAL DE ANOS: {len(PERIODO)}".center(80))
    print("=" * 80 + "\033[0m")

    if not aplicar_filtros(driver, espera):
        driver.quit()
        return

    anos_baixados = []
    anos_sem_dados = []
    indice_ano = 0
    tentativas_erro = 0

    while indice_ano < len(PERIODO):
        ano = PERIODO[indice_ano]

        try:
            if not driver_esta_ativo(driver):
                log_status(ano, "Driver inativo. Reiniciando...", "ERRO")
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = iniciar_driver()
                espera = WebDriverWait(driver, 60)
                driver.get(URL)
                time.sleep(3)
                if not aplicar_filtros(driver, espera):
                    print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                    return
                tentativas_erro = 0
                continue

            limpar_downloads_temp()
            log_status(ano, "Selecionando período", "INFO")

            espera.until(
                EC.presence_of_element_located((By.ID, "formModeloTabulador:anoInicio"))
            )
            Select(
                driver.find_element(By.ID, "formModeloTabulador:anoInicio")
            ).select_by_value(str(ano))
            Select(
                driver.find_element(By.ID, "formModeloTabulador:anoFim")
            ).select_by_value(str(ano))
            time.sleep(1)

            log_status(ano, "Processando consulta...", "INFO")
            if not clicar_ok_com_retry(driver, espera):
                raise Exception("Falha ao clicar no botão OK após múltiplas tentativas")

            aguardar_resultado_ou_erro(driver)

            if verificar_erro_campos_obrigatorios(driver):
                log_status(ano, "Erro de campos obrigatórios! Reconfigurando...", "ERRO")
                driver.refresh()
                time.sleep(3)
                if not aplicar_filtros(driver, espera):
                    print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                    driver.quit()
                    return
                tentativas_erro = 0
                continue

            # O site às vezes retorna "sem resultado" por lentidão, não por falta real de dados --
            # por isso a consulta é refeita uma segunda vez antes de aceitar que o ano não tem dados.
            if verificar_sem_resultado(driver):
                log_status(ano, "Sem dados (1ª verificação). Tentando novamente...", "AVISO")
                if not clicar_ok_com_retry(driver, espera):
                    raise Exception("Falha ao clicar no botão OK na 2ª tentativa")
                aguardar_resultado_ou_erro(driver)

                if verificar_erro_campos_obrigatorios(driver):
                    log_status(ano, "Erro de campos obrigatórios! Reconfigurando...", "ERRO")
                    driver.refresh()
                    time.sleep(3)
                    if not aplicar_filtros(driver, espera):
                        print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                        driver.quit()
                        return
                    tentativas_erro = 0
                    continue

                if verificar_sem_resultado(driver):
                    log_status(ano, "Sem dados confirmado após 2ª tentativa", "AVISO")
                    anos_sem_dados.append(ano)
                    indice_ano += 1
                    tentativas_erro = 0
                    continue

            log_status(ano, "Gerando arquivo CSV...", "INFO")
            if not clicar_gerar_csv_com_retry(driver, espera):
                raise Exception("Falha ao clicar no botão Gerar CSV após múltiplas tentativas")

            arquivo_encontrado = None
            for _ in range(40):
                arquivos = glob.glob(os.path.join(PASTA_DOWNLOADS, "ModeloTabulador_*.csv"))
                if arquivos and not any(
                    nome.endswith(".crdownload") for nome in os.listdir(PASTA_DOWNLOADS)
                ):
                    arquivo_encontrado = max(arquivos, key=os.path.getmtime)
                    break
                time.sleep(1)

            if arquivo_encontrado:
                novo_nome = f"{ano}-{CIDADE}-{UF}.csv"
                shutil.move(arquivo_encontrado, os.path.join(PASTA_DESTINO_CIDADE, novo_nome))
                log_status(ano, f"Arquivo salvo: {novo_nome}", "OK")
                anos_baixados.append(ano)
                indice_ano += 1
                tentativas_erro = 0
            else:
                log_status(ano, "Download não completado. Tentando novamente...", "AVISO")
                time.sleep(3)
                tentativas_erro += 1
                if tentativas_erro >= MAX_TENTATIVAS:
                    log_status(ano, "Muitas falhas. Reconfigurando filtros...", "ERRO")
                    driver.refresh()
                    time.sleep(3)
                    if not aplicar_filtros(driver, espera):
                        print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                        driver.quit()
                        return
                    tentativas_erro = 0

        except Exception as erro:
            mensagem_erro = str(erro)
            log_status(ano, f"Erro: {mensagem_erro[:80]}", "ERRO")
            tentativas_erro += 1

            if not driver_esta_ativo(driver):
                log_status(ano, "Driver/conexão perdida. Reiniciando...", "ERRO")
                try:
                    driver.quit()
                except Exception:
                    pass
                time.sleep(3)
                driver = iniciar_driver()
                espera = WebDriverWait(driver, 60)
                driver.get(URL)
                time.sleep(3)
                if not aplicar_filtros(driver, espera):
                    print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                    return
                tentativas_erro = 0
                continue

            if tentativas_erro >= MAX_TENTATIVAS:
                log_status(ano, "Muitas falhas. Reconfigurando filtros...", "ERRO")
                driver.refresh()
                time.sleep(3)
                if not aplicar_filtros(driver, espera):
                    print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                    driver.quit()
                    return
                tentativas_erro = 0
            else:
                log_status(ano, f"Tentativa {tentativas_erro}/{MAX_TENTATIVAS}. Aguardando...", "AVISO")
                time.sleep(5)

    try:
        driver.quit()
    except Exception:
        pass

    print("\n\033[1;32m" + "=" * 80)
    print("EXTRAÇÃO FINALIZADA!".center(80))
    print("=" * 80 + "\033[0m")
    print(f"\nESTATÍSTICAS:")
    print(f"  • Total de anos no período : {len(PERIODO)}")
    print(f"  • CSVs baixados com sucesso: {len(anos_baixados)}")
    print(f"  • Anos sem dados           : {len(anos_sem_dados)}")

    anos_faltantes = [
        ano for ano in PERIODO if ano not in anos_baixados and ano not in anos_sem_dados
    ]

    if anos_baixados:
        print(f"\n  Baixados  : {sorted(anos_baixados)}")
    if anos_sem_dados:
        print(f"  Sem dados : {sorted(anos_sem_dados)}")
    if anos_faltantes:
        print(f"\n  ⚠ FALTARAM: {sorted(anos_faltantes)}")
        print(f"    Execute novamente com PERIODO = {anos_faltantes}")
    else:
        print("\n  ✓ Todos os anos foram processados!")

    print(f"\n  Arquivos salvos em: {PASTA_DESTINO_CIDADE}\n")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    os.system("cls" if os.name == "nt" else "clear")
    executar()