import asyncio
import database as db
import sqlite3
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

async def test_database():
    print("--- Testing database.py functions ---")
    await db.init_db()
    print("init_db() passed")

    # 1. get_dorama_by_id
    d = await db.get_dorama_by_id(1)
    print("get_dorama_by_id(1):", d["title"] if d else "None")

    # 2. get_dorama_by_code
    d_code = await db.get_dorama_by_code(101)
    print("get_dorama_by_code(101):", d_code["title"] if d_code else "None")

    # 3. get_dorama_by_slug
    d_slug = await db.get_dorama_by_slug("doktor-x-oq-mafia")
    print("get_dorama_by_slug:", d_slug["title"] if d_slug else "None")

    # 4. search_doramas
    res = await db.search_doramas("ovchi")
    print(f"search_doramas('ovchi'): found {len(res)}")

    # 5. get_latest_doramas
    latest = await db.get_latest_doramas(limit=10, offset=0)
    print(f"get_latest_doramas(): found {len(latest)}")

    # 6. get_top_doramas
    top = await db.get_top_doramas(limit=5)
    print(f"get_top_doramas(): found {len(top)}")

    # 7. get_episodes
    eps = await db.get_episodes(18)
    print(f"get_episodes(18): found {len(eps)}")

    # 8. get_episode
    ep = await db.get_episode(18, 1)
    print("get_episode(18, 1):", ep["channel_message_id"] if ep else "None")

    # 9. test user registration
    new_user, inviter = await db.register_user(999999999, "testuser", "Test", False, None)
    print(f"register_user(): new={new_user}, inviter={inviter}")

    # 10. get_user
    u = await db.get_user(999999999)
    print("get_user():", u["tg_id"] if u else "None")

    # 11. is_user_unlocked
    unlocked, reason, cur_refs, req_refs = await db.is_user_unlocked(999999999, 4, 7141955036)
    print(f"is_user_unlocked(ep 4): unlocked={unlocked}, reason={reason}")

    # 12. bookmarks
    bookmarked = await db.toggle_bookmark(999999999, 18)
    print("toggle_bookmark():", bookmarked)
    is_b = await db.is_bookmarked(999999999, 18)
    print("is_bookmarked():", is_b)
    b_list = await db.get_user_bookmarks(999999999)
    print(f"get_user_bookmarks(): found {len(b_list)}")

    # 13. history
    await db.save_last_watched(999999999, 18, 1)
    last_ep = await db.get_last_watched(999999999, 18)
    print("get_last_watched():", last_ep)

    # 14. subscribers
    sub = await db.toggle_subscription(999999999, 18)
    print("toggle_subscription():", sub)
    is_sub = await db.is_subscribed(999999999, 18)
    print("is_subscribed():", is_sub)
    subs = await db.get_dorama_subscribers(18)
    print(f"get_dorama_subscribers(18): found {len(subs)}")

    # 15. VIP orders
    order_id = await db.create_vip_order(999999999, "1_month", 9000, "file_test_receipt")
    print("create_vip_order(): order_id =", order_id)
    order = await db.get_vip_order(order_id)
    print("get_vip_order(): status =", order["status"])
    await db.update_order_status(order_id, "approved")
    print("update_order_status() approved")

    # 16. grant_vip
    await db.grant_vip(999999999, 30)
    u_vip = await db.get_user(999999999)
    print("grant_vip(): is_vip =", u_vip["is_vip"], "until =", u_vip["vip_until"])

    # 17. get_all_user_ids
    u_ids = await db.get_all_user_ids()
    print(f"get_all_user_ids(): found {len(u_ids)}")

    # 18. stats
    stats = await db.get_stats()
    print("get_stats():", stats)

    # Cleanup test user
    conn = sqlite3.connect(r'E:\Agent\Drama Bot\doramas.db')
    conn.execute("DELETE FROM users WHERE tg_id = 999999999")
    conn.execute("DELETE FROM bookmarks WHERE user_id = 999999999")
    conn.execute("DELETE FROM user_history WHERE user_id = 999999999")
    conn.execute("DELETE FROM dorama_subscribers WHERE user_id = 999999999")
    conn.execute("DELETE FROM vip_orders WHERE user_id = 999999999")
    conn.commit()
    conn.close()
    print("Cleanup test user complete")

if __name__ == "__main__":
    asyncio.run(test_database())
