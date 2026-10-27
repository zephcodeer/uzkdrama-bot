import re
import sys

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

with open(r"E:\Agent\Drama Bot\keyboards.py", "r", encoding="utf-8") as f:
    text = f.read()

btns = re.findall(r"InlineKeyboardButton\((.*?)\)", text, re.DOTALL)
print(f"Total buttons: {len(btns)}")
for idx, b in enumerate(btns, 1):
    t_m = re.search(r'text=f?["\'](.*?)["\']', b)
    t = t_m.group(1) if t_m else "???"
    has_custom = "icon_custom_emoji_id" in b
    print(f"{idx}: text='{t}' | custom_icon={has_custom}")
