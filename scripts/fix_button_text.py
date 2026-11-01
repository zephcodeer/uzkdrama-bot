path = r"E:\Agent\Drama Bot\bot.py"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

has_crlf = "\r\n" in content
content_lf = content.replace("\r\n", "\n")

# Replace both occurrences
old_btn = 'text=f"{ce(\'play\')} Doramani tomosha qilish"'
new_btn = 'text="🎬 Doramani tomosha qilish", icon_custom_emoji_id="5348125953090403204"'

count = content_lf.count(old_btn)
print(f"Found {count} occurrences of old_btn")

if count > 0:
    content_lf = content_lf.replace(old_btn, new_btn)
    final_content = content_lf.replace("\n", "\r\n") if has_crlf else content_lf
    with open(path, "wb") as f:
        f.write(final_content.encode("utf-8"))
    print("SUCCESS: Fixed broken button texts in bot.py!")
else:
    print("ERROR: old_btn not found")
