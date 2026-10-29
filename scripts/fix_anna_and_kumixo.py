import urllib.request
import os
import shutil
from PIL import Image
import io

BASE_DIR = r"E:\Agent\Drama Bot"

# 1. 295 is duplicate of 138 (Tale of the Nine Tailed 1938)
src_138 = os.path.join(BASE_DIR, "posters", "toqqiz_dumli_tulki_s2.jpg")
dst_295 = os.path.join(BASE_DIR, "posters", "kumixo-1938.jpg")
shutil.copy2(src_138, dst_295)
print("[295] Kumixo 1938 copied from 138. Exists:", os.path.exists(dst_295))

# 2. Anna (tt21146902)
anna_urls = [
    "https://m.media-amazon.com/images/M/MV5BMTQ5ZmZjYjktY2ZmZi00ZTVhLTk0NTctZTJhNGNkNTg0MjY3XkEyXkFqcGc@._V1_FMjpg_UX1000_.jpg",
    "https://m.media-amazon.com/images/M/MV5BMTQ5ZmZjYjktY2ZmZi00ZTVhLTk0NTctZTJhNGNkNTg0MjY3XkEyXkFqcGc@._V1_QL75_UY800_.jpg",
    "https://m.media-amazon.com/images/M/MV5BMTQ5ZmZjYjktY2ZmZi00ZTVhLTk0NTctZTJhNGNkNTg0MjY3XkEyXkFqcGc@._V1_.jpg"
]
for u in anna_urls:
    try:
        req = urllib.request.Request(u, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = resp.read()
        im = Image.open(io.BytesIO(data))
        dest = os.path.join(BASE_DIR, "posters", "anna-2022.jpg")
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(dest, "JPEG", quality=92)
        print(f"[293] Anna SUCCESS: {im.size} saved to posters/anna-2022.jpg ({round(len(data)/1024, 1)} KB)")
        break
    except Exception as e:
        print("Anna try failed:", e)
