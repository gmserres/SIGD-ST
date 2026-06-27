@echo off
title SIGD-ST - Backend
cd /d "%~dp0.."
cd backend

if not exist ".venv" (
  echo Creando entorno virtual...
  python -m venv .venv
  if errorlevel 1 (
    "C:\Users\Usuario\AppData\Local\Programs\Python\Python312\python.exe" -m venv .venv
  )
)

call .venv\Scripts\activate
pip install -r requirements.txt

echo Backend: http://localhost:8000
echo API docs: http://localhost:8000/docs
uvicorn app.main:app --reload
pause
