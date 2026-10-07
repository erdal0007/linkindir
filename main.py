"""LinkIndir — telefona video indirme servisi (yt-dlp + FastAPI)
Çalıştır:  pip install -r requirements.txt  &&  uvicorn main:app --host 0.0.0.0 --port 8000
"""
import os, re, uuid, tempfile, threading, time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yt_dlp

app = FastAPI(title="LinkIndir")
TMP = os.path.join(tempfile.gettempdir(), "linkindir")
os.makedirs(TMP, exist_ok=True)

class Req(BaseModel):
    url: str
    mode: str = "video"   # "video" | "audio"

def _opts(mode: str, out: str):
    base = {"outtmpl": out, "quiet": True, "noplaylist": True, "no_warnings": True}
    if mode == "audio":
        base["format"] = "bestaudio/best"
        base["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
    else:
        # Telefonda direkt oynaması için mp4 tercih edilir
        # Filigransız (watermark'sız) sürümü tercih et, mp4 olsun
        nw = "[format_note!*=atermark]"
        base["format"] = (f"bv*[ext=mp4][height<=1080]{nw}+ba[ext=m4a]/"
                          f"b[ext=mp4]{nw}/b{nw}/bv*[ext=mp4]+ba/best")
        base["format_sort"] = ["hasvid", "res:1080", "ext:mp4:m4a"]
        base["merge_output_format"] = "mp4"
    return base

@app.post("/api/info")
def info(r: Req):
    try:
        with yt_dlp.YoutubeDL({"quiet": True, "noplaylist": True, "skip_download": True}) as y:
            i = y.extract_info(r.url, download=False)
    except Exception as e:
        raise HTTPException(400, f"Bağlantı okunamadı: {e}")
    return {
        "title": i.get("title"),
        "thumbnail": i.get("thumbnail"),
        "duration": i.get("duration"),
        "uploader": i.get("uploader") or i.get("channel"),
        "site": i.get("extractor_key"),
    }

FILES: dict[str, tuple[str, str]] = {}   # id -> (path, filename)

@app.post("/api/download")
def download(r: Req):
    jid = uuid.uuid4().hex
    out = os.path.join(TMP, f"{jid}.%(ext)s")
    try:
        with yt_dlp.YoutubeDL(_opts(r.mode, out)) as y:
            i = y.extract_info(r.url, download=True)
    except Exception as e:
        raise HTTPException(400, f"İndirilemedi: {e}")
    files = [f for f in os.listdir(TMP) if f.startswith(jid)]
    if not files:
        raise HTTPException(500, "Dosya oluşmadı")
    path = os.path.join(TMP, files[0])
    ext = path.rsplit(".", 1)[-1]
    name = re.sub(r"[^\w\- ]+", "", i.get("title") or "video").strip()[:60] or "video"
    FILES[jid] = (path, f"{name}.{ext}")
    threading.Thread(target=_cleanup, args=(path, jid), daemon=True).start()
    return {"id": jid, "name": f"{name}.{ext}", "size": os.path.getsize(path)}

@app.get("/api/file/{jid}")
def get_file(jid: str):
    item = FILES.get(jid)
    if not item or not os.path.exists(item[0]):
        raise HTTPException(404, "Dosya süresi doldu, tekrar indir")
    path, fname = item
    mt = "audio/mpeg" if fname.endswith(".mp3") else "video/mp4"
    return FileResponse(path, filename=fname, media_type=mt)

def _cleanup(path: str, jid: str):
    time.sleep(1800)  # 30 dk sonra geçici dosyayı sil
    FILES.pop(jid, None)
    try: os.remove(path)
    except OSError: pass

STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/", StaticFiles(directory=STATIC, html=True), name="static")
