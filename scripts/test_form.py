import urllib.request
import re

headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
req = urllib.request.Request("https://playuz.net/", headers=headers)
with urllib.request.urlopen(req, timeout=10) as resp:
    html = resp.read().decode('utf-8', 'ignore')

forms = re.findall(r'<form[^>]*action=["\']?([^"\'>\s]+)[^>]*>(.*?)</form>', html, re.S)
for act, body in forms:
    print("Form action:", act)
    inputs = re.findall(r'<input[^>]+name=["\']?([^"\'>\s]+)[^>]*>', body)
    print("Inputs:", inputs)
