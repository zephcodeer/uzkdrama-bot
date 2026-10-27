import urllib.request
import re

url = "https://doramalar.net/dorama/ovchi-itlar-37/2-fasl-6-qism"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', 'ignore')
        print("HTML Length:", len(html))
        # Look for iframe
        iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
        print("Iframes:", iframes)
        # Look for ok.ru links
        ok_links = re.findall(r'https?://(?:www\.)?ok\.ru/(?:video|videoembed)/\d+', html)
        print("OK.ru links in page:", ok_links)
        # Look for video or file params
        files = re.findall(r'["\']?(?:file|src|url)["\']?\s*:\s*["\']([^"\']+)["\']', html)
        print("Files/urls found:", files[:5])
        mp4s = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', html)
        print("MP4s:", mp4s[:5])
except Exception as e:
    print("Error:", e)
