"""LinkIndir — telefona video indirme servisi (yt-dlp + FastAPI)
Çalıştır:  pip install -r requirements.txt  &&  uvicorn main:app --host 0.0.0.0 --port 8000
"""
import os, re, uuid, tempfile, threading, time
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import yt_dlp, shutil
HAS_FFMPEG = shutil.which("ffmpeg") is not None

app = FastAPI(title="LinkIndir")
TMP = os.path.join(tempfile.gettempdir(), "linkindir")
os.makedirs(TMP, exist_ok=True)

class Req(BaseModel):
    url: str
    mode: str = "video"   # "video" | "audio"

def _opts(mode: str, out: str):
    base = {"outtmpl": out, "quiet": True, "noplaylist": True, "no_warnings": True}
    # Filigransız + iPhone uyumlu (H.264) formatlar; AV1/VP9/HEVC dışarı
    nw = "[format_note!*=atermark][vcodec!*=av01][vcodec!*=vp0][vcodec!*=hev][vcodec!*=hvc]"
    if mode == "audio":
        if HAS_FFMPEG:
            base["format"] = "bestaudio/best"
            base["postprocessors"] = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
        else:
            base["format"] = "ba[ext=m4a]/ba/best"
    else:
        # Önce TEK PARÇA (görüntü+ses birlikte) mp4; birleştirme ancak ffmpeg varsa
        single = f"b[ext=mp4][vcodec!*=none][acodec!*=none]{nw}/b[vcodec!*=none][acodec!*=none]{nw}"
        if HAS_FFMPEG:
            base["format"] = f"{single}/bv*[ext=mp4]{nw}+ba[ext=m4a]/bv*+ba/best"
            base["merge_output_format"] = "mp4"
        else:
            base["format"] = f"{single}/b[ext=mp4]/b/best"
        base["format_sort"] = ["hasvid", "hasaud", "vcodec:h264", "acodec:aac", "res:1080", "ext:mp4:m4a"]
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
    files = [os.path.join(TMP, f) for f in os.listdir(TMP) if f.startswith(jid)]
    if not files:
        raise HTTPException(500, "Dosya oluşmadı")
    path = max(files, key=os.path.getsize)
    # Güvence: video H.264 değilse (veya kodek bilinmiyorsa) iPhone için dönüştür
    if r.mode != "audio" and HAS_FFMPEG:
        vc = (i.get("vcodec") or "").lower()
        if not (vc.startswith("avc") or vc.startswith("h264")):
            conv = os.path.join(TMP, f"{jid}_h264.mp4")
            import subprocess
            res = subprocess.run(["ffmpeg", "-y", "-i", path, "-c:v", "libx264", "-preset", "veryfast",
                                  "-pix_fmt", "yuv420p", "-c:a", "aac", "-movflags", "+faststart", conv],
                                 capture_output=True)
            if res.returncode == 0 and os.path.exists(conv):
                try: os.remove(path)
                except OSError: pass
                path = conv
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
