import os
import re
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.config import URL_CONSULTA


# ===============================
# CONFIGURACIÓN DEL NAVEGADOR
# ===============================

def obtener_ruta_edge() -> Optional[str]:
    """
    Busca la ruta de instalación de Microsoft Edge en ubicaciones comunes de Windows.

    Returns:
        Ruta del ejecutable de Edge si existe. Si no se encuentra, retorna None.
    """
    rutas_posibles = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            return ruta

    return None


def configurar_driver() -> webdriver.Edge:
    """
    Crea y configura una instancia del navegador Edge para Selenium.

    Returns:
        Instancia configurada de Edge WebDriver.

    Raises:
        FileNotFoundError: Si Microsoft Edge no está instalado en el equipo.
    """
    options = Options()
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")

    ruta_edge = obtener_ruta_edge()
    if not ruta_edge:
        raise FileNotFoundError("No se encontró Microsoft Edge instalado en el equipo.")

    options.binary_location = ruta_edge

    driver = webdriver.Edge(options=options)
    driver.set_window_size(1200, 800)
    return driver


def crear_wait(driver, timeout: int = 20) -> WebDriverWait:
    """
    Crea un objeto WebDriverWait reutilizable.

    Args:
        driver: Instancia activa del navegador.
        timeout: Tiempo máximo de espera en segundos.

    Returns:
        Instancia de WebDriverWait.
    """
    return WebDriverWait(driver, timeout)


# ===============================
# CONSULTA DE RADICADOS
# ===============================

def consultar_radicado(driver, wait, radicado: str) -> dict:
    """
    Consulta un radicado en la plataforma de la Rama Judicial y extrae
    la información principal del proceso.

    Args:
        driver: Instancia activa de Selenium WebDriver.
        wait: Instancia de WebDriverWait.
        radicado: Número de radicado a consultar.

    Returns:
        Diccionario con la información extraída del proceso.

    Raises:
        ValueError: Si no se encuentran resultados para el radicado.
    """
    driver.get(URL_CONSULTA)

    # Campo principal de búsqueda por número de radicación
    campo = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "input[placeholder*='23'], input[id*='NumeroRadicacion']")
        )
    )
    campo.clear()
    campo.send_keys(radicado)
    time.sleep(1)

    # Selecciona la opción "Todos" antes de ejecutar la búsqueda
    label_todos = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Todos')]"))
    )
    driver.execute_script("arguments[0].click();", label_todos)
    campo.send_keys(Keys.ENTER)

    # Espera a que aparezcan filas con resultados
    wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody/tr")))
    filas = driver.find_elements(By.XPATH, "//table/tbody/tr")

    if not filas:
        raise ValueError("No se encontraron resultados para el radicado.")

    fila = filas[0]
    columnas = fila.find_elements(By.TAG_NAME, "td")

    demandante = "No identificado"
    demandado = "No identificado"
    juzgado = "No identificado"
    fechas = []

    # Recorre las columnas de la fila encontrada para extraer datos relevantes
    for col in columnas:
        texto = col.text.strip()
        texto_upper = texto.upper()

        if "DEMANDANTE" in texto_upper or "ACCIONANTE" in texto_upper:
            if demandante == "No identificado":
                demandante = texto.split(":")[-1].strip()

        elif "DEMANDADO" in texto_upper or "INDICIADO" in texto_upper or "CAUSANTE" in texto_upper:
            if demandado == "No identificado":
                demandado = texto.split(":")[-1].strip()

        elif "JUZGADO" in texto_upper or "DESPACHO" in texto_upper:
            juzgado = texto.strip()

        fechas.extend(re.findall(r"\d{4}-\d{2}-\d{2}", texto))

    # Construcción amigable del campo "Partes"
    partes = []

    if demandante != "No identificado":
        partes.append(f"Demandante: {demandante}")

    if demandado != "No identificado":
        partes.append(f"Demandado: {demandado}")

    partes_texto = " | ".join(partes) if partes else "No identificadas"

    return {
        "Radicado": radicado,
        "Juzgado": juzgado,
        "Demandante": demandante,
        "Demandado": demandado,
        "Partes": partes_texto,
        "Fecha_radicacion": min(fechas) if fechas else "Sin fecha",
        "Fecha_ultima_actuacion": max(fechas) if fechas else "Sin fecha",
    }