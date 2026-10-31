import re

path = r"E:\Agent\Drama Bot\database.py"
with open(path, "rb") as f:
    content = f.read().decode("utf-8")

old_check = """    q = (query or "").strip()
    if len(q) < 2:
        return []"""

new_check = """    q = (query or "").strip()
    if not q:
        return []
    if len(q) < 2 and not q.isdigit():
        return []"""

old_code = """        # 1. To'liq kino kodi mosligi
        if q_norm == code_str:
            score = 100.0
        # 2. To'liq nom mosligi"""

new_code = """        # 1. To'liq kino kodi mosligi
        if q_norm == code_str:
            score = 100.0
        elif q_norm.isdigit() and code_str.startswith(q_norm):
            score = 85.0 + (len(q_norm) / len(code_str)) * 10.0
        # 2. To'liq nom mosligi"""

# Normalize \r\n to \n for replacement
has_crlf = "\r\n" in content
content_lf = content.replace("\r\n", "\n")

if old_check in content_lf and old_code in content_lf:
    content_lf = content_lf.replace(old_check, new_check)
    content_lf = content_lf.replace(old_code, new_code)
    final_content = content_lf.replace("\n", "\r\n") if has_crlf else content_lf
    with open(path, "wb") as f:
        f.write(final_content.encode("utf-8"))
    print("SUCCESS: database.py updated with digit prefix search!")
else:
    print("Could not find targets in database.py")
