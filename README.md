# LinkIndir — telefona video indirme uygulaması (ücretsiz, açık kaynak)

Instagram, YouTube, TikTok, X, Facebook vb. bağlantıları yapıştır → telefona indir.
yt-dlp'nin desteklediği 1000+ site çalışır.

## 1) Sunucuyu çalıştır (bir kez)
Bilgisayarda:
    pip install -r requirements.txt
    (ffmpeg kurulu olmalı: Windows → winget install ffmpeg / Mac → brew install ffmpeg)
    uvicorn main:app --host 0.0.0.0 --port 8000

Veya Docker:
    docker build -t linkindir . && docker run -p 8000:8000 linkindir

Ücretsiz bulut (Render / Railway / Fly.io): bu klasörü GitHub'a koy, "Dockerfile" ile deploy et.

## 2) Telefona kur
Telefonun tarayıcısında sunucunun adresini aç
(aynı Wi-Fi'da ise  http://BILGISAYAR-IP:8000 ).
- iPhone: Safari → Paylaş → "Ana Ekrana Ekle"
- Android: Chrome → ⋮ → "Ana ekrana ekle"
Artık uygulama simgesi gibi açılır; indirilen dosyalar telefonun İndirilenler/Dosyalar klasörüne gider.

## Notlar
- Instagram'da bazı gizli hesaplar için sunucuya çerez vermek gerekebilir (yt-dlp --cookies).
- İndirdiğin içeriğin telif haklarına ve platform kurallarına kendin uymalısın; kendi
  içeriklerin veya izinli içerikler için kullan.
- yt-dlp'yi ara sıra güncelle:  pip install -U yt-dlp

## Kendi bilgisayarından çalıştırma (ücretsiz, kalıcı)
- Mac: Terminal'de `bash baslat-mac.sh`
- Windows: `baslat-windows.bat` dosyasına çift tıkla
Ekranda çıkan `https://….trycloudflare.com` adresini telefonda aç → Ana Ekrana Ekle.
Not: Bu adres bilgisayar her yeniden başladığında değişir; sabit adres için
Cloudflare hesabı + alan adı ile kalıcı tünel kurulabilir.
