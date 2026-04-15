import os
from datetime import datetime

import pandas as pd


# ===============================
# ESTRUCTURA DEL REPORTE
# ===============================

COLUMNAS_RESULTADO = [
    "Radicado",
    "Juzgado",
    "Demandante",
    "Demandado",
    "Partes",
    "Fecha_radicacion",
    "Fecha_ultima_actuacion",
]


# ===============================
# EXPORTACIÓN A EXCEL
# ===============================

def exportar_excel(resultados: list[dict], errores: list[dict], output_dir: str):
    """
    Genera un archivo Excel con dos hojas:
    - Procesos: resultados exitosos
    - Errores: radicados que fallaron

    Args:
        resultados: Lista de diccionarios con procesos consultados exitosamente.
        errores: Lista de diccionarios con errores por radicado.
        output_dir: Carpeta donde se guardará el archivo.

    Returns:
        Tupla con:
        - ruta del archivo generado
        - DataFrame final de resultados ordenado
    """
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_salida = os.path.join(output_dir, f"reporte_procesos_{fecha_hoy}.xlsx")

    df_resultado = pd.DataFrame(resultados, columns=COLUMNAS_RESULTADO)

    # Convierte la fecha de última actuación para permitir orden correcto
    df_resultado["Fecha_ultima_actuacion"] = pd.to_datetime(
        df_resultado["Fecha_ultima_actuacion"],
        errors="coerce"
    )

    df_resultado = df_resultado.sort_values(
        by="Fecha_ultima_actuacion",
        ascending=False,
        na_position="last"
    )

    df_errores = pd.DataFrame(errores, columns=["Radicado", "Error"])

    with pd.ExcelWriter(archivo_salida, engine="openpyxl") as writer:
        df_resultado.to_excel(writer, sheet_name="Procesos", index=False)
        df_errores.to_excel(writer, sheet_name="Errores", index=False)

    return archivo_salida, df_resultado