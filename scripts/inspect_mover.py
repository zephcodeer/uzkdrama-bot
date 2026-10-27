import urllib.request
import ssl
import json
import re

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = 'https://mover.uz/watch/uGmXQUji'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'})
try:
    with urllib.request.urlopen(req, context=ctx, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
    print('HTML len:', len(html))
    with open('E:/Agent/Drama Bot/mover_test.html', 'w', encoding='utf-8') as f:
        f.write(html)
    
    # search for media
    media = re.findall(r'https?://[^\s"\'<>]+\.(?:mp4|m3u8)[^\s"\'<>]*', html)
    print('Media urls:', media)
    
    # search for video tags
    video_tag = re.findall(r'<video[^>]+src=["\']([^"\']+)["\']', html)
    print('Video tag:', video_tag)
    
    # search for source tags
    sources = re.findall(r'<source[^>]+src=["\']([^"\']+)["\']', html)
    print('Sources:', sources)

    # search for data attributes or script json
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    print(f'Scripts count: {len(scripts)}')
    for i, s in enumerate(scripts):
        if any(k in s for k in ['video', 'player', 'm3u8', 'mp4', 'file', 'stream', 'hls']):
            print(f'\n--- Script {i} ---')
            print(s[:500])

except Exception as e:
    print('Error:', e)
