import pytest
import sqlite3
from pathlib import Path
import sys

DRAMA_BOT_ROOT = Path(r"E:\Agent\Drama Bot")
DB_PATH = DRAMA_BOT_ROOT / "doramas.db"
sys.path.insert(0, str(DRAMA_BOT_ROOT))

from keyboards import build_display_episodes


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def test_code_531_sequence_swap():
    """Verify Code 531 (Afsonaviy telbalar) episodes 7 and 8 swap."""
    with get_db() as conn:
        cur = conn.cursor()
        d531 = cur.execute("SELECT id, code, title, total_episodes FROM doramas WHERE code = 531").fetchone()
        assert d531 is not None
        assert d531["total_episodes"] == 8

        eps = cur.execute(
            "SELECT episode_number, channel_message_id, file_size FROM episodes "
            "WHERE dorama_id = ? ORDER BY episode_number",
            (d531["id"],)
        ).fetchall()
        assert len(eps) == 8

        eps_map = {r["episode_number"]: r["channel_message_id"] for r in eps}
        assert eps_map[7] == 5767, "Episode 7 must point to msg 5767 (7-qism)"
        assert eps_map[8] == 5766, "Episode 8 must point to msg 5766 (8-qism)"


def test_code_528_prune_alien_episodes():
    """Verify Code 528 (Drakeni sevdirish rejasi 2-fasl) has exactly 16 episodes."""
    with get_db() as conn:
        cur = conn.cursor()
        d528 = cur.execute("SELECT id, code, title, total_episodes, status FROM doramas WHERE code = 528").fetchone()
        assert d528 is not None
        assert d528["total_episodes"] == 16
        assert d528["status"] == "Tugallangan"

        eps = cur.execute(
            "SELECT episode_number, channel_message_id FROM episodes "
            "WHERE dorama_id = ? ORDER BY episode_number",
            (d528["id"],)
        ).fetchall()
        assert len(eps) == 16, f"Expected 16 episodes, found {len(eps)}"
        assert max(r["episode_number"] for r in eps) == 16
        assert min(r["episode_number"] for r in eps) == 1

        # Check alien episodes 17..23 do not exist
        alien = cur.execute(
            "SELECT COUNT(*) FROM episodes WHERE dorama_id = ? AND episode_number > 16",
            (d528["id"],)
        ).fetchone()[0]
        assert alien == 0, "Alien episodes must not exist in database"


def test_code_522_grouped_episodes_and_buttons():
    """Verify Code 522 (Sevgi dunyoni oʻzgartiradi) 64 episodes and 24 buttons."""
    with get_db() as conn:
        cur = conn.cursor()
        d522 = cur.execute("SELECT id, code, title, total_episodes, category FROM doramas WHERE code = 522").fetchone()
        assert d522 is not None
        assert d522["total_episodes"] == 64
        assert d522["category"] in ("mini_drama", "duanju")

        eps = cur.execute(
            "SELECT episode_number, channel_message_id, quality FROM episodes "
            "WHERE dorama_id = ? ORDER BY episode_number",
            (d522["id"],)
        ).fetchall()
        assert len(eps) == 64, f"Expected 64 episodes in DB, found {len(eps)}"

        # Check bundled ranges
        msg_counts = {}
        for r in eps:
            msg_counts[r["channel_message_id"]] = msg_counts.get(r["channel_message_id"], 0) + 1

        assert msg_counts[5616] == 6, "Msg 5616 should bundle episodes 1..6"
        assert msg_counts[5617] == 2, "Msg 5617 should bundle episodes 7..8"
        assert msg_counts[5620] == 2, "Msg 5620 should bundle episodes 11..12"
        assert msg_counts[5639] == 34, "Msg 5639 should bundle episodes 31..64"

        # Verify UI buttons
        buttons = build_display_episodes([
            {"episode_number": r["episode_number"], "channel_message_id": r["channel_message_id"], "quality": r["quality"]}
            for r in eps
        ])
        assert len(buttons) == 24, f"Expected exactly 24 UI buttons, got {len(buttons)}"
        assert buttons[0]["label"] == "1-6-qism"
        assert buttons[1]["label"] == "7-8-qism"
        assert buttons[2]["label"] == "9-qism"
        assert buttons[4]["label"] == "11-12-qism"
        assert buttons[-1]["label"] == "31-64-qism"


def test_code_517_user_invariant_untouched():
    """Verify Code 517 (Buyuk fitnachi) episodes order is strictly preserved and total_episodes reflects series."""
    with get_db() as conn:
        cur = conn.cursor()
        d517 = cur.execute("SELECT id, code, title, total_episodes FROM doramas WHERE code = 517").fetchone()
        assert d517 is not None
        assert d517["total_episodes"] in (16, 32)

        eps = cur.execute(
            "SELECT episode_number, channel_message_id FROM episodes "
            "WHERE dorama_id = ? ORDER BY episode_number",
            (d517["id"],)
        ).fetchall()
        assert len(eps) == 2
        assert eps[0]["episode_number"] == 1 and eps[0]["channel_message_id"] == 5454
        assert eps[1]["episode_number"] == 2 and eps[1]["channel_message_id"] == 5453
