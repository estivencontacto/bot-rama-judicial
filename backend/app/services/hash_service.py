import hashlib


def build_process_hash(data: dict) -> str:
    payload = "|".join(
        str(data.get(key, ""))
        for key in ["Demandante", "Demandado", "Juzgado", "Fecha_ultima_actuacion"]
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()
