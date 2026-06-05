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
from urllib.parse import urljoin

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
DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
DEMANDANTE_LABELS = ["DEMANDANTE", "ACCIONANTE"]
DEMANDADO_LABELS = ["DEMANDADO", "INDICIADO", "CAUSANTE"]


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


def _normalizar_texto(texto: str | None) -> str:
    """Limpia espacios repetidos sin cambiar el contenido juridico."""
    return re.sub(r"\s+", " ", (texto or "").strip())


def _extraer_valor_etiquetado(texto: str, etiquetas: list[str], etiquetas_corte: list[str]) -> str | None:
    """Extrae valores de celdas que contienen varias etiquetas procesales."""
    if not texto:
        return None

    etiquetas_patron = "|".join(re.escape(etiqueta) for etiqueta in etiquetas)
    corte_patron = "|".join(re.escape(etiqueta) for etiqueta in etiquetas_corte)
    patron = re.compile(
        rf"(?:{etiquetas_patron})(?:/[A-ZÁÉÍÓÚÑ\s]+)*\s*:\s*(.*?)(?=(?:{corte_patron})(?:/[A-ZÁÉÍÓÚÑ\s]+)*\s*:|$)",
        re.IGNORECASE | re.DOTALL,
    )
    match = patron.search(texto)
    if not match:
        return None
    valor = _normalizar_texto(match.group(1))
    return valor or None


def _parsear_sujetos(texto: str) -> tuple[str | None, str | None]:
    """Separa demandante y demandado aunque vengan en la misma celda."""
    demandante = _extraer_valor_etiquetado(texto, DEMANDANTE_LABELS, DEMANDADO_LABELS)
    demandado = _extraer_valor_etiquetado(texto, DEMANDADO_LABELS, DEMANDANTE_LABELS)
    return demandante, demandado


def _extraer_resumen_resultado(fila) -> dict:
    """Lee la fila principal de resultados antes de entrar al detalle."""
    columnas = fila.find_elements(By.TAG_NAME, "td")
    demandante = None
    demandado = None
    juzgado = None
    fechas: list[str] = []

    for col in columnas:
        texto = col.text.strip()
        texto_upper = texto.upper()

        sujeto_demandante, sujeto_demandado = _parsear_sujetos(texto)
        demandante = demandante or sujeto_demandante
        demandado = demandado or sujeto_demandado

        if not juzgado and ("JUZGADO" in texto_upper or "DESPACHO" in texto_upper):
            juzgado = _normalizar_texto(texto)

        fechas.extend(DATE_RE.findall(texto))

    return {
        "Juzgado": juzgado or "No identificado",
        "Demandante": demandante or "No identificado",
        "Demandado": demandado or "No identificado",
        "Fecha_radicacion": min(fechas) if fechas else None,
        "Fecha_ultima_actuacion": max(fechas) if fechas else None,
    }


def _click_detalle_resultado(driver, wait, fila, radicado: str) -> bool:
    """Abre el detalle del proceso desde el link del radicado."""
    candidatos = []
    selectores = [
        ".//*[@href]",
        ".//*[@ng-reflect-router-link]",
        f".//a[contains(normalize-space(), '{radicado}')]",
        f".//td[contains(normalize-space(), '{radicado}')]",
        ".//a",
        ".//button",
    ]
    for selector in selectores:
        candidatos.extend(fila.find_elements(By.XPATH, selector))

    for candidato in candidatos:
        try:
            href = candidato.get_attribute("href") or candidato.get_attribute("ng-reflect-router-link")
            if href:
                driver.get(urljoin(driver.current_url, href))
                WebDriverWait(driver, 6).until(
                    EC.presence_of_element_located(
                        (
                            By.XPATH,
                            "//*[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'DETALLE DEL PROCESO')]",
                        )
                    )
                )
                return True

            ventanas_antes = set(driver.window_handles)
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", candidato)
            time.sleep(0.2)
            try:
                candidato.click()
            except Exception:
                driver.execute_script("arguments[0].click();", candidato)

            ventanas_despues = set(driver.window_handles)
            nuevas_ventanas = ventanas_despues - ventanas_antes
            if nuevas_ventanas:
                driver.switch_to.window(nuevas_ventanas.pop())

            WebDriverWait(driver, 6).until(
                EC.presence_of_element_located(
                    (
                        By.XPATH,
                        "//*[contains(translate(., 'abcdefghijklmnopqrstuvwxyz', 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'), 'DETALLE DEL PROCESO')]",
                    )
                )
            )
            return True
        except Exception:
            continue

    logger.warning("No se pudo abrir el detalle del radicado %s desde la fila de resultados.", radicado)
    return False


def _buscar_tabla_actuaciones(driver):
    """Ubica la tabla de actuaciones por sus encabezados visibles."""
    tablas = driver.find_elements(By.XPATH, "//table")
    for tabla in tablas:
        encabezado = tabla.text.upper()
        if "FECHA DE ACTU" in encabezado and "ANOTACI" in encabezado:
            return tabla
    return None


def _extraer_actuaciones_detalle(driver, wait) -> list[dict]:
    """Extrae fecha, actuacion y anotacion desde el detalle del proceso."""
    tab_selectors = [
        "//div[@role='tab' and contains(translate(normalize-space(), 'abcdefghijklmnopqrstuvwxyzáéíóú', 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚ'), 'ACTUACIONES')]",
        "//button[contains(translate(normalize-space(), 'abcdefghijklmnopqrstuvwxyzáéíóú', 'ABCDEFGHIJKLMNOPQRSTUVWXYZÁÉÍÓÚ'), 'ACTUACIONES')]",
    ]
    for selector in tab_selectors:
        try:
            tab = wait.until(EC.element_to_be_clickable((By.XPATH, selector)))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tab)
            time.sleep(0.2)
            try:
                tab.click()
            except Exception:
                driver.execute_script("arguments[0].click();", tab)
            time.sleep(1.0)
            break
        except Exception:
            continue

    try:
        tabla = WebDriverWait(driver, 6).until(lambda active_driver: _buscar_tabla_actuaciones(active_driver))
    except Exception:
        tabla = _buscar_tabla_actuaciones(driver)
    if not tabla:
        logger.warning("No se encontro tabla de actuaciones en el detalle del proceso.")
        return []

    actuaciones: list[dict] = []
    for fila in tabla.find_elements(By.XPATH, ".//tbody/tr"):
        columnas = [_normalizar_texto(col.text) for col in fila.find_elements(By.TAG_NAME, "td")]
        if len(columnas) < 3:
            continue
        actuaciones.append(
            {
                "Fecha": columnas[0] or None,
                "Actuacion": columnas[1] or "Actuacion sin titulo",
                "Anotacion": columnas[2] or None,
                "Fecha_inicia_termino": columnas[3] if len(columnas) > 3 else None,
                "Fecha_finaliza_termino": columnas[4] if len(columnas) > 4 else None,
                "Fecha_registro": columnas[5] if len(columnas) > 5 else None,
            }
        )
    return actuaciones


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

    resumen = _extraer_resumen_resultado(filas[0])
    actuaciones = []
    if _click_detalle_resultado(driver, wait, filas[0], radicado):
        actuaciones = _extraer_actuaciones_detalle(driver, wait)

    fecha_ultima_actuacion = resumen["Fecha_ultima_actuacion"]
    if actuaciones and actuaciones[0].get("Fecha"):
        fecha_ultima_actuacion = actuaciones[0]["Fecha"]

    partes = []
    if resumen["Demandante"] != "No identificado":
        partes.append(f"Demandante: {resumen['Demandante']}")
    if resumen["Demandado"] != "No identificado":
        partes.append(f"Demandado: {resumen['Demandado']}")

    return {
        "Radicado": radicado,
        "Juzgado": resumen["Juzgado"],
        "Demandante": resumen["Demandante"],
        "Demandado": resumen["Demandado"],
        "Partes": " | ".join(partes) if partes else "No identificadas",
        "Fecha_radicacion": resumen["Fecha_radicacion"],
        "Fecha_ultima_actuacion": fecha_ultima_actuacion,
        "Ultima_actuacion": actuaciones[0]["Actuacion"] if actuaciones else None,
        "Ultima_anotacion": actuaciones[0]["Anotacion"] if actuaciones else None,
        "Actuaciones": actuaciones,
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
