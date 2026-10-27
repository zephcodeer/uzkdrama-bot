import re
import aiosqlite
from config import DB_PATH


def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA foreign_keys = ON;")
        await db.execute("PRAGMA journal_mode = WAL;")
        await db.execute("PRAGMA synchronous = NORMAL;")
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
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # Migration: agar code ustuni yo'q bo'lsa qo'shish
        try:
            await db.execute("ALTER TABLE doramas ADD COLUMN code INTEGER;")
            await db.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_doramas_code ON doramas(code);")
        except Exception:
            pass

        # Barcha kodi bo'lmagan doramalarga avtomat 100+id kod berish
        try:
            await db.execute("UPDATE doramas SET code = 100 + id WHERE code IS NULL;")
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
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tg_id INTEGER UNIQUE NOT NULL,
                username TEXT DEFAULT '',
                first_name TEXT DEFAULT '',
                is_premium INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        # Xatcho'plar (Bookmarks)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS bookmarks (
                user_id INTEGER NOT NULL,
                dorama_id INTEGER NOT NULL REFERENCES doramas(id) ON DELETE CASCADE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id, dorama_id)
            );
        """)
        # Oxirgi ko'rilgan qism (History)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_history (
                user_id INTEGER NOT NULL,
                dorama_id INTEGER NOT NULL REFERENCES doramas(id) ON DELETE CASCADE,
                last_episode INTEGER NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id, dorama_id)
            );
        """)
        # Yangi qismlar uchun obunachilar (Subscribers)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS dorama_subscribers (
                user_id INTEGER NOT NULL,
                dorama_id INTEGER NOT NULL REFERENCES doramas(id) ON DELETE CASCADE,
                subscribed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(user_id, dorama_id)
            );
        """)

        # Referral va VIP ustunlari migratsiyasi
        for col_sql in [
            "ALTER TABLE users ADD COLUMN referrals_count INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN invited_by INTEGER DEFAULT NULL;",
            "ALTER TABLE users ADD COLUMN is_vip INTEGER DEFAULT 0;",
            "ALTER TABLE users ADD COLUMN vip_until TIMESTAMP DEFAULT NULL;",
        ]:
            try:
                await db.execute(col_sql)
            except Exception:
                pass

        # VIP Buyurtmalar jadvali (Click / Payme / Cheklar)
        await db.execute("""
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
        await db.commit()


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


def normalize_search_text(text: str) -> str:
    """Apostroflar va maxsus belgilarni tozalash (o'rgimchak -> orgimchak, yolg'on -> yolgon)."""
    t = re.sub(r"['`‘’ʻʼ]", "", (text or "").lower())
    t = re.sub(r"[\-_/()[\].,:;!?+]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def get_search_tokens(text: str) -> list[str]:
    norm = normalize_search_text(text)
    return [w for w in norm.split() if len(w) >= 2]


async def search_doramas(query: str, limit: int = 10, offset: int = 0):
    """
    Qidiruv talablari:
    1. Faqat kino nomi (title) va kalit so'zlar/janr bo'yicha (description butunlay chiqarib tashlangan).
    2. Case-insensitive qidiruv va apostroflarga chidamli (o'rgimchak -> orgimchak).
    3. Ko'p so'zli va yil bilan qidirishni to'liq qo'llab-quvvatlaydi (masalan: "orgimchak odam 2026").
    4. Fuzzy search threshold kamida 80% (0.80).
    5. Natijalar aniqlik darajasi bo'yicha saralangan (to'liq mos kelganlar -> qisman mos kelganlar -> fuzzy).
    6. Strip/trim qilingan va kamida 2 ta harf bo'lishi shart.
    """
    import difflib
    import re

    q = (query or "").strip()
    if len(q) < 2:
        return []

    q_lower = q.lower()
    q_norm = normalize_search_text(q)
    q_tokens = get_search_tokens(q)

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
        title_lower = title.lower()
        title_norm = normalize_search_text(title)
        title_tokens = get_search_tokens(title)

        genre_lower = (d.get("genre") or "").lower()
        genre_norm = normalize_search_text(d.get("genre") or "")
        code_str = str(d.get("code") or "")
        year_str = str(d.get("year") or "")

        score = 0.0

        # 1. To'liq kod mosligi
        if q_lower == code_str or q_norm == code_str:
            score = 100.0
        # 2. To'liq nom mosligi
        elif q_lower == title_lower or q_norm == title_norm:
            score = 95.0
        # 3. Nom aynan shu so'z bilan boshlansa (Prefix)
        elif title_lower.startswith(q_lower) or title_norm.startswith(q_norm):
            score = 90.0
        # 4. Nom ichida to'liq uchrasa (Substring)
        elif q_norm in title_norm or q_lower in title_lower:
            score = 85.0
        # 5. Tokenlar (So'zlar) bo'yicha ko'p so'zli qidiruv ("orgimchak odam 2026", "temir odam 2")
        elif q_tokens and title_tokens:
            matched_tokens = 0
            has_distinct = False
            for qt in q_tokens:
                if qt == year_str and len(year_str) >= 4:
                    matched_tokens += 1
                    continue
                if qt in title_tokens:
                    matched_tokens += 1
                    if len(qt) >= 4:
                        has_distinct = True
                    continue
                for tt in title_tokens:
                    if (len(qt) >= 4 and tt.startswith(qt)) or (len(tt) >= 4 and qt.startswith(tt)):
                        matched_tokens += 1
                        has_distinct = True
                        break
                    if len(qt) >= 4 and len(tt) >= 4:
                        if difflib.SequenceMatcher(None, qt, tt).ratio() >= 0.80:
                            matched_tokens += 1
                            has_distinct = True
                            break

            match_ratio = matched_tokens / len(q_tokens)
            if has_distinct and match_ratio >= 0.5:
                score = 65.0 + (match_ratio * 15.0)

        if score == 0.0:
            # 6. Kalit so'z / janr mosligi
            if q_lower in genre_lower or q_norm in genre_norm:
                score = 50.0
            else:
                # 7. Fuzzy search butun sarlavha bo'yicha (kamida 80% - 0.80)
                full_ratio = difflib.SequenceMatcher(None, q_norm, title_norm).ratio()
                if full_ratio >= 0.80:
                    score = full_ratio * 45.0

        if score > 0:
            scored_doramas.append((score, d.get("views", 0), d))

    scored_doramas.sort(key=lambda x: (x[0], x[1]), reverse=True)
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
    async with aiosqlite.connect(DB_PATH) as db:
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
    async with aiosqlite.connect(DB_PATH) as db:
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
    async with aiosqlite.connect(DB_PATH) as db:
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
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            """INSERT INTO vip_orders (user_id, plan, amount, receipt_file_id, status)
               VALUES (?, ?, ?, ?, 'pending')""",
            (user_id, plan, amount, receipt_file_id)
        ) as cursor:
            order_id = cursor.lastrowid
            await db.commit()
            return order_id


async def get_vip_order(order_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM vip_orders WHERE id = ?", (order_id,)) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def update_order_status(order_id: int, status: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE vip_orders SET status = ? WHERE id = ?", (status, order_id))
        await db.commit()


# --- Xatcho'plar (Bookmarks) ---
async def toggle_bookmark(user_id: int, dorama_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
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
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM bookmarks WHERE user_id = ? AND dorama_id = ?",
            (user_id, dorama_id)
        ) as cursor:
            return bool(await cursor.fetchone())


async def get_user_bookmarks(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT d.* FROM doramas d
               JOIN bookmarks b ON d.id = b.dorama_id
               WHERE b.user_id = ?
               ORDER BY b.created_at DESC""",
            (user_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


# --- Tarix (Oxirgi ko'rilgan qism) ---
async def save_last_watched(user_id: int, dorama_id: int, episode_num: int):
    async with aiosqlite.connect(DB_PATH) as db:
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
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT last_episode FROM user_history WHERE user_id = ? AND dorama_id = ?",
            (user_id, dorama_id)
        ) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else None


# --- Yangi qismlar uchun obunachilar (Notifications) ---
async def toggle_subscription(user_id: int, dorama_id: int) -> bool:
    async with aiosqlite.connect(DB_PATH) as db:
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
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT 1 FROM dorama_subscribers WHERE user_id = ? AND dorama_id = ?",
            (user_id, dorama_id)
        ) as cursor:
            return bool(await cursor.fetchone())


async def get_dorama_subscribers(dorama_id: int) -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT user_id FROM dorama_subscribers WHERE dorama_id = ?",
            (dorama_id,)
        ) as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]


async def get_all_user_ids() -> list[int]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT tg_id FROM users") as cursor:
            rows = await cursor.fetchall()
            return [r[0] for r in rows]


async def get_stats():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT COUNT(*) FROM users") as c1:
            total_users = (await c1.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1") as c2:
            premium_users = (await c2.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM doramas") as c3:
            total_doramas = (await c3.fetchone())[0]
        async with db.execute("SELECT COUNT(*) FROM episodes") as c4:
            total_episodes = (await c4.fetchone())[0]
        async with db.execute("SELECT SUM(views) FROM doramas") as c5:
            total_views = (await c5.fetchone())[0] or 0

        # Bugun qo'shilganlar
        async with db.execute("SELECT COUNT(*) FROM users WHERE DATE(joined_at) = DATE('now')") as c6:
            today_users = (await c6.fetchone())[0]

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
    "turk": ("Turk Serial va Kinolari", "WHERE category = 'turk' OR country = 'Turkiya'"),
    "marvel": ("Marvel & DC Kinolari", "WHERE category = 'marvel' OR genre LIKE '%Marvel%' OR title LIKE '%Marvel%'"),
    "foreign": ("Xorij va Gollivud Kinolari", "WHERE category = 'foreign' OR country LIKE '%AQSH%' OR country LIKE '%Gollivud%'"),
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
