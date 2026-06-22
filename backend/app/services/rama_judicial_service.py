from __future__ import annotations

from backend.app.services.scraper_service import configurar_driver, consultar_con_retries, crear_wait


def buscar_proceso_cpnu(numero_proceso: str) -> dict:
    """Consulta la CPNJ reutilizando el scraper Selenium existente."""
    driver = configurar_driver()
    try:
        wait = crear_wait(driver)
        return consultar_con_retries(driver, wait, numero_proceso)
    finally:
        driver.quit()
