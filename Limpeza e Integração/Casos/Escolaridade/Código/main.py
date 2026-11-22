# Extrai do RHC-INCA os casos de câncer de mama (C50), MG, sexo feminino, por escolaridade, em todos os anos.

import shutil
import time
from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

# Configuração de pastas e filtros da consulta

PASTA_DOWNLOADS = Path("/home/anna/Downloads")
PASTA_SAIDA = Path("/home/anna/tcc/Limpeza e Integração/Casos/Escolaridade/Dados")
PASTA_SAIDA.mkdir(parents=True, exist_ok=True)

URL_BASE = "https://irhc.inca.gov.br/RHCNet/visualizaTabNetExterno.action"

LINHA_ID = "12"  # Procedência
COLUNA_ID = "14"  # escolaridade
SEXO_ID = "2"  # Feminino
UF_PROCEDENCIA = "MG"
LOCALIZACAO_PRIMARIA = "C50"  # Mama

ANOS = [
    2023, 2022, 2021, 2020, 2019, 2018, 2017, 2016, 2015, 2014,
    2013, 2012, 2011, 2010, 2009, 2008, 2007, 2006, 2005, 2004,
    2003, 2002, 2001, 2000, 1999, 1998, 1997, 1996, 1995, 1994,
    1993, 1992, 1991, 1990, 1989, 1988, 1986, 1985,
]


# Funções auxiliares

def criar_driver() -> webdriver.Chrome:
    """Abre o Chrome controlado pelo Selenium, configurado para salvar downloads direto em PASTA_DOWNLOADS."""
    preferencias = {
        "download.default_directory": str(PASTA_DOWNLOADS),
        "download.prompt_for_download": False,
        "download.directory_upgrade": True,
        "safebrowsing.enabled": True,
    }
    opcoes = Options()
    opcoes.add_experimental_option("prefs", preferencias)
    opcoes.add_argument("--no-sandbox")
    opcoes.add_argument("--disable-dev-shm-usage")
    opcoes.add_argument("--window-size=1400,900")

    servico = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=servico, options=opcoes)
    driver.implicitly_wait(10)
    return driver


def esperar_nova_aba(driver, abas_conhecidas: set, tempo_limite: int = 15) -> str:
    """Espera abrir uma aba/janela nova (diferente das já conhecidas) e devolve o seu handle."""
    limite = time.time() + tempo_limite
    while time.time() < limite:
        novas = set(driver.window_handles) - abas_conhecidas
        if novas:
            return novas.pop()
        time.sleep(0.5)
    raise TimeoutError("Nova aba não abriu no tempo esperado.")


def clicar_via_js(driver, elemento):
    """Clica no elemento via JavaScript (mais confiável que o clique normal do Selenium nesse site)."""
    driver.execute_script("arguments[0].click();", elemento)


def remover_arquivos_tabulador_antigos():
    """Remove CSVs de downloads anteriores, para não confundir com o próximo arquivo baixado."""
    for arquivo in PASTA_DOWNLOADS.glob("tabulador_*.csv"):
        arquivo.unlink()


def esperar_download(tempo_limite: int = 90) -> Path:
    """Espera o navegador terminar de baixar o CSV do tabulador (ignora arquivos ainda em .crdownload) e devolve o mais recente."""
    limite = time.time() + tempo_limite
    while time.time() < limite:
        candidatos = [
            arquivo for arquivo in PASTA_DOWNLOADS.glob("tabulador_*.csv")
            if not arquivo.name.endswith(".crdownload")
        ]
        if candidatos:
            return max(candidatos, key=lambda arquivo: arquivo.stat().st_mtime)
        time.sleep(1)
    raise TimeoutError("Download não concluído.")


def definir_select_por_id_js(driver, id_select: str, valor: str):
    """Define o valor de um <select> pelo `id`, disparando o evento `change` (necessário para o JS do site reagir)."""
    driver.execute_script("""
        var sel = document.getElementById(arguments[0]);
        if (!sel) throw new Error("Select id=" + arguments[0] + " não encontrado");
        sel.value = arguments[1];
        sel.dispatchEvent(new Event('change', {bubbles: true}));
    """, id_select, valor)
    time.sleep(0.4)


def definir_select_por_rotulo_js(driver, rotulo: str, valor: str) -> str:
    """Define o valor de um <select> localizado pelo rótulo (texto da célula da tabela ao lado), já que o formulário não dá id estável a todos os campos. Devolve uma string de status para diagnóstico."""
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
    """, rotulo, valor)
    return resultado


# Navegação até o formulário

def navegar_ate_formulario(driver):
    """Percorre as telas iniciais do RHC-INCA (seleção de base, confirmação) até chegar no formulário de consulta, trocando de aba a cada etapa."""
    driver.get(URL_BASE)
    time.sleep(2)

    abas = set(driver.window_handles)
    link = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'selecionaBase')]"))
    )
    clicar_via_js(driver, link)
    driver.switch_to.window(esperar_nova_aba(driver, abas))
    time.sleep(2)

    abas = set(driver.window_handles)
    enviar = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'envia()')]"))
    )
    clicar_via_js(driver, enviar)
    driver.switch_to.window(esperar_nova_aba(driver, abas))
    time.sleep(2)


# Preenchimento do formulário

def preencher_formulario(driver, ano: int):
    """Preenche no formulário do tabulador: layout linha/coluna, ano, sexo, UF de procedência, procedência em branco
    (todas), escolaridade em branco (todas, pois é a variável de interesse na coluna) e localização primária C50 (mama)."""
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.ID, "linha")))

    definir_select_por_id_js(driver, "linha", LINHA_ID)
    definir_select_por_id_js(driver, "coluna", COLUNA_ID)
    # Seleciona o ano da consulta na lista de períodos disponíveis
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

    definir_select_por_id_js(driver, "sexo", SEXO_ID)

    resultado = definir_select_por_rotulo_js(driver, "UF de procedência", UF_PROCEDENCIA)
    if "NAO" in resultado:
        # Se o select não foi localizado pelo rótulo, tenta achar diretamente a opção com esse valor em qualquer select da página
        driver.execute_script("""
            for (var s of document.querySelectorAll('select')) {
                for (var o of s.options) {
                    if (o.value === arguments[0]) {
                        s.value = arguments[0];
                        s.dispatchEvent(new Event('change', {bubbles:true}));
                        return 'fallback OK';
                    }
                }
            }
        """, UF_PROCEDENCIA)
    time.sleep(0.5)

    definir_select_por_rotulo_js(driver, "Procedência", "")
    time.sleep(0.5)

    definir_select_por_id_js(driver, "escolaridade", "")
    time.sleep(0.5)

    resultado = definir_select_por_rotulo_js(driver, "Localização primária", LOCALIZACAO_PRIMARIA)

    if "OPCAO_NAO_ENCONTRADA" in resultado or "NAO" in resultado:
        # A lista de opções de localização primária pode carregar com atraso (depende da UF escolhida) --
        # espera um pouco e tenta de novo em qualquer select da página.
        time.sleep(4)
        driver.execute_script("""
            for (var s of document.querySelectorAll('select')) {
                for (var o of s.options) {
                    if (o.value === arguments[0]) {
                        s.value = arguments[0];
                        s.dispatchEvent(new Event('change', {bubbles:true}));
                        return 'OK';
                    }
                }
            }
        """, LOCALIZACAO_PRIMARIA)

    time.sleep(1)


# Consulta, download e retorno ao formulário

def clicar_mostra(driver):
    """Clica em 'Mostra' para executar a consulta e espera o link de download do CSV aparecer no resultado."""
    botao = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//input[@value='Mostra']"))
    )
    clicar_via_js(driver, botao)
    WebDriverWait(driver, 90).until(
        EC.presence_of_element_located((By.XPATH, "//a[contains(@href, 'downloadTabulador')]"))
    )
    time.sleep(1)


def baixar_csv(driver, ano: int) -> Path:
    """Baixa o CSV do resultado e o move/renomeia para PASTA_SAIDA como `RacaCor-{ano}.csv`."""
    remover_arquivos_tabulador_antigos()
    link = driver.find_element(By.XPATH, "//a[contains(@href, 'downloadTabulador')]")
    clicar_via_js(driver, link)
    baixado = esperar_download(tempo_limite=90)
    destino = PASTA_SAIDA / f"Escolaridade-{ano}.csv"
    shutil.move(str(baixado), str(destino))
    return destino


def voltar_formulario(driver):
    """Volta da tela de resultado para o formulário de consulta, para preencher o próximo ano."""
    voltar = WebDriverWait(driver, 15).until(
        EC.element_to_be_clickable((By.XPATH, "//a[contains(@href, 'enviarDados')]"))
    )
    clicar_via_js(driver, voltar)
    time.sleep(2)


# Execução principal

def main():
    """Navega até o formulário uma vez e, para cada ano em ANOS, preenche, consulta, baixa o CSV e volta ao formulário,
    registrando ano a ano quais baixaram com sucesso e quais falharam (sem interromper o laço num erro isolado)."""
    driver = criar_driver()
    anos_baixados = []
    anos_com_erro = []

    try:
        navegar_ate_formulario(driver)

        for ano in ANOS:
            try:
                preencher_formulario(driver, ano)
                clicar_mostra(driver)
                baixar_csv(driver, ano)
                voltar_formulario(driver)
                anos_baixados.append(ano)

            except Exception as erro:
                print(f"[ERRO] Ano {ano}: {erro}")
                anos_com_erro.append(ano)
                try:
                    voltar_formulario(driver)
                except Exception:
                    try:
                        driver.back()
                        time.sleep(3)
                    except Exception:
                        break

    finally:
        driver.quit()

    print(f"\nBaixados com sucesso: {sorted(anos_baixados)}")
    if anos_com_erro:
        print(f"Com erro: {sorted(anos_com_erro)}")


if __name__ == "__main__":
    main()
