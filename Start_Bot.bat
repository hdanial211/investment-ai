@echo off
color 0b
title Investment AI Launcher
echo ========================================================
echo         MEMULAKAN BITCOIN INVESTMENT AI
echo ========================================================
echo.

echo [1/3] Menghidupkan Otak AI (Backend Server Python)...
start "Backend - Investment AI" cmd /k "cd /d "%~dp0backend" && venv\Scripts\python -m uvicorn main:app --reload --port 8000"

echo [2/3] Menghidupkan Paparan Dashboard (Frontend Next.js)...
start "Frontend - Investment AI" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo [3/3] Sila tunggu 5 saat sebelum peramban (browser) dibuka...
timeout /t 5 /nobreak >nul
start http://localhost:3000

echo.
echo SEMUANYA SELESAI !
echo.
echo --------------------------------------------------------
echo NOTA PENTING:
echo Terdapat dua tetingkap/terminal hitam yang baru sahaja dibuka.
echo JANGAN TUTUP dua tetingkap tersebut. Kalau anda tutup tetingkap tu,
echo bot akan tidur dan takkan jalankan auto-buy/sell.
echo Anda boleh "Minimize" sahaja.
echo --------------------------------------------------------
echo.
pause
