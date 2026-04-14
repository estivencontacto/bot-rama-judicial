# Bot de Monitoreo de Procesos Judiciales

Sistema automatizado desarrollado en Python para consultar procesos judiciales en la plataforma de la Rama Judicial de Colombia, generar reportes estructurados en Excel y enviar notificaciones en tiempo real mediante consumo de servicios API REST.

---

## Descripción

Este proyecto permite automatizar la consulta de múltiples radicados judiciales, procesar la información obtenida y generar alertas sin intervención manual.

El sistema integra técnicas de web scraping con Selenium, procesamiento de datos con Pandas y comunicación con servicios externos a través de APIs REST.

---

## Características

- Consulta automatizada de múltiples procesos judiciales
- Extracción de juzgado, partes, fecha de radicación y última actuación
- Manejo individual de errores por radicado (tolerancia a fallos)
- Generación de reportes en Excel con estructura organizada
- Registro de errores en hoja separada para auditoría
- Persistencia de estado local mediante JSON
- Integración con servicios externos mediante API REST para notificaciones
- Configuración segura mediante variables de entorno
- Arquitectura modular orientada a mantenimiento y escalabilidad

---

## Stack Técnico

- Python
- Selenium (Automatización y Web Scraping)
- Pandas (Procesamiento de datos)
- OpenPyXL (Generación de archivos Excel)
- Requests (Consumo de APIs REST)
- python-dotenv (Gestión de variables de entorno)
- JSON (Persistencia de estado)

---

## Integración con APIs

El sistema implementa comunicación con servicios externos mediante el consumo de una API REST para el envío de notificaciones automatizadas.

Esto permite entregar resultados en tiempo real sin necesidad de intervención manual, facilitando el monitoreo continuo de procesos judiciales.

---

## Estructura del Proyecto


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
└── ejecutar_bot.bat


---

## Instalación

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
Configuración
1. Crear archivo .env

Crear un archivo en la raíz del proyecto llamado:

.env

Copiando el contenido de:

.env.example
Configuración del Bot y Variables de Entorno

El sistema utiliza un servicio externo basado en API REST para enviar notificaciones automatizadas.

2. Crear el bot
Abrir Telegram
Buscar:
@BotFather
Ejecutar:
/newbot
Asignar nombre y username
Copiar el token generado
3. Obtener Chat ID
Enviar cualquier mensaje al bot creado
Abrir en navegador:
https://api.telegram.org/bot<TU_TOKEN>/getUpdates
Buscar:
"chat": {
  "id": 123456789
}

Ese número es el CHAT_ID

4. Configurar variables

Editar el archivo .env:

TELEGRAM_TOKEN=tu_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
5. Seguridad
No subir el archivo .env al repositorio
Mantener las credenciales privadas
Utilizar .env.example como plantilla pública
Ejecución
.\venv\Scripts\python.exe run.py
Salidas del sistema
Reporte Excel en output/
Hoja de errores
Archivo JSON de estado
Notificación automatizada en tiempo real
Flujo del sistema
Lectura de radicados desde Excel
Consulta automatizada con Selenium
Extracción de datos
Manejo de errores
Generación de Excel
Persistencia del estado
Envío de notificación mediante API REST
Posibles mejoras
Notificar solo cuando existan cambios
Implementar sistema de logs
Integrar base de datos
Desplegar en la nube
Añadir pruebas unitarias
Autor

Estiven Agudelo

Licencia

MIT License