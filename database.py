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


async def search_doramas(query: str, limit: int = 10, offset: int = 0):
    """
    Qidiruv talablari:
    1. Faqat kino nomi (title) va kalit so'zlar/janr bo'yicha (description butunlay chiqarib tashlangan).
    2. Case-insensitive qidiruv.
    3. Fuzzy search threshold kamida 80% (0.80).
    4. Natijalar aniqlik darajasi bo'yicha saralangan (to'liq mos kelganlar -> qisman mos kelganlar -> fuzzy).
    5. Strip/trim qilingan va kamida 2 ta harf bo'lishi shart.
    """
    import difflib
    import re

    q = (query or "").strip()
    if len(q) < 2:
        return []

    q_lower = q.lower()

    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Description ustuni olinmaydi
        async with db.execute("""
            SELECT id, code, title, slug, genre, year, poster_url, total_episodes, views, status, country, actors
            FROM doramas
        """) as cursor:
            all_doramas = [dict(r) for r in await cursor.fetchall()]

    scored_doramas = []

    for d in all_doramas:
        title = d.get("title") or ""
        title_lower = title.lower()
        genre_lower = (d.get("genre") or "").lower()
        code_str = str(d.get("code") or "")

        score = 0.0

        # 1. To'liq kod mosligi
        if q_lower == code_str:
            score = 100.0
        # 2. To'liq nom mosligi
        elif q_lower == title_lower:
            score = 95.0
        # 3. Nom aynan shu so'z bilan boshlansa (Prefix)
        elif title_lower.startswith(q_lower):
            score = 90.0
        # 4. Nom ichida alohida so'z sifatida to'liq uchrasa (Word match)
        elif re.search(r'\b' + re.escape(q_lower) + r'\b', title_lower):
            score = 80.0
        # 5. Nom ichida qism sifatida uchrasa (Substring match, case-insensitive)
        elif q_lower in title_lower:
            score = 70.0
        # 6. Kalit so'z / janr bo'yicha mos kelsa
        elif q_lower in genre_lower:
            score = 50.0
        else:
            # 7. Fuzzy search (Threshold kamida 80% - 0.80)
            words = [w for w in re.split(r"[\s,.-]+", title_lower) if w]
            best_word_ratio = 0.0
            for w in words:
                r = difflib.SequenceMatcher(None, q_lower, w).ratio()
                if r > best_word_ratio:
                    best_word_ratio = r

            full_ratio = difflib.SequenceMatcher(None, q_lower, title_lower).ratio()
            best_ratio = max(best_word_ratio, full_ratio)

            if best_ratio >= 0.80:
                score = best_ratio * 45.0  # 36.0 - 45.0 ball

        if score > 0:
            scored_doramas.append((score, d.get("views", 0), d))

    # 4-talab: Aniqlik darajasi (Score DESC), keyin ko'rishlar soni (Views DESC) bo'yicha saralash
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
    - Admin va VIP uchun doim ochiq
    - Oddiy foydalanuvchilar uchun har bir qism alohida taklif talab qiladi:
      4-qism = 1 ta do'st
      5-qism = 2 ta do'st
      6-qism = 3 ta do'st ... (har bir keyingi qism uchun +1 ta referal)
    Qaytaradi: (unlocked, reason, current_refs, required_refs)
    """
    if episode_number <= 3:
        return True, "free", 0, 0
    if admin_id and tg_id == admin_id:
        return True, "admin", 0, 0

    user = await get_user(tg_id)
    if not user:
        return False, "locked", 0, max(1, episode_number - 3)

    # VIP tekshiruvi
    if user.get("is_vip"):
        vip_until = user.get("vip_until")
        if not vip_until:
            return True, "vip", user.get("referrals_count", 0), 0
        try:
            import datetime
            exp = datetime.datetime.fromisoformat(str(vip_until))
            if exp > datetime.datetime.utcnow():
                return True, "vip", user.get("referrals_count", 0), 0
        except Exception:
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
            vip_until = (datetime.datetime.utcnow() + datetime.timedelta(days=days)).strftime("%Y-%m-%d %H:%M:%S")

        await db.execute(
            "UPDATE users SET is_vip = 1, vip_until = ? WHERE tg_id = ?",
            (vip_until, tg_id)
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
