import os

bot_path = "bot.py"
with open(bot_path, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update send_episode
old_send = """                f"{ce('film')} <b>«{title}» — {ep_label}</b> [{quality_badge}]\\n"

                f"━━━━━━━━━━━━━━━━━━\\n"

                f"{ce('popcorn')} <i>Yoqimli tomosha!</i>\\n"

                f"{ce('sparkles')} @{(await bot.get_me()).username}\""""

new_send = """                f"{ce('film')} <b>«{title}» — {ep_label}</b> [{quality_badge}]\\n"

                f"━━━━━━━━━━━━━━━━━━\\n"

                f"{ce('popcorn')} <i>Yoqimli tomosha!</i>\\n\\n"

                f"⚖️ <b>Eslatma va ogohlantirish:</b>\\n"

                f"<i>Serial ichida paydo bo'ladigan har qanday qimor yoki bukmekerlik reklamalari tarjimon studiyalar tomonidan joylangan bo'lib, bot ma'muriyatiga mutlaqo aloqador emas. Biz qimor va tavakkalchilik o'yinlariga aslo targ'ib qilmaymiz!</i>\\n"

                f"━━━━━━━━━━━━━━━━━━\\n"

                f"{ce('sparkles')} @{(await bot.get_me()).username}\""""

if old_send in content:
    content = content.replace(old_send, new_send, 1)
    print("Patched send_episode successfully!")
else:
    print("WARNING: old_send not found!")

# 2. Update show_dorama_detail
old_detail = """        f"{desc_str}"

        f"{ce('point_right')} <b>Kerakli qism tugmasini bosib tomosha qiling:</b>\""""

new_detail = """        f"{desc_str}"

        f"⚖️ <i>Eslatma: Seriallar ichidagi har qanday bukmekerlik reklamalari tarjimon guruhlarga tegishli bo'lib, bot ma'muriyatiga aloqador emas va unga targ'ib qilinmaydi.</i>\\n"

        f"━━━━━━━━━━━━━━━━━━\\n"

        f"{ce('point_right')} <b>Kerakli qism tugmasini bosib tomosha qiling:</b>\""""

if old_detail in content:
    content = content.replace(old_detail, new_detail, 1)
    print("Patched show_dorama_detail successfully!")
else:
    print("WARNING: old_detail not found!")

with open(bot_path, "w", encoding="utf-8") as f:
    f.write(content)

print("Saved bot.py updates!")
