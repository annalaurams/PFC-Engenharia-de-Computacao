import os
import time
import glob
import shutil
import traceback
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    NoSuchElementException,
    StaleElementReferenceException,
    TimeoutException,
    WebDriverException,
)

# Configuração
#
# Mesma lógica do main_extracao.py original, mas percorrendo em lote os
# municípios que não têm nenhum registro na base de mortalidade (por isso
# ficaram sem Regional de Saúde em tabela_municipios_regionais.csv — ver
# municipios_tratamento.ipynb). Regional de cada um conferida uma a uma.

UF = "MG"

MUNICIPIOS = [
    {"cidade": "Cajuri",                   "regional": "Ponte Nova"}
   # {"cidade": "Dores de Campos",          "regional": "São João Del Rei"},
    #{"cidade": "Toledo",                   "regional": "Pouso Alegre"},
]

# Mesmo intervalo coberto pela base de mortalidade do projeto (1979-2024) —
# nenhum desses municípios tem registro em ano nenhum hoje, então não há
# como restringir o período de antemão como no script original (que usava
# uma lista de anos específica, já sabida como faltante, para uma única
# cidade).
#PERIODO = list(range(1979, 2025))
PERIODO = [2002, 2008, 2010, 2012, 2014, 2016, 2017, 2021, 2022]

DOWNLOADS_PATH = "/home/anna/Downloads"
BASE_PROJECT_PATH = "/home/anna/tcc/Limpeza e Integração/Mortalidade/Cidades Atendidas por Cada Regional"

URL = "https://www.inca.gov.br/MortalidadeWeb/pages/Modelo10/consultar.xhtml"
MAX_TENTATIVAS = 3

os.system("cls" if os.name == "nt" else "clear")

# ________________________________________________________________________________
# Utilidades


def log_status(cidade, ano, mensagem, tipo="INFO"):
    cores = {"INFO": "34", "OK": "32", "ERRO": "31", "AVISO": "33"}
    print(f"\033[{cores.get(tipo, '37')}m[{tipo}] {cidade} | Ano {ano} | {mensagem}\033[0m")


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


def clicar_com_retry(driver, obter_elemento, max_tentativas=4, espera_entre_tentativas=2):
    """
    Clica em um elemento obtido via `obter_elemento()` (callable, para
    resolver o elemento de novo a cada tentativa — evita
    StaleElementReferenceException em elementos que o PrimeFaces
    recria depois de um AJAX). Usada nos pontos mais instáveis do
    formulário (picklist de diagnóstico), que não tinham retry nenhum
    e por isso quebravam o script inteiro por qualquer soluço de
    timing na página.
    """
    ultimo_erro = None
    for tentativa in range(max_tentativas):
        try:
            elemento = obter_elemento()
            driver.execute_script(
                "arguments[0].scrollIntoView({behavior:'smooth',block:'center'});", elemento
            )
            time.sleep(0.5)
            try:
                elemento.click()
            except ElementClickInterceptedException:
                driver.execute_script("arguments[0].click();", elemento)
            return True
        except (StaleElementReferenceException, ElementClickInterceptedException,
                NoSuchElementException, TimeoutException) as e:
            ultimo_erro = e
            time.sleep(espera_entre_tentativas)
    if ultimo_erro is not None:
        print(f"[AVISO] clicar_com_retry esgotou tentativas: {type(ultimo_erro).__name__}: {ultimo_erro}")
    return False


def aplicar_filtros(driver, wait, cidade, regional_saude):
    try:
        select_by_id(driver, "formModeloTabulador:comboSexo", "2")
        time.sleep(2)

        if not clicar_com_retry(
            driver,
            lambda: wait.until(
                EC.element_to_be_clickable((By.XPATH, "//li[contains(text(),'C50 - MAMA')]"))
            ),
        ):
            raise Exception("Não foi possível clicar no item 'C50 - MAMA' da picklist")
        time.sleep(1)

        if not clicar_com_retry(
            driver,
            lambda: wait.until(
                EC.element_to_be_clickable((By.CLASS_NAME, "ui-picklist-button-add"))
            ),
        ):
            raise Exception("Não foi possível clicar no botão de adicionar da picklist")
        time.sleep(2)

        select_by_id(driver, "formModeloTabulador:nivelLocalidade", "5")
        time.sleep(3)

        select_by_id(driver, "formModeloTabulador:regiao", "3")
        time.sleep(3)

        select_by_id(driver, "formModeloTabulador:estado", "17")
        time.sleep(3)

        select_by_id(driver, "formModeloTabulador:regionalSaude", regional_saude, by="text")
        time.sleep(4)

        wait.until(EC.presence_of_element_located((By.ID, "formModeloTabulador:localidades")))
        select_municipio = Select(driver.find_element(By.ID, "formModeloTabulador:localidades"))

        municipio_encontrado = False
        for opcao in select_municipio.options:
            if cidade in opcao.text and f"- {UF}" in opcao.text:
                select_municipio.select_by_visible_text(opcao.text)
                municipio_encontrado = True
                break

        if not municipio_encontrado:
            print(f"\n[ERRO] Município '{cidade}' não encontrado na lista da regional '{regional_saude}'!")
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
        print(f"Filtros aplicados com sucesso! ({cidade} — Regional {regional_saude})".center(80))
        print("=" * 80)
        return True

    except Exception as e:
        # WebDriverException muitas vezes vem com str(e) vazio (só a
        # stacktrace nativa do chromedriver) — sem o tipo da exceção e o
        # traceback completo não dá pra saber em qual linha realmente
        # falhou. Imprime os dois para o próximo erro vir com informação
        # de verdade.
        print(f"\n[ERRO] Falha ao aplicar filtros para {cidade} ({type(e).__name__}): {e}")
        print(traceback.format_exc())
        if isinstance(e, WebDriverException) and not str(e).strip():
            print(
                "[DICA] Exceção sem mensagem de texto costuma indicar Chrome e "
                "chromedriver desalinhados (webdriver_manager baixou uma versão "
                "diferente da instalada) ou a sessão do navegador travando no meio "
                "de um AJAX pesado da página do INCA. Confira 'google-chrome "
                "--version' e tente rodar de novo."
            )
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


def baixar_periodo(driver, wait, cidade, regional_saude, pasta_destino_cidade):
    """
    Roda o período completo (PERIODO) para uma única cidade — mesma
    lógica de retry/reconfiguração do script original, só que reaplicando
    aplicar_filtros(cidade, regional_saude) sempre que precisar
    reconfigurar (erro de campos obrigatórios, driver perdido, muitas
    falhas seguidas), em vez de reusar CIDADE/REGIONAL_SAUDE fixos.

    Retorna (driver, anos_baixados, anos_sem_dados).
    """
    anos_baixados = []
    anos_sem_dados = []
    indice_ano = 0
    tentativas_erro = 0

    while indice_ano < len(PERIODO):
        ano = PERIODO[indice_ano]

        try:
            if not driver_esta_ativo(driver):
                log_status(cidade, ano, "Driver inativo. Reiniciando...", "ERRO")
                try:
                    driver.quit()
                except Exception:
                    pass
                driver = iniciar_driver()
                wait = WebDriverWait(driver, 60)
                driver.get(URL)
                time.sleep(3)
                if not aplicar_filtros(driver, wait, cidade, regional_saude):
                    print(f"\n[ERRO] Falha ao reconfigurar filtros para {cidade}. Pulando cidade...")
                    return driver, anos_baixados, anos_sem_dados
                tentativas_erro = 0
                continue

            limpar_downloads_temp()
            log_status(cidade, ano, "Selecionando período", "INFO")

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

            log_status(cidade, ano, "Processando consulta...", "INFO")
            if not clicar_ok_com_retry(driver, wait):
                raise Exception("Falha ao clicar no botão OK após múltiplas tentativas")

            time.sleep(20)

            if verificar_erro_campos_obrigatorios(driver):
                log_status(cidade, ano, "Erro de campos obrigatórios! Reconfigurando...", "ERRO")
                driver.refresh()
                time.sleep(3)
                if not aplicar_filtros(driver, wait, cidade, regional_saude):
                    print(f"\n[ERRO] Falha ao reconfigurar filtros para {cidade}. Pulando cidade...")
                    return driver, anos_baixados, anos_sem_dados
                tentativas_erro = 0
                continue

            if verificar_sem_resultado(driver):
                log_status(cidade, ano, "Sem dados (1ª verificação). Tentando novamente...", "AVISO")
                if not clicar_ok_com_retry(driver, wait):
                    raise Exception("Falha ao clicar no botão OK na 2ª tentativa")
                time.sleep(15)

                if verificar_erro_campos_obrigatorios(driver):
                    log_status(cidade, ano, "Erro de campos obrigatórios! Reconfigurando...", "ERRO")
                    driver.refresh()
                    time.sleep(3)
                    if not aplicar_filtros(driver, wait, cidade, regional_saude):
                        print(f"\n[ERRO] Falha ao reconfigurar filtros para {cidade}. Pulando cidade...")
                        return driver, anos_baixados, anos_sem_dados
                    tentativas_erro = 0
                    continue

                if verificar_sem_resultado(driver):
                    log_status(cidade, ano, "Sem dados confirmado após 2ª tentativa", "AVISO")
                    anos_sem_dados.append(ano)
                    indice_ano += 1
                    tentativas_erro = 0
                    continue

            log_status(cidade, ano, "Gerando arquivo CSV...", "INFO")
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
                novo_nome = f"{ano}-{cidade}-{UF}.csv"
                shutil.move(arquivo_encontrado, os.path.join(pasta_destino_cidade, novo_nome))
                log_status(cidade, ano, f"Arquivo salvo: {novo_nome}", "OK")
                anos_baixados.append(ano)
                indice_ano += 1
                tentativas_erro = 0
            else:
                log_status(cidade, ano, "Download não completado. Tentando novamente...", "AVISO")
                time.sleep(3)
                tentativas_erro += 1
                if tentativas_erro >= MAX_TENTATIVAS:
                    log_status(cidade, ano, "Muitas falhas. Reconfigurando filtros...", "ERRO")
                    driver.refresh()
                    time.sleep(3)
                    if not aplicar_filtros(driver, wait, cidade, regional_saude):
                        print(f"\n[ERRO] Falha ao reconfigurar filtros para {cidade}. Pulando cidade...")
                        return driver, anos_baixados, anos_sem_dados
                    tentativas_erro = 0

        except Exception as e:
            erro_msg = str(e)
            log_status(cidade, ano, f"Erro: {erro_msg[:80]}", "ERRO")
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
                log_status(cidade, ano, "Driver/conexão perdida. Reiniciando...", "ERRO")
                try:
                    driver.quit()
                except Exception:
                    pass
                time.sleep(3)
                driver = iniciar_driver()
                wait = WebDriverWait(driver, 60)
                driver.get(URL)
                time.sleep(3)
                if not aplicar_filtros(driver, wait, cidade, regional_saude):
                    print(f"\n[ERRO] Falha ao reconfigurar filtros para {cidade}. Pulando cidade...")
                    return driver, anos_baixados, anos_sem_dados
                tentativas_erro = 0
                continue

            if tentativas_erro >= MAX_TENTATIVAS:
                log_status(cidade, ano, "Muitas falhas. Reconfigurando filtros...", "ERRO")
                driver.refresh()
                time.sleep(3)
                if not aplicar_filtros(driver, wait, cidade, regional_saude):
                    print(f"\n[ERRO] Falha ao reconfigurar filtros para {cidade}. Pulando cidade...")
                    return driver, anos_baixados, anos_sem_dados
                tentativas_erro = 0
            else:
                log_status(cidade, ano, f"Tentativa {tentativas_erro}/{MAX_TENTATIVAS}. Aguardando...", "AVISO")
                time.sleep(5)

    return driver, anos_baixados, anos_sem_dados


def executar():
    print("\033[1;36m" + "=" * 80)
    print("EXTRAÇÃO EM LOTE — MUNICÍPIOS SEM REGISTRO NA MORTALIDADE".center(80))
    print(f"TOTAL DE MUNICÍPIOS: {len(MUNICIPIOS)}".center(80))
    print(f"ANOS POR MUNICÍPIO: {PERIODO[0]}-{PERIODO[-1]} ({len(PERIODO)} anos)".center(80))
    print("=" * 80 + "\033[0m")
    for m in MUNICIPIOS:
        print(f"  • {m['cidade']} — Regional {m['regional']}")

    input("\nVerifique a lista acima e pressione ENTER para iniciar a extração em lote\n")

    driver = iniciar_driver()
    wait = WebDriverWait(driver, 60)

    resumo_por_cidade = {}

    for municipio in MUNICIPIOS:
        cidade = municipio["cidade"]
        regional_saude = municipio["regional"]

        pasta_destino_cidade = os.path.join(BASE_PROJECT_PATH, regional_saude, f"{cidade}-{UF}")
        os.makedirs(pasta_destino_cidade, exist_ok=True)

        print("\n" + "\033[1;36m" + "=" * 80)
        print(f"CIDADE: {cidade}-{UF} | REGIONAL: {regional_saude}".center(80))
        print("=" * 80 + "\033[0m")

        filtros_ok = False
        for tentativa_filtros in range(1, 3):  # 1 tentativa + 1 retry com página recarregada
            driver.get(URL)
            time.sleep(3)
            if aplicar_filtros(driver, wait, cidade, regional_saude):
                filtros_ok = True
                break
            print(f"[AVISO] Tentativa {tentativa_filtros}/2 de aplicar filtros falhou para {cidade}.")
            time.sleep(3)

        if not filtros_ok:
            print(f"\n[ERRO] Não foi possível aplicar os filtros para {cidade} após 2 tentativas. Pulando para o próximo município...")
            resumo_por_cidade[cidade] = {"baixados": [], "sem_dados": [], "faltantes": list(PERIODO)}
            continue

        driver, anos_baixados, anos_sem_dados = baixar_periodo(
            driver, wait, cidade, regional_saude, pasta_destino_cidade
        )

        anos_faltantes = [
            a for a in PERIODO if a not in anos_baixados and a not in anos_sem_dados
        ]
        resumo_por_cidade[cidade] = {
            "baixados": anos_baixados,
            "sem_dados": anos_sem_dados,
            "faltantes": anos_faltantes,
        }

        print(f"\n[{cidade}] Baixados: {len(anos_baixados)} | Sem dados: {len(anos_sem_dados)} | Faltantes: {len(anos_faltantes)}")
        print(f"[{cidade}] Arquivos salvos em: {pasta_destino_cidade}")

    try:
        driver.quit()
    except Exception:
        pass

    print("\n\033[1;32m" + "=" * 80)
    print("EXTRAÇÃO EM LOTE FINALIZADA!".center(80))
    print("=" * 80 + "\033[0m")

    for cidade, resultado in resumo_por_cidade.items():
        print(f"\n{cidade}:")
        print(f"  • Baixados  : {len(resultado['baixados'])} -> {sorted(resultado['baixados'])}")
        print(f"  • Sem dados : {len(resultado['sem_dados'])} -> {sorted(resultado['sem_dados'])}")
        if resultado["faltantes"]:
            print(f"  ⚠ FALTARAM : {sorted(resultado['faltantes'])}")

    print("\n" + "=" * 80 + "\n")


if __name__ == "__main__":
    executar()
