import sqlite3
import os
from PIL import Image, ImageFilter

conn = sqlite3.connect('doramas.db')
c = conn.cursor()

# 1. Update Code 246: Haqiqiy ta'lim (Teach You a Lesson)
# Process poster
src_poster = r"E:\Agent\Drama Bot\scripts\teach_lesson_poster.png"
dst_poster = r"E:\Agent\Drama Bot\posters\haqiqiy-talim-teach-you-a-lesson.jpg"

if os.path.exists(src_poster):
    im = Image.open(src_poster).convert("RGB")
    im_resized = im.resize((600, 900), Image.Resampling.LANCZOS)
    im_sharp = im_resized.filter(ImageFilter.UnsharpMask(radius=1.2, percent=110, threshold=2))
    im_sharp.save(dst_poster, "JPEG", quality=95, optimize=True)
    print("Saved Teach You a Lesson poster to:", dst_poster)

c.execute("""
    UPDATE doramas SET
        title = 'Haqiqiy taʼlim (Teach You a Lesson)',
        aliases = 'Teach You a Lesson, True Education, Get Schooled, 참교육, Haqiqiy talim, Kim Mu-yeol, Jin Ki-joo, Lee Sung-min',
        actors = 'Kim Mu-yeol, Jin Ki-joo, Lee Sung-min, Pyo Ji-hoon',
        year = 2026,
        genre = 'Maktab, Jangari, Huquq, Ekshn',
        description = 'O''quvchilar va o''qituvchilar huquqlarini himoya qilish byurosi inspektorlari maktablardagi zo''ravonlik va jinoyatchilikka qarshi ayovsiz kurashadi.',
        poster_url = 'posters/haqiqiy-talim-teach-you-a-lesson.jpg'
    WHERE code = 246
""")
print("Updated Code 246 in DB")

# 2. Clean Code 215: Ta'lim guruhi (Study Group)
c.execute("""
    UPDATE doramas SET
        title = 'Ta''lim guruhi (Study Group)',
        aliases = 'Study Group, Talim guruhi, O''quv guruhi, 스터디그룹, Hwang Min-hyun, Han Ji-eun',
        actors = 'Hwang Min-hyun, Han Ji-eun, Cha Woo-min, Lee Jong-hyun',
        year = 2025,
        genre = 'Jangari, Maktab, Jang san''ati, Komediya',
        description = 'Faqat o''qishni xohlaydigan, biroq do''stlarini himoya qilish uchun kuchli jangga kirishadigan Yun Ga-min va uning o''quv guruhi sarguzashtlari.'
    WHERE code = 215
""")
print("Updated Code 215 in DB")

# 3. Clean Code 419: Mo'jizakor telbalar (The WONDERfools)
c.execute("""
    UPDATE doramas SET
        title = 'Mo’jizakor telbalar (The WONDERfools)',
        aliases = 'Mo’jizakor telbalar, The WONDERfools, Wonderfools, 원더풀스, Park Eun-bin, Cha Eun-woo, Choi Dae-hoon, Im Sung-jae',
        actors = 'Park Eun-bin, Cha Eun-woo, Choi Dae-hoon, Im Sung-jae, Kim Hae-sook',
        year = 2026,
        genre = 'Komediya, Fantastika, Sarguzasht, Jangari',
        description = '1999-yil sexi-oxirida kutilmaganda g''ayritabiiy qobiliyatlarga ega bo''lib qolgan mahalliy telbalar shahar tinchligini himoya qilishga kirishadilar.',
        poster_url = 'posters/code_419.jpg'
    WHERE code = 419
""")
print("Updated Code 419 in DB")

conn.commit()
conn.close()
print("All DB updates committed!")
