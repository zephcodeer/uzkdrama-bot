import difflib
import re

import aiosqlite

from config import DB_PATH, USER_DB_PATH





def slugify(text: str) -> str:

    text = text.lower().strip()

    text = re.sub(r"[^\w\s-]", "", text)

    text = re.sub(r"[\s_-]+", "-", text)

    return text.strip("-")





async def apply_sqlite_pragmas(db: aiosqlite.Connection):
    """RAM va diskni maksimal darajada tejash uchun SQLite sozlamalari."""
    await db.execute("PRAGMA cache_size = -2000;")
    await db.execute("PRAGMA temp_store = MEMORY;")
    await db.execute("PRAGMA mmap_size = 0;")
    await db.execute("PRAGMA wal_autocheckpoint = 100;")


async def optimize_db():
    """RAM va diskni bo'shatish uchun SQLite bazalarini optimizatsiya qiladi."""
    for path in [DB_PATH, USER_DB_PATH]:
        try:
            async with aiosqlite.connect(path) as db:
                await db.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                await db.execute("PRAGMA optimize;")
        except Exception:
            pass


async def init_db():
    """Baza tuzilmasini yaratish va yangilash (WAL rejimida)."""
    # 1. Kontent bazasi (doramas.db - Kinolar va Qismlar katalogi)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA synchronous = NORMAL;"); await apply_sqlite_pragmas(db)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS doramas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code INTEGER UNIQUE,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                genre TEXT DEFAULT 'Dorama',
                year INTEGER DEFAULT 2026,
                description TEXT DEFAULT '',
                poster_url TEXT DEFAULT '',
                total_episodes INTEGER DEFAULT 0,
                views INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                category TEXT DEFAULT 'korea',
                status TEXT DEFAULT 'Ongoing',
                country TEXT DEFAULT 'Janubiy Koreya',
                actors TEXT DEFAULT ''
            );
        """)
        try:
            await db.execute("ALTER TABLE doramas ADD COLUMN code INTEGER;")
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_doramas_code ON doramas(code);")
        except Exception:
            pass

        for col_sql in [
            "ALTER TABLE doramas ADD COLUMN category TEXT DEFAULT 'korea';",
            "ALTER TABLE doramas ADD COLUMN status TEXT DEFAULT 'Ongoing';",
            "ALTER TABLE doramas ADD COLUMN country TEXT DEFAULT 'Janubiy Koreya';",
            "ALTER TABLE doramas ADD COLUMN actors TEXT DEFAULT '';",
        ]:
            try:
                await db.execute(col_sql)
            except Exception:
                pass

        await db.execute("""
            CREATE TABLE IF NOT EXISTS episodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dorama_id INTEGER NOT NULL REFERENCES doramas(id) ON DELETE CASCADE,
                episode_number INTEGER NOT NULL,
                channel_message_id INTEGER NOT NULL,
                file_id TEXT DEFAULT '',
                file_size INTEGER DEFAULT 0,
                quality TEXT DEFAULT '1080p',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(dorama_id, episode_number)
            );
        """)
        await db.commit()

    # 2. Foydalanuvchilar va VIP bazasi (userdata.db - GIT PULL VA RESTARTLARDAN 100% HIMOYALANGAN)
    async with aiosqlite.connect(USER_DB_PATH) as udb:
        await udb.execute("PRAGMA foreign_keys = ON;")
        await udb.execute("PRAGMA journal_mode = WAL;")
        await udb.execute("PRAGMA synchronous = NORMAL;"); await apply_sqlite_pragmas(udb)
        await udb.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE NOT NULL,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                is_premium INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                referrals_count INTEGER DEFAULT 0,
                invited_by INTEGER DEFAULT NULL,
                is_vip INTEGER DEFAULT 0,
                vip_until TIMESTAMP DEFAULT NULL
            );
        """)
        await udb.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                user_id INTEGER NOT NULL,
                dorama_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id, dorama_id)
            );
        """)
        await udb.execute("""
            CREATE TABLE IF NOT EXISTS user_history (
                user_id INTEGER NOT NULL,
                dorama_id INTEGER NOT NULL,
                last_episode INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id, dorama_id)
            );
        """)
        await udb.execute("""
            CREATE TABLE IF NOT EXISTS dorama_subscribers (
                user_id INTEGER NOT NULL,
                dorama_id INTEGER NOT NULL,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id, dorama_id)
            );
        """)
        await udb.execute("""
            CREATE TABLE IF NOT EXISTS vip_orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                plan TEXT NOT NULL,
                amount INTEGER NOT NULL,
                receipt_file_id TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await udb.execute("""
            CREATE TABLE IF NOT EXISTS system_settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
        """)
        await udb.execute("""
            CREATE TABLE IF NOT EXISTS dorama_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                suggestion TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                admin_response TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await udb.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('promo_free_override', 'auto');")
        await udb.execute("INSERT OR IGNORE INTO system_settings (key, value) VALUES ('min_users_for_vip', '100');")
        for col_sql in [
            "ALTER TABLE users ADD COLUMN referrals_count INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN invited_by INTEGER DEFAULT NULL;",
            "ALTER TABLE users ADD COLUMN is_vip INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN vip_until TIMESTAMP DEFAULT NULL;",
        ]:
            try:
                await udb.execute(col_sql)
            except Exception:
                pass
        await udb.commit()

    # 3. Avtomatik Zaxira ko'chirish: doramas.db dagi foydalanuvchilarni userdata.db ga xavfsiz ko'chirish
    try:
        async with aiosqlite.connect(DB_PATH) as db, aiosqlite.connect(USER_DB_PATH) as udb:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'") as cur:
                if await cur.fetchone():
                    async with db.execute("SELECT tg_id, username, first_name, is_premium, joined_at, referrals_count, invited_by, is_vip, vip_until FROM users") as ucur:
                        rows = await ucur.fetchall()
                        for r in rows:
                            await udb.execute("""
                                INSERT INTO users (tg_id, username, first_name, is_premium, joined_at, referrals_count, invited_by, is_vip, vip_until)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                                ON CONFLICT(tg_id) DO UPDATE SET
                                    is_vip = MAX(users.is_vip, excluded.is_vip),
                                    vip_until = COALESCE(users.vip_until, excluded.vip_until),
                                    referrals_count = MAX(users.referrals_count, excluded.referrals_count)
                            """, tuple(r))
                    await udb.commit()
    except Exception:
        pass


# --- Tizim Sozlamalari va Bepul Aksiya Rejimi (System Settings & Promo Mode) ---

async def get_system_setting(key: str, default: str = "") -> str:
    """Tizim sozlamasini o'qish (userdata.db)."""
    async with aiosqlite.connect(USER_DB_PATH) as udb:
        async with udb.execute("SELECT value FROM system_settings WHERE key = ?", (key,)) as cur:
            row = await cur.fetchone()
            return row[0] if row else default


async def set_system_setting(key: str, value: str):
    """Tizim sozlamasini yozish (userdata.db)."""
    async with aiosqlite.connect(USER_DB_PATH) as udb:
        await udb.execute("""
            INSERT INTO system_settings (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, str(value)))
        await udb.commit()


async def is_promo_free_mode() -> bool:
    """
    Vaqtinchalik barcha qismlar bepul bo'lgan aksiya rejimi.
    Foydalanuvchilar soni 100 taga yetguncha (yoki admin majburiy yoqsa) faol bo'ladi.
    """
    override = await get_system_setting("promo_free_override", "auto")
    if override in ("1", "on"):
        return True
    if override in ("0", "off"):
        return False

    min_users_str = await get_system_setting("min_users_for_vip", "100")
    min_users = int(min_users_str) if min_users_str.isdigit() else 100

    async with aiosqlite.connect(USER_DB_PATH) as udb:
        async with udb.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            user_count = row[0] if row else 0

    return user_count < min_users


async def get_promo_status() -> dict:
    """Admin panel va xabarlar uchun promo rejim holati haqida to'liq ma'lumot."""
    override = await get_system_setting("promo_free_override", "auto")
    min_users_str = await get_system_setting("min_users_for_vip", "100")
    min_users = int(min_users_str) if min_users_str.isdigit() else 100

    async with aiosqlite.connect(USER_DB_PATH) as udb:
        async with udb.execute("SELECT COUNT(*) FROM users") as cur:
            row = await cur.fetchone()
            user_count = row[0] if row else 0

    is_active = (override in ("1", "on")) or (override == "auto" and user_count < min_users)
    return {
        "is_active": is_active,
        "override": override,
        "user_count": user_count,
        "min_users": min_users
    }


async def add_or_get_dorama(title: str, genre: str = "Dorama", year: int = 2026, description: str = "", poster_url: str = "") -> int:

    slug = slugify(title)

    async with aiosqlite.connect(DB_PATH) as db:

        async with db.execute("SELECT id FROM doramas WHERE slug = ?", (slug,)) as cursor:

            row = await cursor.fetchone()

            if row:

                return row[0]



        async with db.execute(

            """INSERT INTO doramas (title, slug, genre, year, description, poster_url)

               VALUES (?, ?, ?, ?, ?, ?)""",

            (title, slug, genre, year, description, poster_url)

        ) as cursor:

            dorama_id = cursor.lastrowid

            # Avtomat kod berish (masalan: 101, 102...)

            code = 100 + dorama_id

            await db.execute("UPDATE doramas SET code = ? WHERE id = ?", (code, dorama_id))

            await db.commit()

            return dorama_id





async def add_episode(dorama_id: int, episode_number: int, channel_message_id: int, file_id: str = "", file_size: int = 0, quality: str = "720p"):

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute(

            """INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)

               VALUES (?, ?, ?, ?, ?, ?)

               ON CONFLICT(dorama_id, episode_number) DO UPDATE SET

               channel_message_id = excluded.channel_message_id,

               file_id = excluded.file_id,

               file_size = excluded.file_size,

               quality = excluded.quality""",

            (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)

        )

        await db.execute(

            """UPDATE doramas SET total_episodes = (

                SELECT COUNT(*) FROM episodes WHERE dorama_id = ?

            ) WHERE id = ?""",

            (dorama_id, dorama_id)

        )

        await db.commit()





async def get_dorama_by_id(dorama_id: int):

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT * FROM doramas WHERE id = ?", (dorama_id,)) as cursor:

            row = await cursor.fetchone()

            return dict(row) if row else None





async def get_dorama_by_code(code: int):

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT * FROM doramas WHERE code = ?", (code,)) as cursor:

            row = await cursor.fetchone()

            return dict(row) if row else None





async def get_dorama_by_slug(slug: str):

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT * FROM doramas WHERE slug = ?", (slug,)) as cursor:

            row = await cursor.fetchone()

            return dict(row) if row else None





async def get_episodes(dorama_id: int):

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        async with db.execute(

            "SELECT * FROM episodes WHERE dorama_id = ? ORDER BY episode_number ASC",

            (dorama_id,)

        ) as cursor:

            rows = await cursor.fetchall()

            return [dict(r) for r in rows]





async def get_episode(dorama_id: int, ep_num: int):

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        async with db.execute(

            "SELECT * FROM episodes WHERE dorama_id = ? AND episode_number = ?",

            (dorama_id, ep_num)

        ) as cursor:

            row = await cursor.fetchone()

            return dict(row) if row else None





COMMON_STOPWORDS = {
    "mening", "sening", "uning", "bizning", "sizning", "ularning",
    "bir", "va", "bu", "o'sha", "shu", "u", "bilan", "uchun", "ham", "eng",
    "1", "2", "3", "fasl", "qism", "serial", "film", "kino",
    "the", "a", "an", "of", "and", "in", "to", "my", "your", "season", "part"
}

UZBEK_SUFFIXES = [
    "ligimning", "ligimizga", "ligimizda", "ligimizdan", "ligimizni", "ligimiz",
    "ligingizga", "ligingizda", "ligingizdan", "ligingizni", "ligingiz",
    "liklarining", "liklariga", "liklarida", "liklaridan", "liklarini", "liklar",
    "ligimga", "ligimda", "ligimdan", "ligimni", "ligim",
    "ligingga", "ligingda", "ligingdan", "ligingni", "liging",
    "ligiga", "ligida", "ligidan", "ligini", "ligining", "ligisi", "ligi", "lig",
    "likka", "likda", "likdan", "likni", "likning", "lik",
    "larning", "lariga", "larida", "lardan", "larini", "larim", "laring", "larimiz", "laringiz",
    "imizga", "imizda", "imizdan", "imizni", "ingizga", "ingizda", "ingizdan", "ingizni",
    "dagi", "dagilar", "dek", "day",
    "ning", "dan", "lar", "cha",
    "imga", "imda", "imdan", "imni", "im", "igim",
    "ingga", "ingda", "ingdan", "ingni", "ing",
    "iga", "ida", "idan", "ini", "isi", "imiz", "ingiz", "si", "ma",
    "ga", "ka", "qa", "da", "ni", "i"
]

def stem_uzbek_token(w: str) -> str:
    w = w.lower().strip()
    w = re.sub(r"[ʻʼ'\`’‘]", "", w)
    for sfx in sorted(UZBEK_SUFFIXES, key=len, reverse=True):
        if w.endswith(sfx) and len(w) - len(sfx) >= 3:
            w = w[:-len(sfx)]
            break
    if len(w) >= 4 and w[-1] == w[-2]:
        w = w[:-1]
    return w

def normalize_search_text(text: str) -> str:
    """Apostroflar va maxsus belgilarni tozalash (o'rgimchak -> orgimchak, yolg'on -> yolgon)."""
    t = re.sub(r"['`‘’ʻʼ]", "", (text or "").lower())
    t = re.sub(r"[\-_/()[\].,:;!?+]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def get_search_tokens(text: str) -> list[str]:
    norm = normalize_search_text(text)
    return [w for w in norm.split() if len(w) >= 2]

def match_token(qt: str, tt: str) -> float:
    if qt == tt:
        return 1.0
    qs = stem_uzbek_token(qt)
    ts = stem_uzbek_token(tt)
    if len(qs) >= 3 and len(ts) >= 3 and qs == ts:
        return 0.95
    if len(qs) >= 4 and len(ts) >= 4 and (ts.startswith(qs) or qs.startswith(ts)):
        return 0.90
    if len(qt) >= 4 and len(tt) >= 4:
        if qt[:4] == tt[:4]:
            r = difflib.SequenceMatcher(None, qt, tt).ratio()
            if r >= 0.65:
                return 0.85
        r = difflib.SequenceMatcher(None, qt, tt).ratio()
        if r >= 0.80:
            return r * 0.85
    return 0.0

async def search_doramas(query: str, limit: int = 10, offset: int = 0):
    """
    Intellektual Semantik va Morfologik Qidiruv:
    1. O'zbek tili morfemik ildizini aniqlash (-lik, -ligim, -lar, -dagi).
    2. Stop-so'zlarni ('mening', 'sening', 'bir', 'va') ajratib, faqat ular bo'yicha ifloslanishni to'sish.
    3. Ko'p so'zli so'rovlarda barcha so'zlarga mos kelgan kino darhol #1 o'ringa chiqadi.
    4. Yil, kod, inglizcha va o'zbekcha nomlar bo'yicha mukammal reytinglash.
    """
    import difflib

    q = (query or "").strip()
    if len(q) < 2:
        return []

    q_norm = normalize_search_text(q)
    raw_tokens = q_norm.split()
    informative_tokens = [w for w in raw_tokens if w not in COMMON_STOPWORDS]

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT id, code, title, slug, genre, year, poster_url, total_episodes, views, status, country, actors
            FROM doramas
        """) as cursor:
            all_doramas = [dict(r) for r in await cursor.fetchall()]

    scored_doramas = []

    for d in all_doramas:
        title = d.get("title") or ""
        t_clean = normalize_search_text(title)
        t_tokens = t_clean.split()

        genre_clean = normalize_search_text(d.get("genre") or "")
        code_str = str(d.get("code") or "")
        year_str = str(d.get("year") or "")

        score = 0.0

        # 1. To'liq kino kodi mosligi
        if q_norm == code_str:
            score = 100.0
        # 2. To'liq nom mosligi
        elif q_norm == t_clean:
            score = 98.0
        # 3. Nom aynan so'rov bilan boshlansa (Prefix)
        elif t_clean.startswith(q_norm):
            score = 96.0
        # 4. Aniq ibora substring sifatida uchrasa
        elif q_norm in t_clean and len(q_norm) >= 4:
            score = 90.0
        else:
            # 5. Tokenlar bo'yicha intellektual vaznli qidiruv
            if raw_tokens and t_tokens:
                total_token_score = 0.0
                matched_informative = 0
                matched_count = 0

                for qt in raw_tokens:
                    is_stop = qt in COMMON_STOPWORDS
                    best_match = 0.0
                    for tt in t_tokens:
                        m = match_token(qt, tt)
                        if m > best_match:
                            best_match = m
                    if best_match > 0:
                        matched_count += 1
                        weight = 0.3 if is_stop else 1.0
                        total_token_score += best_match * weight
                        if not is_stop and best_match >= 0.65:
                            matched_informative += 1

                # Kamida talab qilinadigan muhim so'zlar soni:
                # 1 ta bo'lsa -> 1 ta
                # 2 ta bo'lsa -> 2 ta (ikkala so'z ham qatnashishi SHART, masalan "oy oshiqlar"da faqat "oy" mos kelgan boshqa doramalar qat'iyan to'siladi)
                # 3 ta bo'lsa -> kamida 2 ta
                # 4+ ta bo'lsa -> kamida 67%
                if len(informative_tokens) <= 2:
                    min_req_informative = len(informative_tokens)
                else:
                    min_req_informative = max(2, int(len(informative_tokens) * 0.67 + 0.5))

                if informative_tokens and matched_informative < min_req_informative:
                    score = 0.0
                elif not informative_tokens and matched_count == 0:
                    score = 0.0
                else:
                    max_possible_weight = sum(0.3 if w in COMMON_STOPWORDS else 1.0 for w in raw_tokens)
                    ratio = total_token_score / max_possible_weight if max_possible_weight > 0 else 0
                    if matched_count == len(raw_tokens):
                        score = 80.0 + (ratio * 12.0)
                    elif ratio >= 0.5:
                        score = 45.0 + (ratio * 25.0)

        # 6. Agar sarlavhadan topilmasa, janr bo'yicha ehtiyotkor fallback
        if score == 0.0 and genre_clean:
            if q_norm in genre_clean:
                score = 35.0

        if score > 0:
            scored_doramas.append((score, d.get("views", 0), d))

    # Ball va ko'rishlar soni bo'yicha saralash
    scored_doramas.sort(key=lambda x: (x[0], x[1]), reverse=True)

    # Yuqori aniqlikdagi natija (score >= 80) mavjud bo'lsa, chala/zaif past balli natijalarni (noise) tozalash
    if scored_doramas and scored_doramas[0][0] >= 80.0:
        best_score = scored_doramas[0][0]
        scored_doramas = [item for item in scored_doramas if item[0] >= max(50.0, best_score * 0.75)]

    sorted_results = [item[2] for item in scored_doramas]
    return sorted_results[offset:offset + limit]

async def get_latest_doramas(limit: int = 10, offset: int = 0):

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        async with db.execute(

            """SELECT * FROM doramas 

               WHERE total_episodes > 0

               ORDER BY id DESC LIMIT ? OFFSET ?""",

            (limit, offset)

        ) as cursor:

            rows = await cursor.fetchall()

            return [dict(r) for r in rows]







async def get_ongoing_doramas():

    """Hozirda davom etayotgan (Ongoing) barcha seriallar va ularning yuklangan qismlari soni."""

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        async with db.execute("""

            SELECT d.id, d.code, d.title, d.total_episodes, d.status, d.poster_url,

                   COUNT(e.id) as uploaded_episodes

            FROM doramas d

            LEFT JOIN episodes e ON d.id = e.dorama_id

            WHERE d.status = 'Ongoing' OR LOWER(d.status) LIKE '%ongo%'

            GROUP BY d.id

            ORDER BY d.code ASC

        """) as cursor:

            rows = await cursor.fetchall()

            return [dict(r) for r in rows]



async def get_top_doramas(limit: int = 10, offset: int = 0):

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        async with db.execute(

            """SELECT * FROM doramas 

               ORDER BY views DESC, id DESC LIMIT ? OFFSET ?""",

            (limit, offset)

        ) as cursor:

            rows = await cursor.fetchall()

            return [dict(r) for r in rows]





async def increment_views(dorama_id: int):

    async with aiosqlite.connect(DB_PATH) as db:

        await db.execute("UPDATE doramas SET views = views + 1 WHERE id = ?", (dorama_id,))

        await db.commit()





async def register_user(tg_id: int, username: str, first_name: str, is_premium: bool, referrer_id: int = None) -> tuple[bool, int | None]:

    """

    Foydalanuvchini ro'yxatga oladi. Agar yangi bo'lsa va referral link bilan kirsa,

    taklif qilgan do'stiga referrals_count oshiradi.

    Qaytaradi: (is_new, rewarded_referrer_id)

    """

    async with aiosqlite.connect(USER_DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT id, tg_id FROM users WHERE tg_id = ?", (tg_id,)) as cursor:

            existing = await cursor.fetchone()



        if existing:

            await db.execute(

                """UPDATE users SET username = ?, first_name = ?, is_premium = ?

                   WHERE tg_id = ?""",

                (username or "", first_name or "", 1 if is_premium else 0, tg_id)

            )

            await db.commit()

            return False, None



        # Yangi foydalanuvchi

        rewarded_ref = None

        if referrer_id and referrer_id != tg_id:

            async with db.execute("SELECT id FROM users WHERE tg_id = ?", (referrer_id,)) as cursor:

                ref_user = await cursor.fetchone()

            if ref_user:

                rewarded_ref = referrer_id

                await db.execute("UPDATE users SET referrals_count = referrals_count + 1 WHERE tg_id = ?", (referrer_id,))



        await db.execute(

            """INSERT INTO users (tg_id, username, first_name, is_premium, invited_by)

               VALUES (?, ?, ?, ?, ?)""",

            (tg_id, username or "", first_name or "", 1 if is_premium else 0, rewarded_ref)

        )

        await db.commit()

        return True, rewarded_ref





async def get_user(tg_id: int):

    async with aiosqlite.connect(USER_DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT * FROM users WHERE tg_id = ?", (tg_id,)) as cursor:

            row = await cursor.fetchone()

            return dict(row) if row else None





async def is_user_unlocked(tg_id: int, episode_number: int, admin_id: int = 0) -> tuple[bool, str, int, int]:

    """

    1, 2, 3-qismlar barcha uchun ochiq.

    4-qism va undan keyingilar:

    - Admin va VIP uchun doim ochiq (hech qachon qulflanmaydi)

    - Oddiy foydalanuvchilar uchun taklif talab qilinadi

    Qaytaradi: (unlocked, reason, current_refs, required_refs)

    """

    if episode_number <= 3:

        return True, "free", 0, 0

    if (admin_id and tg_id == admin_id) or tg_id == 7141955036:

        return True, "admin", 0, 0

    # Vaqtinchalik barcha qismlar 100% bepul aksiya rejimi (kamida 100+ odam bo'lguncha)
    if await is_promo_free_mode():
        return True, "promo_free", 0, 0



    user = await get_user(tg_id)

    if not user:

        return False, "locked", 0, max(1, episode_number - 3)



    # VIP tekshiruvi: Agar is_vip = 1 yoki True bo'lsa

    if user.get("is_vip") in (1, "1", True):

        vip_until = user.get("vip_until")

        if not vip_until:

            return True, "vip", user.get("referrals_count", 0), 0

        try:

            import datetime

            v_str = str(vip_until).strip()

            if "T" in v_str:

                exp = datetime.datetime.fromisoformat(v_str)

            else:

                exp = datetime.datetime.strptime(v_str.split(".")[0], "%Y-%m-%d %H:%M:%S")

            now = datetime.datetime.now()

            if exp > now:

                return True, "vip", user.get("referrals_count", 0), 0

        except Exception:

            # Har qanday parsing xatosida ham is_vip aktiv bo'lsa ochib berish

            return True, "vip", user.get("referrals_count", 0), 0



    current_refs = user.get("referrals_count") or 0

    required_refs = episode_number - 3



    if current_refs >= required_refs:

        return True, "referral", current_refs, required_refs



    return False, "locked", current_refs, required_refs





async def grant_vip(tg_id: int, days: int = 30):

    import datetime

    async with aiosqlite.connect(USER_DB_PATH) as db:

        if days >= 3650:

            vip_until = None

        else:

            vip_until = (datetime.datetime.now() + datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")



        # Foydalanuvchi bo'lmasa ham bazaga kiritib, VIP ni kafolatli faollashtirish (UPSERT)

        await db.execute(

            """INSERT INTO users (tg_id, is_vip, vip_until, referrals_count)

               VALUES (?, 1, ?, 0)

               ON CONFLICT(tg_id) DO UPDATE SET is_vip = 1, vip_until = excluded.vip_until""",

            (tg_id, vip_until)

        )

        await db.commit()





async def create_vip_order(user_id: int, plan: str, amount: int, receipt_file_id: str = "") -> int:

    async with aiosqlite.connect(USER_DB_PATH) as db:

        async with db.execute(

            """INSERT INTO vip_orders (user_id, plan, amount, receipt_file_id, status)

               VALUES (?, ?, ?, ?, 'pending')""",

            (user_id, plan, amount, receipt_file_id)

        ) as cursor:

            order_id = cursor.lastrowid

            await db.commit()

            return order_id





async def get_vip_order(order_id: int):

    async with aiosqlite.connect(USER_DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        async with db.execute("SELECT * FROM vip_orders WHERE id = ?", (order_id,)) as cursor:

            row = await cursor.fetchone()

            return dict(row) if row else None





async def update_order_status(order_id: int, status: str):

    async with aiosqlite.connect(USER_DB_PATH) as db:

        await db.execute("UPDATE vip_orders SET status = ? WHERE id = ?", (status, order_id))

        await db.commit()





# --- Xatcho'plar (Bookmarks) ---

async def toggle_bookmark(user_id: int, dorama_id: int) -> bool:

    async with aiosqlite.connect(USER_DB_PATH) as db:

        async with db.execute(

            "SELECT 1 FROM bookmarks WHERE user_id = ? AND dorama_id = ?",

            (user_id, dorama_id)

        ) as cursor:

            exists = await cursor.fetchone()



        if exists:

            await db.execute(

                "DELETE FROM bookmarks WHERE user_id = ? AND dorama_id = ?",

                (user_id, dorama_id)

            )

            await db.commit()

            return False  # O'chirildi

        else:

            await db.execute(

                "INSERT INTO bookmarks (user_id, dorama_id) VALUES (?, ?)",

                (user_id, dorama_id)

            )

            await db.commit()

            return True  # Qo'shildi





async def is_bookmarked(user_id: int, dorama_id: int) -> bool:

    async with aiosqlite.connect(USER_DB_PATH) as db:

        async with db.execute(

            "SELECT 1 FROM bookmarks WHERE user_id = ? AND dorama_id = ?",

            (user_id, dorama_id)

        ) as cursor:

            return bool(await cursor.fetchone())





async def get_user_bookmarks(user_id: int):
    """Foydalanuvchining barcha xatcho'plari (saqlangan doramalari)."""
    async with aiosqlite.connect(USER_DB_PATH) as udb:
        udb.row_factory = aiosqlite.Row
        async with udb.execute(
            "SELECT dorama_id FROM bookmarks WHERE user_id = ? ORDER BY created_at DESC",
            (user_id,)
        ) as cursor:
            d_ids = [r["dorama_id"] for r in await cursor.fetchall()]

    if not d_ids:
        return []

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        placeholders = ",".join("?" for _ in d_ids)
        async with db.execute(f"SELECT * FROM doramas WHERE id IN ({placeholders})", d_ids) as cursor:
            doramas_dict = {r["id"]: dict(r) for r in await cursor.fetchall()}
            return [doramas_dict[did] for did in d_ids if did in doramas_dict]


async def save_last_watched(user_id: int, dorama_id: int, episode_num: int):

    async with aiosqlite.connect(USER_DB_PATH) as db:

        await db.execute(

            """INSERT INTO user_history (user_id, dorama_id, last_episode, updated_at)

               VALUES (?, ?, ?, CURRENT_TIMESTAMP)

               ON CONFLICT(user_id, dorama_id) DO UPDATE SET

               last_episode = excluded.last_episode,

               updated_at = CURRENT_TIMESTAMP""",

            (user_id, dorama_id, episode_num)

        )

        await db.commit()





async def get_last_watched(user_id: int, dorama_id: int) -> int | None:

    async with aiosqlite.connect(USER_DB_PATH) as db:

        async with db.execute(

            "SELECT last_episode FROM user_history WHERE user_id = ? AND dorama_id = ?",

            (user_id, dorama_id)

        ) as cursor:

            row = await cursor.fetchone()

            return row[0] if row else None





# --- Yangi qismlar uchun obunachilar (Notifications) ---

async def toggle_subscription(user_id: int, dorama_id: int) -> bool:

    async with aiosqlite.connect(USER_DB_PATH) as db:

        async with db.execute(

            "SELECT 1 FROM dorama_subscribers WHERE user_id = ? AND dorama_id = ?",

            (user_id, dorama_id)

        ) as cursor:

            exists = await cursor.fetchone()



        if exists:

            await db.execute(

                "DELETE FROM dorama_subscribers WHERE user_id = ? AND dorama_id = ?",

                (user_id, dorama_id)

            )

            await db.commit()

            return False  # O'chirildi

        else:

            await db.execute(

                "INSERT INTO dorama_subscribers (user_id, dorama_id) VALUES (?, ?)",

                (user_id, dorama_id)

            )

            await db.commit()

            return True  # Obuna bo'ldi





async def is_subscribed(user_id: int, dorama_id: int) -> bool:

    async with aiosqlite.connect(USER_DB_PATH) as db:

        async with db.execute(

            "SELECT 1 FROM dorama_subscribers WHERE user_id = ? AND dorama_id = ?",

            (user_id, dorama_id)

        ) as cursor:

            return bool(await cursor.fetchone())





async def get_dorama_subscribers(dorama_id: int) -> list[int]:

    async with aiosqlite.connect(USER_DB_PATH) as db:

        async with db.execute(

            "SELECT user_id FROM dorama_subscribers WHERE dorama_id = ?",

            (dorama_id,)

        ) as cursor:

            rows = await cursor.fetchall()

            return [r[0] for r in rows]





async def get_all_user_ids() -> list[int]:

    async with aiosqlite.connect(USER_DB_PATH) as db:

        async with db.execute("SELECT tg_id FROM users") as cursor:

            rows = await cursor.fetchall()

            return [r[0] for r in rows]





async def get_stats():
    """Bot umumiy statistikasi."""
    async with aiosqlite.connect(USER_DB_PATH) as udb:
        async with udb.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with udb.execute("SELECT COUNT(*) FROM users WHERE is_vip = 1") as c2:
            premium_users = (await c2.fetchone())[0]
        async with udb.execute("SELECT COUNT(*) FROM users WHERE DATE(joined_at) = DATE('now')") as c6:
            today_users = (await c6.fetchone())[0]

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM doramas") as c3:
            total_doramas = (await c3.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM episodes") as c4:
            total_episodes = (await c4.fetchone())[0]
        async with db.execute("SELECT SUM(views) FROM doramas") as c5:
            total_views = (await c5.fetchone())[0] or 0

    return {
        "total_users": total_users,
        "today_users": today_users,
        "premium_users": premium_users,
        "total_doramas": total_doramas,
        "total_episodes": total_episodes,
        "total_views": total_views,
    }


CATEGORY_QUERIES = {

    "korea": ("Janubiy Koreya Doramalari", "WHERE category = 'korea' OR country = 'Janubiy Koreya'"),
    "china": ("Xitoy Serial va Doramalari", "WHERE category = 'china' OR country = 'Xitoy'"),

    "turk": ("Turk Serial va Kinolari", "WHERE category = 'turk' OR country = 'Turkiya'"),

    "marvel": ("Marvel & DC Kinolari", "WHERE category = 'marvel' OR genre LIKE '%Marvel%' OR title LIKE '%Marvel%'"),

    "foreign": ("Xorij va Gollivud Kinolari", "WHERE category = 'foreign' OR country LIKE '%AQSH%' OR country LIKE '%Gollivud%' OR country LIKE '%Yaponiya%' OR country LIKE '%Filippin%'"),

    "genre_action": ("Jangari & Ekshn", "WHERE genre LIKE '%Jangari%' OR genre LIKE '%Ekshn%'"),

    "genre_romance": ("Romantika & Melodrama", "WHERE genre LIKE '%Romantika%' OR genre LIKE '%Melodrama%'"),

    "genre_thriller": ("Triller & Kriminal", "WHERE genre LIKE '%Triller%' OR genre LIKE '%Detektiv%' OR genre LIKE '%Kriminal%'"),

    "genre_fantasy": ("Fentezi & Fantastika", "WHERE genre LIKE '%Fentezi%' OR genre LIKE '%Fantastika%'"),

    "genre_comedy": ("Komediya", "WHERE genre LIKE '%Komediya%'"),

    "genre_horror": ("Zombi & Dahshat", "WHERE genre LIKE '%Dahshat%' OR genre LIKE '%Zombi%'"),

    "genre_historical": ("Tarixiy Filmlar", "WHERE genre LIKE '%Tarixiy%'")

}



async def get_category_counts() -> dict:

    """Barcha kategoriya va janrlardagi kinolar sonini qaytaradi."""

    counts = {}

    async with aiosqlite.connect(DB_PATH) as db:

        for cat_key, (name, where_clause) in CATEGORY_QUERIES.items():

            async with db.execute(f"SELECT COUNT(*) FROM doramas {where_clause}") as cursor:

                row = await cursor.fetchone()

                counts[cat_key] = row[0] if row else 0

    return counts



async def get_doramas_by_category(cat_key: str, limit: int = 8, offset: int = 0) -> tuple[str, list]:

    """Kategoriya yoki janr bo'yicha saralab olish."""

    meta = CATEGORY_QUERIES.get(cat_key, ("Kategoriya", ""))

    title, where_clause = meta

    async with aiosqlite.connect(DB_PATH) as db:

        db.row_factory = aiosqlite.Row

        sql = f"""SELECT * FROM doramas 

                  {where_clause}

                  ORDER BY views DESC, id DESC

                  LIMIT ? OFFSET ?"""

        async with db.execute(sql, (limit, offset)) as cursor:

            rows = await cursor.fetchall()

            return title, [dict(r) for r in rows]



async def add_dorama_suggestion(user_id: int, username: str, first_name: str, suggestion: str) -> int:
    """Foydalanuvchi taklifini bazaga saqlaydi va uning ID sini qaytaradi."""
    async with aiosqlite.connect(USER_DB_PATH) as udb:
        await apply_sqlite_pragmas(udb)
        cursor = await udb.execute(
            """
            INSERT INTO dorama_suggestions (user_id, username, first_name, suggestion)
            VALUES (?, ?, ?, ?)
            """,
            (user_id, username or '', first_name or '', suggestion)
        )
        await udb.commit()
        return cursor.lastrowid

async def get_dorama_suggestions(status: str = None, limit: int = 20) -> list[dict]:
    """Admin uchun takliflar ro'yxatini qaytaradi."""
    async with aiosqlite.connect(USER_DB_PATH) as udb:
        await apply_sqlite_pragmas(udb)
        udb.row_factory = aiosqlite.Row
        if status:
            cursor = await udb.execute(
                "SELECT * FROM dorama_suggestions WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                (status, limit)
            )
        else:
            cursor = await udb.execute(
                "SELECT * FROM dorama_suggestions ORDER BY created_at DESC LIMIT ?",
                (limit,)
            )
        rows = await cursor.fetchall()
        return [dict(r) for r in rows]

async def update_suggestion_status(suggestion_id: int, status: str, admin_response: str = "") -> bool:
    """Taklif holatini yangilaydi (accepted / rejected / completed)."""
    async with aiosqlite.connect(USER_DB_PATH) as udb:
        await apply_sqlite_pragmas(udb)
        await udb.execute(
            "UPDATE dorama_suggestions SET status = ?, admin_response = ? WHERE id = ?",
            (status, admin_response, suggestion_id)
        )
        await udb.commit()
        return True

async def get_dorama_suggestion(suggestion_id: int) -> dict | None:
    """Bitta taklif ma'lumotlarini qaytaradi."""
    async with aiosqlite.connect(USER_DB_PATH) as udb:
        await apply_sqlite_pragmas(udb)
        udb.row_factory = aiosqlite.Row
        cursor = await udb.execute("SELECT * FROM dorama_suggestions WHERE id = ?", (suggestion_id,))
        row = await cursor.fetchone()
        return dict(row) if row else None
