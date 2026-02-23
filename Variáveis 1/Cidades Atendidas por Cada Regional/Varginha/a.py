#! /usr/bin/python3

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

CIDADE = "São Bento Abade"
REGIONAL_SAUDE = "Varginha"
UF = "MG"

PERIODO = [	2000, 2015, 2019, 2021		]


DOWNLOADS_PATH = "/home/anna/Downloads"
BASE_PROJECT_PATH = "/home/anna/Documentos/PFC I/Variáveis 1/Cidades Atendidas por Cada Regional/Varginha"
PASTA_DESTINO_CIDADE = os.path.join(BASE_PROJECT_PATH, f"{CIDADE}-{UF}")
os.makedirs(PASTA_DESTINO_CIDADE, exist_ok=True)

URL = "https://www.inca.gov.br/MortalidadeWeb/pages/Modelo10/consultar.xhtml"


# ──────────────────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────────────────

def limpar_tela():
    os.system("cls" if os.name == "nt" else "clear")


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
    """
    Localiza um <select> pelo atributo `name` e seleciona uma opção.
    Usa By.VALUE por padrão; use by="text" para visible text.
    """
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
    """
    Localiza um <select> pelo `id` e seleciona uma opção.
    """
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
    """Aguarda o spinner de AJAX sumir (ajax-loader.gif fica display:none)."""
    try:
        WebDriverWait(driver, timeout).until(
            lambda d: d.execute_script(
                "return document.readyState === 'complete'"
            )
        )
        # Aguarda o loader do PrimeFaces sumir, se existir
        WebDriverWait(driver, timeout).until(
            lambda d: all(
                not el.is_displayed()
                for el in d.find_elements(By.CSS_SELECTOR, "img.loading")
            )
        )
    except Exception:
        pass  # Segue em frente mesmo se timeout


# ──────────────────────────────────────────────────────────────────────────────
# Funções de verificação
# ──────────────────────────────────────────────────────────────────────────────

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


# ──────────────────────────────────────────────────────────────────────────────
# Aplicar filtros
# ──────────────────────────────────────────────────────────────────────────────

def aplicar_filtros(driver, wait):
    """Aplica todos os filtros fixos (não mudam a cada ano)."""
    try:
        # ── Sexo ──────────────────────────────────────────────────────────────
        log("Selecionando sexo: Feminino")
        select_by_id(driver, "formModeloTabulador:comboSexo", "2")
        time.sleep(2)

        # ── CID ───────────────────────────────────────────────────────────────
        log("Selecionando CID: C50 - MAMA")
        wait.until(
            EC.element_to_be_clickable((By.XPATH, "//li[contains(text(),'C50 - MAMA')]"))
        ).click()
        time.sleep(1)

        log("Adicionando CID à seleção")
        driver.find_element(By.CLASS_NAME, "ui-picklist-button-add").click()
        time.sleep(2)

        # ── Nível / Região / Estado / Regional / Município ────────────────────
        log("Selecionando nível: Municípios")
        select_by_id(driver, "formModeloTabulador:nivelLocalidade", "5")
        time.sleep(3)

        log("Selecionando região: Sudeste")
        select_by_id(driver, "formModeloTabulador:regiao", "3")
        time.sleep(3)

        log("Selecionando estado: Minas Gerais")
        select_by_id(driver, "formModeloTabulador:estado", "17")
        time.sleep(3)

        log(f"Selecionando Regional de Saúde: {REGIONAL_SAUDE}")
        select_by_id(driver, "formModeloTabulador:regionalSaude", REGIONAL_SAUDE, by="text")
        time.sleep(4)

        log(f"Selecionando município: {CIDADE}")
        wait.until(EC.presence_of_element_located((By.ID, "formModeloTabulador:localidades")))
        select_municipio = Select(driver.find_element(By.ID, "formModeloTabulador:localidades"))

        municipio_encontrado = False
        for opcao in select_municipio.options:
            if CIDADE in opcao.text and f"- {UF}" in opcao.text:
                select_municipio.select_by_visible_text(opcao.text)
                municipio_encontrado = True
                log(f"Município encontrado: {opcao.text.strip()}")
                break

        if not municipio_encontrado:
            print(f"\n[ERRO] Município '{CIDADE}' não encontrado na lista!")
            for opcao in select_municipio.options:
                print(f"  - {opcao.text.strip()}")
            return False

        time.sleep(2)

        log("Clicando em 'Adicionar' para mover o município para selecionados")
        driver.find_element(By.ID, "formModeloTabulador:add").click()
        time.sleep(3)

        # ── Linha: Localização primária do tumor ──────────────────────────────
        # CORREÇÃO: o name real é formModeloTabulador:j_idt155 (não j_idt153)
        log("Selecionando linha: Localização primária do tumor")
        select_by_name(driver, "formModeloTabulador:j_idt155", "2")
        time.sleep(1)
        aguardar_ajax(driver)
        time.sleep(2)

        # ── Coluna: Faixa etária ──────────────────────────────────────────────
        log("Selecionando coluna: Faixa etária")
        select_by_id(driver, "formModeloTabulador:opcaoColuna", "2")
        aguardar_ajax(driver, timeout=15)
        time.sleep(3)

        # ── Faixa etária: 0 até 99+ ───────────────────────────────────────────
        # Quando coluna = Faixa etária, os campos são idadeFaixaIni / idadeFaixaFim
        log("Selecionando faixa etária: 0 até 99+")
        try:
            select_by_id(driver, "formModeloTabulador:idadeFaixaIni", "0")
        except Exception:
            log("[AVISO] Campo idadeFaixaIni não encontrado — pulando")

        try:
            select_by_id(driver, "formModeloTabulador:idadeFaixaFim", "999")
        except Exception:
            log("[AVISO] Campo idadeFaixaFim não encontrado — pulando")

        time.sleep(1)

        print("\n" + "=" * 80)
        print("[✔] Todos os filtros aplicados com sucesso!".center(80))
        print("=" * 80)
        return True

    except Exception as e:
        print(f"\n[ERRO] Falha ao aplicar filtros: {e}")
        return False


# ──────────────────────────────────────────────────────────────────────────────
# Clicar no botão OK (gerar tabela)
# ──────────────────────────────────────────────────────────────────────────────

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
                log(f"OK — estratégia {i+1} (tentativa {tentativa+1}/{max_tentativas})")
                btn = estrategia()
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", btn
                )
                time.sleep(0.5)
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", btn)
                log("✓ Botão OK clicado")
                return True
            except Exception as e:
                log(f"  estratégia {i+1} falhou: {str(e)[:60]}")
                continue

        if tentativa < max_tentativas - 1:
            log("Aguardando antes de nova tentativa no OK...")
            time.sleep(3)

    log("ERRO: Não foi possível clicar no botão OK")
    return False


# ──────────────────────────────────────────────────────────────────────────────
# Clicar no botão Gerar CSV
# ──────────────────────────────────────────────────────────────────────────────

def clicar_gerar_csv_com_retry(driver, wait, max_tentativas=5):
    estrategias = [
        # ID exato obtido do HTML fornecido
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
                log(f"CSV — estratégia {i+1} (tentativa {tentativa+1}/{max_tentativas})")
                btn = estrategia()
                driver.execute_script(
                    "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", btn
                )
                time.sleep(0.5)
                try:
                    btn.click()
                except ElementClickInterceptedException:
                    driver.execute_script("arguments[0].click();", btn)
                log("✓ Botão Gerar CSV clicado")
                return True
            except Exception as e:
                log(f"  estratégia {i+1} falhou: {str(e)[:60]}")
                continue

        if tentativa < max_tentativas - 1:
            log("Aguardando antes de nova tentativa no CSV...")
            time.sleep(3)

    log("ERRO: Não foi possível clicar no botão Gerar CSV")
    return False


# ──────────────────────────────────────────────────────────────────────────────
# Execução principal
# ──────────────────────────────────────────────────────────────────────────────

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

    anos_baixados = []
    anos_sem_dados = []
    indice_ano = 0
    tentativas_erro = 0
    MAX_TENTATIVAS = 3

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

            # ── Período ───────────────────────────────────────────────────────
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

            # ── Clicar OK ─────────────────────────────────────────────────────
            log_status(ano, "Processando consulta...", "INFO")
            if not clicar_ok_com_retry(driver, wait):
                raise Exception("Falha ao clicar no botão OK após múltiplas tentativas")

            time.sleep(20)

            # ── Verificar erro de campos obrigatórios ─────────────────────────
            if verificar_erro_campos_obrigatorios(driver):
                log_status(ano, "⚠ Erro de campos obrigatórios! Reconfigurando...", "ERRO")
                driver.refresh()
                time.sleep(3)
                if not aplicar_filtros(driver, wait):
                    print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                    driver.quit()
                    return
                tentativas_erro = 0
                continue

            # ── Verificar sem resultado ───────────────────────────────────────
            if verificar_sem_resultado(driver):
                log_status(ano, "⊘ Sem dados (1ª verificação). Tentando novamente...", "AVISO")
                if not clicar_ok_com_retry(driver, wait):
                    raise Exception("Falha ao clicar no botão OK na 2ª tentativa")
                time.sleep(15)

                if verificar_erro_campos_obrigatorios(driver):
                    log_status(ano, "⚠ Erro de campos obrigatórios! Reconfigurando...", "ERRO")
                    driver.refresh()
                    time.sleep(3)
                    if not aplicar_filtros(driver, wait):
                        print("\n[ERRO] Falha ao reconfigurar filtros. Encerrando...")
                        driver.quit()
                        return
                    tentativas_erro = 0
                    continue

                if verificar_sem_resultado(driver):
                    log_status(ano, "⊘ Sem dados confirmado após 2ª tentativa", "AVISO")
                    anos_sem_dados.append(ano)
                    indice_ano += 1
                    tentativas_erro = 0
                    continue

            # ── Gerar CSV ─────────────────────────────────────────────────────
            log_status(ano, "Gerando arquivo CSV...", "INFO")
            if not clicar_gerar_csv_com_retry(driver, wait):
                raise Exception("Falha ao clicar no botão Gerar CSV após múltiplas tentativas")

            # ── Aguardar download ─────────────────────────────────────────────
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
                log_status(ano, f"✓ Arquivo salvo: {novo_nome}", "OK")
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

    # ── Relatório final ───────────────────────────────────────────────────────
    print("\n\033[1;32m" + "=" * 80)
    print("[✓] EXTRAÇÃO FINALIZADA!".center(80))
    print("=" * 80 + "\033[0m")
    print(f"\n📊 ESTATÍSTICAS:")
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