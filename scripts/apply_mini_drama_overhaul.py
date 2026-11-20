"""
apply_mini_drama_overhaul.py
Surgically updates doramas.db to classify all short vertical/micro-dramas as 'mini_drama',
corrects country and legacy category values, and verifies category queries.
"""
import sqlite3
import os

DB_PATH = r"E:\Agent\Drama Bot\doramas.db"

def apply_database_updates():
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    print("[1] Updating Code 520 & 521 to category='mini_drama' and country='Xitoy'...")
    cur.execute("""
        UPDATE doramas
        SET category = 'mini_drama', country = 'Xitoy'
        WHERE code IN (520, 521)
    """)
    print(f"    Rows affected: {cur.rowcount}")

    print("[2] Updating Code 522 to category='mini_drama'...")
    cur.execute("""
        UPDATE doramas
        SET category = 'mini_drama'
        WHERE code = 522
    """)
    print(f"    Rows affected: {cur.rowcount}")

    print("[3] Fixing legacy Code 482 ('dorama' -> 'foreign')...")
    cur.execute("""
        UPDATE doramas
        SET category = 'foreign'
        WHERE code = 482 AND category = 'dorama'
    """)
    print(f"    Rows affected: {cur.rowcount}")

    conn.commit()

    print("\n[4] Verification:")
    cur.execute("SELECT id, code, title, category, country, total_episodes FROM doramas WHERE code IN (520, 521, 522, 482)")
    for row in cur.fetchall():
        print("   ", row)

    conn.close()
    print("\n[DONE] Mini-Drama database updates successfully applied!")

if __name__ == "__main__":
    apply_database_updates()
