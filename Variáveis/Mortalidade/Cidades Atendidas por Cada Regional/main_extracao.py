import os
import time
import glob
import shutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    TimeoutException,
)

# Configuração

CIDADE = "Unaí"
REGIONAL_SAUDE = "Unaí"
UF = "MG"

PERIODO = [
    1981, 1984, 1987, 1988, 1989, 1990, 1993, 1994, 1996, 1997, 1998, 2001, 2002, 2004, 2005, 2006, 2007, 2008, 2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018, 2019, 2020, 2021, 2022, 2023, 2024
]

DOWNLOADS_PATH = "/home/anna/Downloads"
BASE_PROJECT_PATH = "/home/anna/tcc/variaveis/Variáveis 1/Cidades Atendidas por Cada Regional/Unaí"
PASTA_DESTINO_CIDADE = os.path.join(BASE_PROJECT_PATH, f"{CIDADE}-{UF}")
os.makedirs(PASTA_DESTINO_CIDADE, exist_ok=True)

URL = "https://www.inca.gov.br/MortalidadeWeb/pages/Modelo10/consultar.xhtml"
MAX_TENTATIVAS = 3

os.system("cls" if os.name == "nt" else "clear")

# ________________________________________________________________________________
# Utilidades

def log_status(ano, mensagem, tipo="INFO"):
    cores = {"INFO": "34", "OK": "32", "ERRO": "31", "AVISO": "33"}
    print(f"\033[{cores.get(tipo, '37')}m[{tipo}] Ano {ano} | {mensagem}\033[0m")


def iniciar_driver():
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": DOWNLOADS_PATH,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("detach", True)
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )


def driver_esta_ativo(driver):
    try:
        _ = driver.current_url
        return True
    except Exception:
        return False


def limpar_downloads_temp():
    for f in glob.glob(os.path.join(DOWNLOADS_PATH, "ModeloTabulador_*.csv")):
        try:
            os.remove(f)
        except Exception:
            pass


def select_by_name(driver, name, value_or_text, by="value", timeout=15):
    wait = WebDriverWait(driver, timeout)
    element = wait.until(
        EC.presence_of_element_located((By.CSS_SELECTOR, f'select[name="{name}"]'))
    )
    sel = Select(element)
    if by == "value":
        sel.select_by_value(value_or_text)
    else:
        sel.select_by_visible_text(value_or_text)


def select_by_id(driver, element_id, value_or_text, by="value", timeout=15):
    wait = WebDriverWait(driver, timeout)
    element = wait.until(
        EC.presence_of_element_located((By.ID, element_id))
    )
    sel = Select(element)
    if by == "value":
        sel.select_by_value(value_or_text)
    else:
        sel.select_by_visible_text(value_or_text)


def aguardar_ajax(driver, timeout=10):
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(
                "return document.readyState === 'complete'"
            )
        )
        WebDriverWait(driver, timeout).until(
            lambda d: all(
                not el.is_displayed()
                for el in d.find_elements(By.CSS_SELECTOR, "img.loading")
            )
        )
    except Exception:
        pass

def verificar_erro_campos_obrigatorios(driver):
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
    try:
        elemento = driver.find_element(By.ID, "panelResultado")
        texto = elemento.text
        if "Esta consulta retornou sem resultado" in texto or "retornou sem resultado" in texto:
            return True
    except Exception:
        pass
    return False


def aplicar_filtros(driver, wait):
    try:
        select_by_id(driver, "formModeloTabulador:comboSexo", "2")
        time.sleep(2)

        wait.until(
            EC.element_to_be_clickable((By.XPATH, "//li[contains(text(),'C50 - MAMA')]"))
        ).click()
        time.sleep(1)

        driver.find_element(By.CLASS_NAME, "ui-picklist-button-add").click()
        time.sleep(2)

        select_by_id(driver, "formModeloTabulador:nivelLocalidade", "5")
        time.sleep(3)

        select_by_id(driver, "formModeloTabulador:regiao", "3")
        time.sleep(3)

        select_by_id(driver, "formModeloTabulador:estado", "17")
        time.sleep(3)

        select_by_id(driver, "formModeloTabulador:regionalSaude", REGIONAL_SAUDE, by="text")
        time.sleep(4)

        wait.until(EC.presence_of_element_located((By.ID, "formModeloTabulador:localidades")))
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

        select_by_name(driver, "formModeloTabulador:j_idt155", "2")
        time.sleep(1)
        aguardar_ajax(driver)
        time.sleep(2)

        select_by_id(driver, "formModeloTabulador:opcaoColuna", "2")
        aguardar_ajax(driver, timeout=15)
        time.sleep(3)

        try:
            select_by_id(driver, "formModeloTabulador:idadeFaixaIni", "0")
        except Exception:
            pass

        try:
            select_by_id(driver, "formModeloTabulador:idadeFaixaFim", "999")
        except Exception:
            pass

        time.sleep(1)

        print("\n" + "=" * 80)
        print("Filtros aplicados com sucesso!".center(80))
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n[ERRO] Falha ao aplicar filtros: {e}")
        return False

# ________________________________________________________________________________
# Extração: Processamento e Download


def clicar_ok_com_retry(driver, wait, max_tentativas=5):
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
        for i, estrategia in enumerate(estrategias):
            try:
                btn = estrategia()
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", btn
                )
                time.sleep(0.5)
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", btn)
                return True
            except Exception:
                continue

        if tentativa < max_tentativas - 1:
            time.sleep(3)

    return False

def clicar_gerar_csv_com_retry(driver, wait, max_tentativas=5):
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
        for i, estrategia in enumerate(estrategias):
            try:
                btn = estrategia()
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", btn
                )
                time.sleep(0.5)
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", btn)
                return True
            except Exception:
                continue

        if tentativa < max_tentativas - 1:
            time.sleep(3)

    return False

# ________________________________________________________________________________
# Operações Principais


def executar():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 60)
    driver.get(URL)

    print("\033[1;36m" + "=" * 80)
    print(f"CIDADE: {CIDADE}-{UF} | REGIONAL: {REGIONAL_SAUDE}".center(80))
    print(f"ANOS A EXTRAIR: {PERIODO}".center(80))
    print(f"TOTAL DE ANOS: {len(PERIODO)}".center(80))
    print("=" * 80 + "\033[0m")

    if not aplicar_filtros(driver, wait):
        driver.quit()
        return

    input("\nVerifique os filtros e pressione ENTER para iniciar os downloads\n")

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
                wait = WebDriverWait(driver, 60)
                driver.get(URL)
                time.sleep(3)
                if not aplicar_filtros(driver, wait):
                    print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                    return
                tentativas_erro = 0
                continue

            limpar_downloads_temp()
            log_status(ano, "Selecionando período", "INFO")

            wait.until(
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
            if not clicar_ok_com_retry(driver, wait):
                raise Exception("Falha ao clicar no botão OK após múltiplas tentativas")

            time.sleep(20)

            if verificar_erro_campos_obrigatorios(driver):
                log_status(ano, "Erro de campos obrigatórios! Reconfigurando...", "ERRO")
                driver.refresh()
                time.sleep(3)
                if not aplicar_filtros(driver, wait):
                    print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                    driver.quit()
                    return
                tentativas_erro = 0
                continue

            if verificar_sem_resultado(driver):
                log_status(ano, "Sem dados (1ª verificação). Tentando novamente...", "AVISO")
                if not clicar_ok_com_retry(driver, wait):
                    raise Exception("Falha ao clicar no botão OK na 2ª tentativa")
                time.sleep(15)

                if verificar_erro_campos_obrigatorios(driver):
                    log_status(ano, "Erro de campos obrigatórios! Reconfigurando...", "ERRO")
                    driver.refresh()
                    time.sleep(3)
                    if not aplicar_filtros(driver, wait):
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
            if not clicar_gerar_csv_com_retry(driver, wait):
                raise Exception("Falha ao clicar no botão Gerar CSV após múltiplas tentativas")

            arquivo_encontrado = None
            for _ in range(40):
                arquivos = glob.glob(os.path.join(DOWNLOADS_PATH, "ModeloTabulador_*.csv"))
                if arquivos and not any(
                    f.endswith(".crdownload") for f in os.listdir(DOWNLOADS_PATH)
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
                    if not aplicar_filtros(driver, wait):
                        print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                        driver.quit()
                        return
                    tentativas_erro = 0

        except Exception as e:
            erro_msg = str(e)
            log_status(ano, f"Erro: {erro_msg[:80]}", "ERRO")
            tentativas_erro += 1

            if any(
                p in erro_msg
                for p in [
                    "Connection refused",
                    "HTTPConnectionPool",
                    "invalid session",
                    "Session",
                    "chrome not reachable",
                ]
            ):
                log_status(ano, "Driver/conexão perdida. Reiniciando...", "ERRO")
                try:
                    driver.quit()
                except Exception:
                    pass
                time.sleep(3)
                driver = iniciar_driver()
                wait = WebDriverWait(driver, 60)
                driver.get(URL)
                time.sleep(3)
                if not aplicar_filtros(driver, wait):
                    print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                    return
                tentativas_erro = 0
                continue

            if tentativas_erro >= MAX_TENTATIVAS:
                log_status(ano, "Muitas falhas. Reconfigurando filtros...", "ERRO")
                driver.refresh()
                time.sleep(3)
                if not aplicar_filtros(driver, wait):
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
        a for a in PERIODO if a not in anos_baixados and a not in anos_sem_dados
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
    executar()