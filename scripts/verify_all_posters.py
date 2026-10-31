import os
from PIL import Image

poster_dir = r"E:\Agent\Drama Bot\posters"
missing = []
invalid = []

for code in range(101, 480):
    p = os.path.join(poster_dir, f"code_{code}.jpg")
    if not os.path.exists(p):
        missing.append(code)
    else:
        try:
            with Image.open(p) as img:
                if img.size != (500, 750):
                    invalid.append((code, img.size))
        except Exception as e:
            invalid.append((code, str(e)))

print(f"Total doramas checked: 379 (101 to 479)")
print(f"Missing posters: {len(missing)} -> {missing}")
print(f"Invalid size posters: {len(invalid)} -> {invalid}")
