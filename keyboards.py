from urllib.parse import quote
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Foydalanuvchi taqdim etgan va tasdiqlangan Premium Custom Emoji ID lari
ICON_POPCORN = "5371081166013078244"   # Yangi doramalar
ICON_FIRE = "5251329454801710673"      # Top doramalar
ICON_SEARCH = "5411377339458145570"    # Qidiruv (Duck)
ICON_STATS = "6154657967317717391"     # Statistika (Green Chart)
ICON_ACTION = "5368653135101310687"    # Kino / Dorama (Action)
ICON_SERIES = "5368653135101310687"    # Seriallar / Kategoriyalar
ICON_SPARKLE = "5451636889717062286"   # Ulashish (Sparkles)
ICON_CROWN = "5431505596316665041"     # Admin / Premium (Crown)
ICON_VIP = "5229011542011299168"       # VIP Yangi Ajoyib Crown
ICON_BELL = "5258342814273513092"      # Bildirishnoma (Golden Bell)
ICON_BOOKMARK = "5190683945351535076"  # Sevimlilar (Star Eyes)
ICON_NUMBER = "5262556520788273962"    # Kino kodi (Red Numbers)
ICON_BROADCAST = "5429295161333007624" # Ommaviy xabar (Duck Megaphone)
ICON_PLAY = "5348125953090403204"      # Davom etish / Play

# Yangi animatsiyali ikonka ID lari
ICON_LOCK = "5206432422194849059"
ICON_UNLOCK = "5465443379917629504"
ICON_FRIENDS = "5453957997418004470"
ICON_TARGET = "5350460637182993292"
ICON_PARTY = "5208541126583136130"
ICON_USER = "5408846628763217930"
ICON_DIAMOND = "5229173741451230931"
ICON_CARD = "5445353829304387411"
ICON_CAMERA = "5235837920081887219"
ICON_PACKAGE = "5854908544712707500"
ICON_CASH = "6033106828018062225"
ICON_CALENDAR = "5429242943120623604"
ICON_CHECK_GREEN = "5462919317832082236"
ICON_CROSS_RED = "6032903688949862892"
ICON_HOME = "5208782954716733247"
ICON_ARROW_LEFT = "5379889851879410922"
ICON_ARROW_RIGHT = "5213297128553590938"
ICON_BACK = "5352759161945867747"
ICON_CLIPBOARD = "6107099184563754673"
ICON_RED_CIRCLE = "5364250321176505463"
ICON_BELL_OFF = "5244807637157029775"
ICON_BULB = "5422439311196834318"
ICON_MAILBOX = "5350421256627838238"

# Foydalanuvchi taqdim etgan toifalar, janrlar va tizim animatsiyalari
ICON_GENRE_ACTION = "5415803084213329506"       # 💥 Jangari
ICON_GENRE_ROMANCE = "5465540480538254161"      # 💖 Romantika
ICON_GENRE_THRILLER = "5239965074415701227"     # 🧠 Triller
ICON_GENRE_FANTASY = "5350367161514732241"      # 🔮 Fentezi
ICON_GENRE_COMEDY = "5249007745805328497"       # 😂 Komediya
ICON_GENRE_HORROR = "5190680981824085932"       # 🧟 Zombi / Dahshat
ICON_GENRE_HISTORICAL = "5210952531676516344"   # 👑 Tarixiy toj
ICON_SCROLL = "5388922215347534633"             # 📜 Pergament
ICON_MARVEL = "5292113682560458323"             # 🦸‍♂️ Marvel & DC
ICON_KOREA = "5460922127974672624"              # 🇰🇷 Janubiy Koreya
ICON_CHINA = "5447548939844725331"              # 🇨🇳 Xitoy
ICON_TURK = "5229155784192965272"               # 🇹🇷 Turkiya
ICON_FOREIGN = "5886574861844746216"            # 🎬 Xorij & Gollivud
ICON_WARNING = "5462935376714802451"            # ⚠️ Ogohlantirish
ICON_LOADING = "5451732530048802485"            # ⏳ Kutilmoqda
ICON_RESTART = "5127377673596700174"            # 🔄 Qayta yuklash
ICON_ROCKET = "6041761071155386269"             # 🚀 Deploy
ICON_FOLDER = "5433653135799228968"             # 📁 Papka
ICON_INFO = "5334544901428229844"               # ℹ️ Ma'lumot
ICON_NUM_1 = "5456269518751948393"              # 1️⃣ Bosqich
ICON_NUM_2 = "5456250195694080809"              # 2️⃣ Bosqich
ICON_NUM_3 = "5456382802809347478"              # 3️⃣ Bosqich
ICON_GIFT = "6024007883966912557"               # 🎁 Sovg'a / Aksiya

def main_menu_kb(is_admin: bool = False, is_promo: bool = True) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Barcha Doramalar",
            callback_data="menu_latest:0",
            icon_custom_emoji_id=ICON_POPCORN
        ),
        InlineKeyboardButton(
            text="Kategoriyalar",
            callback_data="menu_categories",
            icon_custom_emoji_id=ICON_SERIES
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Top Ko'rilganlar",
            callback_data="menu_top",
            icon_custom_emoji_id=ICON_FIRE
        ),
        InlineKeyboardButton(
            text="Qidirish (yoki kod)",
            callback_data="menu_search",
            icon_custom_emoji_id=ICON_SEARCH
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Mening Sevimlilarim",
            callback_data="menu_bookmarks",
            icon_custom_emoji_id=ICON_BOOKMARK
        ),
        InlineKeyboardButton(
            text="Statistika",
            callback_data="menu_stats",
            icon_custom_emoji_id=ICON_STATS
        ),
    )
    builder.row(
        InlineKeyboardButton(
            text="Dorama Taklif Qilish",
            callback_data="menu_suggest",
            icon_custom_emoji_id=ICON_BULB
        )
    )

    if is_admin:
        builder.row(
            InlineKeyboardButton(
                text="Admin Panel",
                callback_data="menu_admin",
                icon_custom_emoji_id=ICON_CROWN
            )
        )

    vip_label = "Aksiya: Barcha Qismlar Bepul!" if is_promo else "VIP A'zolik (Qulflarsiz)"
    vip_icon = ICON_GIFT if is_promo else ICON_VIP
    builder.row(
        InlineKeyboardButton(
            text=vip_label,
            callback_data="menu_vip",
            icon_custom_emoji_id=vip_icon
        )
    )

    return builder.as_markup()

def promo_free_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Kinolarni Ko'rish",
            callback_data="menu_latest:0",
            icon_custom_emoji_id=ICON_POPCORN
        ),
        InlineKeyboardButton(
            text="Bosh Menyu",
            callback_data="menu_home",
            icon_custom_emoji_id=ICON_ARROW_LEFT
        )
    )
    return builder.as_markup()

def doramas_list_kb(doramas: list, prefix: str = "doramas", page: int = 0, has_next: bool = False) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in doramas:
        code_str = f"[{d.get('code', d.get('id', ''))}] " if d.get('code') else ""
        ep_count = d.get('total_episodes')
        ep_str = f" ({ep_count} qism)" if ep_count else ""
        raw_title = d.get('title', 'Noma\'lum')

        # Telegram mobil tugmalarida '...' deb uzilib qolmasligi uchun uzun nomlarni ixchamlashtirish
        btn_title = raw_title
        if len(f"{code_str}{btn_title}{ep_str}") > 35 and "(" in raw_title:
            cand = raw_title.split("(")[0].strip()
            if len(cand) >= 3:
                btn_title = cand

        builder.row(
            InlineKeyboardButton(
                text=f"{code_str}{btn_title}{ep_str}",
                callback_data=f"view_dorama:{d['id']}",
                icon_custom_emoji_id=ICON_ACTION
            )
        )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Orqaga",
                callback_data=f"{prefix}:{page - 1}",
                icon_custom_emoji_id=ICON_ARROW_LEFT
            )
        )
    if has_next:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Keyingisi",
                callback_data=f"{prefix}:{page + 1}",
                icon_custom_emoji_id=ICON_ARROW_RIGHT
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    if prefix.startswith("cat:"):
        builder.row(
            InlineKeyboardButton(
                text="Kategoriyalar",
                callback_data="menu_categories",
                icon_custom_emoji_id=ICON_SERIES
            ),
            InlineKeyboardButton(
                text="Bosh menyu",
                callback_data="menu_home",
                icon_custom_emoji_id=ICON_HOME
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="Bosh sahifa",
                callback_data="menu_home",
                icon_custom_emoji_id=ICON_HOME
            )
        )
    return builder.as_markup()

def build_display_episodes(episodes: list) -> list:
    """
    Bitta video faylga bir nechta qism birlashtirilgan bo'lsa (masalan: 1-2 qism, 5-6 qism),
    ularni avtomatik bitta tugmaga birlashtiradi.
    """
    from collections import defaultdict
    msg_to_eps = defaultdict(list)
    for ep in episodes:
        msg_to_eps[ep['channel_message_id']].append(ep['episode_number'])

    grouped = []
    seen = set()
    for ep in episodes:
        msg_id = ep['channel_message_id']
        if msg_id in seen:
            continue
        seen.add(msg_id)

        eps = msg_to_eps[msg_id]
        min_ep = min(eps)
        max_ep = max(eps)
        if len(eps) > 1 and max_ep > min_ep:
            label = f"{min_ep}-{max_ep}-qism"
        else:
            label = f"{min_ep}-qism"

        grouped.append({
            'start_ep': min_ep,
            'end_ep': max_ep,
            'label': label,
            'channel_message_id': msg_id,
            'episode_number': min_ep,
            'quality': ep.get('quality', '1080p')
        })
    return grouped

def dorama_detail_kb(
    dorama_id: int,
    episodes: list,
    bot_username: str = "",
    page: int = 0,
    per_page: int = 15,
    last_watched: int | None = None,
    bookmarked: bool = False,
    subscribed: bool = False
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    display_items = build_display_episodes(episodes)
    total_items = len(display_items)

    # 1. Davom etish tugmasi
    if last_watched:
        next_item = next((it for it in display_items if it['end_ep'] > last_watched), None)
        if next_item:
            builder.row(
                InlineKeyboardButton(
                    text=f"Davom etish: {next_item['label']}",
                    callback_data=f"get_ep:{dorama_id}:{next_item['start_ep']}",
                    icon_custom_emoji_id=ICON_PLAY
                )
            )

    start_idx = page * per_page
    end_idx = start_idx + per_page
    curr_items = display_items[start_idx:end_idx]

    # Qismlar tugmalari (har qatorda 5 tadan)
    row = []
    for item in curr_items:
        watched_mark = " ✓" if last_watched and item['end_ep'] <= last_watched else ""
        row.append(
            InlineKeyboardButton(
                text=f"{item['label']}{watched_mark}",
                callback_data=f"get_ep:{dorama_id}:{item['start_ep']}"
            )
        )
        if len(row) == 5:
            builder.row(*row)
            row = []
    if row:
        builder.row(*row)

    # Sahifalash
    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Oldingi",
                callback_data=f"ep_page:{dorama_id}:{page - 1}",
                icon_custom_emoji_id=ICON_ARROW_LEFT
            )
        )
    if end_idx < total_items:
        nav_buttons.append(
            InlineKeyboardButton(
                text="Keyingi",
                callback_data=f"ep_page:{dorama_id}:{page + 1}",
                icon_custom_emoji_id=ICON_ARROW_RIGHT
            )
        )

    if nav_buttons:
        builder.row(*nav_buttons)

    # Xatcho'p va Bildirishnoma
    bm_text = "Saqlangan" if bookmarked else "Saqlab qo'yish"
    sub_text = "O'chirish" if subscribed else "Yangi qismlarni kuzatish"

    builder.row(
        InlineKeyboardButton(
            text=bm_text,
            callback_data=f"toggle_bm:{dorama_id}",
            icon_custom_emoji_id=ICON_BOOKMARK
        ),
        InlineKeyboardButton(
            text=sub_text,
            callback_data=f"toggle_sub:{dorama_id}",
            icon_custom_emoji_id=ICON_BELL
        ),
    )

    # Ulashish tugmasi
    dorama_link = f"https://t.me/{bot_username}?start=d_{dorama_id}"
    share_msg = "Zo'r dorama topdim! Birga ko'ramiz:"
    share_url = f"https://t.me/share/url?url={quote(dorama_link, safe='')}&text={quote(share_msg)}"
    builder.row(
        InlineKeyboardButton(
            text="Do'stlarga ulashish",
            url=share_url,
            icon_custom_emoji_id=ICON_SPARKLE
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Bosh Menyu",
            callback_data="menu_home",
            icon_custom_emoji_id=ICON_HOME
        ),
        InlineKeyboardButton(
            text="Orqaga",
            callback_data="menu_latest:0",
            icon_custom_emoji_id=ICON_BACK
        )
    )
    return builder.as_markup()

def admin_panel_kb(promo_info: dict = None) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Ommaviy Xabar (Broadcast)",
            callback_data="admin_broadcast",
            icon_custom_emoji_id=ICON_BROADCAST
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Ongoing (Davom etayotganlar)",
            callback_data="admin_ongoing_list",
            icon_custom_emoji_id=ICON_ACTION
        ),
        InlineKeyboardButton(
            text="Dorama Takliflari",
            callback_data="admin_suggestions_list",
            icon_custom_emoji_id=ICON_CLIPBOARD
        )
    )

    promo_active = promo_info.get("is_active", True) if promo_info else True
    user_cnt = promo_info.get("user_count", 0) if promo_info else 0
    limit = promo_info.get("min_users", 100) if promo_info else 100
    st_text = f"Aksiya Rejimi: Bepul ({user_cnt}/{limit})" if promo_active else f"VIP Rejimi: Yopiq ({user_cnt}/{limit})"
    st_icon = ICON_GIFT if promo_active else ICON_LOCK
    builder.row(
        InlineKeyboardButton(
            text=st_text,
            callback_data="admin_toggle_promo",
            icon_custom_emoji_id=st_icon
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Aksiya Xabarini Tarqatish",
            callback_data="admin_broadcast_promo",
            icon_custom_emoji_id=ICON_BROADCAST
        )
    )

    builder.row(
        InlineKeyboardButton(
            text="GitHub'dan Yangilash (Git Pull)",
            callback_data="admin_git_update",
            icon_custom_emoji_id=ICON_SPARKLE
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="To'liq Statistika",
            callback_data="menu_stats",
            icon_custom_emoji_id=ICON_STATS
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Bosh menyu",
            callback_data="menu_home",
            icon_custom_emoji_id=ICON_HOME
        )
    )
    return builder.as_markup()

def back_to_menu_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Bosh menyu",
            callback_data="menu_home",
            icon_custom_emoji_id=ICON_HOME
        )
    )
    return builder.as_markup()

def episode_player_kb(
    dorama_id: int,
    current_ep: int,
    has_next: bool = False,
    bookmarked: bool = False,
    next_ep: int | None = None
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    next_target = next_ep if next_ep is not None else (current_ep + 1)
    nav_row = []
    if current_ep > 1:
        nav_row.append(
            InlineKeyboardButton(
                text="Oldingi qism",
                callback_data=f"get_ep:{dorama_id}:{current_ep - 1}",
                icon_custom_emoji_id=ICON_ARROW_LEFT
            )
        )
    if has_next:
        nav_row.append(
            InlineKeyboardButton(
                text="Keyingi qism",
                callback_data=f"get_ep:{dorama_id}:{next_target}",
                icon_custom_emoji_id=ICON_ARROW_RIGHT
            )
        )
    if nav_row:
        builder.row(*nav_row)

    bm_text = "Saqlangan" if bookmarked else "Saqlab qo'yish"
    builder.row(
        InlineKeyboardButton(
            text="Barcha qismlar",
            callback_data=f"view_dorama:{dorama_id}",
            icon_custom_emoji_id=ICON_SERIES
        ),
        InlineKeyboardButton(
            text=bm_text,
            callback_data=f"toggle_bm:{dorama_id}",
            icon_custom_emoji_id=ICON_BOOKMARK
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Bosh menyu",
            callback_data="menu_home",
            icon_custom_emoji_id=ICON_HOME
        )
    )
    return builder.as_markup()

def episode_lock_kb(dorama_id: int, user_id: int, bot_username: str, current_refs: int = 0, needed_refs: int = 1) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    ref_link = f"https://t.me/{bot_username}?start=ref_{user_id}"
    share_msg = "Men eng zo'r Koreys doramalarini shu botda tomosha qilyapman! Sen ham kir: "
    share_url = f"https://t.me/share/url?url={quote(ref_link, safe='')}&text={quote(share_msg)}"

    req_total = current_refs + needed_refs
    builder.row(
        InlineKeyboardButton(
            text=f"Do'stlarni taklif qilish ({current_refs}/{req_total})",
            url=share_url,
            icon_custom_emoji_id=ICON_FRIENDS
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="VIP A'zolik (9 000 so'm)",
            callback_data="menu_vip",
            icon_custom_emoji_id=ICON_CROWN
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Barcha qismlar ro'yxati",
            callback_data=f"view_dorama:{dorama_id}",
            icon_custom_emoji_id=ICON_CLIPBOARD
        ),
        InlineKeyboardButton(
            text="Bosh Menyu",
            callback_data="menu_home",
            icon_custom_emoji_id=ICON_HOME
        )
    )
    return builder.as_markup()

def vip_plans_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="1 oylik — 9 000 so'm",
            callback_data="buy_vip:1m",
            icon_custom_emoji_id=ICON_DIAMOND
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="6 oylik — 34 000 so'm",
            callback_data="buy_vip:6m",
            icon_custom_emoji_id=ICON_DIAMOND
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="1 yillik — 49 000 so'm",
            callback_data="buy_vip:1y",
            icon_custom_emoji_id=ICON_DIAMOND
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Cheksiz — 79 000 so'm",
            callback_data="buy_vip:life",
            icon_custom_emoji_id=ICON_VIP
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Orqaga",
            callback_data="menu_home",
            icon_custom_emoji_id=ICON_BACK
        )
    )
    return builder.as_markup()

def vip_payment_method_kb(plan: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="To'lov chekini yuborish",
            callback_data=f"submit_receipt:{plan}",
            icon_custom_emoji_id=ICON_CAMERA
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Boshqa tarif tanlash",
            callback_data="menu_vip",
            icon_custom_emoji_id=ICON_BACK
        )
    )
    return builder.as_markup()

def admin_order_kb(order_id: int, user_id: int, days: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Tasdiqlash (+VIP)",
            callback_data=f"admin_approve:{order_id}:{user_id}:{days}",
            icon_custom_emoji_id=ICON_CHECK_GREEN
        ),
        InlineKeyboardButton(
            text="Rad etish",
            callback_data=f"admin_reject:{order_id}:{user_id}",
            icon_custom_emoji_id=ICON_CROSS_RED
        )
    )
    return builder.as_markup()

def ongoing_doramas_kb(doramas: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for d in doramas:
        code = d.get('code', d.get('id', ''))
        title = d.get("title", "Noma'lum")
        uploaded = d.get('uploaded_episodes', d.get('total_episodes', 0))
        builder.row(
            InlineKeyboardButton(
                text=f"[{code}] {title} ({uploaded}-qism)",
                callback_data=f"view_dorama:{d['id']}",
                icon_custom_emoji_id=ICON_ACTION
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="Admin Panel",
            callback_data="menu_admin",
            icon_custom_emoji_id=ICON_CROWN
        ),
        InlineKeyboardButton(
            text="Bosh menyu",
            callback_data="menu_home",
            icon_custom_emoji_id=ICON_HOME
        )
    )
    return builder.as_markup()

def categories_hub_kb(counts: dict = None) -> InlineKeyboardMarkup:
    counts = counts or {}
    builder = InlineKeyboardBuilder()

    # Mintaqalar va Olamlar
    builder.row(
        InlineKeyboardButton(
            text=f"Janubiy Koreya ({counts.get('korea', 0)})",
            callback_data="cat:korea:0",
            icon_custom_emoji_id=ICON_KOREA
        ),
        InlineKeyboardButton(
            text=f"Xitoy ({counts.get('china', 0)})",
            callback_data="cat:china:0",
            icon_custom_emoji_id=ICON_CHINA
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"Turkiya ({counts.get('turk', 0)})",
            callback_data="cat:turk:0",
            icon_custom_emoji_id=ICON_TURK
        ),
        InlineKeyboardButton(
            text=f"Marvel & DC ({counts.get('marvel', 0)})",
            callback_data="cat:marvel:0",
            icon_custom_emoji_id=ICON_MARVEL
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"Xorij & Gollivud ({counts.get('foreign', 0)})",
            callback_data="cat:foreign:0",
            icon_custom_emoji_id=ICON_FOREIGN
        )
    )

    # Asosiy Janrlar
    builder.row(
        InlineKeyboardButton(
            text=f"Jangari ({counts.get('genre_action', 0)})",
            callback_data="cat:genre_action:0",
            icon_custom_emoji_id=ICON_GENRE_ACTION
        ),
        InlineKeyboardButton(
            text=f"Romantika ({counts.get('genre_romance', 0)})",
            callback_data="cat:genre_romance:0",
            icon_custom_emoji_id=ICON_GENRE_ROMANCE
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"Triller ({counts.get('genre_thriller', 0)})",
            callback_data="cat:genre_thriller:0",
            icon_custom_emoji_id=ICON_GENRE_THRILLER
        ),
        InlineKeyboardButton(
            text=f"Fentezi ({counts.get('genre_fantasy', 0)})",
            callback_data="cat:genre_fantasy:0",
            icon_custom_emoji_id=ICON_GENRE_FANTASY
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"Komediya ({counts.get('genre_comedy', 0)})",
            callback_data="cat:genre_comedy:0",
            icon_custom_emoji_id=ICON_GENRE_COMEDY
        ),
        InlineKeyboardButton(
            text=f"Zombi & Dahshat ({counts.get('genre_horror', 0)})",
            callback_data="cat:genre_horror:0",
            icon_custom_emoji_id=ICON_GENRE_HORROR
        )
    )
    builder.row(
        InlineKeyboardButton(
            text=f"Tarixiy ({counts.get('genre_historical', 0)})",
            callback_data="cat:genre_historical:0",
            icon_custom_emoji_id=ICON_GENRE_HISTORICAL
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Bosh Menyu",
            callback_data="menu_home",
            icon_custom_emoji_id=ICON_HOME
        )
    )
    return builder.as_markup()


def suggestion_admin_kb(suggestion_id: int, user_id: int) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Qabul qilish",
            callback_data=f"sug_accept:{suggestion_id}:{user_id}",
            icon_custom_emoji_id=ICON_CHECK_GREEN
        ),
        InlineKeyboardButton(
            text="Rad etish",
            callback_data=f"sug_reject:{suggestion_id}:{user_id}",
            icon_custom_emoji_id=ICON_CROSS_RED
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="Foydalanuvchiga Javob Yozish",
            callback_data=f"sug_reply:{suggestion_id}:{user_id}",
            icon_custom_emoji_id=ICON_BROADCAST
        )
    )
    return builder.as_markup()

def suggestions_list_kb(suggestions: list) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for s in suggestions:
        st = s.get('status', 'pending')
        if st == 'accepted':
            icon_id = ICON_CHECK_GREEN
        elif st == 'rejected':
            icon_id = ICON_CROSS_RED
        else:
            icon_id = ICON_BULB
        title = (s.get('suggestion') or '')[:30]
        builder.row(
            InlineKeyboardButton(
                text=f"[{s['id']}] {title}",
                callback_data=f"view_sug:{s['id']}",
                icon_custom_emoji_id=icon_id
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="Admin Panel",
            callback_data="menu_admin",
            icon_custom_emoji_id=ICON_ARROW_LEFT
        )
    )
    return builder.as_markup()


def stats_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Yangilash",
            callback_data="menu_stats",
            icon_custom_emoji_id=ICON_RESTART
        ),
        InlineKeyboardButton(
            text="Bosh Menyu",
            callback_data="menu_home",
            icon_custom_emoji_id=ICON_HOME
        )
    )
    return builder.as_markup()
