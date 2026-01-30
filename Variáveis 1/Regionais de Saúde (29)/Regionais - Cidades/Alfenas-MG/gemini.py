import os
import time
import glob
import shutil
import pandas as pd
from io import StringIO
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager

# ===================== CONFIGURAÇÕES =====================
CIDADE = "Barbacena"
UF = "MG"
ANO_INICIAL = 1979
ANO_FINAL = 2024

DOWNLOADS = os.path.expanduser("~/Downloads")
BASE_DIR = "/home/usuario/Documentos/novo/Código"
PASTA_CIDADE = os.path.join(BASE_DIR, f"{CIDADE}-{UF}")
os.makedirs(PASTA_CIDADE, exist_ok=True)

URL = "https://www.inca.gov.br/MortalidadeWeb/pages/Modelo10/consultar.xhtml"

def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def banner(texto):
    print("=" * 65)
    print(f" {texto.center(63)} ")
    print("=" * 65)

def iniciar_driver():
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": DOWNLOADS,
        "download.prompt_for_download": False,
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("detach", True)
    
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )
    return driver

# ===================== EXECUÇÃO =====================
driver = iniciar_driver()
wait = WebDriverWait(driver, 20) # Aumentado para 20s para conexões lentas

def executar():
    global driver
    driver.get(URL)
    
    limpar_tela()
    banner("CONFIGURAÇÃO MANUAL")
    print(f"\n[*] Cidade alvo: {CIDADE}-{UF}")
    print("[!] Configure os filtros (Causa, Idade, Sexo) exceto o PERÍODO.")
    input("\n[✅] Após configurar, pressione ENTER para iniciar...")

    ano = ANO_INICIAL
    while ano <= ANO_FINAL:
        try:
            limpar_tela()
            banner(f"PROCESSANDO: {CIDADE} | ANO: {ano}")

            # 1. Selecionar Período
            select_ini = Select(wait.until(EC.presence_of_element_located((By.ID, "formModeloTabulador:anoInicio"))))
            select_fim = Select(driver.find_element(By.ID, "formModeloTabulador:anoFim"))
            
            select_ini.select_by_value(str(ano))
            select_fim.select_by_value(str(ano))

            # 2. Clicar OK
            print("[*] Solicitando dados ao servidor...")
            btn_ok = driver.find_element(By.ID, "formModeloTabulador:j_idt202")
            btn_ok.click()

            # 3. Aguardar o botão CSV aparecer (Isso garante que o processamento acabou)
            print("[*] Aguardando processamento da tabela...")
            btn_csv = wait.until(
                EC.element_to_be_clickable((By.ID, "formModeloTabuladorLinks:j_idt398"))
            )

            # 4. Clicar no CSV via JavaScript (mais garantido)
            print("[*] Baixando CSV...")
            driver.execute_script("arguments[0].click();", btn_csv)

            # 5. Mover e Renomear arquivo
            time.sleep(2) # Pequena pausa para o arquivo tocar o disco
            sucesso_download = False
            for _ in range(15): # Tenta achar o arquivo por 15 segundos
                arquivos = glob.glob(os.path.join(DOWNLOADS, "ModeloTabulador_*.csv"))
                if arquivos:
                    arquivo_recente = max(arquivos, key=os.path.getmtime)
                    nome_final = os.path.join(PASTA_CIDADE, f"{ano}-{CIDADE}-{UF}.csv")
                    shutil.move(arquivo_recente, nome_final)
                    print(f"[OK] Salvo: {ano}-{CIDADE}-{UF}.csv")
                    sucesso_download = True
                    break
                time.sleep(1)

            if sucesso_download:
                ano += 1
            else:
                print(f"[!] Falha no download do ano {ano}. Tentando novamente...")

        except Exception as e:
            if "invalid session id" in str(e).lower() or "no such window" in str(e).lower():
                print("\n[!] SESSÃO CAIU! Reabrindo navegador...")
                try: driver.quit()
                except: pass
                driver = iniciar_driver()
                driver.get(URL)
                input("[!] Reconfigure os filtros e pressione ENTER para continuar...")
                continue # Tenta o mesmo ano novamente
            
            print(f"\n[X] Erro no ano {ano}: {e}")
            resp = input("\n[1] Tentar de novo\n[2] Pular ano\nEscolha: ")
            if resp == "2":
                ano += 1

    banner("AUTOMAÇÃO FINALIZADA!")

if __name__ == "__main__":
    executar()