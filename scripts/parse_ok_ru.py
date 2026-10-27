import urllib.request
import re
import json
import html as html_lib

url = "https://ok.ru/video/15972275784242"
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

req = urllib.request.Request(url, headers=headers)
with urllib.request.urlopen(req, timeout=10) as resp:
    page = resp.read().decode('utf-8', 'ignore')

print("Page length:", len(page))

# Find data-options
opts = re.findall(r'data-options=["\']({.*?})["\']', page)
print("Found data-options count:", len(opts))

for opt_str in opts:
    decoded = html_lib.unescape(opt_str)
    try:
        data = json.loads(decoded)
        print("Keys in data-options:", list(data.keys()))
        if "flashvars" in data:
            print("Keys in flashvars:", list(data["flashvars"].keys()))
            meta_val = data["flashvars"].get("metadata")
            print("Type of metadata in flashvars:", type(meta_val))
            if isinstance(meta_val, dict):
                meta = meta_val
            elif isinstance(meta_val, str):
                meta = json.loads(meta_val)
            else:
                meta = {}
            print("Title:", meta.get("movie", {}).get("title"))
            videos = meta.get("videos", [])
            print("Videos count:", len(videos))
            for v in videos:
                q = v.get('name')
                u = v.get('url')
                if q in ['full', 'hd']:
                    try:
                        req_head = urllib.request.Request(u, headers=headers, method='HEAD')
                        with urllib.request.urlopen(req_head, timeout=10) as r:
                            sz = int(r.headers.get('Content-Length', 0)) / (1024*1024)
                            print(f"  -> DIRECT {q.upper()} SIZE: {sz:.1f} MB | Content-Type: {r.headers.get('Content-Type')}")
                    except Exception as err:
                        print(f"  -> Error checking {q}: {err}")
            hls = meta.get("hlsManifestUrl")
            if hls:
                print("  HLS Manifest:", hls[:80])
        else:
            print("Preview of data:", str(data)[:400])
    except Exception as e:
        print("Error parsing option:", e)
