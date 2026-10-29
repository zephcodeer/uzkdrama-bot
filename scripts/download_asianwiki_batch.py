import urllib.request
import os
from PIL import Image
import io

BASE_DIR = r"E:\Agent\Drama Bot"
POSTERS_DIR = os.path.join(BASE_DIR, "posters")

DIRECT_ASIANWIKI = {
    138: ("posters/toqqiz_dumli_tulki_s2.jpg", "https://asianwiki.com/images/f/f7/Tale_of_the_Nine_Tailed_1938-p2.jpg"),
    268: ("posters/ozga-sayyoralik-mahbubim.jpg", "https://asianwiki.com/images/6/61/You_Who_Came_From_the_Stars-p1.jpg"),
    277: ("posters/samdalriga-xush-kelibsiz.jpg", "https://asianwiki.com/images/a/aa/Welcome_to_Samdalri-p2.jpg"),
    285: ("posters/ruh-barmoqlari-spirit-fingers.jpg", "https://asianwiki.com/images/9/96/Spirit_Fingers-p.jpg"),
    290: ("posters/qadrli-hong-rang-tangeum.jpg", "https://asianwiki.com/images/7/75/Dear_Hongrang-p1.jpg"),
    293: ("posters/anna-2022.jpg", "https://asianwiki.com/images/d/d8/Anna_Korean_Drama-p1.jpg"),
    295: ("posters/kumixo-1938.jpg", "https://asianwiki.com/images/f/f7/Tale_of_the_Nine_Tailed_1938-p2.jpg")
}

for code, (rel_path, url) in DIRECT_ASIANWIKI.items():
    dest = os.path.join(BASE_DIR, rel_path)
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = resp.read()
        im = Image.open(io.BytesIO(data))
        if im.mode != "RGB":
            im = im.convert("RGB")
        im.save(dest, "JPEG", quality=92)
        print(f"[{code}] SUCCESS: {im.size} saved to {rel_path} ({round(len(data)/1024, 1)} KB)")
    except Exception as e:
        print(f"[{code}] FAILED: {e}")
