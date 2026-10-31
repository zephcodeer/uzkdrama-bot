import re
import sys
import json
from bs4 import BeautifulSoup

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

filepath = r"c:\Users\MuhammadSodiq\Downloads\uzkdrama_246_posterlar_tuzatilgan.html"

with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

print(f"File size in chars: {len(content)}")
print("--- PREVIEW START (first 1200 chars) ---")
print(content[:1200])
print("--- PREVIEW END ---")

# Search for JSON objects or variables
scripts = re.findall(r"<script[^>]*>(.*?)</script>", content, re.DOTALL | re.IGNORECASE)
print(f"Total script tags found: {len(scripts)}")
for i, s in enumerate(scripts):
    print(f"Script #{i+1} length: {len(s)} chars. First 200 chars:")
    print(s[:200].strip())
    print("-" * 40)

# Check for img tags
img_tags = re.findall(r"<img[^>]+>", content, re.IGNORECASE)
print(f"Total img tags: {len(img_tags)}")
for i, tag in enumerate(img_tags[:5]):
    print(f"Img #{i+1}: {tag[:150]}")

# Check for table or cards
cards = re.findall(r'class=["\'][^"\']*(?:card|poster|dorama|item)[^"\']*["\']', content, re.IGNORECASE)
print(f"Card-like classes found: {len(cards)}")
