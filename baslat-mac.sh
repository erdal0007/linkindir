#!/bin/bash
# LinkIndir — Mac: tek komutla kur + çalıştır + telefona açık adres üret
set -e
cd "$(dirname "$0")"
command -v brew >/dev/null || { echo "Homebrew yok, kuruluyor..."; /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; }
brew list ffmpeg >/dev/null 2>&1 || brew install ffmpeg
brew list cloudflared >/dev/null 2>&1 || brew install cloudflared
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
pip install -q -U -r requirements.txt
echo "Sunucu başlıyor..."
uvicorn main:app --host 0.0.0.0 --port 8000 > server.log 2>&1 &
sleep 3
echo
echo "=== Aşağıda https://....trycloudflare.com ile biten adres çıkacak; onu telefonda aç ==="
echo
cloudflared tunnel --url http://localhost:8000 2>&1 | grep --line-buffered -o 'https://[a-z0-9-]*\.trycloudflare\.com' &
wait
