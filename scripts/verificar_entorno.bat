@echo off
title SIGD-ST - Verificar entorno
echo ==========================================
echo SIGD-ST - Verificacion de entorno
echo ==========================================
echo.

echo [1/4] Python
python --version
if errorlevel 1 (
  if exist "C:\Users\Usuario\AppData\Local\Programs\Python\Python312\python.exe" (
    "C:\Users\Usuario\AppData\Local\Programs\Python\Python312\python.exe" --version
  ) else (
    echo ERROR: Python no encontrado.
  )
)
echo.

echo [2/4] Node
set "PATH=%PATH%;C:\Program Files\nodejs"
node --version
if errorlevel 1 echo ERROR: Node.js no encontrado.
echo.

echo [3/4] npm
npm --version
if errorlevel 1 echo ERROR: npm no encontrado.
echo.

echo [4/4] Carpetas
if exist backend (echo OK backend) else (echo ERROR falta backend)
if exist frontend (echo OK frontend) else (echo ERROR falta frontend)

echo.
pause
