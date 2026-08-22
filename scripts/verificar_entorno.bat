@echo off
title SIGD-ST - Verificar entorno
echo ==========================================
echo SIGD-ST - Verificacion de entorno
echo ==========================================
echo.

echo [1/4] Python
where python >nul 2>nul
if errorlevel 1 (
  echo ERROR: Python no encontrado en PATH.
) else (
python --version
)
echo.

echo [2/4] Node
where node >nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js no encontrado en PATH.
) else (
  node --version
)
echo.

echo [3/4] npm
where npm >nul 2>nul
if errorlevel 1 (
  echo ERROR: npm no encontrado en PATH.
) else (
  npm --version
)
echo.

echo [4/4] Carpetas
if exist backend (echo OK backend) else (echo ERROR falta backend)
if exist frontend (echo OK frontend) else (echo ERROR falta frontend)

echo.
pause
