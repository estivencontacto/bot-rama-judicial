# ⚖️ Bot de Monitoreo de Procesos Judiciales

Sistema automatizado desarrollado en Python para consultar procesos judiciales en la plataforma de la Rama Judicial de Colombia, generar reportes en Excel y enviar notificaciones en tiempo real mediante consumo de servicios API REST.

---

## 📌 Descripción

Este proyecto permite automatizar la consulta de múltiples radicados judiciales, eliminando la necesidad de revisión manual.

El sistema realiza:
- extracción automatizada de información
- procesamiento estructurado de datos
- generación de reportes
- envío de notificaciones en tiempo real

Todo integrado en un flujo automatizado y tolerante a errores.

---

## 🚀 Características

- Consulta automatizada de múltiples procesos judiciales
- Extracción de:
  - juzgado
  - partes (demandante/demandado)
  - fecha de radicación
  - última actuación
- Manejo individual de errores por radicado (no detiene el proceso)
- Generación de reporte Excel con:
  - hoja de resultados
  - hoja de errores
- Persistencia de estado local en JSON
- Integración con API REST para notificaciones
- Configuración segura mediante variables de entorno
- Arquitectura modular orientada a escalabilidad

---

## 🧠 Stack Técnico

- Python
- Selenium (Web Scraping y automatización)
- Pandas (Procesamiento de datos)
- OpenPyXL (Generación de Excel)
- Requests (Consumo de APIs REST)
- python-dotenv (Variables de entorno)
- JSON (Persistencia de estado)

---

## 🔌 Integración con APIs

El sistema utiliza una API REST para enviar notificaciones automáticas con el estado de los procesos.

Esto permite:
- monitoreo en tiempo real
- automatización completa del flujo
- eliminación de tareas manuales

---

## 📁 Estructura del Proyecto


bot-rama-judicial/
├── src/
│ ├── config.py
│ ├── scraper.py
│ ├── reportes.py
│ ├── estado.py
│ ├── telegram_utils.py
│ └── main.py
├── data/
├── output/
├── assets/
├── .env.example
├── .gitignore
├── requirements.txt
├── README.md
├── LICENSE
├── run.py


---

## ⚙️ Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/estivencontacto/bot-rama-judicial.git
cd bot-rama-judicial
2. Crear entorno virtual
py -m venv venv
3. Activar entorno virtual
.\venv\Scripts\Activate.ps1
4. Instalar dependencias
.\venv\Scripts\python.exe -m pip install -r requirements.txt
🔐 Configuración
1. Crear archivo .env

En la raíz del proyecto, crea un archivo:

.env

Usa como base:

.env.example
🤖 Configuración del Bot
2. Crear bot
Abre Telegram
Busca:
@BotFather
Ejecuta:
/newbot
Asigna:
nombre
username
Copia el token generado
3. Obtener Chat ID
Envía un mensaje a tu bot
Abre en el navegador:
https://api.telegram.org/bot<TU_TOKEN>/getUpdates
Busca:
"chat": {
  "id": 123456789
}

Ese número es tu CHAT_ID

4. Configurar variables

En .env:

TELEGRAM_TOKEN=tu_token
TELEGRAM_CHAT_ID=tu_chat_id
🔒 Seguridad
❌ No subir .env a GitHub
✅ Usar .env.example como plantilla
🔁 Revocar tokens si fueron expuestos
▶️ Ejecución
.\venv\Scripts\python.exe run.py
📊 Salidas del sistema

El sistema genera:

📁 output/reporte_procesos_YYYY-MM-DD.xlsx
📄 hoja "Procesos"
⚠️ hoja "Errores"
📄 archivo JSON con estado
📩 notificación automática en Telegram