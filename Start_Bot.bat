@echo off
setlocal
title Investment AI - Rust Launcher
echo ========================================================
echo         INVESTMENT AI - RUST + AI + DASHBOARD
echo ========================================================
echo.
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0ops\windows\Start-Bot.ps1" %*
if errorlevel 1 (
    echo.
    echo GAGAL. Sila semak mesej di atas. Dagangan live tidak diaktifkan.
    pause
    exit /b 1
)
echo.
echo Dashboard: http://127.0.0.1:8100
echo Mod SHADOW: tiada pesanan sebenar dihantar.
echo.
echo ========================================================
echo   LOG MONITOR - Ctrl+C berhenti monitor sahaja.
echo   Enjin tetap berjalan di latar belakang.
echo ========================================================
powershell.exe -NoLogo -NoProfile -ExecutionPolicy Bypass -File "%~dp0ops\windows\Watch-Logs.ps1"
endlocal
