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

# ===================== CONFIGURAÇÕES =====================
CIDADE = "Diamantina"
UF = "MG"
ANO_INICIAL = 1979
ANO_FINAL = 2024

DOWNLOADS_PATH = "/home/usuario/Downloads"
BASE_PROJECT_PATH = "/home/usuario/Documentos/PFC I/Código"
PASTA_DESTINO_CIDADE = os.path.join(BASE_PROJECT_PATH, f"{CIDADE}-{UF}")
os.makedirs(PASTA_DESTINO_CIDADE, exist_ok=True)

URL = "https://www.inca.gov.br/MortalidadeWeb/pages/Modelo10/consultar.xhtml"

# ===================== AUXILIARES =====================
def log_status(ano, msg, tipo="INFO"):
    cores = {"INFO": "34", "OK": "32", "ERRO": "31", "AVISO": "33"}
    print(f"\033[{cores[tipo]}m[{tipo}] Ano {ano} | {msg}\033[0m")

def iniciar_driver():
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": DOWNLOADS_PATH}
    options.add_experimental_option("prefs", prefs)
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

def limpar_downloads_temp():
    for f in glob.glob(os.path.join(DOWNLOADS_PATH, "ModeloTabulador_*.csv")):
        try:
            os.remove(f)
        except:
            pass

def existe_mensagem_sem_resultado(driver):
    try:
        driver.find_element(
            By.XPATH,
            "//span[contains(text(),'Esta consulta retornou sem resultado')]"
        )
        return True
    except:
        return False

def existe_mensagem_erro(driver):
    try:
        driver.find_element(By.ID, "formModeloTabulador:msgCamposVazios")
        return True
    except:
        return False

def corrigir_campos_obrigatorios(driver, wait):
    log_status("—", "Corrigindo campos obrigatórios", "AVISO")

    # Reaplicar CID
    cid = wait.until(EC.presence_of_element_located((
        By.XPATH, "//li[contains(text(),'C50 - MAMA')]"
    )))
    cid.click()
    time.sleep(0.5)

    btn_add = driver.find_element(By.XPATH, "//span[text()='Adicionar']")
    btn_add.click()
    time.sleep(1)

    # Sexo: Masculino → Feminino
    sexo = Select(driver.find_element(By.ID, "formModeloTabulador:comboSexo"))
    sexo.select_by_value("1")
    time.sleep(0.5)
    sexo.select_by_value("2")

    # Formato: Gráfico linha → Tabela
    formato = Select(driver.find_element(
        By.ID,
        "formModeloTabulador:formatoLocalidadeNacionalOuRegiao"
    ))
    formato.select_by_value("3")
    time.sleep(0.5)
    formato.select_by_value("1")

# ===================== MOTOR PRINCIPAL =====================
def executar():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40)
    driver.get(URL)

    input("\n[!] Configure os filtros iniciais e pressione ENTER...")

    ano = ANO_INICIAL
    while ano <= ANO_FINAL:
        tentativas = 0
        sucesso = False

        while tentativas < 2 and not sucesso:
            try:
                limpar_downloads_temp()

                # Seleção do ano
                Select(driver.find_element(By.ID, "formModeloTabulador:anoInicio")).select_by_value(str(ano))
                Select(driver.find_element(By.ID, "formModeloTabulador:anoFim")).select_by_value(str(ano))

                # OK
                driver.find_element(By.ID, "formModeloTabulador:j_idt202").click()
                time.sleep(5)

                # Corrigir erros obrigatórios
                if existe_mensagem_erro(driver):
                    corrigir_campos_obrigatorios(driver, wait)
                    driver.find_element(By.ID, "formModeloTabulador:j_idt202").click()
                    time.sleep(5)

                # Sem resultado
                if existe_mensagem_sem_resultado(driver):
                    tentativas += 1
                    log_status(ano, f"Sem resultado (tentativa {tentativas}/2)", "AVISO")
                    continue

                # Tentar localizar botão CSV
                try:
                    # Espera a tabela de resultado existir (sinal de que o backend respondeu)
                wait.until(EC.presence_of_element_located(
                    (By.ID, "formModeloTabulador:tabelaResultado")
                ))

                # Localiza o botão CSV SEM depender de clickable
                btn_csv = wait.until(EC.presence_of_element_located(
                    (By.ID, "formModeloTabuladorLinks:j_idt398")
                ))

                # Scroll até o botão (isso é CRÍTICO)
                driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn_csv)
                time.sleep(1)

                # Clique JS direto (PrimeFaces aceita)
                driver.execute_script("""
                    arguments[0].dispatchEvent(new MouseEvent('click', {
                        bubbles: true,
                        cancelable: true,
                        view: window
                    }));
                """, btn_csv)

                log_status(ano, "Clique no Gerar CSV executado", "INFO")

                except:
                    tentativas += 1
                    log_status(ano, f"CSV não disponível (tentativa {tentativas}/2)", "AVISO")
                    continue

            

                # Espera download
                arquivo = None
                for _ in range(30):
                    arquivos = glob.glob(os.path.join(DOWNLOADS_PATH, "ModeloTabulador_*.csv"))
                    if arquivos and not any(f.endswith(".crdownload") for f in os.listdir(DOWNLOADS_PATH)):
                        arquivo = max(arquivos, key=os.path.getmtime)
                        break
                    time.sleep(1)

                if arquivo:
                    nome = f"{ano}-{CIDADE}-{UF}.csv"
                    shutil.move(arquivo, os.path.join(PASTA_DESTINO_CIDADE, nome))
                    log_status(ano, "CSV salvo com sucesso", "OK")
                    sucesso = True

            except Exception:
                tentativas += 1
                log_status(ano, f"Erro inesperado ({tentativas}/2)", "ERRO")
                time.sleep(5)

        if not sucesso:
            log_status(ano, "Ano sem tabela disponível", "AVISO")

        ano += 1

    print("\n\033[1;32m[✓] Extração finalizada!\033[0m")

if __name__ == "__main__":
    executar()
