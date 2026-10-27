import urllib.request
import re

url = "https://ok.ru/profile/559051303248/video"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', 'ignore')
        matches = re.findall(r'href=["\']/video/(\d+)["\'][^>]*title=["\']([^"\']+)["\']', html)
        print("Videos by profile:", len(matches))
        for vid, title in matches:
            if "ovchi" in title.lower():
                print(f"  {title.strip()} -> https://ok.ru/video/{vid}")
except Exception as e:
    print("Error:", e)
