import json
import hashlib


def construir_estado(resultados: list[dict]) -> dict:
    return {
        r["Radicado"]: {
            "hash": hashlib.md5(
                f"{r['Demandante']}|{r['Demandado']}|{r['Juzgado']}|{r['Fecha_ultima_actuacion']}".encode("utf-8")
            ).hexdigest()
        }
        for r in resultados
    }


def guardar_estado(ruta_archivo: str, estado: dict) -> None:
    with open(ruta_archivo, "w", encoding="utf-8") as archivo:
        json.dump(estado, archivo, indent=2, ensure_ascii=False)
        