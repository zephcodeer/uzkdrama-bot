import urllib.request
import os
from PIL import Image
import io

BASE_DIR = r"E:\Agent\Drama Bot"

MAPPINGS = {
    138: ("posters/toqqiz_dumli_tulki_s2.jpg", "https://m.media-amazon.com/images/M/MV5BNWYxNDM2NDYtM2EwOS00NTMxLThmNGQtMTJiZWEzMDJiMDQ1XkEyXkFqcGc@._V1_.jpg"),
    239: ("posters/men-bugundan-insonman-65.jpg", "https://m.media-amazon.com/images/M/MV5BN2FmOGEwYjctYTllYS00OWYyLTkzNDktOWMzZWY3MWY0ODk3XkEyXkFqcGc@._V1_.jpg"),
    268: ("posters/ozga-sayyoralik-mahbubim.jpg", "https://m.media-amazon.com/images/M/MV5BMjM4MzhmYTAtY2EwYi00ZTI1LWI0OTYtZmNkNzFiYWM0NzU2XkEyXkFqcGc@._V1_.jpg"),
    277: ("posters/samdalriga-xush-kelibsiz.jpg", "https://m.media-amazon.com/images/M/MV5BZTRkMmFmM2YtYmFiYi00NGZkLWIzOTUtNGYxOGMxMjRmNWRkXkEyXkFqcGc@._V1_.jpg"),
    293: ("posters/anna-2022.jpg", "https://m.media-amazon.com/images/M/MV5BMTQ5ZmZjYjktY2ZmZi00ZTVhLTk0NTctZTJhNGNkNTg0MjY3XkEyXkFqcGc@._V1_.jpg"),
    295: ("posters/kumixo-1938.jpg", "https://m.media-amazon.com/images/M/MV5BNWYxNDM2NDYtM2EwOS00NTMxLThmNGQtMTJiZWEzMDJiMDQ1XkEyXkFqcGc@._V1_.jpg")
}

for code, (rel_path, url) in MAPPINGS.items():
    dest = os.path.join(BASE_DIR, rel_path)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=12) as resp:
        data = resp.read()
    im = Image.open(io.BytesIO(data))
    if im.mode != "RGB":
        im = im.convert("RGB")
    im.save(dest, "JPEG", quality=92)
    print(f"[{code}] SUCCESS: {im.size} saved to {rel_path} ({round(os.path.getsize(dest)/1024, 1)} KB)")
