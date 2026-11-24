import asyncio
import pytest
from unittest.mock import MagicMock, AsyncMock
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from autopilot_donor_listener import (
    clean_dorama_title,
    parse_episodes,
    process_direct_storage_message,
)


def test_direct_drop_single_episode_parsing():
    text = "Choson nikoh agentligi❤️\n\n13-qism O‘zbek tilida [MinxoTv ]"
    title = clean_dorama_title(text)
    eps = parse_episodes(text)
    assert title.lower() == "choson nikoh agentligi"
    assert eps == [13]


def test_direct_drop_batch_range_parsing():
    text = "Baxt Qasri (1-22 qismlar) Barcha qismlari jamlangan"
    title = clean_dorama_title(text)
    eps = parse_episodes(text)
    assert "baxt qasri" in title.lower()
    assert len(eps) == 22
    assert eps[0] == 1
    assert eps[-1] == 22


def test_direct_drop_filename_fallback():
    fname = "Doktor_X_Oq_Mafiya_11_qism_1080p.mp4"
    cleaned = fname.replace("_", " ").rsplit(".", 1)[0]
    title = clean_dorama_title(cleaned)
    eps = parse_episodes(cleaned)
    assert "doktor x" in title.lower()
    assert eps == [11]
