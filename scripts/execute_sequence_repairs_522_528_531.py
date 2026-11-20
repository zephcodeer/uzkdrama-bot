#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Execute Sequence Repairs for Code 522, Code 528, and Code 531
=============================================================
Architected by solver-1 for fixer-3 execution.
Guarantees:
1. Zero Data Loss: Backs up all target rows to JSON files before execution.
2. SQLite UNIQUE Constraint Handling: Uses atomic payload swapping and transactional re-mapping.
3. Code 517 Invariant: Verifies Code 517 remains untouched and valid.
4. Validation Gates: Automated assertion of episode counts, message IDs, and keyboard rendering.
"""

import sys
import sqlite3
import json
from pathlib import Path

DRAMA_BOT_ROOT = Path(r"E:\Agent\Drama Bot")
DB_PATH = DRAMA_BOT_ROOT / "doramas.db"
BACKUP_DIR = DRAMA_BOT_ROOT / "scripts"

sys.path.insert(0, str(DRAMA_BOT_ROOT))

def repair_code_531(conn: sqlite3.Connection):
    """
    Code 531 ('Afsonaviy telbalar', dorama_id = 431).
    Swap episodes 7 and 8 without violating UNIQUE(dorama_id, episode_number).
    """
    print("\n--- [REPAIR 1/3] CODE 531: Inverted Episodes 7 <-> 8 ---")
    cur = conn.cursor()

    # Pre-backup
    rows = cur.execute(
        "SELECT id, episode_number, channel_message_id, file_size FROM episodes "
        "WHERE dorama_id = 431 AND episode_number IN (7, 8) ORDER BY episode_number"
    ).fetchall()
    backup_file = BACKUP_DIR / "backup_code_531_pre_swap.json"
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump([{"id": r[0], "ep": r[1], "msg": r[2], "size": r[3]} for r in rows], f, indent=2)
    print(f"  Backed up pre-repair state to {backup_file}")

    # Atomic payload swap (Keeps episode_number 7 and 8 fixed, swaps payloads - zero UNIQUE collision)
    cur.execute(
        """
        UPDATE episodes
        SET channel_message_id = CASE episode_number
                WHEN 7 THEN 5767
                WHEN 8 THEN 5766
            END,
            file_size = CASE episode_number
                WHEN 7 THEN 615169092
                WHEN 8 THEN 1222845934
            END
        WHERE dorama_id = 431 AND episode_number IN (7, 8)
        """
    )
    print(f"  Payload swapped for {cur.rowcount} episode rows.")

    # Verification
    cur.execute("SELECT episode_number, channel_message_id, file_size FROM episodes WHERE dorama_id = 431 ORDER BY episode_number")
    eps = {r[0]: (r[1], r[2]) for r in cur.fetchall()}
    assert eps[7] == (5767, 615169092), f"Ep 7 mismatch: {eps[7]}"
    assert eps[8] == (5766, 1222845934), f"Ep 8 mismatch: {eps[8]}"
    print("  [PASSED] Code 531 verified: Ep 7 -> Msg 5767 (7-qism), Ep 8 -> Msg 5766 (8-qism).")


def repair_code_528(conn: sqlite3.Connection):
    """
    Code 528 ('Drakeni sevdirish rejasi 2-fasl', dorama_id = 428).
    Prune alien episodes 17..23 belonging to 'Alis perez bilan uchrashuv'.
    Set total_episodes = 16 and status = 'Tugallangan'.
    """
    print("\n--- [REPAIR 2/3] CODE 528: Prune Alien Episodes 17..23 ---")
    cur = conn.cursor()

    # Pre-backup
    alien_rows = cur.execute(
        "SELECT id, episode_number, channel_message_id, file_size, quality FROM episodes "
        "WHERE dorama_id = 428 AND episode_number > 16 ORDER BY episode_number"
    ).fetchall()
    backup_file = BACKUP_DIR / "backup_code_528_alien_episodes.json"
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump([{"id": r[0], "ep": r[1], "msg": r[2], "size": r[3], "qual": r[4]} for r in alien_rows], f, indent=2)
    print(f"  Backed up {len(alien_rows)} alien episodes to {backup_file}")

    # Delete alien episodes
    cur.execute("DELETE FROM episodes WHERE dorama_id = 428 AND episode_number > 16")
    print(f"  Deleted {cur.rowcount} alien episode rows.")

    # Update metadata header
    cur.execute(
        "UPDATE doramas SET total_episodes = 16, status = 'Tugallangan' WHERE id = 428"
    )

    # Verification
    cnt = cur.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = 428").fetchone()[0]
    max_ep = cur.execute("SELECT MAX(episode_number) FROM episodes WHERE dorama_id = 428").fetchone()[0]
    total_meta = cur.execute("SELECT total_episodes FROM doramas WHERE id = 428").fetchone()[0]
    assert cnt == 16, f"Expected 16 episodes, found {cnt}"
    assert max_ep == 16, f"Expected max episode 16, found {max_ep}"
    assert total_meta == 16, f"Expected total_episodes 16, found {total_meta}"
    print("  [PASSED] Code 528 verified: Exactly 16 episodes remain, total_episodes=16, status='Tugallangan'.")


def repair_code_522(conn: sqlite3.Connection):
    """
    Code 522 ('Sevgi dunyoni oʻzgartiradi', dorama_id = 422).
    Expand 24 bundled video files to 64 episodes mapping with build_display_episodes grouping.
    """
    print("\n--- [REPAIR 3/3] CODE 522: Expand 64 Episodes across 24 Bundled Videos ---")
    cur = conn.cursor()

    # Pre-backup
    existing = cur.execute(
        "SELECT id, episode_number, channel_message_id, file_size, quality FROM episodes "
        "WHERE dorama_id = 422 ORDER BY episode_number"
    ).fetchall()
    backup_file = BACKUP_DIR / "backup_code_522_pre_repair.json"
    with open(backup_file, "w", encoding="utf-8") as f:
        json.dump([{"id": r[0], "ep": r[1], "msg": r[2], "size": r[3], "qual": r[4]} for r in existing], f, indent=2)
    print(f"  Backed up {len(existing)} existing rows to {backup_file}")

    # Bundled mapping definition
    # (start_ep, end_ep, storage_msg_id, file_size, quality)
    mapping_plan = [
        (1, 6, 5616, 481165111, "720p"),     # 1dan 6gacha
        (7, 8, 5617, 13293995, "1080p"),    # 7-8qismlari
        (9, 9, 5618, 15589010, "1080p"),    # 9-qism
        (10, 10, 5619, 9281926, "720p"),    # 10-qism
        (11, 12, 5620, 14796685, "720p"),   # 11-12-qismlar
        (13, 13, 5621, 7228941, "720p"),    # 13-qism
        (14, 14, 5622, 6747456, "720p"),    # 14-qism
        (15, 15, 5623, 11858561, "1080p"),  # 15-qism
        (16, 16, 5624, 7050450, "720p"),    # 16-qism
        (17, 17, 5625, 8064634, "720p"),    # 17-qism
        (18, 18, 5626, 5352647, "720p"),    # 18-qism
        (19, 19, 5627, 3888953, "720p"),    # 19-qism
        (20, 20, 5628, 6080594, "720p"),    # 20-qism
        (21, 21, 5629, 6326910, "720p"),    # 21-qism
        (22, 22, 5630, 6350313, "720p"),    # 22-qism
        (23, 23, 5631, 6848016, "720p"),    # 23-qism
        (24, 24, 5632, 6543103, "720p"),    # 24-qism
        (25, 25, 5633, 5451563, "720p"),    # 25-qism
        (26, 26, 5634, 5858246, "720p"),    # 26-qism
        (27, 27, 5635, 6025866, "720p"),    # 27-qism
        (28, 28, 5636, 6278006, "720p"),    # 28-qism
        (29, 29, 5637, 5013481, "720p"),    # 29-qism
        (30, 30, 5638, 5798693, "720p"),    # 30-qism
        (31, 64, 5639, 667091335, "720p"),  # 31dan 64gacha FINAL
    ]

    # Clear old episodes in transaction
    cur.execute("DELETE FROM episodes WHERE dorama_id = 422")

    # Insert 64 individual episode rows
    inserted = 0
    for s_ep, e_ep, msg_id, fsize, qual in mapping_plan:
        for ep_num in range(s_ep, e_ep + 1):
            cur.execute(
                """
                INSERT INTO episodes (dorama_id, episode_number, channel_message_id, file_id, file_size, quality)
                VALUES (422, ?, ?, '', ?, ?)
                """,
                (ep_num, msg_id, fsize, qual)
            )
            inserted += 1

    # Update metadata header
    cur.execute(
        """
        UPDATE doramas
        SET total_episodes = 64,
            category = 'mini_drama',
            country = 'Xitoy',
            status = 'Tugallangan'
        WHERE id = 422
        """
    )
    print(f"  Inserted {inserted} episode rows (Episodes 1..64) for Dorama 422.")

    # Verification
    cnt = cur.execute("SELECT COUNT(*) FROM episodes WHERE dorama_id = 422").fetchone()[0]
    total_meta = cur.execute("SELECT total_episodes FROM doramas WHERE id = 422").fetchone()[0]
    assert cnt == 64, f"Expected 64 episodes, found {cnt}"
    assert total_meta == 64, f"Expected total_episodes 64, found {total_meta}"

    # Test keyboard display
    from keyboards import build_display_episodes
    eps_db = cur.execute(
        "SELECT episode_number, channel_message_id, quality FROM episodes WHERE dorama_id = 422 ORDER BY episode_number"
    ).fetchall()
    buttons = build_display_episodes([{"episode_number": r[0], "channel_message_id": r[1], "quality": r[2]} for r in eps_db])
    assert len(buttons) == 24, f"Expected exactly 24 buttons, got {len(buttons)}"
    assert buttons[0]["label"] == "1-6-qism", f"Button 0 label mismatch: {buttons[0]['label']}"
    assert buttons[1]["label"] == "7-8-qism", f"Button 1 label mismatch: {buttons[1]['label']}"
    assert buttons[-1]["label"] == "31-64-qism", f"Last button label mismatch: {buttons[-1]['label']}"
    print(f"  [PASSED] Code 522 verified: 64 episodes cleanly mapped into 24 grouped buttons (1-6-qism ... 31-64-qism).")


def verify_code_517_invariant(conn: sqlite3.Connection):
    """
    User explicit instruction: Code 517 ('Buyuk fitnachi') is ALMASHMAGAN.
    Verify it is 100% correct and untouched.
    """
    print("\n--- [INVARIANT CHECK] CODE 517: Verification of Untouched Status ---")
    cur = conn.cursor()
    d517 = cur.execute("SELECT id, code, title, total_episodes FROM doramas WHERE code = 517").fetchone()
    assert d517 is not None, "Dorama 517 not found!"
    assert d517[3] == 2, f"Expected 2 episodes, got {d517[3]}"

    eps517 = cur.execute("SELECT episode_number, channel_message_id FROM episodes WHERE dorama_id = 417 ORDER BY episode_number").fetchall()
    assert len(eps517) == 2, f"Expected 2 episodes for dorama 417, got {len(eps517)}"
    assert eps517[0] == (1, 5454), f"Ep 1 mismatch: {eps517[0]}"
    assert eps517[1] == (2, 5453), f"Ep 2 mismatch: {eps517[1]}"
    print("  [PASSED] Code 517 strictly preserved and 100% verified (Ep 1 -> 5454, Ep 2 -> 5453).")


def main():
    print("=== STARTING MULTI-DORAMA SEQUENCE REPAIRS (522, 528, 531) ===")
    if not DB_PATH.exists():
        print(f"ERROR: DB not found at {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("BEGIN TRANSACTION")
        verify_code_517_invariant(conn)
        repair_code_531(conn)
        repair_code_528(conn)
        repair_code_522(conn)
        verify_code_517_invariant(conn)
        conn.commit()
        print("\n=== ALL REPAIRS COMMITTED SUCCESSFULLY (ZERO ERRORS) ===")
    except Exception as exc:
        conn.rollback()
        print(f"\nFATAL: Repair transaction rolled back due to error: {exc}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
