import urllib.request
import re
import io
from PIL import Image

def get_imdb_hd_poster(imdb_id):
    url = f"https://www.imdb.com/title/{imdb_id}/"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"}
    )
    try:
        with urllib.request.urlopen(req, timeout=8) as r:
            html = r.read().decode("utf-8")
        m = re.search(r'"image":\s*"(https://m\.media-amazon\.com/images/M/[^"]+)"', html)
        if m:
            raw_url = m.group(1)
            clean_url = re.sub(r"\._V1_.*\.jpg", "._V1_.jpg", raw_url)
            return clean_url
    except Exception as e:
        print(f"{imdb_id} error: {e}")
    return None

hulk_url = get_imdb_hd_poster("tt0286716")
inc_hulk_url = get_imdb_hd_poster("tt0800080")

print("Hulk 2003 HD:", hulk_url)
print("The Incredible Hulk 2008 HD:", inc_hulk_url)

if hulk_url:
    req = urllib.request.Request(hulk_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        img = Image.open(io.BytesIO(r.read()))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save("posters/hulk-2003.jpg", "JPEG", quality=92)
        print(f"Hulk 2003 saved: {img.size}")

if inc_hulk_url:
    req = urllib.request.Request(inc_hulk_url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=10) as r:
        img = Image.open(io.BytesIO(r.read()))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        img.save("posters/the-incredible-hulk-2008.jpg", "JPEG", quality=92)
        print(f"The Incredible Hulk 2008 saved: {img.size}")
