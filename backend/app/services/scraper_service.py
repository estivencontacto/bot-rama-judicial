"""Scraper Selenium para consulta de radicados.

Mantiene la metodologia original de consulta web, pero preparada para modo
headless, retries, timeouts y ejecucion en Docker o escritorio local.
"""

from __future__ import annotations

import logging
import os
import re
import time
from dataclasses import dataclass
from typing import Optional

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from backend.app.core.settings import get_settings


logger = logging.getLogger(__name__)


class ScraperError(RuntimeError):
    """Error base para fallos controlados del scraper."""
    pass


class RadicadoSinResultados(ScraperError):
    """Se usa cuando la Rama Judicial no retorna filas para el radicado."""
    pass


@dataclass
class ScraperConfig:
    """Configuracion efectiva del scraper tomada desde variables de entorno."""
    headless: bool
    timeout_seconds: int
    max_retries: int
    retry_delay_seconds: float
    url_consulta: str


def obtener_ruta_edge() -> Optional[str]:
    """Detecta Microsoft Edge en Windows para mantener compatibilidad local."""
    rutas_posibles = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    ]
    for ruta in rutas_posibles:
        if os.path.exists(ruta):
            return ruta
    return None


def get_scraper_config() -> ScraperConfig:
    """Construye la configuracion tipada del scraper."""
    settings = get_settings()
    return ScraperConfig(
        headless=settings.selenium_headless,
        timeout_seconds=settings.selenium_timeout_seconds,
        max_retries=settings.scraper_max_retries,
        retry_delay_seconds=settings.scraper_retry_delay_seconds,
        url_consulta=settings.rama_judicial_url,
    )


def _common_options(options, use_headless: bool):
    """Aplica opciones comunes para reducir ruido y soportar contenedores."""
    options.add_argument("--disable-notifications")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--no-sandbox")
    if use_headless:
        options.add_argument("--headless=new")
    return options


def configurar_driver(headless: bool | None = None):
    """Inicializa Chrome o Edge con parametros seguros para automatizacion."""
    settings = get_settings()
    use_headless = settings.selenium_headless if headless is None else headless

    if settings.selenium_browser.lower() == "chrome":
        options = _common_options(ChromeOptions(), use_headless)
        driver = webdriver.Chrome(options=options)
    else:
        options = _common_options(EdgeOptions(), use_headless)
        ruta_edge = obtener_ruta_edge()
        if ruta_edge:
            options.binary_location = ruta_edge
        driver = webdriver.Edge(options=options)

    driver.set_page_load_timeout(settings.selenium_timeout_seconds + 10)
    driver.set_window_size(1366, 900)
    return driver


def crear_wait(driver, timeout: int | None = None) -> WebDriverWait:
    """Crea un wait explicito reutilizable para eventos de la pagina."""
    settings = get_settings()
    return WebDriverWait(driver, timeout or settings.selenium_timeout_seconds)


def consultar_radicado(driver, wait, radicado: str) -> dict:
    """Consulta un radicado y normaliza los datos relevantes del resultado."""
    settings = get_settings()
    driver.get(settings.rama_judicial_url)

    campo = wait.until(
        EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "input[placeholder*='23'], input[id*='NumeroRadicacion']")
        )
    )
    campo.clear()
    campo.send_keys(radicado)
    time.sleep(0.7)

    label_todos = wait.until(EC.element_to_be_clickable((By.XPATH, "//label[contains(text(), 'Todos')]")))
    driver.execute_script("arguments[0].click();", label_todos)
    campo.send_keys(Keys.ENTER)

    wait.until(EC.presence_of_element_located((By.XPATH, "//table/tbody/tr")))
    filas = driver.find_elements(By.XPATH, "//table/tbody/tr")
    if not filas:
        raise RadicadoSinResultados("No se encontraron resultados para el radicado.")

    columnas = filas[0].find_elements(By.TAG_NAME, "td")
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
            juzgado = texto
        fechas.extend(re.findall(r"\d{4}-\d{2}-\d{2}", texto))

    partes = []
    if demandante != "No identificado":
        partes.append(f"Demandante: {demandante}")
    if demandado != "No identificado":
        partes.append(f"Demandado: {demandado}")

    return {
        "Radicado": radicado,
        "Juzgado": juzgado,
        "Demandante": demandante,
        "Demandado": demandado,
        "Partes": " | ".join(partes) if partes else "No identificadas",
        "Fecha_radicacion": min(fechas) if fechas else None,
        "Fecha_ultima_actuacion": max(fechas) if fechas else None,
    }


def consultar_con_retries(driver, wait, radicado: str) -> dict:
    """Reintenta la consulta ante timeouts o fallos transitorios del sitio."""
    config = get_scraper_config()
    last_error: Exception | None = None
    for attempt in range(1, config.max_retries + 1):
        try:
            logger.info("Consultando radicado %s intento %s/%s", radicado, attempt, config.max_retries)
            return consultar_radicado(driver, wait, radicado)
        except (TimeoutException, WebDriverException, ScraperError, ValueError) as exc:
            last_error = exc
            logger.warning("Fallo consultando radicado %s: %s", radicado, exc)
            if attempt < config.max_retries:
                time.sleep(config.retry_delay_seconds * attempt)
    raise ScraperError(str(last_error) if last_error else "Error desconocido en scraper")
