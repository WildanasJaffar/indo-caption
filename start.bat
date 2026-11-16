@echo off
title IndoCaption - Local AI Auto Caption Editor
echo ===================================================
echo     IndoCaption - Local AI Auto Caption Editor
echo ===================================================
echo.

echo [1/2] Menjalankan Backend FastAPI (Port 8000)...
start "IndoCaption Backend" cmd /k "cd backend && venv\Scripts\python.exe run.py"

echo [2/2] Menjalankan Frontend Vue 3 (Port 5173)...
start "IndoCaption Frontend" cmd /k "cd frontend && npm run dev"

echo.
echo ===================================================
echo Backend:  http://127.0.0.1:8000
echo Frontend: http://localhost:5173
echo.
echo Aplikasi siap digunakan di browser!
echo ===================================================
pause

