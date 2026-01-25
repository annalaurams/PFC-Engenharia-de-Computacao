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
CIDADE = "Pedra Azul"
UF = "MG"
ANO_INICIAL = 1979
ANO_FINAL = 2024

DOWNLOADS_PATH = "/home/usuario/Downloads"
BASE_PROJECT_PATH = "/home/usuario/Documentos/PFC I/Código"
PASTA_DESTINO_CIDADE = os.path.join(BASE_PROJECT_PATH, f"{CIDADE}-{UF}")

os.makedirs(PASTA_DESTINO_CIDADE, exist_ok=True)
URL = "https://www.inca.gov.br/MortalidadeWeb/pages/Modelo10/consultar.xhtml"

# ===================== AUXILIARES =====================
def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def log_status(ano, mensagem, tipo="INFO"):
    cores = {"INFO": "34", "OK": "32", "ERRO": "31", "AVISO": "33"}
    print(f"\033[{cores.get(tipo, '37')}m[{tipo}] Ano {ano} | {mensagem}\033[0m")

def iniciar_driver():
    options = webdriver.ChromeOptions()
    prefs = {"download.default_directory": DOWNLOADS_PATH}
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("detach", True)
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)

def limpar_downloads_temp():
    for f in glob.glob(os.path.join(DOWNLOADS_PATH, "ModeloTabulador_*.csv")):
        try: os.remove(f)
        except: pass

# ===================== MOTOR PRINCIPAL =====================
def executar():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 40) # Tempo maior para o servidor do INCA
    
    driver.get(URL)
    limpar_tela()
    print("\033[1;36m" + "="*65)
    print(f" EXTRATOR CORRIGIDO: {CIDADE}-{UF} ".center(65))
    print("="*65 + "\033[0m")
    
    input(f"\n[!] Configure os filtros e pressione ENTER...")

    ano = ANO_INICIAL
    while ano <= ANO_FINAL:
        try:
            limpar_downloads_temp()
            
            # 1. Seleção de Anos
            wait.until(EC.presence_of_element_located((By.ID, "formModeloTabulador:anoInicio")))
            Select(driver.find_element(By.ID, "formModeloTabulador:anoInicio")).select_by_value(str(ano))
            Select(driver.find_element(By.ID, "formModeloTabulador:anoFim")).select_by_value(str(ano))

            # 2. Clique no OK e Espera de Processamento
            driver.find_element(By.ID, "formModeloTabulador:j_idt202").click()
            log_status(ano, "Aguardando resposta do servidor (pode demorar)...", "INFO")
            
            # Espera o 'loading' sumir (o PrimeFaces usa um dialog de aguarde)
            time.sleep(5) # Delay inicial para o dialog aparecer

            # 3. Clique no CSV
            btn_csv = wait.until(EC.element_to_be_clickable((By.ID, "formModeloTabuladorLinks:j_idt398")))
            driver.execute_script("arguments[0].click();", btn_csv)
            
            # 4. Monitoramento do Download
            arquivo_encontrado = None
            for _ in range(30): # 30 segundos de espera pelo arquivo
                arquivos = glob.glob(os.path.join(DOWNLOADS_PATH, "ModeloTabulador_*.csv"))
                if arquivos:
                    # Garantir que não é um download incompleto (.crdownload)
                    if not any(f.endswith(".crdownload") for f in os.listdir(DOWNLOADS_PATH)):
                        arquivo_encontrado = max(arquivos, key=os.path.getmtime)
                        break
                time.sleep(1)
            
            if arquivo_encontrado:
                novo_nome = f"{ano}-{CIDADE}-{UF}.csv"
                shutil.move(arquivo_encontrado, os.path.join(PASTA_DESTINO_CIDADE, novo_nome))
                log_status(ano, f"Salvo: {novo_nome}", "OK")
                ano += 1 # Sucesso, vai para o próximo
            else:
                log_status(ano, "Timeout no download. Tentando novamente este ano...", "AVISO")
                # Não incrementa o ano para tentar de novo

        except Exception as e:
            log_status(ano, f"Erro de conexão ou sistema. Tentando recuperar...", "ERRO")
            time.sleep(5)
            if "HTTPConnectionPool" in str(e) or "invalid session id" in str(e):
                driver.quit()
                driver = iniciar_driver()
                driver.get(URL)
                input("[!] Sessão perdida. Reconfigure e dê ENTER...")
            else:
                resp = input("\n[1] Tentar de novo | [2] Pular ano: ")
                if resp == "2": ano += 1

    print("\n\033[1;32m[✓] Processo concluído com sucesso!\033[0m")

if __name__ == "__main__":
    executar()