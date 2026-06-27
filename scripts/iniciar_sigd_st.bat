@echo off
title SIGD-ST - Inicio local
cd /d "%~dp0.."
echo Iniciando SIGD-ST...
echo Se abriran dos ventanas: backend y frontend.
echo Luego abrir http://localhost:5173
start "SIGD-ST Backend" cmd /k "%~dp0iniciar_backend.bat"
timeout /t 4 > nul
start "SIGD-ST Frontend" cmd /k "%~dp0iniciar_frontend.bat"
pause
