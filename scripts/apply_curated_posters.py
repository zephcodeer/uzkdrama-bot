import sys
import os
import json
import sqlite3
import urllib.request
import urllib.parse
from PIL import Image
import io

DB_PATH = "doramas.db"
POSTERS_DIR = "posters"

def slugify(text):
    text = text.lower().strip()
    clean = ""
    for c in text:
        if c.isalnum() or c in (" ", "-", "_"):
            clean += c
    clean = "-".join(clean.split())
    return clean[:40] or "poster"

def apply_selections(payload):
    if isinstance(payload, str):
        payload = json.loads(payload)

    selections = payload.get("selections", {})
    if not selections:
        print("Xatolik: Hech qanday tanlov topilmadi!")
        return 0

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    applied_count = 0
    skipped_count = 0
    error_count = 0

    print(f"Jami {len(selections)} ta dorama bo'yicha tanlovlar qabul qilindi.")

    for code_str, data in selections.items():
        try:
            code = int(code_str)
        except ValueError:
            continue

        choice = data.get("choice")
        target_url = data.get("url")

        c.execute("SELECT code, title, poster_url FROM doramas WHERE code = ?", (code,))
        row = c.fetchone()
        if not row:
            print(f"[# {code}] Bazada bunday dorama topilmadi, o'tkazib yuborildi.")
            continue

        d_code, d_title, d_curr_poster = row

        if choice == "A":
            # Hozirgi poster ma'qullandi
            skipped_count += 1
            print(f"[# {code}] {d_title} -> Variant A (Hozirgi poster ma'qullandi)")
            continue

        if not target_url or not target_url.startswith("http"):
            print(f"[# {code}] {d_title} -> Noto'g'ri rasm havolasi: {target_url}")
            error_count += 1
            continue

        # Option B yoki CUSTOM tanlangan: rasmni yuklab olamiz
        try:
            print(f"[# {code}] {d_title} -> Yangi poster yuklab olinmoqda ({choice})...")
            req = urllib.request.Request(
                target_url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                img_data = resp.read()

            if len(img_data) < 5000:
                print(f"[# {code}] Xato: Rasm hajmi juda kichik ({len(img_data)} bayt)!")
                error_count += 1
                continue

            # PIL orqali formatni tekshirish va optimallashtirish
            img = Image.open(io.BytesIO(img_data))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            # Fayl nomini aniqlash
            slug = slugify(d_title)
            filename = f"{d_code}_{slug}.jpg"
            local_path = os.path.join(POSTERS_DIR, filename)

            img.save(local_path, "JPEG", quality=92)

            # DB ga yangi nisbiy yo'lni yozish
            rel_poster_url = f"posters/{filename}".replace("\\", "/")
            c.execute("UPDATE doramas SET poster_url = ? WHERE code = ?", (rel_poster_url, code))
            conn.commit()

            print(f"[# {code}] ✅ MUVAFFAQIYATLI: {rel_poster_url} saqlandi ({img.size[0]}x{img.size[1]})")
            applied_count += 1

        except Exception as e:
            print(f"[# {code}] Xatolik yuz berdi: {e}")
            error_count += 1

    conn.close()

    print("\n" + "="*50)
    print(f"XULOSA:")
    print(f"  ✅ Yangilangan posterlar: {applied_count} ta")
    print(f"  ⏭️ O'zgarishsiz qoldirilgan (A): {skipped_count} ta")
    print(f"  ⚠️ Xatolar: {error_count} ta")
    print("="*50)
    return applied_count

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Foydalanish:")
        print("  python scripts/apply_curated_posters.py <json_fayl_yoki_matn>")
        sys.exit(1)

    arg = sys.argv[1]
    if os.path.exists(arg):
        with open(arg, "r", encoding="utf-8") as f:
            content = f.read()
    else:
        content = arg

    apply_selections(content)
