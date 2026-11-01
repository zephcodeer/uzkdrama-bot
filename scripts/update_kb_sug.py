path = r"E:\Agent\Drama Bot\keyboards.py"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

has_crlf = "\r\n" in content
content_lf = content.replace("\r\n", "\n")

target = """def suggestion_admin_kb(suggestion_id: int, user_id: int) -> InlineKeyboardMarkup:
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
    return builder.as_markup()"""

replacement = """def suggestion_admin_kb(suggestion_id: int, user_id: int, matched_code: int | None = None) -> InlineKeyboardMarkup:
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
    if matched_code:
        builder.row(
            InlineKeyboardButton(
                text=f"🎬 Allaqachon bor ({matched_code}-kod)",
                callback_data=f"sug_exist:{suggestion_id}:{user_id}:{matched_code}",
                icon_custom_emoji_id=ICON_PLAY
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="🎬 Allaqachon bor",
                callback_data=f"sug_exist_ask:{suggestion_id}:{user_id}",
                icon_custom_emoji_id=ICON_PLAY
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="Foydalanuvchiga Javob Yozish",
            callback_data=f"sug_reply:{suggestion_id}:{user_id}",
            icon_custom_emoji_id=ICON_BROADCAST
        )
    )
    return builder.as_markup()"""

if target in content_lf:
    content_lf = content_lf.replace(target, replacement, 1)
    final_content = content_lf.replace("\n", "\r\n") if has_crlf else content_lf
    with open(path, "wb") as f:
        f.write(final_content.encode("utf-8"))
    print("SUCCESS: keyboards.py updated with suggestion_admin_kb matched_code support!")
else:
    print("ERROR: Target not found in keyboards.py!")
