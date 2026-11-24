import re
import pytest
from typing import Tuple

import sys
from pathlib import Path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from autopilot_donor_listener import (
    is_subtitle_release,
    is_uzbek_dubbed,
    clean_dorama_title,
    normalize_for_filter,
)


def test_crash_2_subtitle_leak():
    caption = """🎬 ➺ Crash 2: Xavfli yo‘l

🎞 ➺ 1-qism #yonu
🇺🇿 ➺ O'zbek Tilida(uzb sub)
🌍 ➺ Janubiy Koreya
⚔️ ➺ Kriminal, Detektiv, Triller
📩 ➺ @YonuTv_1

Barchasi @YonuTv_1 kanalida — o'tkazib yubormang!🐣"""
    is_sub, marker = is_subtitle_release(caption)
    assert is_sub is True
    assert "sub" in marker.lower()


def test_orinbosar_subtitle_leak():
    caption = """🎬 ➺ Oʻrinbosar

🎞 ➺ 1-qism #yonu
🇺🇿 ➺ O'zbek Tilida(uzb sub)
🌍 ➺ Janubiy Koreya
⚔ ➺  Sirli, Triller, Jinoyat
📥 ➺ @YonuTv_1"""
    is_sub, marker = is_subtitle_release(caption)
    assert is_sub is True
    assert "sub" in marker.lower()


def test_niqobdagi_subtitr_blocked():
    caption = """**Niqobdagi Muhabbat 🖤 11-qism**
**Manba: YonuTv (subtitr)**
**Sifat: 720p**
#Niqobdagi_Muhabbat
#Love_In_Disguise"""
    is_sub, marker = is_subtitle_release(caption)
    assert is_sub is True
    assert "subtitr" in marker.lower()


def test_safe_word_subscribe_not_blocked():
    caption = """Kanalimizga subscribe bo'ling va eng so'nggi doramalarni tomosha qiling!
Dorama: Sevgi qismati
1-qism
O'zbek tilida dublyaj"""
    is_sub, marker = is_subtitle_release(caption)
    assert is_sub is False
    has_dub, dub_marker = is_uzbek_dubbed(caption)
    assert has_dub is True


def test_niqobdagi_dubbed_accepted():
    caption = """#niqobdagi_muhabbat/ #Mening_aybdor_insonim
10-qism 
Uzbek tilida 🇺🇿
#Choson_tv"""
    is_sub, marker = is_subtitle_release(caption)
    assert is_sub is False
    has_dub, dub_marker = is_uzbek_dubbed(caption)
    assert has_dub is True
    title = clean_dorama_title(caption)
    assert "niqobdagi" in title.lower() or "aybdor" in title.lower()


def test_yashirin_niqobdagi_sevgi_dubbed():
    caption = """#Yashirin_niqobdagi_Sevgi
10-qism 
Özbek tilida:Choson tv"""
    is_sub, marker = is_subtitle_release(caption)
    assert is_sub is False
    has_dub, dub_marker = is_uzbek_dubbed(caption)
    assert has_dub is True
    title = clean_dorama_title(caption)
    assert "yashirin niqobdagi sevgi" in title.lower()


def test_doktor_x_choson_handle():
    caption = """#Doktor_X
6-QISM

🌟 MANBA : @Choson_tv"""
    is_sub, marker = is_subtitle_release(caption)
    assert is_sub is False
    has_dub, dub_marker = is_uzbek_dubbed(caption)
    assert has_dub is True
    title = clean_dorama_title(caption)
    assert "doktor x" in title.lower()


def test_cyrillic_subtitles():
    cases = [
        "Сериал: Қонли муҳаббат (уз суб)",
        "Дорама: Сеул кечалари 1-қисм субтитрли",
        "Қисм 3 [саблар билан]",
    ]
    for c in cases:
        is_sub, marker = is_subtitle_release(c)
        assert is_sub is True, f"Failed on Cyrillic sub: {c}"
