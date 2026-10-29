import urllib.request
import re
from PIL import Image
import io

asianwiki_pages = [
    "Welcome_to_Samdal-ri",
    "Tale_of_the_Nine_Tailed_1938",
    "My_Love_From_the_Star",
    "Anna_(Korean_Drama)",
    "Today%27s_Webtoon",
    "Head_Over_Heels_(Korean_Drama)",
    "Spirit_Fingers",
    "Dear_Hongrang"
]

for p in asianwiki_pages:
    url = f"https://asianwiki.com/{p}"
    req = urllib.request.Request(url, headers={
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    })
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
        # Find poster img
        m = re.findall(r'src=["\'](https://static\.wikia\.nocookie\.net/asianwiki/images/[^"\']+)["\']', html)
        if not m:
            m = re.findall(r'src=["\'](/images/[^"\']+\.jpg)["\']', html)
            m = [f"https://asianwiki.com{x}" for x in m]
        if m:
            # Test download first image
            img_url = m[0]
            req_img = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req_img, timeout=8) as r_img:
                raw = r_img.read()
            im = Image.open(io.BytesIO(raw))
            print(f"{p} -> {im.size} | {img_url}")
        else:
            print(f"{p} -> No image found in HTML")
    except Exception as e:
        print(f"{p} -> Error: {e}")
