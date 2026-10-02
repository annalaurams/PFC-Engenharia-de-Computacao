# Extrai do TABNET/SISCAN os exames de mamografia (MG) por município e faixa etária, um CSV por ano.

import argparse
import os
import shutil
import time
from datetime import date
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Configuração e filtros da consulta

URL = "https://tabnet.datasus.gov.br/cgi/dhdat.exe?siscan/mamografia_atendmg.def"

PASTA_DOWNLOADS_PADRAO = os.path.expanduser("~/Downloads")
PASTA_SAIDA_PADRAO = "/home/anna/tcc/Limpeza e Integração/Mamografia/Dados"

FILTRO_LINHA = "Munic.da un.saúde"
FILTRO_COLUNA = "Faixa etária"
FILTRO_CONTEUDO = "Exames"
FILTRO_SEXO = "Feminino"
FILTRO_RACA_COR = "Todas as categorias"
FILTRO_ESCOLARIDADE = "Todas as categorias"

ANO_INICIAL_SERIE = 2012  # primeiro ano com série completa no SISCAN para este tabulador
ANOS_PADRAO = list(range(date.today().year - 1, ANO_INICIAL_SERIE, -1))


# Funções auxiliares

def garantir_pasta(caminho: str) -> None:
    os.makedirs(caminho, exist_ok=True)


def criar_driver(pasta_downloads: str, sem_interface: bool) -> webdriver.Chrome:
    opcoes = webdriver.ChromeOptions()
    preferencias = {
        "download.default_directory": os.path.abspath(pasta_downloads),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    opcoes.add_experimental_option("prefs", preferencias)
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")

    if sem_interface:
        opcoes.add_argument("--headless=new")

    servico = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servico, options=opcoes)
    driver.set_page_load_timeout(120)

    try:
        driver.execute_cdp_cmd(
            "Page.setDownloadBehavior",
            {"behavior": "allow", "downloadPath": os.path.abspath(pasta_downloads)},
        )
    except Exception:
        pass
    return driver


def selecionar_opcao_por_texto(driver: webdriver.Chrome, elemento_select, texto: str) -> None:
    encontrou = driver.execute_script(
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
        elemento_select,
        texto,
    )
    if not encontrou:
        raise NoSuchElementException(f"Opção '{texto}' não encontrada no select")


def clicar_com_seguranca(driver: webdriver.Chrome, elemento) -> None:
    try:
        elemento.click()
    except Exception:
        driver.execute_script("arguments[0].click();", elemento)


def rolar_ate_o_fim(driver: webdriver.Chrome, passos: int = 10, pausa_s: float = 0.5) -> None:
    for passo in range(1, passos + 1):
        driver.execute_script(
            f"window.scrollTo(0, document.body.scrollHeight * {passo / passos});"
        )
        time.sleep(pausa_s)
    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
    time.sleep(1)


def mudar_para_janela_de_resultado(driver: webdriver.Chrome, janela_original: str, tempo_limite_s: int = 60) -> bool:
    limite = time.time() + tempo_limite_s
    while time.time() < limite:
        novas_janelas = [h for h in driver.window_handles if h != janela_original]
        if novas_janelas:
            driver.switch_to.window(novas_janelas[-1])
            return True
        time.sleep(0.5)

    return False


def encontrar_link_csv(driver: webdriver.Chrome) -> str:
    estrategias = [
        (By.XPATH, "//a[normalize-space(text())='Salva como CSV']"),
        (By.XPATH, "//a[contains(text(),'CSV') and contains(@href,'.csv')]"),
        (By.CSS_SELECTOR, "table.escondido a[href$='.csv']"),
        (By.CSS_SELECTOR, "a[href*='csv/'][href$='.csv']"),
        (By.XPATH, "//a[contains(@href,'mamografia') and contains(@href,'.csv')]"),
        (By.XPATH, "//a[contains(@href,'.csv')]"),
    ]

    for por, seletor in estrategias:
        try:
            elemento = WebDriverWait(driver, 8).until(
                EC.presence_of_element_located((por, seletor))
            )
            href = elemento.get_attribute("href")
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

    raise NoSuchElementException("Link 'Salva como CSV' não encontrado")


def baixar_com_requests(driver: webdriver.Chrome, url: str, caminho_destino: str) -> None:
    garantir_pasta(os.path.dirname(caminho_destino))

    sessao = requests.Session()
    for cookie in driver.get_cookies():
        sessao.cookies.set(cookie["name"], cookie["value"])

    try:
        user_agent = driver.execute_script("return navigator.userAgent")
    except Exception:
        user_agent = "Mozilla/5.0"

    cabecalhos = {
        "User-Agent": user_agent,
        "Referer": driver.current_url,
    }

    with sessao.get(url, headers=cabecalhos, stream=True, timeout=180) as resposta:
        resposta.raise_for_status()
        with open(caminho_destino, "wb") as arquivo:
            for bloco in resposta.iter_content(chunk_size=64 * 1024):
                if bloco:
                    arquivo.write(bloco)


def mover_sobrescrevendo(origem: str, destino: str) -> None:
    garantir_pasta(os.path.dirname(destino))
    if os.path.exists(destino):
        os.remove(destino)
    shutil.move(origem, destino)


def baixar_csv_por_ano(
    driver: webdriver.Chrome,
    ano: int,
    pasta_downloads: str,
    pasta_saida: str,
    espera_s: int = 60,
) -> str:
    driver.get(URL)
    espera = WebDriverWait(driver, espera_s)

    janela_original = driver.current_window_handle

    # Preenchimento dos filtros
    selecionar_opcao_por_texto(driver, espera.until(EC.presence_of_element_located((By.ID, "L"))), FILTRO_LINHA)
    selecionar_opcao_por_texto(driver, espera.until(EC.presence_of_element_located((By.ID, "C"))), FILTRO_COLUNA)
    selecionar_opcao_por_texto(driver, espera.until(EC.presence_of_element_located((By.ID, "I"))), FILTRO_CONTEUDO)
    selecionar_opcao_por_texto(driver, espera.until(EC.presence_of_element_located((By.ID, "A"))), str(ano))

    try:
        selecionar_opcao_por_texto(driver, espera.until(EC.presence_of_element_located((By.ID, "S8"))), FILTRO_SEXO)
    except (TimeoutException, NoSuchElementException):
        pass

    try:
        selecionar_opcao_por_texto(driver, espera.until(EC.presence_of_element_located((By.ID, "S1"))), FILTRO_RACA_COR)
    except (TimeoutException, NoSuchElementException):
        pass

    try:
        selecionar_opcao_por_texto(driver, espera.until(EC.presence_of_element_located((By.ID, "S7"))), FILTRO_ESCOLARIDADE)
    except (TimeoutException, NoSuchElementException):
        pass

    # Execução da consulta e download do CSV
    botao_mostra = espera.until(
        EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[type="button"][value="Mostra"]'))
    )
    clicar_com_seguranca(driver, botao_mostra)

    mudou_de_janela = mudar_para_janela_de_resultado(driver, janela_original, tempo_limite_s=60)

    if not mudou_de_janela:
        time.sleep(5)

    rolar_ate_o_fim(driver, passos=10, pausa_s=0.5)
    time.sleep(2)

    href_csv = encontrar_link_csv(driver)
    url_csv = urljoin(driver.current_url, href_csv)
    url_analisada = urlparse(url_csv)
    if not url_analisada.scheme or not url_analisada.netloc:
        raise ValueError(f"URL inválida: {url_csv}")

    nome_temporario = os.path.basename(url_analisada.path)
    caminho_temporario = os.path.join(os.path.abspath(pasta_downloads), nome_temporario)
    baixar_com_requests(driver, url_csv, caminho_temporario)

    caminho_saida = os.path.join(os.path.abspath(pasta_saida), f"mamografia_{ano}.csv")
    mover_sobrescrevendo(caminho_temporario, caminho_saida)

    if mudou_de_janela:
        try:
            driver.close()
            driver.switch_to.window(janela_original)
        except Exception:
            pass

    return caminho_saida


def definir_anos(
    anos_informados: Optional[List[int]],
    ano_inicial: Optional[int],
    ano_final: Optional[int],
) -> List[int]:
    if anos_informados:
        return [int(ano) for ano in anos_informados]
    if ano_inicial is None and ano_final is None:
        return ANOS_PADRAO
    if ano_inicial is None or ano_final is None:
        raise ValueError("Use ambos --start-year e --end-year, ou apenas --years.")
    passo = -1 if int(ano_inicial) >= int(ano_final) else 1
    return list(range(int(ano_inicial), int(ano_final) + passo, passo))


# Execução principal

def main() -> int:
    analisador = argparse.ArgumentParser(
        description="Baixa CSV do TABNET (SISCAN Mamografia) por ano."
    )
    analisador.add_argument("--years", nargs="+", type=int)
    analisador.add_argument("--start-year", type=int)
    analisador.add_argument("--end-year", type=int)
    analisador.add_argument("--download-dir", default=PASTA_DOWNLOADS_PADRAO)
    analisador.add_argument("--output-dir", default=PASTA_SAIDA_PADRAO)
    analisador.add_argument("--headless", action="store_true")
    analisador.add_argument("--wait", type=int, default=60)
    argumentos = analisador.parse_args()

    anos = definir_anos(argumentos.years, argumentos.start_year, argumentos.end_year)
    garantir_pasta(argumentos.download_dir)
    garantir_pasta(argumentos.output_dir)

    driver = criar_driver(pasta_downloads=argumentos.download_dir, sem_interface=argumentos.headless)
    erros = []
    try:
        for ano in anos:
            try:
                baixar_csv_por_ano(
                    driver=driver,
                    ano=int(ano),
                    pasta_downloads=argumentos.download_dir,
                    pasta_saida=argumentos.output_dir,
                    espera_s=int(argumentos.wait),
                )
            except Exception as erro:
                erros.append((ano, str(erro)))
                try:
                    driver.switch_to.window(driver.window_handles[0])
                except Exception:
                    pass
    finally:
        driver.quit()

    if erros:
        print("\nAnos com erro:")
        for ano, mensagem in erros:
            print(f"  {ano}: {mensagem}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
