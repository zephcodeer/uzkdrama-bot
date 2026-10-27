import re

with open(r"E:\Agent\Drama Bot\bot.py", "r", encoding="utf-8") as f:
    text = f.read()

# 1. Remove the first message that sent main_reply_kb in cmd_start
pattern = r'await message\.answer\(\s*f"\{ce\(\'film\'\)\} <b>DORAMA HUB</b> — doimiy menyu faollashdi\.",\s*reply_markup=kb\.main_reply_kb\(is_admin=is_admin\),\s*parse_mode=ParseMode\.HTML\s*\)'

replacement = '''try:
        clean_msg = await message.answer("ㅤ", reply_markup=ReplyKeyboardRemove())
        await clean_msg.delete()
    except Exception:
        pass'''

if re.search(pattern, text):
    text = re.sub(pattern, replacement, text)
    print("Found and replaced in cmd_start!")
else:
    print("Pattern not found in cmd_start")

# 2. In handle_menu_trigger, also ensure ReplyKeyboardRemove is triggered
menu_pattern = r'(@router\.message\(Command\("menu"\)\).*?async def handle_menu_trigger\(message: Message, state: FSMContext\):.*?text = \(.*?\)\n)(\s*await message\.answer\(text, reply_markup=kb\.main_menu_kb)'

def replace_menu(m):
    return m.group(1) + '    try:\n        clean_msg = await message.answer("ㅤ", reply_markup=ReplyKeyboardRemove())\n        await clean_msg.delete()\n    except Exception:\n        pass\n' + m.group(2)

text = re.sub(menu_pattern, replace_menu, text, flags=re.DOTALL)

with open(r"E:\Agent\Drama Bot\bot.py", "w", encoding="utf-8") as f:
    f.write(text)

print("Updated bot.py successfully!")
