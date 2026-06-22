"""Compatibilidad de arquitectura 2.0.

El proyecto conserva `settings.py` como fuente real de configuracion para no
romper imports existentes. Este modulo expone el nombre esperado por la nueva
estructura propuesta.
"""

from backend.app.core.settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]
