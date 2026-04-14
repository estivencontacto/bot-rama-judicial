import time
import pandas as pd
from datetime import datetime
from src.config import (
    ARCHIVO_ESTADO,
    ARCHIVO_LISTADO,
    OUTPUT_DIR,
    validar_configuracion,
)
from src.scraper import configurar_driver, crear_wait, consultar_radicado
from src.estado import construir_estado, guardar_estado
from src.reportes import exportar_excel
from src.telegram_utils import notificar_telegram


def cargar_radicados(ruta_excel: str) -> list[str]:
    df = pd.read_excel(ruta_excel, dtype={"Radicado": str})

    if "Radicado" not in df.columns:
        raise ValueError("El archivo Excel debe tener una columna llamada 'Radicado'.")

    return df["Radicado"].dropna().astype(str).unique().tolist()


def construir_resumen(df_resultado, errores: list[dict]) -> str:
    resumen = (
        "📢 NOTIFICACIÓN DE PROCESOS\n"
        f"📊 RESUMEN GENERAL\n"
        f"✅ Procesados: {len(df_resultado)} | ⚠️ Fallidos: {len(errores)}\n"
        f"🕒 Ejecución: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        f"📌 Ordenados por fecha de última actuación\n\n"
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

def ejecutar() -> None:
    validar_configuracion()

    radicados = cargar_radicados(ARCHIVO_LISTADO)
    resultados = []
    errores = []

    driver = configurar_driver()
    wait = crear_wait(driver, timeout=20)

    try:
        for radicado in radicados:
            try:
                datos = consultar_radicado(driver, wait, radicado)
                resultados.append(datos)
                time.sleep(2)

            except Exception as e:
                mensaje_error = str(e).strip()

                if not mensaje_error:
                    mensaje_error = e.__class__.__name__

                mensaje_error = mensaje_error.split("\n")[0][:250]

                errores.append({
                    "Radicado": radicado,
                    "Error": mensaje_error
            })
    finally:
        driver.quit()

    estado_actual = construir_estado(resultados)
    guardar_estado(ARCHIVO_ESTADO, estado_actual)

    archivo_excel, df_resultado = exportar_excel(resultados, errores, OUTPUT_DIR)
    print(f"✅ Excel exportado: {archivo_excel}")

    resumen = construir_resumen(df_resultado, errores)
    notificar_telegram(resumen)
    print("✅ Resumen enviado a Telegram")