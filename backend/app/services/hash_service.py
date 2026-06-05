import hashlib


def build_process_hash(data: dict) -> str:
    actuaciones = data.get("Actuaciones") or []
    ultima_actuacion = actuaciones[0] if actuaciones else {}
    payload = "|".join(
        str(data.get(key, ""))
        for key in ["Demandante", "Demandado", "Juzgado", "Fecha_ultima_actuacion"]
    )
    payload = "|".join(
        [
            payload,
            str(data.get("Ultima_actuacion", "")),
            str(data.get("Ultima_anotacion", "")),
            str(ultima_actuacion.get("Fecha_registro", "")),
        ]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
