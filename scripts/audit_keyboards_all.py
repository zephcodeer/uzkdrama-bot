import sys
import keyboards as kb

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

errors = []
warnings = []

def check_markup(name, markup):
    if not markup or not hasattr(markup, 'inline_keyboard'):
        errors.append(f"{name}: Not a valid InlineKeyboardMarkup!")
        return
    for row_idx, row in enumerate(markup.inline_keyboard):
        for col_idx, btn in enumerate(row):
            if btn.callback_data is not None:
                cb_len = len(btn.callback_data.encode('utf-8'))
                if cb_len > 64:
                    errors.append(f"{name} [r{row_idx},c{col_idx}]: callback_data {cb_len} > 64 bytes! -> '{btn.callback_data}'")
                elif cb_len > 55:
                    warnings.append(f"{name} [r{row_idx},c{col_idx}]: callback_data {cb_len} bytes -> '{btn.callback_data}'")
            if btn.url and not (btn.url.startswith('http://') or btn.url.startswith('https://') or btn.url.startswith('tg://')):
                errors.append(f"{name} [r{row_idx},c{col_idx}]: Invalid URL scheme -> '{btn.url}'")

print("=== CHECKING ALL 10 KEYBOARD BUILDERS ===")

# 1. main_menu_kb
check_markup("main_menu_kb(admin=False)", kb.main_menu_kb(is_admin=False))
check_markup("main_menu_kb(admin=True)", kb.main_menu_kb(is_admin=True))

# 2. doramas_list_kb
mock_d = [{"id": i, "title": f"Dorama {i}", "code": 100+i, "total_episodes": 16} for i in range(1, 15)]
mock_d_no_eps = [{"id": i, "title": f"Dorama {i}"} for i in range(1, 15)]
check_markup("doramas_list_kb(p0)", kb.doramas_list_kb(mock_d, prefix="doramas", page=0, has_next=True))
check_markup("doramas_list_kb(p1)", kb.doramas_list_kb(mock_d, prefix="top", page=1, has_next=False))
check_markup("doramas_list_kb(empty)", kb.doramas_list_kb([], prefix="search", page=0, has_next=False))

# 3. dorama_detail_kb
mock_eps = [{"episode_number": i, "quality": "1080p", "file_size": 500*1024*1024} for i in range(1, 40)]
for p in range(5):
    check_markup(f"dorama_detail_kb(p{p})", kb.dorama_detail_kb(
        dorama_id=18,
        episodes=mock_eps,
        bot_username="uzkdrama_app",
        page=p,
        last_watched=3,
        bookmarked=True,
        subscribed=True
    ))

# 4. admin_panel_kb
check_markup("admin_panel_kb", kb.admin_panel_kb())

# 5. back_to_menu_kb
check_markup("back_to_menu_kb", kb.back_to_menu_kb())

# 6. episode_player_kb
check_markup("episode_player_kb", kb.episode_player_kb(
    dorama_id=18,
    current_ep=3,
    has_next=True,
    bookmarked=True
))

# 7. episode_lock_kb
check_markup("episode_lock_kb", kb.episode_lock_kb(
    dorama_id=18,
    user_id=7141955036,
    bot_username="uzkdrama_app",
    current_refs=1,
    needed_refs=2
))

# 8. vip_plans_kb
check_markup("vip_plans_kb", kb.vip_plans_kb())

# 9. vip_payment_method_kb
check_markup("vip_payment_method_kb", kb.vip_payment_method_kb("1_month"))

# 10. admin_order_kb
check_markup("admin_order_kb", kb.admin_order_kb(order_id=42, user_id=7141955036, days=30))

print(f"\nErrors found: {len(errors)}")
for e in errors:
    print("  ❌", e)

print(f"Warnings found: {len(warnings)}")
for w in warnings:
    print("  ⚠️", w)

if not errors:
    print("\n✅ ALL KEYBOARDS PASSED TELEGRAM PROTOCOL AUDIT!")
