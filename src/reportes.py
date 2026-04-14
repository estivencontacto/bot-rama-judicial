import os
from datetime import datetime
import pandas as pd


COLUMNAS_RESULTADO = [
    "Radicado",
    "Juzgado",
    "Demandante",
    "Demandado",
    "Partes",
    "Fecha_radicacion",
    "Fecha_ultima_actuacion",
]


def exportar_excel(resultados: list[dict], errores: list[dict], output_dir: str):
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    archivo_salida = os.path.join(output_dir, f"reporte_procesos_{fecha_hoy}.xlsx")

    df_resultado = pd.DataFrame(resultados, columns=COLUMNAS_RESULTADO)
    df_resultado["Fecha_ultima_actuacion"] = pd.to_datetime(
        df_resultado["Fecha_ultima_actuacion"], errors="coerce"
    )
    df_resultado = df_resultado.sort_values(
        by="Fecha_ultima_actuacion", ascending=False, na_position="last"
    )

    df_errores = pd.DataFrame(errores, columns=["Radicado", "Error"])

    with pd.ExcelWriter(archivo_salida, engine="openpyxl") as writer:
        df_resultado.to_excel(writer, sheet_name="Procesos", index=False)
        df_errores.to_excel(writer, sheet_name="Errores", index=False)

    return archivo_salida, df_resultado