@echo off
title IndoCaption Desktop
echo ========================================================
echo     IndoCaption Desktop - Native Windows App
echo ========================================================
echo.
echo Menjalankan aplikasi desktop IndoCaption...
.\backend\venv\Scripts\python.exe desktop_app.py
if errorlevel 1 (
    echo.
    echo Terjadi kendala saat membuka aplikasi desktop.
    pause
)
