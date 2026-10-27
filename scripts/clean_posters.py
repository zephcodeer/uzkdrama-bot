import sqlite3
import urllib.request
import urllib.parse
import re
import ssl
import sys
import os
from PIL import Image

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

POSTERS_DIR = r"E:\Agent\Drama Bot\posters"
os.makedirs(POSTERS_DIR, exist_ok=True)

c = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
cur = c.cursor()

# Set Ovchi itlar to local poster
ovchi_poster = os.path.join(POSTERS_DIR, "ovchi_itlar.jpg").replace("\\", "/")
if os.path.exists(ovchi_poster):
    cur.execute("UPDATE doramas SET poster_url = ? WHERE id IN (18, 35)", (ovchi_poster,))
    print(f"Updated Ovchi itlar poster to {ovchi_poster}")

# Clear 404 amazon posters to prevent invalid requests
cur.execute("UPDATE doramas SET poster_url = NULL WHERE poster_url LIKE 'https://m.media-amazon.com%'")
print(f"Cleared broken amazon poster URLs in database. Affected: {cur.rowcount}")

c.commit()
c.close()
