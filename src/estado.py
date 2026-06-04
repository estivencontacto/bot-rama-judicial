import hashlib
import json


# ===============================
# CONSTRUCCIÓN DEL ESTADO
# ===============================

def construir_estado(resultados: list[dict]) -> dict:
    """
    Construye un diccionario de estado basado en un hash por radicado.

    El hash permite comparar cambios entre ejecuciones futuras.

    Args:
        resultados: Lista de procesos consultados exitosamente.

    Returns:
        Diccionario indexado por radicado con hash resumido del estado actual.
    """
    return {
        r["Radicado"]: {
            "hash": hashlib.md5(
                f"{r['Demandante']}|{r['Demandado']}|{r['Juzgado']}|{r['Fecha_ultima_actuacion']}".encode("utf-8")
            ).hexdigest()
        }
        for r in resultados
    }


# ===============================
# PERSISTENCIA DEL ESTADO
# ===============================

def guardar_estado(ruta_archivo: str, estado: dict) -> None:
    """
    Guarda el estado actual del sistema en formato JSON.

    Args:
        ruta_archivo: Ruta donde se almacenará el archivo JSON.
        estado: Diccionario con el estado actual de los procesos.
    """
    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        json.dump(estado, archivo, indent=2, ensure_ascii=False)