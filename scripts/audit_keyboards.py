import sys
import keyboards as kb

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def check_markup(name, markup):
    if not markup or not hasattr(markup, 'inline_keyboard'):
        return
    for row_idx, row in enumerate(markup.inline_keyboard):
        for col_idx, btn in enumerate(row):
            if btn.callback_data:
                cb_len = len(btn.callback_data.encode('utf-8'))
                if cb_len > 64:
                    print(f"❌ ERROR in {name} [row {row_idx}, col {col_idx}]: callback_data exceeds 64 bytes! Length: {cb_len} -> '{btn.callback_data}'")
                elif cb_len > 50:
                    print(f"⚠️ WARNING in {name}: callback_data is close to limit: {cb_len} bytes -> '{btn.callback_data}'")
            # Check url
            if btn.url and not (btn.url.startswith('http') or btn.url.startswith('tg://')):
                print(f"❌ ERROR in {name}: invalid URL: {btn.url}")

print("=== TESTING ALL KEYBOARDS ===")

# 1. main_menu_kb
check_markup("main_menu_kb", kb.main_menu_kb())

# 2. dorama_detail_kb (various states and page sizes)
mock_episodes = [
    {"episode_number": i, "quality": "1080p", "file_size": 500*1024*1024}
    for i in range(1, 100)
]
for p in range(1, 10):
    markup = kb.dorama_detail_kb(
        dorama_id=18,
        episodes=mock_episodes,
        bot_username="uzkdrama_app",
        page=p,
        last_watched=5,
        bookmarked=True,
        subscribed=True
    )
    check_markup(f"dorama_detail_kb(page={p})", markup)

# 3. search_results_kb
mock_doramas = [
    {"id": i, "title": f"Dorama Title {i}", "year": 2024, "total_episodes": 16, "status": "Tugallangan", "genre": "Ekshn"}
    for i in range(1, 25)
]
check_markup("search_results_kb", kb.search_results_kb(mock_doramas, "ovchi", page=1, total_pages=3))

# 4. vip_plans_kb
check_markup("vip_plans_kb", kb.vip_plans_kb())

# 5. payment_methods_kb
check_markup("payment_methods_kb", kb.payment_methods_kb("1_month"))

# 6. admin_order_kb
check_markup("admin_order_kb", kb.admin_order_kb(12345, 999999999, 30))

# 7. admin_panel_kb
check_markup("admin_panel_kb", kb.admin_panel_kb())

# 8. channel_subscribe_kb
check_markup("channel_subscribe_kb", kb.channel_subscribe_kb("@testchannel", "118"))

# 9. my_profile_kb
check_markup("my_profile_kb", kb.my_profile_kb("uzkdrama_app", 999999999))

print("=== KEYBOARD AUDIT COMPLETE ===")
