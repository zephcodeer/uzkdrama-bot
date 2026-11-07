import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

def patch_database():
    with open('database.py', 'r', encoding='utf-8') as f:
        text = f.read()

    guard_code = '''async def check_channel_message_collision(channel_message_id: int, dorama_id: int):
    """Tekshiradi: agar channel_message_id boshqa dramaga allaqachon biriktirilgan bo'lsa, o'sha dorama va qism ma'lumotlarini qaytaradi."""
    if not channel_message_id or channel_message_id <= 0:
        return None
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(
            """SELECT e.dorama_id, e.episode_number, d.code, d.title
               FROM episodes e
               JOIN doramas d ON e.dorama_id = d.id
               WHERE e.channel_message_id = ? AND e.dorama_id != ?
               LIMIT 1""",
            (channel_message_id, dorama_id)
        ) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None


async def add_episode(dorama_id: int, episode_number: int, channel_message_id: int, file_id: str = "", file_size: int = 0, quality: str = "720p", allow_cross_collision: bool = False):
    if not allow_cross_collision and channel_message_id and channel_message_id > 0:
        collision = await check_channel_message_collision(channel_message_id, dorama_id)
        if collision:
            err_msg = (
                f"KROSS-TO'QNASHUV TAQIQLANDI: storage_message_id={channel_message_id} "
                f"allaqachon boshqa dorama [{collision['code']}] '{collision['title']}' "
                f"ning {collision['episode_number']}-qismiga biriktirilgan! "
                f"Dorama ID={dorama_id} ga noto'g'ri bog'lanish oldi olindi."
            )
            logger.error(err_msg)
            raise ValueError(err_msg)
'''

    old_def = 'async def add_episode(dorama_id: int, episode_number: int, channel_message_id: int, file_id: str = "", file_size: int = 0, quality: str = "720p"):'
    if old_def not in text:
        print("Warning: old_def not found in database.py, maybe already patched?")
    else:
        new_text = text.replace(old_def, guard_code, 1)
        with open('database.py', 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("Successfully patched database.py with cross-collision guard!")

def patch_bot():
    with open('bot.py', 'r', encoding='utf-8') as f:
        text = f.read()

    # Target in send_episode
    old_target = '''    ep = await db.get_episode(dorama_id, ep_num)

    if not ep:

        await bot.send_message(user_id, f"{ce('bell')} Ushbu qism hali bazaga joylanmagan.")

        return'''

    new_target = '''    ep = await db.get_episode(dorama_id, ep_num)

    if not ep or not ep.get("channel_message_id") or ep["channel_message_id"] <= 0:
        back_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=f"{ce('folder')} Doramaga qaytish", callback_data=f"dorama_{dorama_id}")],
            [InlineKeyboardButton(text=f"{ce('home')} Bosh menyu", callback_data="main_menu")]
        ])
        await bot.send_message(
            user_id,
            f"{ce('bell')} Ushbu qism hozircha bazaga yuklanmagan yoki tez orada joylanadi.\n"
            f"Iltimos, tez orada qayta tekshiring!",
            reply_markup=back_kb
        )
        return'''

    if old_target not in text:
        print("Warning: old_target not found in bot.py, checking alternative...")
        # Check normalized
        import re
        pat = re.compile(r'ep = await db\.get_episode\(dorama_id, ep_num\)\s+if not ep:\s+await bot\.send_message\(user_id, f"\{ce\(\'bell\'\)\} Ushbu qism hali bazaga joylanmagan\."\)\s+return')
        if pat.search(text):
            text = pat.sub(new_target, text, count=1)
            with open('bot.py', 'w', encoding='utf-8') as f:
                f.write(text)
            print("Successfully patched bot.py via regex!")
        else:
            print("Could not match send_episode block in bot.py")
    else:
        new_text = text.replace(old_target, new_target, 1)
        with open('bot.py', 'w', encoding='utf-8') as f:
            f.write(new_text)
        print("Successfully patched bot.py send_episode handler!")

if __name__ == '__main__':
    patch_database()
    patch_bot()
