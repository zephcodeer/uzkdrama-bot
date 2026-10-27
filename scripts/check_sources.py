import urllib.request
import re

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

urls = [
    'https://uzmovi.me/seriall/7407-doktor-x-oq-mafia-1-2-3-4-5-6-7-8-9-10-11-qism-drama-korea-seriali-uzbek-tilida-barcha-qismlar-2026-hd-skachat.html',
    'https://asilmedia.biz/load/serialy/tarzhima_serial_tarjima_seriallar/doktor_x_barcha_qismlari_uzbek_tilida/7-1-0-1457',
    'https://salomtv.uz/uz/serials/doktor-iks?season_id=97c25d62-9b47-4eba-8b00-8ce8b07d8f4c',
    'https://playuz.net/koreys_seriallar_uz/1655-doktor-x-oq-mafia-1-2-3-4-5-6-7-8-10-12-qism-koreya-seriali-drama-2026-uzbek-tilida-tarjima-barcha-qismlar.html'
]

for u in urls:
    host = u.split('/')[2]
    print(f"\n=================== {host} ===================")
    try:
        req = urllib.request.Request(u, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            html = resp.read().decode('utf-8', 'ignore')
            print("HTML Length:", len(html))
            
            # Find video links, iframes, and episode buttons
            mp4s = re.findall(r'https?://[^\s"\'<>]+\.mp4[^\s"\'<>]*', html)
            m3u8s = re.findall(r'https?://[^\s"\'<>]+\.m3u8[^\s"\'<>]*', html)
            iframes = re.findall(r'<iframe[^>]+src=["\']([^"\']+)["\']', html)
            file_params = re.findall(r'["\']?(?:file|url|video)["\']?\s*:\s*["\']([^"\']+)["\']', html)
            
            print("MP4s:", len(mp4s), mp4s[:5])
            print("M3U8s:", len(m3u8s), m3u8s[:3])
            print("Iframes:", len(iframes), iframes[:3])
            print("File params:", len(file_params), file_params[:5])
            
            # Find any episode tabs or playlist entries
            series = re.findall(r'(?:qism|seria|episode)[^<]{0,40}', html, re.I)
            print("Series matches sample:", series[:5])
    except Exception as e:
        print(f"Error fetching {u}: {e}")
