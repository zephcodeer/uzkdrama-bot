import urllib.request
import re

url = "https://www.soompi.com/article/1529107wpp/suzy-transforms-into-a-mysterious-woman-living-a-double-life-in-poster-for-new-drama-anna"
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode("utf-8", errors="ignore")
    # find images from 0.soompi.io or wp.com
    imgs = re.findall(r'https://[^\s"\'<>]+\.(?:jpg|jpeg|png)', html)
    print("Found images:", len(imgs))
    for img in set(imgs):
        if "soompi.io" in img or "wp.com" in img:
            print("  ", img)
except Exception as e:
    print("Error:", e)
