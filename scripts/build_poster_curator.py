import sqlite3
import urllib.request
import urllib.parse
import json
import os
from concurrent.futures import ThreadPoolExecutor

DB_PATH = "doramas.db"
OUTPUT_HTML = "poster_curator.html"

# 1. Fetch doramas from database
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute("""
    SELECT code, title, year, genre, poster_url, aliases
    FROM doramas
    ORDER BY code DESC
""")
rows = c.fetchall()
conn.close()

print(f"Bazada jami {len(rows)} ta dorama topildi. Muqobil posterlar qidirilmoqda...")

def fetch_alternative_poster(row):
    code, title, year, genre, poster_a, aliases = row
    queries = []

    # 1. Title in parentheses if any
    if "(" in title and ")" in title:
        q_bracket = title[title.rfind("(") + 1 : title.rfind(")")].strip()
        queries.append((q_bracket, year))
        queries.append((q_bracket, None))

    # 2. Aliases first clean item
    if aliases:
        for a in aliases.split(","):
            a_clean = a.strip()
            if a_clean and len(a_clean) > 2:
                queries.append((a_clean, year))
                queries.append((a_clean, None))
                break

    # 3. Clean main title
    clean_t = title.split("(")[0].split("-")[0].split(",")[0].strip()
    queries.append((clean_t, year))
    queries.append((clean_t, None))

    for q, y in queries:
        try:
            url = f"http://www.omdbapi.com/?apikey=bd182e04&t={urllib.parse.quote(q)}"
            if y:
                url += f"&y={y}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=3.5) as resp:
                data = json.loads(resp.read().decode())
                if data.get("Response") == "True" and data.get("Poster") and data["Poster"] != "N/A":
                    return code, data["Poster"]
        except Exception:
            pass

    return code, None

alt_posters = {}
with ThreadPoolExecutor(max_workers=12) as executor:
    for code, alt_url in executor.map(fetch_alternative_poster, rows):
        if alt_url:
            alt_posters[code] = alt_url

print(f"Jami {len(alt_posters)} ta dorama uchun muqobil (Option B) posterlar topildi!")

# 2. Assemble dataset for HTML
dataset = []
for r in rows:
    code, title, year, genre, poster_a, aliases = r
    poster_b = alt_posters.get(code, "")
    dataset.append({
        "code": code,
        "title": title,
        "year": year or 2024,
        "genre": genre or "Dorama",
        "poster_a": poster_a,
        "poster_b": poster_b,
        "aliases": aliases or ""
    })

dataset_json = json.dumps(dataset, ensure_ascii=False)

# 3. Build HTML file with Arounda / Public design system
html_content = f"""<!DOCTYPE html>
<html lang="uz">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>PUBLIC — Dorama Poster Curator</title>
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700;800;900&family=Space+Grotesk:wght@500;700&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg-dark: #161316;
            --bg-card: rgba(26, 21, 26, 0.85);
            --border-warm: #453027;
            --accent-orange: #FF6D29;
            --accent-glow: rgba(255, 109, 41, 0.35);
            --text-white: #FFFFFF;
            --text-muted: #BABABA;
            --font-main: 'Outfit', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-display: 'Space Grotesk', sans-serif;
        }}

        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
            user-select: none;
        }}

        body {{
            background-color: var(--bg-dark);
            color: var(--text-white);
            font-family: var(--font-main);
            min-height: 100vh;
            overflow-x: hidden;
            position: relative;
        }}

        /* Ambient Glow Backgrounds */
        .ambient-glow-1 {{
            position: fixed;
            top: -150px;
            left: -150px;
            width: 600px;
            height: 600px;
            background: radial-gradient(circle, rgba(255, 109, 41, 0.18) 0%, transparent 70%);
            filter: blur(80px);
            pointer-events: none;
            z-index: 0;
        }}

        .ambient-glow-2 {{
            position: fixed;
            bottom: -200px;
            right: -100px;
            width: 700px;
            height: 700px;
            background: radial-gradient(circle, rgba(69, 48, 39, 0.45) 0%, transparent 70%);
            filter: blur(100px);
            pointer-events: none;
            z-index: 0;
        }}

        /* Header Bar */
        header {{
            position: sticky;
            top: 0;
            z-index: 50;
            backdrop-filter: blur(24px);
            background: rgba(22, 19, 22, 0.82);
            border-bottom: 1px solid var(--border-warm);
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .brand-section {{
            display: flex;
            align-items: center;
            gap: 18px;
        }}

        .public-logo {{
            font-family: var(--font-display);
            font-size: 28px;
            font-weight: 900;
            letter-spacing: 2px;
            text-transform: uppercase;
            color: var(--text-white);
            background: #FFFFFF;
            color: #000;
            padding: 4px 14px;
            border-radius: 8px;
            display: inline-block;
            box-shadow: 0 4px 20px rgba(255, 255, 255, 0.15);
        }}

        .brand-title {{
            display: flex;
            flex-direction: column;
        }}

        .brand-title h1 {{
            font-size: 16px;
            font-weight: 700;
            letter-spacing: 0.5px;
        }}

        .brand-title span {{
            font-size: 12px;
            color: var(--text-muted);
        }}

        .stats-pill {{
            display: flex;
            align-items: center;
            gap: 12px;
            background: rgba(69, 48, 39, 0.35);
            border: 1px solid var(--border-warm);
            padding: 8px 18px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 600;
        }}

        .stats-pill .badge-orange {{
            color: var(--accent-orange);
        }}

        .header-actions {{
            display: flex;
            align-items: center;
            gap: 14px;
        }}

        .btn-export {{
            background: var(--accent-orange);
            color: #FFFFFF;
            border: none;
            padding: 10px 22px;
            border-radius: 9999px;
            font-family: var(--font-main);
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
            box-shadow: 0 4px 20px rgba(255, 109, 41, 0.4);
        }}

        .btn-export:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 25px rgba(255, 109, 41, 0.6);
        }}

        /* Search & Filter Strip */
        .filter-strip {{
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 20px;
            position: relative;
            z-index: 10;
        }}

        .search-box {{
            flex: 1;
            max-width: 420px;
            position: relative;
        }}

        .search-box input {{
            width: 100%;
            background: rgba(69, 48, 39, 0.25);
            border: 1px solid var(--border-warm);
            padding: 12px 18px 12px 42px;
            border-radius: 9999px;
            color: #FFFFFF;
            font-family: var(--font-main);
            font-size: 14px;
            outline: none;
            transition: border-color 0.2s ease;
        }}

        .search-box input:focus {{
            border-color: var(--accent-orange);
            background: rgba(69, 48, 39, 0.45);
        }}

        .search-box svg {{
            position: absolute;
            left: 16px;
            top: 50%;
            transform: translateY(-50%);
            width: 16px;
            height: 16px;
            fill: var(--text-muted);
        }}

        .filter-tags {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}

        .filter-btn {{
            background: transparent;
            border: 1px solid var(--border-warm);
            color: var(--text-muted);
            padding: 8px 16px;
            border-radius: 9999px;
            font-size: 13px;
            font-weight: 500;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .filter-btn.active, .filter-btn:hover {{
            background: rgba(255, 109, 41, 0.15);
            border-color: var(--accent-orange);
            color: #FFFFFF;
        }}

        /* Main Workspace Arena */
        main {{
            position: relative;
            z-index: 10;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px 32px 120px;
        }}

        /* Dorama Header Card */
        .dorama-banner {{
            background: var(--bg-card);
            border: 1px solid var(--border-warm);
            border-radius: 20px;
            padding: 22px 28px;
            margin-bottom: 24px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            backdrop-filter: blur(16px);
        }}

        .dorama-info {{
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .code-pill {{
            background: var(--accent-orange);
            color: #FFF;
            font-weight: 800;
            font-size: 16px;
            padding: 8px 16px;
            border-radius: 12px;
            letter-spacing: 0.5px;
        }}

        .dorama-titles h2 {{
            font-size: 22px;
            font-weight: 700;
            margin-bottom: 4px;
        }}

        .dorama-titles p {{
            font-size: 13px;
            color: var(--text-muted);
        }}

        .keyboard-hint {{
            display: flex;
            align-items: center;
            gap: 8px;
            color: var(--text-muted);
            font-size: 13px;
        }}

        .kbd {{
            background: rgba(255, 255, 255, 0.1);
            border: 1px solid rgba(255, 255, 255, 0.2);
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: 700;
            color: #FFF;
        }}

        /* Duel Comparison Stage */
        .duel-container {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 32px;
        }}

        .poster-card {{
            background: var(--bg-card);
            border: 2px solid var(--border-warm);
            border-radius: 24px;
            padding: 24px;
            display: flex;
            flex-direction: column;
            align-items: center;
            position: relative;
            cursor: pointer;
            transition: all 0.25s cubic-bezier(0.16, 1, 0.3, 1);
            backdrop-filter: blur(20px);
        }}

        .poster-card:hover {{
            transform: translateY(-4px);
            border-color: rgba(255, 109, 41, 0.5);
        }}

        .poster-card.selected {{
            border-color: var(--accent-orange);
            box-shadow: 0 0 35px var(--accent-glow);
            background: rgba(36, 25, 25, 0.95);
        }}

        .card-header-badge {{
            width: 100%;
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }}

        .badge-choice {{
            font-size: 14px;
            font-weight: 800;
            letter-spacing: 1px;
            padding: 6px 14px;
            border-radius: 9999px;
            background: rgba(69, 48, 39, 0.5);
            border: 1px solid var(--border-warm);
            color: #FFFFFF;
        }}

        .poster-card.selected .badge-choice {{
            background: var(--accent-orange);
            color: #FFFFFF;
            border-color: var(--accent-orange);
        }}

        .check-badge {{
            display: none;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            background: var(--accent-orange);
            color: #FFF;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            font-weight: 900;
        }}

        .poster-card.selected .check-badge {{
            display: flex;
        }}

        /* Poster Image Frame */
        .poster-frame {{
            width: 100%;
            max-width: 440px;
            height: 580px;
            border-radius: 16px;
            overflow: hidden;
            position: relative;
            background: #0d0b0d;
            border: 1px solid rgba(255, 255, 255, 0.08);
            display: flex;
            align-items: center;
            justify-content: center;
        }}

        .poster-frame img {{
            width: 100%;
            height: 100%;
            object-fit: cover;
            transition: transform 0.3s ease;
        }}

        .poster-card:hover .poster-frame img {{
            transform: scale(1.02);
        }}

        .poster-frame .no-image-text {{
            color: var(--text-muted);
            font-size: 14px;
            text-align: center;
            padding: 20px;
        }}

        .zoom-btn {{
            position: absolute;
            bottom: 14px;
            right: 14px;
            background: rgba(0, 0, 0, 0.75);
            backdrop-filter: blur(8px);
            border: 1px solid rgba(255, 255, 255, 0.2);
            color: #FFF;
            padding: 8px 12px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            opacity: 0;
            transition: opacity 0.2s ease;
        }}

        .poster-card:hover .zoom-btn {{
            opacity: 1;
        }}

        .card-footer-action {{
            width: 100%;
            margin-top: 20px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }}

        .btn-select {{
            flex: 1;
            padding: 12px 20px;
            border-radius: 12px;
            border: 1px solid var(--border-warm);
            background: rgba(69, 48, 39, 0.3);
            color: #FFFFFF;
            font-family: var(--font-main);
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            text-align: center;
        }}

        .poster-card.selected .btn-select {{
            background: var(--accent-orange);
            border-color: var(--accent-orange);
            color: #FFFFFF;
        }}

        .btn-select:hover {{
            background: var(--accent-orange);
            border-color: var(--accent-orange);
        }}

        /* Custom URL Input Box */
        .custom-url-box {{
            margin-top: 28px;
            background: var(--bg-card);
            border: 1px solid var(--border-warm);
            border-radius: 18px;
            padding: 18px 24px;
            display: flex;
            align-items: center;
            gap: 16px;
        }}

        .custom-url-box input {{
            flex: 1;
            background: rgba(0, 0, 0, 0.4);
            border: 1px solid var(--border-warm);
            padding: 12px 18px;
            border-radius: 10px;
            color: #FFF;
            font-family: var(--font-main);
            font-size: 14px;
            outline: none;
        }}

        .custom-url-box input:focus {{
            border-color: var(--accent-orange);
        }}

        .btn-apply-url {{
            background: rgba(255, 109, 41, 0.2);
            border: 1px solid var(--accent-orange);
            color: var(--accent-orange);
            padding: 12px 20px;
            border-radius: 10px;
            font-weight: 700;
            font-size: 13px;
            cursor: pointer;
            transition: all 0.2s ease;
        }}

        .btn-apply-url:hover {{
            background: var(--accent-orange);
            color: #FFF;
        }}

        .search-helpers {{
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .helper-btn {{
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-warm);
            color: var(--text-muted);
            padding: 10px 14px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 6px;
        }}

        .helper-btn:hover {{
            border-color: var(--accent-orange);
            color: #FFF;
        }}

        /* Fixed Bottom Control Bar */
        .bottom-bar {{
            position: fixed;
            bottom: 0;
            left: 0;
            right: 0;
            z-index: 50;
            background: rgba(22, 19, 22, 0.88);
            border-top: 1px solid var(--border-warm);
            backdrop-filter: blur(24px);
            padding: 16px 32px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }}

        .nav-controls {{
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .btn-nav {{
            background: rgba(69, 48, 39, 0.35);
            border: 1px solid var(--border-warm);
            color: #FFFFFF;
            padding: 12px 24px;
            border-radius: 9999px;
            font-family: var(--font-main);
            font-size: 14px;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.2s ease;
            display: flex;
            align-items: center;
            gap: 8px;
        }}

        .btn-nav:hover:not(:disabled) {{
            background: rgba(255, 109, 41, 0.2);
            border-color: var(--accent-orange);
        }}

        .btn-nav:disabled {{
            opacity: 0.3;
            cursor: not-allowed;
        }}

        /* Modal Lightbox */
        .modal-overlay {{
            position: fixed;
            inset: 0;
            background: rgba(0, 0, 0, 0.92);
            backdrop-filter: blur(16px);
            z-index: 100;
            display: none;
            align-items: center;
            justify-content: center;
            padding: 40px;
        }}

        .modal-overlay.active {{
            display: flex;
        }}

        .modal-img {{
            max-width: 90vw;
            max-height: 90vh;
            border-radius: 12px;
            box-shadow: 0 0 50px rgba(0, 0, 0, 0.8);
            border: 1px solid rgba(255, 255, 255, 0.2);
        }}

        /* Toast Alert */
        .toast {{
            position: fixed;
            top: 24px;
            right: 24px;
            background: #161316;
            border: 1px solid var(--accent-orange);
            color: #FFFFFF;
            padding: 16px 24px;
            border-radius: 14px;
            font-weight: 700;
            box-shadow: 0 8px 30px var(--accent-glow);
            z-index: 200;
            transform: translateY(-50px);
            opacity: 0;
            transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            display: flex;
            align-items: center;
            gap: 12px;
        }}

        .toast.show {{
            transform: translateY(0);
            opacity: 1;
        }}
    </style>
</head>
<body>

    <div class="ambient-glow-1"></div>
    <div class="ambient-glow-2"></div>

    <!-- Header -->
    <header>
        <div class="brand-section">
            <span class="public-logo">PUBLIC</span>
            <div class="brand-title">
                <h1>POSTER CURATOR STUDIO</h1>
                <span>UzKDrama Platform Parity & Aesthetics</span>
            </div>
        </div>

        <div class="stats-pill">
            <span>Dorama: <b id="stat-current" class="badge-orange">1</b> / <b id="stat-total">246</b></span>
            <span>•</span>
            <span>Tanlandi: <b id="stat-selected" class="badge-orange">0</b> ta</span>
        </div>

        <div class="header-actions">
            <button class="btn-export" onclick="exportSelections()">
                <span>⚡ Kodni Nusxalash</span>
            </button>
        </div>
    </header>

    <!-- Filters & Search -->
    <div class="filter-strip">
        <div class="search-box">
            <svg viewBox="0 0 24 24"><path d="M15.5 14h-.79l-.28-.27A6.471 6.471 0 0 0 16 9.5 6.5 6.5 0 1 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l5 4.99L20.49 19l-4.99-5zm-6 0C7.01 14 5 11.99 5 9.5S7.01 5 9.5 5 14 7.01 14 9.5 11.99 14 9.5 14z"/></svg>
            <input type="text" id="search-input" placeholder="Kino kodi yoki nomi bo'yicha tezkor sakrash..." oninput="onSearchInput()">
        </div>

        <div class="filter-tags">
            <button class="filter-btn active" onclick="setFilter('all')">Barchasi (246)</button>
            <button class="filter-btn" onclick="setFilter('recent')">So'nggilar (340-346)</button>
            <button class="filter-btn" onclick="setFilter('unselected')">Kutilayotganlar</button>
            <button class="filter-btn" onclick="setFilter('custom')">O'zgartirilganlar</button>
        </div>
    </div>

    <!-- Main Workspace -->
    <main>
        <!-- Dorama Info Card -->
        <div class="dorama-banner">
            <div class="dorama-info">
                <span class="code-pill" id="view-code">#346</span>
                <div class="dorama-titles">
                    <h2 id="view-title">Agent Kimning qaytishi (Manager Kim 2025)</h2>
                    <p id="view-meta">Janr: Jangari, Triller • Yili: 2025 • Aliases: Manager Kim</p>
                </div>
            </div>
            <div class="keyboard-hint">
                <span>Tanlash: <span class="kbd">A</span> yoki <span class="kbd">B</span></span>
                <span>•</span>
                <span>O'tish: <span class="kbd">←</span> <span class="kbd">→</span></span>
            </div>
        </div>

        <!-- Duel Container -->
        <div class="duel-container">
            <!-- Variant A Card -->
            <div class="poster-card" id="card-a" onclick="selectChoice('A')">
                <div class="card-header-badge">
                    <span class="badge-choice">VARIANT A (Hozirgi Baza)</span>
                    <span class="check-badge">✓</span>
                </div>
                <div class="poster-frame">
                    <img id="img-a" src="" alt="Variant A">
                    <button class="zoom-btn" onclick="openZoom(event, 'A')">Kattalashtirish ↗</button>
                </div>
                <div class="card-footer-action">
                    <button class="btn-select" id="btn-select-a">Variant A ni tanlash</button>
                </div>
            </div>

            <!-- Variant B Card -->
            <div class="poster-card" id="card-b" onclick="selectChoice('B')">
                <div class="card-header-badge">
                    <span class="badge-choice">VARIANT B (Muqobil HD / TMDB)</span>
                    <span class="check-badge">✓</span>
                </div>
                <div class="poster-frame">
                    <img id="img-b" src="" alt="Variant B" onerror="this.src='https://via.placeholder.com/600x840/221b22/bababa?text=Variant+B+mavjud+emas'">
                    <button class="zoom-btn" onclick="openZoom(event, 'B')">Kattalashtirish ↗</button>
                </div>
                <div class="card-footer-action">
                    <button class="btn-select" id="btn-select-b">Variant B ni tanlash</button>
                </div>
            </div>
        </div>

        <!-- Custom URL & Search Helpers -->
        <div class="custom-url-box">
            <input type="text" id="custom-url-input" placeholder="Ikkala variant ham yoqmadimi? Istalgan rasmiy poster havolasini shu yerga qo'ying...">
            <button class="btn-apply-url" onclick="applyCustomUrl()">Qo'llash (Variant C)</button>

            <div class="search-helpers">
                <a id="link-google" href="#" target="_blank" class="helper-btn">
                    <span>Google Rasm</span> ↗
                </a>
                <a id="link-tmdb" href="#" target="_blank" class="helper-btn">
                    <span>TMDB</span> ↗
                </a>
            </div>
        </div>
    </main>

    <!-- Bottom Bar Controls -->
    <div class="bottom-bar">
        <div class="nav-controls">
            <button class="btn-nav" id="btn-prev" onclick="prevDorama()">← Oldingi (A)</button>
            <button class="btn-nav" id="btn-next" onclick="nextDorama()">Keyingi (D) →</button>
        </div>

        <div style="font-size: 13px; color: var(--text-muted);">
            Tanlovingiz avtomatik xotirada saqlanadi. Istalgan vaqtda <b>"Kodni Nusxalash"</b> tugmasini bosing!
        </div>

        <button class="btn-export" onclick="exportSelections()">
            <span>📋 Eksport Kodini Olish</span>
        </button>
    </div>

    <!-- Modal Lightbox -->
    <div class="modal-overlay" id="modal-lightbox" onclick="closeZoom()">
        <img class="modal-img" id="modal-img" src="" alt="Zoomed Poster">
    </div>

    <!-- Toast Notification -->
    <div class="toast" id="toast-alert">
        <span>✅ Kod nusxalandi! Chatga yuboring.</span>
    </div>

    <script>
        const DORAMAS = {dataset_json};

        let currentIndex = 0;
        let selections = JSON.parse(localStorage.getItem('uzkdrama_poster_selections') || '{{}}');
        let currentFilter = 'all';
        let filteredIndices = DORAMAS.map((_, i) => i);

        function init() {{
            applyFilter();
            renderCurrent();
            updateStats();

            document.addEventListener('keydown', (e) => {{
                if (e.target.tagName === 'INPUT') return;
                if (e.key === 'a' || e.key === 'A' || e.key === '1') selectChoice('A');
                if (e.key === 'b' || e.key === 'B' || e.key === '2') selectChoice('B');
                if (e.key === 'ArrowLeft') prevDorama();
                if (e.key === 'ArrowRight' || e.key === ' ') nextDorama();
                if (e.key === 'Enter') nextDorama();
            }});
        }}

        function applyFilter() {{
            const searchVal = document.getElementById('search-input').value.toLowerCase().trim();
            filteredIndices = [];

            DORAMAS.forEach((d, idx) => {{
                let matchFilter = true;
                if (currentFilter === 'recent') {{
                    matchFilter = d.code >= 340;
                }} else if (currentFilter === 'unselected') {{
                    matchFilter = !selections[d.code];
                }} else if (currentFilter === 'custom') {{
                    matchFilter = selections[d.code] && (selections[d.code].choice === 'B' || selections[d.code].choice === 'CUSTOM');
                }}

                let matchSearch = true;
                if (searchVal) {{
                    matchSearch = d.title.toLowerCase().includes(searchVal) || 
                                  String(d.code).includes(searchVal) || 
                                  d.aliases.toLowerCase().includes(searchVal);
                }}

                if (matchFilter && matchSearch) {{
                    filteredIndices.push(idx);
                }}
            }});

            if (filteredIndices.length === 0) {{
                currentIndex = 0;
            }} else if (currentIndex >= filteredIndices.length) {{
                currentIndex = filteredIndices.length - 1;
            }}
        }}

        function renderCurrent() {{
            if (filteredIndices.length === 0) {{
                document.getElementById('view-title').innerText = "Hech qanday dorama topilmadi";
                document.getElementById('view-code').innerText = "#000";
                return;
            }}

            const actualIdx = filteredIndices[currentIndex];
            const dorama = DORAMAS[actualIdx];

            document.getElementById('view-code').innerText = '#' + dorama.code;
            document.getElementById('view-title').innerText = dorama.title;
            document.getElementById('view-meta').innerText = `Yili: ${{dorama.year}} • Janr: ${{dorama.genre}} • Aliases: ${{dorama.aliases || 'mavjud emas'}}`;

            // Images
            document.getElementById('img-a').src = dorama.poster_a || 'https://via.placeholder.com/600x840/221b22/bababa?text=Variant+A';
            document.getElementById('img-b').src = dorama.poster_b || 'https://via.placeholder.com/600x840/221b22/bababa?text=Variant+B+mavjud+emas';

            // Custom input
            document.getElementById('custom-url-input').value = (selections[dorama.code] && selections[dorama.code].choice === 'CUSTOM') ? selections[dorama.code].url : '';

            // Search helpers
            const cleanTitle = encodeURIComponent(dorama.title.split('(')[0].trim() + ' poster');
            document.getElementById('link-google').href = `https://www.google.com/search?tbm=isch&q=${{cleanTitle}}+poster+HD`;
            document.getElementById('link-tmdb').href = `https://www.themoviedb.org/search?query=${{cleanTitle}}`;

            // Highlight selection
            const currentSel = selections[dorama.code];
            const cardA = document.getElementById('card-a');
            const cardB = document.getElementById('card-b');
            cardA.classList.remove('selected');
            cardB.classList.remove('selected');

            if (currentSel) {{
                if (currentSel.choice === 'A') cardA.classList.add('selected');
                if (currentSel.choice === 'B') cardB.classList.add('selected');
                if (currentSel.choice === 'CUSTOM') {{
                    document.getElementById('img-b').src = currentSel.url;
                    cardB.classList.add('selected');
                }}
            }}

            // Navigation buttons state
            document.getElementById('btn-prev').disabled = (currentIndex === 0);
            document.getElementById('btn-next').disabled = (currentIndex === filteredIndices.length - 1);

            document.getElementById('stat-current').innerText = (currentIndex + 1);
            document.getElementById('stat-total').innerText = filteredIndices.length;
        }}

        function selectChoice(choice) {{
            const actualIdx = filteredIndices[currentIndex];
            const dorama = DORAMAS[actualIdx];

            if (choice === 'A') {{
                selections[dorama.code] = {{ choice: 'A', url: dorama.poster_a }};
            }} else if (choice === 'B') {{
                const targetUrl = dorama.poster_b || dorama.poster_a;
                selections[dorama.code] = {{ choice: 'B', url: targetUrl }};
            }}

            saveSelections();
            renderCurrent();
            updateStats();

            // Auto advance smoothly after small delay
            setTimeout(() => {{
                if (currentIndex < filteredIndices.length - 1) {{
                    nextDorama();
                }}
            }}, 220);
        }}

        function applyCustomUrl() {{
            const url = document.getElementById('custom-url-input').value.trim();
            if (!url) return;
            const actualIdx = filteredIndices[currentIndex];
            const dorama = DORAMAS[actualIdx];

            selections[dorama.code] = {{ choice: 'CUSTOM', url: url }};
            saveSelections();
            renderCurrent();
            updateStats();
            showToast("Maxsus poster saqlandi!");
        }}

        function nextDorama() {{
            if (currentIndex < filteredIndices.length - 1) {{
                currentIndex++;
                renderCurrent();
            }}
        }}

        function prevDorama() {{
            if (currentIndex > 0) {{
                currentIndex--;
                renderCurrent();
            }}
        }}

        function setFilter(filter) {{
            currentFilter = filter;
            document.querySelectorAll('.filter-btn').forEach(btn => btn.classList.remove('active'));
            event.target.classList.add('active');
            applyFilter();
            currentIndex = 0;
            renderCurrent();
        }}

        function onSearchInput() {{
            applyFilter();
            renderCurrent();
        }}

        function saveSelections() {{
            localStorage.setItem('uzkdrama_poster_selections', JSON.stringify(selections));
        }}

        function updateStats() {{
            const count = Object.keys(selections).length;
            document.getElementById('stat-selected').innerText = count;
        }}

        function openZoom(e, variant) {{
            e.stopPropagation();
            const actualIdx = filteredIndices[currentIndex];
            const dorama = DORAMAS[actualIdx];
            const src = (variant === 'A') ? dorama.poster_a : (dorama.poster_b || dorama.poster_a);
            document.getElementById('modal-img').src = src;
            document.getElementById('modal-lightbox').classList.add('active');
        }}

        function closeZoom() {{
            document.getElementById('modal-lightbox').classList.remove('active');
        }}

        function exportSelections() {{
            const payload = {{
                app: "uzkdrama_poster_curator",
                exported_at: new Date().toISOString(),
                total_curated: Object.keys(selections).length,
                selections: selections
            }};

            const jsonStr = JSON.stringify(payload, null, 2);
            navigator.clipboard.writeText(jsonStr).then(() => {{
                showToast("✨ Eksport kodi nusxalandi! Chatga yuboring.");
            }}).catch(() => {{
                prompt("Kodni nusxalang:", jsonStr);
            }});
        }}

        function showToast(text) {{
            const toast = document.getElementById('toast-alert');
            toast.innerText = text;
            toast.classList.add('show');
            setTimeout(() => toast.classList.remove('show'), 2500);
        }}

        window.onload = init;
    </script>
</body>
</html>
"""

with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
    f.write(html_content)

print(f"SUCCESS: {OUTPUT_HTML} fayli 100% muvaffaqiyatli yaratildi!")
