import json
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

filepath = r"c:\Users\MuhammadSodiq\Downloads\uzkdrama_246_posterlar_tuzatilgan.html"

with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
    content = f.read()

# Extract DRAMAS_DATA = [...]
m = re.search(r"const\s+DRAMAS_DATA\s*=\s*(\[.*?\]);?\s*(?:const|let|var|function|\n\s*//)", content, re.DOTALL)
if not m:
    # Try finding the array manually
    start = content.find("const DRAMAS_DATA = [")
    if start != -1:
        start_arr = content.find("[", start)
        # Find closing bracket
        end_arr = content.find("];", start_arr)
        if end_arr != -1:
            raw_json = content[start_arr:end_arr+1]
        else:
            raw_json = None
    else:
        raw_json = None
else:
    raw_json = m.group(1)

if raw_json:
    try:
        data = json.loads(raw_json)
        print(f"SUCCESS: Parsed {len(data)} items from DRAMAS_DATA!")
        print("\nKeys in first item:", list(data[0].keys()))
        print("\nFirst item detail (excluding large fields):")
        sample = {k: (v if not isinstance(v, str) or len(v) < 80 else f"{v[:70]}... (len {len(v)})") for k, v in data[0].items()}
        print(json.dumps(sample, indent=2, ensure_ascii=False))

        # Check what kind of poster fields exist
        poster_fields = [k for k in data[0].keys() if "poster" in k.lower() or "img" in k.lower() or "url" in k.lower() or "image" in k.lower()]
        print("\nPoster-related fields:", poster_fields)
        
        # Check how many have base64 vs url
        b64_count = 0
        url_count = 0
        empty_count = 0
        for item in data:
            for pf in poster_fields:
                val = item.get(pf, "")
                if val:
                    if val.startswith("data:image"):
                        b64_count += 1
                    elif val.startswith("http"):
                        url_count += 1
                    else:
                        pass
        print(f"Base64 posters: {b64_count}, HTTP URLs: {url_count}")

    except Exception as e:
        print("JSON parse error:", e)
else:
    print("Could not extract raw_json, let's debug position")
