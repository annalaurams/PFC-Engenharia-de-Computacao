import argparse
import os
import shutil
import time
from datetime import date
from typing import List, Optional
from urllib.parse import urljoin, urlparse

from selenium import webdriver
from selenium.common.exceptions import (
    ElementClickInterceptedException,
    ElementNotInteractableException,
    NoSuchElementException,
    TimeoutException,
)
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import requests


# Extração: Configuração e variáveis

URL = "https://tabnet.datasus.gov.br/cgi/dhdat.exe?siscan/mamografia_atendmg.def"

DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/Downloads")
DEFAULT_OUTPUT_DIR = "/home/anna/tcc/Limpeza e Integração/Mamografia/Dados"

# Filtros aplicados na consulta (TABNET/SISCAN):
FILTRO_LINHA = "Munic.da un.saúde"
FILTRO_COLUNA = "Faixa etária"
FILTRO_CONTEUDO = "Exames"
FILTRO_SEXO = "Feminino"
FILTRO_RACA_COR = "Todas as categorias"
FILTRO_ESCOLARIDADE = "Todas as categorias"

# 2012 = primeiro ano com série completa disponível no SISCAN para este tabulador
ANO_INICIAL_SERIE = 2012
ANOS_PADRAO = list(range(date.today().year - 1, ANO_INICIAL_SERIE, -1))

# ________________________________________________________________________________
# Extração: Funções auxiliares

def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _build_driver(download_dir: str, headless: bool) -> webdriver.Chrome:
    chrome_options = webdriver.ChromeOptions()
    prefs = {
        "download.default_directory": os.path.abspath(download_dir),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    chrome_options.add_experimental_option("prefs", prefs)
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    if headless:
        chrome_options.add_argument("--headless=new")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.set_page_load_timeout(120)

    try:
        driver.execute_cdp_cmd(
            "Page.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": os.path.abspath(download_dir)},
        )
    except Exception:
        pass
    return driver


def _set_select_by_visible_text(driver: webdriver.Chrome, select_el, text: str) -> None:
    # Executa código JavaScript no navegador para selecionar uma opção pelo texto visível
    ok = driver.execute_script(
        """
        const sel = arguments[0];
        const targetText = arguments[1];
        const isMultiple = !!sel.multiple;
        let found = false;
        if (isMultiple) {
            for (const opt of sel.options) {
                const match = (opt.text || '').trim() === targetText;
                opt.selected = match;
                if (match) found = true;
            }
        } else {
            for (const opt of sel.options) {
                const match = (opt.text || '').trim() === targetText;
                if (match) {
                    sel.value = opt.value;
                    found = true;
                    break;
                }
            }
        }
        if (found) {
            sel.dispatchEvent(new Event('change', { bubbles: true }));
        }
        return found;
        """,
        select_el,
        text,
    )
    if not ok:
        raise NoSuchElementException(f"Opção '{text}' não encontrada no select")


def _safe_click(driver: webdriver.Chrome, el) -> None:
    try:
        el.click()
    except (ElementClickInterceptedException, ElementNotInteractableException):
        driver.execute_script("arguments[0].click();", el)
    except Exception:
        driver.execute_script("arguments[0].click();", el)


def _scroll_to_bottom(driver: webdriver.Chrome, steps: int = 10, pause_s: float = 0.5) -> None:
    for i in range(1, steps + 1):
        driver.execute_script(
            f"window.scrollTo(0, document.body.scrollHeight * {i / steps});"
        )
        time.sleep(pause_s)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)


def _switch_to_result_window(driver: webdriver.Chrome, original_handle: str, timeout_s: int = 60) -> bool:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        handles = driver.window_handles
        new_handles = [h for h in handles if h != original_handle]
        if new_handles:
            driver.switch_to.window(new_handles[-1])
            return True
        time.sleep(0.5)

    return False


def _find_csv_href(driver: webdriver.Chrome) -> str:
    strategies = [
        (By.XPATH,        "//a[normalize-space(text())='Salva como CSV']"),
        (By.XPATH,        "//a[contains(text(),'CSV') and contains(@href,'.csv')]"),
        (By.CSS_SELECTOR, "table.escondido a[href$='.csv']"),
        (By.CSS_SELECTOR, "a[href*='csv/'][href$='.csv']"),
        (By.XPATH,        "//a[contains(@href,'mamografia') and contains(@href,'.csv')]"),
        (By.XPATH,        "//a[contains(@href,'.csv')]"),
    ]

    for by, selector in strategies:
        try:
            el = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((by, selector))
            )
            href = el.get_attribute("href")
            if href:
                return href
        except TimeoutException:
            continue

    href = driver.execute_script(
        """
        for (const a of document.querySelectorAll('a')) {
            const h = (a.getAttribute('href') || '').toLowerCase();
            const t = (a.textContent || '').toLowerCase();
            if (h.endsWith('.csv') || t.includes('salva como csv')) {
                return a.href;
            }
        }
        return null;
        """
    )
    if href:
        return href

    raise NoSuchElementException(
        "Link 'Salva como CSV' não encontrado"
    )


def _download_with_requests(driver: webdriver.Chrome, url: str, dest_path: str) -> None:
    _ensure_dir(os.path.dirname(dest_path))

    session = requests.Session()
    for c in driver.get_cookies():
        session.cookies.set(c["name"], c["value"])

    try:
        user_agent = driver.execute_script("return navigator.userAgent")
    except Exception:
        user_agent = "Mozilla/5.0"

    headers = {
        "User-Agent": user_agent,
        "Referer": driver.current_url,
    }

    with session.get(url, headers=headers, stream=True, timeout=180) as resp:
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)


def _move_overwrite(src: str, dst: str) -> None:
    _ensure_dir(os.path.dirname(dst))
    if os.path.exists(dst):
        os.remove(dst)
    shutil.move(src, dst)


def baixar_csv_por_ano(
    driver: webdriver.Chrome,
    ano: int,
    download_dir: str,
    output_dir: str,
    wait_s: int = 60,
) -> str:
    driver.get(URL)
    wait = WebDriverWait(driver, wait_s)

    original_handle = driver.current_window_handle

    # ________________________________________________________________________________
    # Extração: Preenchimento dos filtros

    _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "L"))), FILTRO_LINHA)
    _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "C"))), FILTRO_COLUNA)
    _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "I"))), FILTRO_CONTEUDO)
    _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "A"))), str(ano))

    try:
        _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "S8"))), FILTRO_SEXO)
    except (TimeoutException, NoSuchElementException):
        pass

    try:
        _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "S1"))), FILTRO_RACA_COR)
    except (TimeoutException, NoSuchElementException):
        pass

    try:
        _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "S7"))), FILTRO_ESCOLARIDADE)
    except (TimeoutException, NoSuchElementException):
        pass

    # ________________________________________________________________________________
    # Extração: Execução e download

    mostra_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="button"][value="Mostra"]'))
    )
    _safe_click(driver, mostra_btn)

    switched = _switch_to_result_window(driver, original_handle, timeout_s=60)

    if not switched:
        time.sleep(5)

    _scroll_to_bottom(driver, steps=10, pause_s=0.5)
    time.sleep(2)

    csv_href = _find_csv_href(driver)
    csv_url = urljoin(driver.current_url, csv_href)
    parsed = urlparse(csv_url)
    if not parsed.scheme or not parsed.netloc:
        raise ValueError(f"URL inválida: {csv_url}")

    temp_name = os.path.basename(parsed.path)
    temp_path = os.path.join(os.path.abspath(download_dir), temp_name)
    _download_with_requests(driver, csv_url, temp_path)

    out_path = os.path.join(os.path.abspath(output_dir), f"mamografia_{ano}.csv")
    _move_overwrite(temp_path, out_path)

    if switched:
        try:
            driver.close()
            driver.switch_to.window(original_handle)
        except Exception:
            pass

    return out_path


def _parse_years(
    args_years: Optional[List[int]],
    start_year: Optional[int],
    end_year: Optional[int],
) -> List[int]:
    if args_years:
        return [int(y) for y in args_years]
    if start_year is None and end_year is None:
        return ANOS_PADRAO
    if start_year is None or end_year is None:
        raise ValueError("Use ambos --start-year e --end-year, ou apenas --years.")
    step = -1 if int(start_year) >= int(end_year) else 1
    return list(range(int(start_year), int(end_year) + step, step))

# ________________________________________________________________________________
# Extração: Operações principais

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Baixa CSV do TABNET (SISCAN Mamografia) por ano."
    )
    parser.add_argument("--years",        nargs="+", type=int)
    parser.add_argument("--start-year",   type=int)
    parser.add_argument("--end-year",     type=int)
    parser.add_argument("--download-dir", default=DEFAULT_DOWNLOAD_DIR)
    parser.add_argument("--output-dir",   default=DEFAULT_OUTPUT_DIR)
    parser.add_argument("--headless",     action="store_true")
    parser.add_argument("--wait",         type=int, default=60)
    args = parser.parse_args()

    years = _parse_years(args.years, args.start_year, args.end_year)
    _ensure_dir(args.download_dir)
    _ensure_dir(args.output_dir)

    driver = _build_driver(download_dir=args.download_dir, headless=args.headless)
    errors = []
    try:
        for year in years:
            try:
                baixar_csv_por_ano(
                    driver=driver,
                    ano=int(year),
                    download_dir=args.download_dir,
                    output_dir=args.output_dir,
                    wait_s=int(args.wait),
                )
            except Exception as e:
                errors.append((year, str(e)))
                try:
                    driver.switch_to.window(driver.window_handles[0])
                except Exception:
                    pass
    finally:
        driver.quit()

    if errors:
        print("\nAnos com erro:")
        for year, msg in errors:
            print(f"  {year}: {msg}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())