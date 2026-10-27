# 🎬 UzKDrama Telegram Bot

O'zbek tilidagi eng yirik va sifatli koreys doramalari katalogi uchun Telegram bot (@uzkdrama_app).

## 🚀 Texnologiyalar
- **Python 3.11+**
- **Aiogram 3.26+** (Asinxron Telegram Bot freymvorki)
- **aiosqlite** (Asinxron SQLite ma'lumotlar bazasi)
- **Pillow** (Rasm va posterlarni qayta ishlash)

---

## 📂 Loyiha Tuzilishi
```
├── bot.py                # Asosiy bot fayli va handlerlar
├── config.py             # Sozlamalar va .env o'qish
├── database.py           # SQLite ma'lumotlar bazasi boshqaruvi
├── emojis.py             # Premium animatsiyali emojilar
├── keyboards.py          # Dinamik menyu va tugmalar
├── doramas.db            # 69 ta dorama va 939 ta qism bazasi
├── posters/              # Rasmiy vertikal HD posterlar (69 ta)
├── requirements.txt      # Kutubxonalar ro'yxati
├── .env.example          # Muhit o'zgaruvchilari namunasi
└── README.md             # Qo'llanma
```

---

## ⚙️ O'rnatish va Ishga Tushirish (Mahalliy)

1. **Repozitoriyni klonlash:**
   ```bash
   git clone https://github.com/zephcodeer/uzkdrama-bot.git
   cd uzkdrama-bot
   ```

2. **Kutubxonalarni o'rnatish:**
   ```bash
   pip install -r requirements.txt
   ```

3. **`.env` faylini yaratish:**
   `.env.example` dan nusxa olib `.env` yarating va tokenlarni kiriting:
   ```env
   BOT_TOKEN=your_bot_token_here
   STORAGE_CHANNEL_ID=-100xxxxxxxxxx
   ADMIN_ID=your_telegram_id
   OMDB_API_KEY=bd182e04
   ```

4. **Botni ishga tushirish:**
   ```bash
   python bot.py
   ```

---

## 🌐 Bot-Hosting.net da 24/7 Ishga Tushirish

1. **Bot-Hosting.net** panelida yangi Python bot serverini yarating.
2. **Startup** bo'limida:
   - **Git Repo Address:** `https://github.com/zephcodeer/uzkdrama-bot`
   - **Branch:** `main`
3. **Files** bo'limida `.env` faylini yaratib, o'z tokenlaringizni joylang.
4. **Console** bo'limida **Start** tugmasini bosing! Bot avtomatik `requirements.txt` ni o'rnatib, 24/7 ishga tushadi.
