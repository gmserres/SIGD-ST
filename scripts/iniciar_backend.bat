@echo off
title SIGD-ST - Backend
cd /d "%~dp0.."
cd backend

if not exist ".venv" (
  echo Creando entorno virtual...
  where python >nul 2>nul
  if errorlevel 1 (
    echo ERROR: Python no encontrado en PATH.
    echo Instale Python 3.12 y vuelva a ejecutar este script.
    exit /b 1
  )
  python -m venv .venv
  if errorlevel 1 (
    echo ERROR: No fue posible crear el entorno virtual.
    exit /b 1
  )
)

call .venv\Scripts\activate
pip install -r requirements.txt

echo Backend: http://localhost:8000
echo API docs: http://localhost:8000/docs
uvicorn app.main:app --reload
pause
