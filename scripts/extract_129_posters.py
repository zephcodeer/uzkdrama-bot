import json, re, sys

sys.stdout.reconfigure(encoding='utf-8', errors='replace')

file_path = r'E:\I\PROFILE\PROFILE LIVE\The News\uzkdrama_barcha_129_ta_drama_hd_posterlar_markazi_FIXED.html'
with open(file_path, 'r', encoding='utf-8') as f:
    text = f.read()

m = re.search(r'const\s+DRAMAS_DATA\s*=\s*(\[\s*\{[\s\S]*?\}\s*\]);', text)
if not m:
    print("Could not find DRAMAS_DATA via regex!")
    sys.exit(1)

json_str = m.group(1)
data = json.loads(json_str)

print(f"Successfully parsed DRAMAS_DATA! Total items: {len(data)}")
print("\nFirst 5 items:")
for item in data[:5]:
    print(item)

print("\nLast 5 items:")
for item in data[-5:]:
    print(item)
