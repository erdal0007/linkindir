@echo off
REM LinkIndir - cift tikla: sunucu + tunel baslar, adres Not Defteri'nde acilir
cd /d "%~dp0"
where python >nul 2>&1 || (echo Python yok. python.org'dan kurup "Add to PATH" isaretleyin. & pause & exit /b)
where ffmpeg >nul 2>&1 || winget install -e --id Gyan.FFmpeg --accept-source-agreements --accept-package-agreements
where cloudflared >nul 2>&1 || winget install -e --id Cloudflare.cloudflared --accept-source-agreements --accept-package-agreements
if not exist .venv python -m venv .venv
.venv\Scripts\python.exe -m pip install -q -U -r requirements.txt
taskkill /f /im cloudflared.exe >nul 2>&1
start "LinkIndir SUNUCU - KAPATMA" .venv\Scripts\python.exe -m uvicorn main:app --host 0.0.0.0 --port 8000
timeout /t 4 >nul
del tunel.log >nul 2>&1
start "LinkIndir TUNEL - KAPATMA" cmd /c "cloudflared tunnel --url http://localhost:8000 2>&1 | findstr /r /c:\"https://.*trycloudflare.com\" > tunel.log"
echo Adres bekleniyor...
:bekle
timeout /t 2 >nul
if not exist tunel.log goto bekle
for /f "tokens=*" %%a in ('findstr /r /c:"https://" tunel.log') do set SATIR=%%a
if not defined SATIR goto bekle
for %%w in (%SATIR%) do echo %%w | findstr /c:"https://" > adres.txt
echo.
echo ===== TELEFONDA ACILACAK ADRES =====
type adres.txt
echo ====================================
echo Bu adres Not Defteri'nde aciliyor; kopyalayip telefona gonderin.
start notepad adres.txt
echo Bilgisayar acik ve iki pencere acik kaldigi surece uygulama calisir.
pause
