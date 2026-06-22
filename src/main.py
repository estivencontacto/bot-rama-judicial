import time
from datetime import datetime

import pandas as pd

from src.config import (
    ARCHIVO_ESTADO,
    ARCHIVO_LISTADO,
    OUTPUT_DIR,
    validar_configuracion,
)
from src.estado import construir_estado, guardar_estado
from src.reportes import exportar_excel
from src.scraper import configurar_driver, crear_wait, consultar_radicado
from src.telegram_utils import notificar_telegram


# ===============================
# CARGA DE DATOS DE ENTRADA
# ===============================

def cargar_radicados(ruta_excel: str) -> list[str]:
    """
    Lee el archivo Excel de entrada y retorna una lista única de radicados.

    Args:
        ruta_excel: Ruta del archivo Excel con la columna 'Radicado'.

    Returns:
        Lista de radicados como cadenas de texto.

    Raises:
        ValueError: Si el archivo no contiene una columna llamada 'Radicado'.
    """
    df = pd.read_excel(ruta_excel, dtype={"Radicado": str})

    if "Radicado" not in df.columns:
        raise ValueError("El archivo Excel debe tener una columna llamada 'Radicado'.")

    return df["Radicado"].dropna().astype(str).unique().tolist()


# ===============================
# CONSTRUCCIÓN DEL RESUMEN
# ===============================

def construir_resumen(df_resultado, errores: list[dict]) -> str:
    """
    Construye el mensaje de resumen que será enviado como notificación.

    Args:
        df_resultado: DataFrame con procesos exitosos.
        errores: Lista de errores por radicado.

    Returns:
        Texto formateado para Telegram.
    """
    resumen = (
        "📢 NOTIFICACIÓN DE PROCESOS\n"
        "📊 RESUMEN GENERAL\n"
        f"✅ Procesados: {len(df_resultado)} | ⚠️ Fallidos: {len(errores)}\n"
        f"🕒 Ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        "📌 Ordenados por fecha de última actuación\n\n"
    )

    for _, row in df_resultado.iterrows():
        fecha_act = (
            row["Fecha_ultima_actuacion"].strftime("%Y-%m-%d")
            if pd.notnull(row["Fecha_ultima_actuacion"])
            else "Sin fecha"
        )

        resumen += (
            "────────────────────\n"
            f"⚖️ Radicado: {row['Radicado']}\n"
            f"🏛️ Juzgado: {row['Juzgado']}\n"
            f"👤 Partes: {row.get('Partes', 'No identificadas')}\n"
            f"📅 Última actuación: {fecha_act}\n"
            f"📋 Radicación: {row['Fecha_radicacion']}\n\n"
        )

    if errores:
        resumen += "────────────────────\n⚠️ RADICADOS CON ERROR:\n"
        for error in errores:
            resumen += f"• {error['Radicado']}: {error['Error']}\n"

    return resumen


# ===============================
# FLUJO PRINCIPAL DEL SISTEMA
# ===============================

def ejecutar() -> None:
    """
    Orquesta el flujo completo del sistema:

    1. Valida la configuración
    2. Carga los radicados
    3. Consulta cada proceso
    4. Registra resultados y errores
    5. Guarda el estado actual
    6. Exporta el reporte Excel
    7. Envía el resumen por Telegram
    """
    validar_configuracion()

    radicados = cargar_radicados(ARCHIVO_LISTADO)
    resultados = []
    errores = []

    # Se crea una única instancia del navegador para reutilizarla
    driver = configurar_driver()
    wait = crear_wait(driver, timeout=20)

    try:
        for radicado in radicados:
            try:
                datos = consultar_radicado(driver, wait, radicado)
                resultados.append(datos)

                # Pausa corta entre consultas para evitar comportamiento agresivo
                time.sleep(2)

            except Exception as e:
                mensaje_error = str(e).strip()

                if not mensaje_error:
                    mensaje_error = e.__class__.__name__

                # Se conserva solo una versión corta del error
                mensaje_error = mensaje_error.split("\n")[0][:250]

                errores.append({
                    "Radicado": radicado,
                    "Error": mensaje_error,
                })

    finally:
        driver.quit()

    # Persistencia del estado actual de la consulta
    estado_actual = construir_estado(resultados)
    guardar_estado(ARCHIVO_ESTADO, estado_actual)

    # Exportación de resultados
    archivo_excel, df_resultado = exportar_excel(resultados, errores, OUTPUT_DIR)
    print(f"✅ Excel exportado: {archivo_excel}")

    # Envío de resumen a Telegram
    resumen = construir_resumen(df_resultado, errores)
    notificar_telegram(resumen)
    print("✅ Resumen enviado a Telegram")