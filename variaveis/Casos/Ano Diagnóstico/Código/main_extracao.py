"""
Automação para extração de dados do Registro Hospitalar de Câncer - INCA
Localização primária: C50 MAMA | UF: Minas Gerais | Sexo: Feminino
Linha: Procedência | Coluna: Ano diagnóstico | Todos os anos disponíveis

Dependências:
    pip install selenium webdriver-manager

Uso:
    python scraper_inca_anodiagnostico.py
"""

import time
import shutil
import logging
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------------------------------------------
# Configuração de pastas
# ---------------------------------------------------------------------------
DOWNLOADS_DIR = Path("/home/anna/Downloads")
OUTPUT_DIR    = Path("/home/anna/tcc/variaveis/Casos/Ano Diagnóstico/Dados")  # <-- alterado
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

BASE_URL = "https://irhc.inca.gov.br/RHCNet/visualizaTabNetExterno.action"

ANOS = [
    2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014,
    2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005, 2004,
    2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996, 1995, 1994,
    1993, 1992, 1991, 1990, 1989, 1988, 1986, 1985,
]

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_driver() -> webdriver.Chrome:
    prefs = {
        "download.default_directory": str(DOWNLOADS_DIR),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    opts = Options()
    opts.add_experimental_option("prefs", prefs)
    # opts.add_argument("--headless=new")  # descomente para rodar sem janela
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
    """Seleciona opção num <select> pelo seu id, via JavaScript."""
    driver.execute_script("""
        var sel = document.getElementById(arguments[0]);
        if (!sel) throw new Error("Select id=" + arguments[0] + " não encontrado");
        sel.value = arguments[1];
        sel.dispatchEvent(new Event('change', {bubbles: true}));
    """, select_id, value)
    time.sleep(0.4)


def js_set_select_by_td_label(driver, label: str, value: str) -> str:
    """
    Localiza um <select> procurando o <td> com texto igual a 'label'
    e pegando o select na mesma <tr>. Retorna mensagem de status.
    """
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
                    // Tenta pegar o próximo <td> que tenha select
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


# ---------------------------------------------------------------------------
# Navegação inicial
# ---------------------------------------------------------------------------

def navegar_ate_formulario(driver):
    log.info("Abrindo página inicial...")
    driver.get(BASE_URL)
    time.sleep(2)

    log.info("Clicando em Consultas...")
    handles = set(driver.window_handles)
    link = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'selecionaBase')]"))
    )
    click_js(driver, link)
    driver.switch_to.window(wait_for_new_tab(driver, handles))
    time.sleep(2)

    log.info("Clicando em Enviar...")
    handles = set(driver.window_handles)
    enviar = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'envia()')]"))
    )
    click_js(driver, enviar)
    driver.switch_to.window(wait_for_new_tab(driver, handles))
    time.sleep(2)
    log.info(f"Formulário aberto: {driver.current_url}")


# ---------------------------------------------------------------------------
# Preenchimento do formulário
# ---------------------------------------------------------------------------

def preencher_formulario(driver, ano: int):
    """
    Ordem exata:
    1. Linha          → Procedência         (select id=linha,        value=12)
    2. Coluna         → Ano diagnóstico     (select id=coluna,       value=22)  <-- alterado
    3. Ano            → ano informado       (select id=periodo)
    4. Sexo           → Feminino            (select id=sexo,         value=2)
    5. UF proced.     → Minas Gerais        (td label "UF de procedência", value=MG)
    6. Procedência    → Todas as categorias (td label "Procedência", value='')
    7. Ano diagnóstico→ Todas as categorias (td label "Ano diagnóstico", value='')  <-- alterado
    8. Loc. prim.     → C50 MAMA           (td label "Localização primária", value=C50)
    """
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "linha")))

    # 1. Linha → Procedência
    log.info("  [1] Linha = Procedência")
    js_set_select_by_id(driver, "linha", "12")

    # 2. Coluna → Ano diagnóstico (value=22)  <-- era value=7 (Faixa etária)
    log.info("  [2] Coluna = Ano diagnóstico")
    js_set_select_by_id(driver, "coluna", "22")

    # 3. Ano — desmarca todos e seleciona só o desejado
    log.info(f"  [3] Ano = {ano}")
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

    # 4. Sexo → Feminino
    log.info("  [4] Sexo = Feminino")
    js_set_select_by_id(driver, "sexo", "2")

    # 5. UF de procedência → MG
    log.info("  [5] UF de procedência = Minas Gerais")
    res = js_set_select_by_td_label(driver, "UF de procedência", "MG")
    log.info(f"      Resultado: {res}")
    if "NAO" in res:
        res2 = driver.execute_script("""
            for (var s of document.querySelectorAll('select')) {
                for (var o of s.options) {
                    if (o.value === 'MG') {
                        s.value = 'MG';
                        s.dispatchEvent(new Event('change', {bubbles:true}));
                        return 'fallback OK: ' + s.name;
                    }
                }
            }
            return 'MG não encontrado';
        """)
        log.info(f"      Fallback UF: {res2}")
    time.sleep(0.5)

    # 6. Procedência → Todas as categorias (value vazio "")
    log.info("  [6] Procedência = Todas as categorias")
    res = js_set_select_by_td_label(driver, "Procedência", "")
    log.info(f"      Resultado: {res}")
    time.sleep(0.5)

    # 7. Ano diagnóstico → Todas as categorias (value="")  <-- alterado
    log.info("  [7] Ano diagnóstico = Todas as categorias")
    res = js_set_select_by_td_label(driver, "Ano diagnóstico", "")
    log.info(f"      Resultado: {res}")
    time.sleep(0.5)

    # 8. Localização primária → C50 MAMA
    log.info("  [8] Localização primária = C50 MAMA")
    res = js_set_select_by_td_label(driver, "Localização primária", "C50")
    log.info(f"      Resultado: {res}")

    if "OPCAO_NAO_ENCONTRADA" in res or "NAO" in res:
        log.warning("      C50 não encontrado — aguardando 4s e retentando...")
        time.sleep(4)
        res2 = driver.execute_script("""
            for (var s of document.querySelectorAll('select')) {
                for (var o of s.options) {
                    if (o.value === 'C50') {
                        s.value = 'C50';
                        s.dispatchEvent(new Event('change', {bubbles:true}));
                        return 'fallback OK: ' + s.name;
                    }
                }
            }
            return 'C50 ainda não encontrado';
        """)
        log.info(f"      Fallback localização: {res2}")

    time.sleep(1)


# ---------------------------------------------------------------------------
# Mostra + download + voltar
# ---------------------------------------------------------------------------

def clicar_mostra(driver):
    log.info("  Clicando em Mostra...")
    btn = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@value='Mostra']"))
    )
    click_js(driver, btn)
    log.info("  Aguardando tabela de resultados...")
    WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'downloadTabulador')]"))
    )
    time.sleep(1)
    log.info("  Tabela carregada!")


def baixar_csv(driver, ano: int) -> Path:
    remove_old_tabulador_files()
    log.info("  Clicando em 'Copia como .CSV'...")
    link = driver.find_element(By.XPATH, "//a[contains(@href, 'downloadTabulador')]")
    click_js(driver, link)
    downloaded = wait_for_download(timeout=90)
    destino = OUTPUT_DIR / f"AnoDiagnostico-{ano}.csv"  # <-- alterado
    shutil.move(str(downloaded), str(destino))
    log.info(f"  Arquivo salvo: {destino.name}")
    return destino


def voltar_formulario(driver):
    log.info("  Voltando ao formulário...")
    back = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'enviarDados')]"))
    )
    click_js(driver, back)
    time.sleep(2)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    log.info("=" * 60)
    log.info("INCA — Câncer de Mama | MG | Feminino | Ano Diagnóstico")
    log.info(f"Saída: {OUTPUT_DIR}")
    log.info("=" * 60)

    driver = make_driver()

    try:
        navegar_ate_formulario(driver)

        for i, ano in enumerate(ANOS):
            log.info(f"\n--- Ano {ano}  ({i+1}/{len(ANOS)}) ---")
            try:
                preencher_formulario(driver, ano)
                clicar_mostra(driver)
                baixar_csv(driver, ano)
                voltar_formulario(driver)

            except Exception as e:
                log.error(f"Erro no ano {ano}: {e}")
                try:
                    voltar_formulario(driver)
                except Exception:
                    try:
                        driver.back()
                        time.sleep(3)
                    except Exception:
                        log.error("Não foi possível recuperar. Encerrando.")
                        break

        log.info("\n" + "=" * 60)
        arquivos = sorted(OUTPUT_DIR.glob("AnoDiagnostico-*.csv"))
        log.info(f"Concluído! {len(arquivos)} arquivo(s) salvo(s) em {OUTPUT_DIR}")
        for f in arquivos:
            log.info(f"  {f.name}")

    finally:
        driver.quit()
        log.info("Navegador fechado.")


if __name__ == "__main__":
    main()