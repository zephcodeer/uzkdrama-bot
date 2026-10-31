import sqlite3, re, sys, os
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
sys.path.insert(0, r'E:\Agent\Drama Bot')

from database import slugify, normalize_search_text
from scripts.parse_new_dramas import parsed_dramas
from scripts.precurated_meta import KNOWN_DRAMA_META

EXCLUDED_MSGS = {4049, 4590, 4591, 4592, 4593, 4594, 4595, 4596, 4597, 4598, 4599, 4600}

POSTERS_DIR = os.path.join(r'E:\Agent\Drama Bot', 'posters')
os.makedirs(POSTERS_DIR, exist_ok=True)

def create_cinematic_poster(filepath: str, title: str, year: int, genre: str, code: int):
    """500x750 yuqori sifatli quyuq zamonaviy poster yaratish."""
    width, height = 500, 750
    img = Image.new("RGB", (width, height), color=(15, 17, 26))
    draw = ImageDraw.Draw(img)

    # Gradient fon
    for y in range(height):
        ratio = y / height
        r = int(18 + 25 * ratio)
        g = int(20 + 15 * ratio)
        b = int(32 + 35 * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))

    # Dekorativ ramka
    draw.rectangle([(15, 15), (width - 15, height - 15)], outline=(45, 55, 75), width=2)
    draw.rectangle([(20, 20), (width - 20, height - 20)], outline=(30, 38, 55), width=1)

    # Shriftlar
    try:
        font_badge = ImageFont.truetype("arialbd.ttf", 22)
        font_code = ImageFont.truetype("arialbd.ttf", 36)
        font_title = ImageFont.truetype("arialbd.ttf", 28)
        font_meta = ImageFont.truetype("arial.ttf", 20)
        font_sub = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font_badge = font_code = font_title = font_meta = font_sub = ImageFont.load_default()

    # Yuqori badge: UZKDRAMA
    badge_text = "UZKDRAMA VIP CINEMA"
    draw.text((width // 2, 60), badge_text, fill=(245, 166, 35), font=font_badge, anchor="mm")

    # KOD
    code_text = f"CODE #{code}"
    draw.text((width // 2, 105), code_text, fill=(130, 170, 255), font=font_code, anchor="mm")

    # Markaziy kartochka
    draw.rounded_rectangle([(35, 170), (width - 35, 520)], radius=15, fill=(24, 28, 42), outline=(50, 60, 85), width=2)

    # Dorama belgisi / icon
    draw.text((width // 2, 230), "🎬", font=font_code, anchor="mm")

    # Sarlavhani bir necha qatorga bo'lish
    words = title.split()
    lines = []
    curr = []
    for w in words:
        curr.append(w)
        if len(" ".join(curr)) > 22:
            lines.append(" ".join(curr[:-1]))
            curr = [w]
    if curr:
        lines.append(" ".join(curr))

    y_pos = 300
    for line in lines[:4]:
        draw.text((width // 2, y_pos), line, fill=(255, 255, 255), font=font_title, anchor="mm")
        y_pos += 38

    # Janr va yil
    meta_line = f"{year}  •  {genre.split(',')[0].strip()}"
    draw.text((width // 2, y_pos + 15), meta_line, fill=(180, 195, 220), font=font_meta, anchor="mm")

    # Pastki qism
    draw.line([(40, 560), (width - 40, 560)], fill=(45, 55, 75), width=1)
    draw.text((width // 2, 600), "PREMIUM HD QUALITY", fill=(100, 220, 160), font=font_meta, anchor="mm")
    draw.text((width // 2, 640), "O'zbekcha Tarjima va Sifatli Ovoz", fill=(140, 150, 175), font=font_sub, anchor="mm")
    draw.text((width // 2, 690), "t.me/uzkdrama_bot", fill=(100, 120, 155), font=font_sub, anchor="mm")

    img.save(filepath, "JPEG", quality=90)

def clean_raw_title(raw: str) -> tuple[str, str]:
    """Sarlavhadan teglarni tozalash va statusni aniqlash."""
    t = raw.strip()
    status = "Tugallangan"

    # Status belgilari
    if re.search(r"davom etmoqda|ongoing", t, re.IGNORECASE):
        status = "Ongoing"

    # Tozalash
    t = re.sub(r"#[A-Za-z0-9_]+", "", t)
    t = re.sub(r"\|.*$", "", t)  # remove trailing | comments
    t = t.replace("_", " ")
    t = re.sub(r"\s+", " ", t).strip()

    # Agar barcha harflar katta bo'lsa (QASOS, SICHQON), Title Case qilish
    if t.isupper() and len(t) > 3:
        t = t.title()

    return t, status

def guess_genre(title: str) -> str:
    tl = title.lower()
    if any(k in tl for k in ["doktor", "shifoxona", "tabib", "kasalxona"]):
        return "Tibbiyot, Drama"
    if any(k in tl for k in ["qasos", "jangari", "ov", "qotil", "jang", "politsiya", "taksi haydovchisi", "agent"]):
        return "Jangari, Kriminal, Triller"
    if any(k in tl for k in ["jin", "arvoh", "iblis", "zombi", "dahshat"]):
        return "Dahshat, Fantastika, Triller"
    if any(k in tl for k in ["sevgi", "muhabbat", "nikoh", "oshiq", "yigit", "yolgonchim"]):
        return "Romantika, Drama, Komediya"
    if any(k in tl for k in ["saroy", "qirol", "qirolicha", "choson", "samuray"]):
        return "Tarixiy, Drama"
    return "Drama, Romantika"

def guess_year(title: str) -> int:
    m = re.search(r"\b(19\d\d|20[0-2]\d)\b", title)
    if m:
        return int(m.group(1))
    return 2024

print("Ingestion helper loaded successfully.")
