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


URL = "https://tabnet.datasus.gov.br/cgi/dhdat.exe?siscan/mamografia_atendmg.def"

DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/Downloads")
DEFAULT_OUTPUT_DIR = "/home/anna/tcc/Variáveis/Mamografia/Dados"


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
    """Rola a página gradualmente até o fim."""
    for i in range(1, steps + 1):
        driver.execute_script(
            f"window.scrollTo(0, document.body.scrollHeight * {i / steps});"
        )
        time.sleep(pause_s)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)


def _switch_to_result_window(driver: webdriver.Chrome, original_handle: str, timeout_s: int = 60) -> bool:
    """
    Aguarda uma nova janela/aba abrir e troca para ela.
    O TABNET abre o relatório em uma nova janela ao clicar em 'Mostra'.
    Retorna True se trocou de janela, False se ficou na mesma.
    """
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        handles = driver.window_handles
        new_handles = [h for h in handles if h != original_handle]
        if new_handles:
            driver.switch_to.window(new_handles[-1])
            print(f"  Nova janela detectada: {driver.current_url}")
            return True
        time.sleep(0.5)

    print("  Nenhuma nova janela — o resultado pode estar na mesma página.")
    return False


def _find_csv_href(driver: webdriver.Chrome) -> str:
    """
    Tenta múltiplas estratégias para encontrar o href do link CSV.
    Imprime todos os links para diagnóstico se falhar.
    """
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
                print(f"  Link CSV encontrado com: {selector}")
                return href
        except TimeoutException:
            continue

    # Fallback via JavaScript
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
        print(f"  Link CSV encontrado via JS: {href}")
        return href

    # Debug: lista todos os links presentes
    all_links = driver.execute_script(
        "return Array.from(document.querySelectorAll('a')).map(a => ({text: a.textContent.trim().slice(0,80), href: a.href}));"
    )
    print("  === Diagnóstico: links encontrados na página ===")
    for lnk in all_links:
        if lnk["href"]:
            print(f"    '{lnk['text']}'  →  {lnk['href']}")

    raise NoSuchElementException(
        "Não foi possível encontrar o link 'Salva como CSV' na página. "
        "Veja o diagnóstico acima."
    )


def _download_with_requests(driver: webdriver.Chrome, url: str, dest_path: str) -> None:
    """Baixa o arquivo usando requests com os cookies da sessão do browser."""
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

    print(f"  Baixando: {url}")
    with session.get(url, headers=headers, stream=True, timeout=180) as resp:
        resp.raise_for_status()
        with open(dest_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=64 * 1024):
                if chunk:
                    f.write(chunk)
    print(f"  Concluído: {os.path.getsize(dest_path)} bytes")


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
    print(f"\n{'='*50}")
    print(f"Processando ano: {ano}")
    print(f"{'='*50}")

    driver.get(URL)
    wait = WebDriverWait(driver, wait_s)

    # Guarda handle da janela original ANTES de clicar Mostra
    original_handle = driver.current_window_handle
    print(f"  Janela original: {original_handle}")

    # ── Configura os selects ──
    print("Configurando: Linha = Munic.da un.saúde")
    _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "L"))), "Munic.da un.saúde")

    print("Configurando: Coluna = Faixa etária")
    _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "C"))), "Faixa etária")

    print("Configurando: Medida = Exames")
    _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "I"))), "Exames")

    print(f"Configurando: Período = {ano}")
    _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "A"))), str(ano))

    print("Configurando: Sexo = Feminino")
    try:
        _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "S8"))), "Feminino")
    except (TimeoutException, NoSuchElementException) as e:
        print(f"  Aviso: {e}")

    print("Configurando: Município = Todas as categorias")
    try:
        _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "S1"))), "Todas as categorias")
    except (TimeoutException, NoSuchElementException) as e:
        print(f"  Aviso: {e}")

    print("Configurando: Faixa etária (filtro) = Todas as categorias")
    try:
        _set_select_by_visible_text(driver, wait.until(EC.presence_of_element_located((By.ID, "S7"))), "Todas as categorias")
    except (TimeoutException, NoSuchElementException) as e:
        print(f"  Aviso: {e}")

    # ── Clica em Mostra ──
    print("Clicando em 'Mostra'...")
    mostra_btn = wait.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="button"][value="Mostra"]'))
    )
    _safe_click(driver, mostra_btn)

    # ── Troca para a nova janela do relatório ──
    print("Aguardando janela do relatório...")
    switched = _switch_to_result_window(driver, original_handle, timeout_s=60)

    # Se não abriu nova janela, aguarda carregar na mesma página
    if not switched:
        time.sleep(5)

    # ── Rola até o fim para revelar os links de exportação ──
    print("Rolando página para revelar links de download...")
    _scroll_to_bottom(driver, steps=10, pause_s=0.5)
    time.sleep(2)

    # ── Encontra e baixa o CSV ──
    print("Procurando link 'Salva como CSV'...")
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
    print(f"Arquivo salvo: {out_path}")

    # ── Fecha janela do relatório e volta para a principal ──
    if switched:
        try:
            driver.close()
            driver.switch_to.window(original_handle)
            print("  Janela do relatório fechada.")
        except Exception as e:
            print(f"  Aviso ao fechar janela: {e}")

    return out_path


def _parse_years(
    args_years: Optional[List[int]],
    start_year: Optional[int],
    end_year: Optional[int],
) -> List[int]:
    if args_years:
        return [int(y) for y in args_years]
    if start_year is None and end_year is None:
        current_year = date.today().year
        return list(range(current_year - 1, 2012, -1))
    if start_year is None or end_year is None:
        raise ValueError("Use ambos --start-year e --end-year, ou apenas --years.")
    step = -1 if int(start_year) >= int(end_year) else 1
    return list(range(int(start_year), int(end_year) + step, step))


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
    print(f"Anos a baixar: {years}")
    _ensure_dir(args.download_dir)
    _ensure_dir(args.output_dir)

    driver = _build_driver(download_dir=args.download_dir, headless=args.headless)
    errors = []
    try:
        for year in years:
            try:
                out = baixar_csv_por_ano(
                    driver=driver,
                    ano=int(year),
                    download_dir=args.download_dir,
                    output_dir=args.output_dir,
                    wait_s=int(args.wait),
                )
                print(f"✓ {year}: {out}")
            except Exception as e:
                print(f"✗ Erro no ano {year}: {e}")
                errors.append((year, str(e)))
                # Tenta recuperar a janela principal
                try:
                    driver.switch_to.window(driver.window_handles[0])
                except Exception:
                    pass
    finally:
        driver.quit()

    if errors:
        print(f"\nErros em {len(errors)} ano(s):")
        for yr, err in errors:
            print(f"  {yr}: {err}")
        return 1

    print("\nTodos os anos baixados com sucesso!")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())