from __future__ import annotations

import json
import sys

from backend.app.services.consulta_service import ejecutar_consulta_background


def main() -> None:
    consulta_id = int(sys.argv[1])
    usuario_id = int(sys.argv[2])
    numeros = json.loads(sys.argv[3]) if len(sys.argv) > 3 else []
    etiqueta = sys.argv[4] if len(sys.argv) > 4 and sys.argv[4] else None
    ejecutar_consulta_background(consulta_id, usuario_id, numeros or None, etiqueta)


if __name__ == "__main__":
    main()
