import urllib.request
import re
import sys

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}

url = "https://playuz.net/index.php?do=search&subaction=search&story=Oltin+qoshiq"
req = urllib.request.Request(url, headers=headers)
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', 'ignore')
        matches = re.findall(r'<a href="(https://playuz\.net/[^"]+\.html)">([^<]+)</a>', html)
        print("Playuz search matches:", len(matches))
        for link, title in matches[:5]:
            print(f"  {title.strip()} -> {link}")
            # Fetch the movie page
            m_req = urllib.request.Request(link, headers=headers)
            with urllib.request.urlopen(m_req, timeout=10) as m_resp:
                m_html = m_resp.read().decode('utf-8', 'ignore')
                mp4s = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', m_html)
                print(f"    Found {len(mp4s)} MP4s:", mp4s[:3])
except Exception as e:
    print("Error:", e)
