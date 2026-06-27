@echo off
title SIGD-ST - Frontend
cd /d "%~dp0.."
set "PATH=%PATH%;C:\Program Files\nodejs"
cd frontend

if not exist "node_modules" (
  npm install
)

echo Frontend: http://localhost:5173
npm run dev
pause
