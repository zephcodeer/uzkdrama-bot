import os
import sys
import re
import ast
import sqlite3
import urllib.parse

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

print("=" * 60)
print("COMPREHENSIVE CODEBASE AUDIT: DORAMA HUB BOT")
print("=" * 60)

issues = []
warnings = []

# --- 1. AUDIT KEYBOARDS & CALLBACK COUPLING ---
with open(r"E:\Agent\Drama Bot\keyboards.py", "r", encoding="utf-8") as f:
    kb_text = f.read()

with open(r"E:\Agent\Drama Bot\bot.py", "r", encoding="utf-8") as f:
    bot_text = f.read()

# Extract all callback_data literals and patterns from keyboards.py
kb_cbs = re.findall(r'callback_data=["\']([^"\']+)["\']', kb_text)
kb_f_cbs = re.findall(r'callback_data=f["\']([^"\']+)["\']', kb_text)

print(f"\n[1] Keyboards Audit:")
print(f"  Total static callback_data: {len(kb_cbs)}")
print(f"  Total f-string callback_data: {len(kb_f_cbs)}")

# Check each static callback_data
for cb in kb_cbs:
    # check if handled in bot.py
    # either F.data == 'cb' or F.data.startswith('...')
    matched = False
    if f'F.data == "{cb}"' in bot_text or f"F.data == '{cb}'" in bot_text:
        matched = True
    else:
        prefix = cb.split(":")[0]
        if f'F.data.startswith("{prefix}:")' in bot_text or f"F.data.startswith('{prefix}:')" in bot_text:
            matched = True
    if not matched:
        issues.append(f"Keyboards -> Bot coupling: Static callback '{cb}' has no matching handler in bot.py!")

# Check each dynamic callback_data prefix
for f_cb in kb_f_cbs:
    prefix = f_cb.split("{")[0].rstrip(":")
    matched = False
    if f'F.data.startswith("{prefix}:")' in bot_text or f"F.data.startswith('{prefix}:')" in bot_text:
        matched = True
    elif prefix in ["submit_receipt"]:
        matched = False
    if not matched:
        issues.append(f"Keyboards -> Bot coupling: Dynamic callback prefix '{prefix}:' (from '{f_cb}') has no handler in bot.py!")

# --- 2. AUDIT EDIT_TEXT ON PHOTO MESSAGES ---
print(f"\n[2] Message Edit Audit:")
edit_text_matches = [m.start() for m in re.finditer(r'\.edit_text\(', bot_text)]
print(f"  Found {len(edit_text_matches)} calls to .edit_text()")

# Check lines where edit_text is called directly on call.message without render_text_screen
lines = bot_text.splitlines()
for idx, line in enumerate(lines, 1):
    if "call.message.edit_text(" in line or "event.message.edit_text(" in line:
        issues.append(f"bot.py:L{idx} calls '.message.edit_text()' directly. If previous message had a photo, Telegram raises TelegramBadRequest ('there is no text in the message to edit')!")

# --- 3. AUDIT STATEFILTERS ---
print(f"\n[3] FSM State Filters Audit:")
for idx, line in enumerate(lines, 1):
    if 'StateFilter("*")' in line:
        issues.append(f"bot.py:L{idx} uses StateFilter('*') which intercepts messages in ALL states (including admin broadcast and VIP receipt processing)!")

# --- 4. AUDIT URL ENCODING IN KEYBOARDS ---
print(f"\n[4] URL Encoding Audit in keyboards.py:")
for idx, line in enumerate(kb_text.splitlines(), 1):
    if "t.me/share/url" in line:
        if "{" in line and "quote" not in line and "quote" not in kb_text:
            issues.append(f"keyboards.py:L{idx} creates t.me/share/url without url-encoding parameters (spaces, special chars can break URL on Telegram mobile/desktop)!")

# --- 5. AUDIT DATABASE SCHEMA & DATA INTEGRITY ---
print(f"\n[5] Database Integrity Audit:")
c = sqlite3.connect(r"E:\Agent\Drama Bot\doramas.db")
c.row_factory = sqlite3.Row

# 5.1 Check doramas table
d_rows = c.execute("SELECT id, title, slug, code, poster_url, total_episodes FROM doramas").fetchall()
print(f"  Doramas count: {len(d_rows)}")
codes = {}
slugs = {}
for d in d_rows:
    # Check duplicate code
    if d['code']:
        if d['code'] in codes:
            issues.append(f"Duplicate dorama code: {d['code']} used by ID {d['id']} ('{d['title']}') and ID {codes[d['code']]}!")
        else:
            codes[d['code']] = d['id']
    # Check duplicate slug
    if d['slug']:
        if d['slug'] in slugs:
            warnings.append(f"Duplicate slug '{d['slug']}' for ID {d['id']} and {slugs[d['slug']]}")
        else:
            slugs[d['slug']] = d['id']
    # Check broken poster_url
    p = d['poster_url'] or ''
    if p.startswith('http'):
        warnings.append(f"Dorama ID {d['id']} ('{d['title']}') has remote HTTP poster URL ('{p[:40]}...'). If CDN blocks Telegram, it throws Bad Request!")
    elif p and not os.path.exists(p):
        issues.append(f"Dorama ID {d['id']} has local poster path '{p}' which does NOT exist on disk!")

# 5.2 Check episodes table
ep_rows = c.execute("SELECT e.id, e.dorama_id, e.episode_number, e.channel_message_id, e.quality, d.title FROM episodes e LEFT JOIN doramas d ON e.dorama_id = d.id").fetchall()
print(f"  Episodes count: {len(ep_rows)}")
for ep in ep_rows:
    if ep['title'] is None:
        issues.append(f"Orphan episode ID {ep['id']}: dorama_id {ep['dorama_id']} does not exist in doramas table!")
    if not ep['channel_message_id']:
        issues.append(f"Episode ID {ep['id']} has 0 or null channel_message_id!")

# 5.3 Check users table
u_rows = c.execute("SELECT * FROM users").fetchall()
print(f"  Users count: {len(u_rows)}")
for u in u_rows:
    if not u['tg_id']:
        issues.append(f"User ID {u['id']} has missing tg_id!")

# --- 6. AUDIT PYTHON SYNTAX & AST IN ALL PROJECT FILES ---
print(f"\n[6] AST Syntax Audit:")
project_dir = r"E:\Agent\Drama Bot"
for fname in ["bot.py", "database.py", "keyboards.py", "config.py", "emojis.py", "uploader.py"]:
    fpath = os.path.join(project_dir, fname)
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            code = f.read()
        ast.parse(code, filename=fname)
        print(f"  ✅ {fname}: Valid Python AST")
    except Exception as e:
        issues.append(f"AST Error in {fname}: {e}")

c.close()

# --- REPORT ---
print("\n" + "=" * 60)
print(f"AUDIT SUMMARY: {len(issues)} ISSUES FOUND, {len(warnings)} WARNINGS")
print("=" * 60)

for i, iss in enumerate(issues, 1):
    print(f"❌ Issue {i}: {iss}")

for w, wrn in enumerate(warnings, 1):
    print(f"⚠️ Warning {w}: {wrn}")
