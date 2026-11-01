import sqlite3
import os
from PIL import Image
import sys

sys.stdout.reconfigure(encoding='utf-8')

conn = sqlite3.connect(r'E:\Agent\Drama Bot\doramas.db')
c = conn.cursor()

c.execute("SELECT code, title, poster_url FROM doramas ORDER BY code ASC")
doramas = c.fetchall()

print(f"Verifying {len(doramas)} doramas in doramas.db...")

missing_files = []
invalid_images = []
sizes = []

for code, title, poster_url in doramas:
    if not poster_url:
        missing_files.append((code, title, 'NO_POSTER_URL'))
        continue
    fpath = os.path.join(r'E:\Agent\Drama Bot', poster_url.replace('/', '\\'))
    if not os.path.exists(fpath):
        missing_files.append((code, title, poster_url))
        continue
    if os.path.getsize(fpath) == 0:
        missing_files.append((code, title, 'EMPTY_FILE'))
        continue
    try:
        with Image.open(fpath) as im:
            sizes.append(im.size)
    except Exception as e:
        invalid_images.append((code, title, poster_url, str(e)))

print("=" * 60)
print(f"Total doramas: {len(doramas)}")
print(f"Missing poster files: {len(missing_files)}")
print(f"Invalid poster images: {len(invalid_images)}")
print(f"Valid poster images: {len(sizes)}")
if missing_files:
    print("\nMissing list:")
    for m in missing_files:
        print("  ", m)
if invalid_images:
    print("\nInvalid list:")
    for inv in invalid_images:
        print("  ", inv)
print("=" * 60)
