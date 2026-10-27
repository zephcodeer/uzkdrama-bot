import urllib.request
import urllib.parse
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

def search_uzmovi(title):
    url = f'https://uzmovi.me/index.php?do=search&subaction=search&story={urllib.parse.quote(title)}'
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode('utf-8', 'ignore')
            links = re.findall(r'<a href="(https://uzmovi\.me/seriall/[^"]+)">([^<]+)</a>', html)
            print(f'Uzmovi for {title}:', len(links), links[:2])
    except Exception as e:
        print('Error:', e)

if __name__ == "__main__":
    search_uzmovi('Oltin qoshiq')
    search_uzmovi('Vinchenzo')
    search_uzmovi('Baxt')
    search_uzmovi('Doona')
