import os
import re
import time
from typing import Optional
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.edge.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from src.config import URL_CONSULTA

from typing import Optional

def obtener_ruta_edge() -> Optional[str]:
    rutas_posibles = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]

    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            return ruta
    return None


def configurar_driver() -> webdriver.Edge:
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
    return WebDriverWait(driver, timeout)


def consultar_radicado(driver, wait, radicado: str) -> dict:
    driver.get(URL_CONSULTA)

    campo = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "input[placeholder*='23'], input[id*='NumeroRadicacion']")
        )
    )
    campo.clear()
    campo.send_keys(radicado)
    time.sleep(1)

    label_todos = wait.until(
        EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Todos')]"))
    )
    driver.execute_script("arguments[0].click();", label_todos)
    campo.send_keys(Keys.ENTER)

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
    