import pytest
import aiosqlite
import os
import database as db
import keyboards as kb
from scripts.autopilot_donor_listener import (
    parse_episodes,
    clean_dorama_title,
    find_or_create_dorama,
    RE_MICRO_DRAMA
)

def test_duanju_category_query_definition():
    assert "duanju" in db.CATEGORY_QUERIES
    name, where_clause = db.CATEGORY_QUERIES["duanju"]
    assert "Vertikal" in name
    assert "DramaBox" in name or "Duanju" in name
    assert "category = 'duanju'" in where_clause
    assert "DramaBox" in where_clause
    assert "ReelShort" in where_clause

def test_duanju_keyboards_rendering():
    markup = kb.categories_hub_kb(counts={"duanju": 15, "mini": 8, "movies": 5})
    buttons = [btn for row in markup.inline_keyboard for btn in row]
    duanju_btns = [btn for btn in buttons if btn.callback_data == "cat:duanju:0"]
    assert len(duanju_btns) == 1
    btn = duanju_btns[0]
    assert btn.text == "Vertikal Micro-Dramalar (Duanju / DramaBox) (15)"
    assert btn.icon_custom_emoji_id == kb.ICON_PHONE

def test_autopilot_range_and_caption_parsing():
    # 1. Bare range (e.g. '1-11', '1-15')
    eps1 = parse_episodes("Milliarder kelin 1-15")
    assert eps1 == list(range(1, 16))

    eps2 = parse_episodes("Baxt sari 1-11")
    assert eps2 == list(range(1, 12))

    # 2. Parenthesized range
    eps3 = parse_episodes("Drama Box | Qasoskor (1-20)")
    assert eps3 == list(range(1, 21))

    # 3. Explicit keywords
    eps4 = parse_episodes("Shahzodaning sevgisi 12-25 qismlar")
    assert eps4 == list(range(12, 26))

    # 4. Age limit should NOT be parsed as episode range
    eps5 = parse_episodes("16-18 yoshdagilar uchun! Birinchi sevgi 5-qism")
    assert eps5 == [5]

def test_autopilot_clean_dorama_title_for_duanju():
    t1 = clean_dorama_title("Drama Box: Milliarder merosxo'r 1-15")
    assert t1 == "Milliarder merosxo'r"

    t2 = clean_dorama_title("🎬 ReelShort - Boy qizning qasosi 1-11 qismlar O'zbek tilida")
    assert t2 == "Boy qizning qasosi"

    t3 = clean_dorama_title("Kichik xonim (1-20)")
    assert t3 == "Kichik xonim"

@pytest.mark.asyncio
async def test_find_or_create_duanju_in_db(tmp_path):
    test_db = tmp_path / "test_dorama.db"
    async with aiosqlite.connect(str(test_db)) as conn:
        await conn.execute("""
            CREATE TABLE doramas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code INTEGER UNIQUE,
                title TEXT NOT NULL,
                slug TEXT UNIQUE NOT NULL,
                category TEXT DEFAULT 'korea',
                genre TEXT DEFAULT 'Dorama',
                country TEXT DEFAULT 'Janubiy Koreya',
                total_episodes INTEGER DEFAULT 1,
                views INTEGER DEFAULT 0,
                status TEXT DEFAULT 'Ongoing',
                description TEXT DEFAULT '',
                aliases TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        await conn.commit()

        # Ingest new micro-drama
        d_id = await find_or_create_dorama(conn, "DramaBox: O'gay ona siri 1-15", is_micro_drama=True)
        assert d_id is not None

        async with conn.execute("SELECT title, category, genre FROM doramas WHERE id = ?", (d_id,)) as cur:
            row = await cur.fetchone()
            assert row[0].lower() == "o'gay ona siri"
            assert row[1] == "duanju"
            assert "Micro-Drama" in row[2]
