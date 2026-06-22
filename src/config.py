import os

from dotenv import load_dotenv


# ===============================
# CARGA DE VARIABLES DE ENTORNO
# ===============================

# Carga las variables definidas en el archivo .env
load_dotenv()


# ===============================
# RUTAS DEL PROYECTO
# ===============================

# Carpeta raíz del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Carpetas de entrada y salida
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_DIR = os.path.join(BASE_DIR, "output")

# Archivos principales del sistema
ARCHIVO_LISTADO = os.path.join(DATA_DIR, "listado_radicados.xlsx")
ARCHIVO_ESTADO = os.path.join(OUTPUT_DIR, "estado_procesos.json")


# ===============================
# CONFIGURACIÓN EXTERNA
# ===============================

# URL de consulta de procesos en la Rama Judicial
URL_CONSULTA = "https://consultaprocesos.ramajudicial.gov.co/Procesos/NumeroRadicacion"

# Variables de entorno para notificaciones
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

# Límite aproximado por mensaje en Telegram
TELEGRAM_MAX = 4000


# ===============================
# VALIDACIÓN DE CONFIGURACIÓN
# ===============================

def validar_configuracion() -> None:
    """
    Valida que las variables críticas del sistema estén configuradas y
    asegura la existencia de las carpetas de trabajo.

    Raises:
        ValueError: Si faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID en el archivo .env
    """
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Faltan TELEGRAM_TOKEN o TELEGRAM_CHAT_ID en el archivo .env")

    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(OUTPUT_DIR, exist_ok=True)