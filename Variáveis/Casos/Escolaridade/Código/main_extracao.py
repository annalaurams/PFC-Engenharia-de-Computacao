# Automação para extração de dados do Registro Hospitalar de Câncer - INCA
# Localização primária: C50 MAMA | UF: Minas Gerais | Sexo: Feminino
# Linha: Procedência | Coluna: Escolaridade | Todos os anos disponíveis

import time
import shutil
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ________________________________________________________________________________
# Extração: Configuração de pastas e variáveis

DOWNLOADS_DIR = Path("/home/anna/Downloads")
OUTPUT_DIR = Path("/home/anna/tcc/variaveis/Casos/Escolaridade/Código")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://irhc.inca.gov.br/RHCNet/visualizaTabNetExterno.action"

ANOS = [
    2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014,
    2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005, 2004,
    2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996, 1995, 1994,
    1993, 1992, 1991, 1990, 1989, 1988, 1986, 1985,
]


# ________________________________________________________________________________
# Extração: Funções auxiliares

def make_driver() -> webdriver.Chrome:
    prefs = {
        "download.default_directory": str(DOWNLOADS_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    opts = Options()
    opts.add_experimental_option("prefs", prefs)
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1400,900")

    service = Service(ChromeDriverManager().install())
    driver  = webdriver.Chrome(service=service, options=opts)
    driver.implicitly_wait(10)
    return driver


def wait_for_new_tab(driver, known_handles: set, timeout: int = 15) -> str:
    end = time.time() + timeout
    while time.time() < end:
        new = set(driver.window_handles) - known_handles
        if new:
            return new.pop()
        time.sleep(0.5)
    raise TimeoutError("Nova aba não abriu no tempo esperado.")


def click_js(driver, element):
    driver.execute_script("arguments[0].click();", element)


def remove_old_tabulador_files():
    for f in DOWNLOADS_DIR.glob("tabulador_*.csv"):
        f.unlink()


def wait_for_download(timeout: int = 90) -> Path:
    end = time.time() + timeout
    while time.time() < end:
        candidates = [
            p for p in DOWNLOADS_DIR.glob("tabulador_*.csv")
            if not p.name.endswith(".crdownload")
        ]
        if candidates:
            return max(candidates, key=lambda p: p.stat().st_mtime)
        time.sleep(1)
    raise TimeoutError("Download não concluído.")


def js_set_select_by_id(driver, select_id: str, value: str):
    driver.execute_script("""
        var sel = document.getElementById(arguments[0]);
        if (!sel) throw new Error("Select id=" + arguments[0] + " não encontrado");
        sel.value = arguments[1];
        sel.dispatchEvent(new Event('change', {bubbles: true}));
    """, select_id, value)
    time.sleep(0.4)


def js_set_select_by_td_label(driver, label: str, value: str) -> str:
    resultado = driver.execute_script("""
        var label = arguments[0];
        var value = arguments[1];
        var tds = document.querySelectorAll('td');
        for (var td of tds) {
            if (td.textContent.trim() === label) {
                var tr = td.closest('tr');
                if (!tr) tr = td.parentElement;
                var sel = tr.querySelector('select');
                if (!sel) {
                    var nextTd = td.nextElementSibling;
                    while (nextTd) {
                        sel = nextTd.querySelector('select');
                        if (sel) break;
                        nextTd = nextTd.nextElementSibling;
                    }
                }
                if (sel) {
                    var found = false;
                    for (var o of sel.options) {
                        if (o.value === value) { found = true; break; }
                    }
                    if (!found) {
                        return 'OPCAO_NAO_ENCONTRADA|' + sel.name + '|opts=' +
                               Array.from(sel.options).slice(0,8).map(o=>o.value).join(',');
                    }
                    sel.value = value;
                    sel.dispatchEvent(new Event('change', {bubbles: true}));
                    return 'OK|' + sel.name;
                }
                return 'SELECT_NAO_ENCONTRADO_NA_TR';
            }
        }
        return 'TD_NAO_ENCONTRADO|label=' + label;
    """, label, value)
    return resultado


# ________________________________________________________________________________
# Extração: Navegação até o formulário

def navegar_ate_formulario(driver):
    driver.get(BASE_URL)
    time.sleep(2)

    handles = set(driver.window_handles)
    link = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'selecionaBase')]"))
    )
    click_js(driver, link)
    driver.switch_to.window(wait_for_new_tab(driver, handles))
    time.sleep(2)

    handles = set(driver.window_handles)
    enviar = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'envia()')]"))
    )
    click_js(driver, enviar)
    driver.switch_to.window(wait_for_new_tab(driver, handles))
    time.sleep(2)


# ________________________________________________________________________________
# Extração: Preenchimento do formulário

def preencher_formulario(driver, ano: int):
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "linha")))

    js_set_select_by_id(driver, "linha", "12")
    js_set_select_by_id(driver, "coluna", "14")
    driver.execute_script("""
        var sel = document.getElementById('periodo');
        for (var i = 0; i < sel.options.length; i++) sel.options[i].selected = false;
        for (var i = 0; i < sel.options.length; i++) {
            if (sel.options[i].value === arguments[0]) {
                sel.options[i].selected = true;
                break;
            }
        }
        sel.dispatchEvent(new Event('change', {bubbles: true}));
    """, str(ano))
    time.sleep(0.5)

    js_set_select_by_id(driver, "sexo", "2")

    res = js_set_select_by_td_label(driver, "UF de procedência", "MG")
    if "NAO" in res:
        driver.execute_script("""
            for (var s of document.querySelectorAll('select')) {
                for (var o of s.options) {
                    if (o.value === 'MG') {
                        s.value = 'MG';
                        s.dispatchEvent(new Event('change', {bubbles:true}));
                        return 'fallback OK';
                    }
                }
            }
        """)
    time.sleep(0.5)

    js_set_select_by_td_label(driver, "Procedência", "")
    time.sleep(0.5)

    js_set_select_by_id(driver, "escolaridade", "")
    time.sleep(0.5)

    res = js_set_select_by_td_label(driver, "Localização primária", "C50")

    if "OPCAO_NAO_ENCONTRADA" in res or "NAO" in res:
        time.sleep(4)
        driver.execute_script("""
            for (var s of document.querySelectorAll('select')) {
                for (var o of s.options) {
                    if (o.value === 'C50') {
                        s.value = 'C50';
                        s.dispatchEvent(new Event('change', {bubbles:true}));
                        return 'OK';
                    }
                }
            }
        """)

    time.sleep(1)


# ________________________________________________________________________________
# Extração: Mostra, download e operações

def clicar_mostra(driver):
    btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@value='Mostra']"))
    )
    click_js(driver, btn)
    WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'downloadTabulador')]"))
    )
    time.sleep(1)


def baixar_csv(driver, ano: int) -> Path:
    remove_old_tabulador_files()
    link = driver.find_element(By.XPATH, "//a[contains(@href, 'downloadTabulador')]")
    click_js(driver, link)
    downloaded = wait_for_download(timeout=90)
    destino = OUTPUT_DIR / f"Escolaridade-{ano}.csv"
    shutil.move(str(downloaded), str(destino))
    return destino


def voltar_formulario(driver):
    back = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'enviarDados')]"))
    )
    click_js(driver, back)
    time.sleep(2)


# ________________________________________________________________________________
# Extração: Operações principais

def main():
    driver = make_driver()

    try:
        navegar_ate_formulario(driver)

        for i, ano in enumerate(ANOS):
            try:
                preencher_formulario(driver, ano)
                clicar_mostra(driver)
                baixar_csv(driver, ano)
                voltar_formulario(driver)

            except Exception as e:
                try:
                    voltar_formulario(driver)
                except Exception:
                    try:
                        driver.back()
                        time.sleep(3)
                    except Exception:
                        break

        arquivos = sorted(OUTPUT_DIR.glob("Escolaridade-*.csv"))

    finally:
        driver.quit()


if __name__ == "__main__":
    main()