@echo off
cd /d "%~dp0"
"C:\Program Files (x86)\Microsoft Visual Studio\Shared\Python39_64\python.exe" -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 > backend-server.log 2>&1
