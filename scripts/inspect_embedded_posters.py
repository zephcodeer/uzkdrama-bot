import json
import re
import sys
import os
import base64
import io
from PIL import Image

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

filepath = r"c:\Users\MuhammadSodiq\Downloads\uzkdrama_246_posterlar_tuzatilgan.html"

with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# 1. Parse DRAMAS_DATA
s_dd = content.find("const DRAMAS_DATA = [")
e_dd = content.find("];", s_dd)
dramas_data = json.loads(content[s_dd+20:e_dd+1])
print(f"DRAMAS_DATA: {len(dramas_data)} items")

# 2. Parse EMBEDDED_POSTERS
s_ep = content.find("const EMBEDDED_POSTERS = {")
e_ep = content.find("};", s_ep)
embedded_posters = json.loads(content[s_ep+25:e_ep+1])
print(f"EMBEDDED_POSTERS: {len(embedded_posters)} keys")

# 3. Compare codes
dd_codes = set(d["code"] for d in dramas_data)
ep_codes = set(embedded_posters.keys())

print(f"Codes in DRAMAS_DATA: min={min(int(c) for c in dd_codes)}, max={max(int(c) for c in dd_codes)}")
print(f"Codes in EMBEDDED_POSTERS: min={min(int(c) for c in ep_codes)}, max={max(int(c) for c in ep_codes)}")

diff = dd_codes - ep_codes
print(f"DRAMAS_DATA codes missing in EMBEDDED_POSTERS: {diff}")

# 4. Check image dimensions and valid base64
valid_images = 0
invalid_images = 0
total_bytes = 0
sample_sizes = []

for code_str, b64_str in embedded_posters.items():
    try:
        # Format is data:image/jpeg;base64,... or data:image/png;base64,...
        header, b64_data = b64_str.split(";base64,")
        raw_bytes = base64.b64decode(b64_data)
        total_bytes += len(raw_bytes)
        img = Image.open(io.BytesIO(raw_bytes))
        valid_images += 1
        if len(sample_sizes) < 10:
            sample_sizes.append((code_str, img.format, img.size, len(raw_bytes)))
    except Exception as e:
        invalid_images += 1
        print(f"Error on code {code_str}: {e}")

print(f"\nImage Analysis:")
print(f"  Valid decodable images: {valid_images} / {len(embedded_posters)}")
print(f"  Invalid images: {invalid_images}")
print(f"  Total raw image payload: {total_bytes / (1024*1024):.2f} MB")
print("\nSample 10 images (code, format, dimensions, bytes):")
for s in sample_sizes:
    print(f"  Code {s[0]}: {s[1]} {s[2][0]}x{s[2][1]} ({s[3]/1024:.1f} KB)")

# Also check comments in HTML about #273
# "// 246 ta drama (101–346); #273 poster mosligi hali tasdiqlanmagan."
print("\nNotes found in file:")
for line in content[:5000].splitlines():
    if "273" in line or "tasdiq" in line or "tuzat" in line:
        print("  ", line.strip())
