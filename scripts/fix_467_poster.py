import urllib.request, ssl, io
from PIL import Image, ImageOps

url = "https://upload.wikimedia.org/wikipedia/en/a/a9/Tada%2C_Kimi_wo_Aishiteru.jpg"
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
try:
    with urllib.request.urlopen(req, timeout=10, context=ctx) as resp:
        data = resp.read()
        img = Image.open(io.BytesIO(data))
        if img.mode != "RGB":
            img = img.convert("RGB")
        fitted = ImageOps.fit(img, (500, 750), method=Image.Resampling.LANCZOS)
        fitted.save(r"E:\Agent\Drama Bot\posters\code_467.jpg", "JPEG", quality=92)
        print("SUCCESS: Code 467 poster downloaded and fitted to 500x750!")
except Exception as e:
    print("Download error:", e)
