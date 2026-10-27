import os
import sys
import sqlite3
import re
from rapidocr_onnxruntime import RapidOCR

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.stderr.reconfigure(encoding='utf-8', errors='replace')

engine = RapidOCR()
screenshots_dir = r"C:\Users\MuhammadSodiq\Pictures\Screenshots"
files = sorted([f for f in os.listdir(screenshots_dir) if f.startswith("Screenshot 2026-10-26 235")])

raw_titles = []
for f in files:
    img_path = os.path.join(screenshots_dir, f)
    result, _ = engine(img_path)
    if result:
        for line in result:
            text = line[1].strip()
            # Clean up common OCR noise
            if len(text) >= 2 and not text.isdigit() and text not in ["Ortga", "Keyingi", "Menyu", "Qidiruv", "Sahifa"]:
                raw_titles.append(text)

# Deduplicate preserving order
seen = set()
unique_titles = []
for t in raw_titles:
    norm = re.sub(r"[^\w\s]", "", t.lower()).strip()
    if norm and norm not in seen:
        seen.add(norm)
        unique_titles.append(t)

print(f"Jami skrinshotlardan ajratilgan unikal doramalar: {len(unique_titles)} ta")

# Compare with database
conn = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c = conn.cursor()
c.execute("""
    SELECT d.id, d.code, d.title, COUNT(e.id) as eps_count
    FROM doramas d
    LEFT JOIN episodes e ON d.id = e.dorama_id
    GROUP BY d.id
""")
db_doramas = c.fetchall()

def find_in_db(title):
    t_clean = re.sub(r"[^\w\s]", "", title.lower()).strip()
    words = [w for w in t_clean.split() if len(w) > 2]
    
    for d_id, code, d_title, eps in db_doramas:
        dt_clean = re.sub(r"[^\w\s]", "", d_title.lower()).strip()
        # Direct match or substring
        if t_clean == dt_clean or t_clean in dt_clean or dt_clean in t_clean:
            return (d_id, code, d_title, eps)
        # Word overlap
        dt_words = [w for w in dt_clean.split() if len(w) > 2]
        if words and dt_words:
            overlap = set(words).intersection(set(dt_words))
            if len(overlap) >= 2 or (len(words) == 1 and overlap):
                return (d_id, code, d_title, eps)
    return None

already_complete = []
in_db_empty = []
missing_completely = []

for t in unique_titles:
    match = find_in_db(t)
    if match:
        d_id, code, d_title, eps = match
        if eps > 0:
            already_complete.append((t, code, d_title, eps))
        else:
            in_db_empty.append((t, code, d_title))
    else:
        missing_completely.append(t)

print("\n" + "="*70)
print(f"1. BOTIMIZDA ALLAQACHON BOR VA TO'LIQ ISHLAYOTGANLAR ({len(already_complete)} ta):")
print("="*70)
for orig, code, db_t, eps in already_complete:
    print(f"  ✅ [{code:3d}] {orig} (Bazada: «{db_t}» - {eps} qism)")

print("\n" + "="*70)
print(f"2. BAZAMIZDA KODI VA POSTERI BOR, LEKIN QISMLARI YO'Q BO'SHLAR ({len(in_db_empty)} ta):")
print("="*70)
for orig, code, db_t in in_db_empty:
    print(f"  ⏳ [{code:3d}] {orig} (Bazada kodi: {code})")

print("\n" + "="*70)
print(f"3. BAZAMIZDA UMUMAN YO'Q, YANGI QO'SHILISHI KERAK BO'LGANLAR ({len(missing_completely)} ta):")
print("="*70)
for i, orig in enumerate(missing_completely, 1):
    print(f"  ❌ {i:2d}. {orig}")

conn.close()
