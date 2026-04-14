# Bot de Monitoreo de Procesos Judiciales

Automatización desarrollada en Python para consultar procesos judiciales en la plataforma de la Rama Judicial de Colombia, generar reportes en Excel y enviar notificaciones automáticas por Telegram.

## Características

- Consulta automatizada de múltiples radicados
- Extracción de juzgado, partes, fecha de radicación y última actuación
- Manejo individual de errores por radicado
- Generación de reporte Excel con hojas de procesos y errores
- Notificación resumida por Telegram
- Persistencia de estado local en JSON
- Arquitectura modular para facilitar mantenimiento y escalabilidad

## Stack técnico

- Python
- Selenium
- Pandas
- OpenPyXL
- Requests
- python-dotenv
- Microsoft Edge WebDriver / Selenium Manager

## Estructura del proyecto

    bot-rama-judicial/
    ├── src/
    │   ├── __init__.py
    │   ├── config.py
    │   ├── telegram_utils.py
    │   ├── scraper.py
    │   ├── reportes.py
    │   ├── estado.py
    │   └── main.py
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

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/estivencontacto/bot-rama-judicial.git
cd bot-rama-judicial