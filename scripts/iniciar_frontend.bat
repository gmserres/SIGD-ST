@echo off
title SIGD-ST - Frontend
cd /d "%~dp0.."
cd frontend

where node >nul 2>nul
if errorlevel 1 (
  echo ERROR: Node.js no encontrado en PATH.
  echo Instale una version compatible y vuelva a ejecutar este script.
  exit /b 1
)

where npm >nul 2>nul
if errorlevel 1 (
  echo ERROR: npm no encontrado en PATH.
  exit /b 1
)

if not exist "node_modules" (
  npm ci
  if errorlevel 1 exit /b 1
)

echo Frontend: http://localhost:5173
npm run dev
pause
