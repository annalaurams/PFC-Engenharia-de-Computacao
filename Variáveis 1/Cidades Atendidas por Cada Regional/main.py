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
from selenium.common.exceptions import ElementClickInterceptedException, NoSuchElementException

CIDADE = "Dom Cavati"  # Nome do município 
REGIONAL_SAUDE = "Coronel Fabriciano"  # Regional de Saúde
UF = "MG"

PERIODO = [
    1979,
    1985,
    1989,
    2006,
    2009,
    2014,
    2015,
    2020,
    2021,
    2022,
    2023
]



# PERIODO = [
#     1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988,
#     1989, 1990, 1991, 1992, 1993, 1994, 1995, 1996, 1997, 1998,
#     1999, 2000, 2001, 2002, 2003, 2004, 2005, 2006, 2007, 2008,
#     2009, 2010, 2011, 2012, 2013, 2014, 2015, 2016, 2017, 2018,
#     2019, 2020, 2021, 2022, 2023, 2024
# ]


DOWNLOADS_PATH = "/home/anna/Downloads"
BASE_PROJECT_PATH = "/home/anna/Documentos/PFC I/Variáveis 1/Cidades Atendidas por Cada Regional/A"
PASTA_DESTINO_CIDADE = os.path.join(BASE_PROJECT_PATH, f"{CIDADE}-{UF}")

os.makedirs(PASTA_DESTINO_CIDADE, exist_ok=True)

URL = "https://www.inca.gov.br/MortalidadeWeb/pages/Modelo10/consultar.xhtml"


def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')

def log_status(ano, mensagem, tipo="INFO"):
    cores = {"INFO": "34", "OK": "32", "ERRO": "31", "AVISO": "33"}
    print(f"\033[{cores.get(tipo, '37')}m[{tipo}] Ano {ano} | {mensagem}\033[0m")

def log(msg):
    print(f"[INFO] {msg}")

def iniciar_driver():
    options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": DOWNLOADS_PATH,
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True
    }
    options.add_experimental_option("prefs", prefs)
    options.add_experimental_option("detach", True)
    
    return webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=options
    )

def driver_esta_ativo(driver):
    """Verifica se o driver ainda está ativo"""
    try:
        _ = driver.current_url
        return True
    except:
        return False

def limpar_downloads_temp():
    for f in glob.glob(os.path.join(DOWNLOADS_PATH, "ModeloTabulador_*.csv")):
        try:
            os.remove(f)
        except:
            pass

def verificar_erro_campos_obrigatorios(driver):
    """Verifica se apareceu mensagem de erro de campos obrigatórios"""
    try:
        elemento = driver.find_element(By.ID, "formModeloTabulador:msgCamposVazios")
        texto = elemento.text
        
        if "Atenção! Corrija estes erros" in texto or "campo" in texto.lower() and "obrigatório" in texto.lower():
            return True
    except:
        pass
    
    return False

def aplicar_filtros(driver, wait):
    """Aplica todos os filtros necessários na página"""
    
    try:
        log("Selecionando sexo: Feminino")
        Select(wait.until(
            EC.presence_of_element_located((By.ID, "formModeloTabulador:comboSexo"))
        )).select_by_value("2")  # Feminino
        time.sleep(2)

        log("Selecionando CID: C50 - MAMA")
        wait.until(EC.element_to_be_clickable(
            (By.XPATH, "//li[contains(text(),'C50 - MAMA')]")
        )).click()
        time.sleep(1)
        
        log("Adicionando CID à seleção")
        driver.find_element(By.CLASS_NAME, "ui-picklist-button-add").click()
        time.sleep(2)

        log("Selecionando nível: Municípios")
        Select(driver.find_element(By.ID, "formModeloTabulador:nivelLocalidade")) \
            .select_by_value("5")  # Municípios
        time.sleep(3)

        log("Selecionando região: Sudeste")
        Select(driver.find_element(By.ID, "formModeloTabulador:regiao")) \
            .select_by_value("3")  # Sudeste
        time.sleep(3)

        log("Selecionando estado: Minas Gerais")
        Select(driver.find_element(By.ID, "formModeloTabulador:estado")) \
            .select_by_value("17")  # MG
        time.sleep(3)

        log(f"Selecionando Regional de Saúde: {REGIONAL_SAUDE}")
        Select(driver.find_element(By.ID, "formModeloTabulador:regionalSaude")) \
            .select_by_visible_text(REGIONAL_SAUDE)
        time.sleep(4)  

        log(f"Selecionando município: {CIDADE}")
        # Aguarda a lista de municípios carregar
        wait.until(EC.presence_of_element_located((By.ID, "formModeloTabulador:localidades")))
        
        # Seleciona o município na lista 
        select_municipio = Select(driver.find_element(By.ID, "formModeloTabulador:localidades"))
        
        # Encontra a opção que contém o nome da cidade
        opcoes = select_municipio.options
        municipio_encontrado = False
        
        for opcao in opcoes:
            if CIDADE in opcao.text and f"- {UF}" in opcao.text:
                select_municipio.select_by_visible_text(opcao.text)
                municipio_encontrado = True
                log(f"Município encontrado: {opcao.text.strip()}")
                break
        
        if not municipio_encontrado:
            print(f"\n[ERRO] Município '{CIDADE}' não encontrado na lista!")
            print("Municípios disponíveis:")
            for opcao in opcoes:
                print(f"  - {opcao.text.strip()}")
            return False
        
        time.sleep(2)
        
        log("Clicando em 'Adicionar' para mover o município para selecionados")
        # Clica no botão Adicionar
        driver.find_element(By.ID, "formModeloTabulador:add").click()
        time.sleep(3)

        log("Selecionando linha: Localização primária do tumor")
        Select(driver.find_element(By.NAME, "formModeloTabulador:j_idt153")) \
            .select_by_value("2")  # Localização primária
        time.sleep(2)

        log("Selecionando coluna: Faixa etária")
        Select(driver.find_element(By.ID, "formModeloTabulador:opcaoColuna")) \
            .select_by_value("2")  # Faixa etária
        time.sleep(2)

        log("Selecionando faixa etária: 0 até 99+")
        Select(driver.find_element(By.ID, "formModeloTabulador:idadeFaixaIni")) \
            .select_by_value("0")
        Select(driver.find_element(By.ID, "formModeloTabulador:idadeFaixaFim")) \
            .select_by_value("999")
        time.sleep(2)

        print("\n" + "=" * 80)
        print("[✔] Todos os filtros aplicados com sucesso!".center(80))
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n[ERRO] Falha ao aplicar filtros: {str(e)[:100]}")
        return False

def verificar_sem_resultado(driver):
    try:
        # Procura pelo elemento que contém a mensagem "Esta consulta retornou sem resultado"
        elemento = driver.find_element(By.ID, "panelResultado")
        texto = elemento.text
        
        if "Esta consulta retornou sem resultado" in texto or "retornou sem resultado" in texto:
            return True
    except:
        pass
    
    return False

def clicar_ok_com_retry(driver, wait, max_tentativas=3):
    """Tenta clicar no botão OK com tratamento de click intercepted"""
    for tentativa in range(max_tentativas):
        try:
            btn_ok = wait.until(EC.element_to_be_clickable((By.ID, "formModeloTabulador:j_idt202")))

            try:
                btn_ok.click()
                return True
            except ElementClickInterceptedException:
                log(f"Click intercepted, tentando com JavaScript (tentativa {tentativa + 1}/{max_tentativas})")
                driver.execute_script("arguments[0].click();", btn_ok)
                return True
                
        except Exception as e:
            if tentativa < max_tentativas - 1:
                time.sleep(2)
            else:
                raise e
    
    return False


def executar():
    driver = iniciar_driver()
    wait = WebDriverWait(driver, 60)

    driver.get(URL)

    limpar_tela()
    print("\033[1;36m" + "=" * 80)
    print(f"CIDADE: {CIDADE}-{UF} | REGIONAL: {REGIONAL_SAUDE}".center(80))
    print(f"ANOS A EXTRAIR: {PERIODO}".center(80))
    print(f"TOTAL DE ANOS: {len(PERIODO)}".center(80))
    print("=" * 80 + "\033[0m")

    if not aplicar_filtros(driver, wait):
        driver.quit()
        return
    
    input("\n[!] Verifique os filtros e pressione ENTER para iniciar os downloads\n")
    
    # Controle de downloads bem-sucedidos
    anos_baixados = []
    anos_sem_dados = []


    indice_ano = 0
    tentativas_erro = 0
    MAX_TENTATIVAS = 3
    
    while indice_ano < len(PERIODO):
        ano = PERIODO[indice_ano]
        
        try:

            if not driver_esta_ativo(driver):
                log_status(ano, "Driver inativo detectado. Reiniciando...", "ERRO")
                try:
                    driver.quit()
                except:
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
            # 1. Selecionar Período
            wait.until(EC.presence_of_element_located((By.ID, "formModeloTabulador:anoInicio")))
            Select(driver.find_element(By.ID, "formModeloTabulador:anoInicio")).select_by_value(str(ano))
            Select(driver.find_element(By.ID, "formModeloTabulador:anoFim")).select_by_value(str(ano))
            time.sleep(1)

            # 2. Clicar no OK
            log_status(ano, "Processando consulta...", "INFO")
            if not clicar_ok_com_retry(driver, wait):
                raise Exception("Falha ao clicar no botão OK após múltiplas tentativas")
            
            time.sleep(20)

            # 3. Verificar se apareceu erro de campos obrigatórios
            if verificar_erro_campos_obrigatorios(driver):
                log_status(ano, "⚠ Erro de campos obrigatórios detectado! Reconfigurando...", "ERRO")
                driver.refresh() 
                time.sleep(3)
                
                if not aplicar_filtros(driver, wait):
                    print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                    driver.quit()
                    return
                
                tentativas_erro = 0
                continue  # Tenta o mesmo ano novamente

            # 4. Verificar se retornou sem resultado 
            if verificar_sem_resultado(driver):
                log_status(ano, "⊘ Sem dados (1ª verificação). Tentando novamente...", "AVISO")
 
                log_status(ano, "Processando consulta novamente...", "INFO")
                if not clicar_ok_com_retry(driver, wait):
                    raise Exception("\nFalha ao clicar no botão OK na segunda tentativa")
                
                time.sleep(15) 
                
                # Verifica erro de campos obrigatórios novamente
                if verificar_erro_campos_obrigatorios(driver):
                    log_status(ano, "⚠ Erro de campos obrigatórios detectado! Reconfigurando...", "ERRO")
                    driver.refresh()
                    time.sleep(3)
                    
                    if not aplicar_filtros(driver, wait):
                        print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                        driver.quit()
                        return
                    
                    tentativas_erro = 0
                    continue
                
                # Verificar se retornou sem resultado novamente
                if verificar_sem_resultado(driver):
                    log_status(ano, "⊘ Sem dados disponíveis (confirmado após 2ª tentativa)", "AVISO")
                    anos_sem_dados.append(ano)
                    indice_ano += 1
                    tentativas_erro = 0
                    continue

            # 5. Clicar para gerar CSV
            log_status(ano, "Gerando arquivo CSV...", "INFO")
            btn_csv = wait.until(EC.element_to_be_clickable((By.ID, "formModeloTabuladorLinks:j_idt398")))
            driver.execute_script("arguments[0].click();", btn_csv)
            
            # 6. Aguardar download
            arquivo_encontrado = None
            for _ in range(40):
                arquivos = glob.glob(os.path.join(DOWNLOADS_PATH, "ModeloTabulador_*.csv"))
                if arquivos:
                    # Verifica se não há downloads em andamento
                    if not any(f.endswith(".crdownload") for f in os.listdir(DOWNLOADS_PATH)):
                        arquivo_encontrado = max(arquivos, key=os.path.getmtime)
                        break
                time.sleep(1)
            
            if arquivo_encontrado:
                novo_nome = f"{ano}-{CIDADE}-{UF}.csv"
                shutil.move(arquivo_encontrado, os.path.join(PASTA_DESTINO_CIDADE, novo_nome))
                log_status(ano, f"✓ Arquivo salvo: {novo_nome}", "OK")
                anos_baixados.append(ano)
                indice_ano += 1
                tentativas_erro = 0  
            else:
                log_status(ano, "Download não completado. Tentando novamente...", "AVISO")
                time.sleep(3)
                tentativas_erro += 1
                
                # Se falhar muitas vezes, reconfigura filtros
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
            
            # Verifica se é erro de conexão
            if any(palavra in erro_msg for palavra in ["Connection refused", "HTTPConnectionPool", "invalid session", "Session", "chrome not reachable"]):
                log_status(ano, "Driver/conexão perdida. Reiniciando completamente...", "ERRO")
                
                try:
                    driver.quit()
                except:
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
            
            # Se teve muitas tentativas de erro, reconfigurar filtros
            if tentativas_erro >= MAX_TENTATIVAS:
                log_status(ano, "Muitas falhas. Reconfigurando filtros automaticamente...", "ERRO")
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
    except:
        pass
    
    print("\n\033[1;32m" + "=" * 80)
    print("[✓] EXTRAÇÃO FINALIZADA!".center(80))
    print("=" * 80 + "\033[0m")
    
    print(f"\n📊 ESTATÍSTICAS:")
    print(f"   • Total de anos no período: {len(PERIODO)}")
    print(f"   • CSVs baixados com sucesso: {len(anos_baixados)}")
    print(f"   • Anos sem dados disponíveis: {len(anos_sem_dados)}")
    
    # Calcular anos que faltaram 
    anos_faltantes = [ano for ano in PERIODO if ano not in anos_baixados and ano not in anos_sem_dados]
    
    if anos_baixados:
        print(f"\nAnos baixados: {sorted(anos_baixados)}")
    
    if anos_sem_dados:
        print(f"\n -> Anos sem dados: {sorted(anos_sem_dados)}")
    
    if anos_faltantes:
        print(f"\nAnos que FALTARAM (não concluídos): {sorted(anos_faltantes)}")
        print(f"   ⚠ Execute novamente com PERIODO = {anos_faltantes} para tentar baixá-los")
    else:
        print(f"\n✓ Todos os anos foram processados!")
    
    print(f"\nArquivos salvos em: {PASTA_DESTINO_CIDADE}\n")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    executar()