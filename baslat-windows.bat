@echo off
REM LinkIndir — Windows: tek tikla kur + calistir + telefona acik adres uret
cd /d "%~dp0"
where python >nul 2>&1 || (echo Python yok. python.org'dan kurup "Add to PATH" isaretleyin. & pause & exit /b)
where ffmpeg >nul 2>&1 || winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
where cloudflared >nul 2>&1 || winget install -e --id Cloudflare.cloudflared --accept-source-agreements --accept-package-agreements
if not exist .venv python -m venv .venv
call .venv\Scripts\activate.bat
pip install -q -U -r requirements.txt
start "LinkIndir Sunucu" cmd /k uvicorn main:app --host 0.0.0.0 --port 8000
timeout /t 4 >nul
echo.
echo === Asagida https://....trycloudflare.com ile biten adres cikacak; onu telefonda acin ===
echo.
cloudflared tunnel --url http://localhost:8000
pause
