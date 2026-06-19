@echo off
color 0b
title Investment AI Launcher
echo ========================================================
echo         MEMULAKAN INVESTMENT AI (BERSEPADU)
echo ========================================================
echo.

echo [1/4] Menghidupkan Otak AI (Backend Server Python)...
start "Backend - Investment AI" cmd /k "cd /d "%~dp0backend" && venv\Scripts\python -m uvicorn api:app --reload --port 8000"

echo [2/4] Menghidupkan Paparan Dashboard (Frontend Next.js)...
start "Frontend - Investment AI" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo [3/4] Enjin Pasukan Elit (Multi-Coin Unified Bot) kini disepadukan...
echo INFO: Enjin berjalan secara langsung di dalam Backend Server untuk mengelakkan konflik memori/pesanan.
echo.

echo [4/4] Sila tunggu 5 saat sebelum peramban (browser) dibuka...
timeout /t 5 /nobreak >nul
start http://localhost:5173

echo.
echo SEMUANYA SELESAI !
echo.
echo --------------------------------------------------------
echo NOTA PENTING:
echo Terdapat TIGA tetingkap/terminal hitam yang baru sahaja dibuka.
echo JANGAN TUTUP tetingkap-tetingkap tersebut. Kalau anda tutup,
echo sistem paparan dan operasi bot automatik akan terhenti.
echo Anda boleh "Minimize" sahaja.
echo --------------------------------------------------------
echo.
pause
