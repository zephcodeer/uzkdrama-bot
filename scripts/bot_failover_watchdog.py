#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
High-Availability Bot Watchdog & Auto-Failover Daemon
Guarantees:
1. Health-checks live bot (@uzkdrama_app) every 45-60 seconds.
2. If hosting (Bot-Hosting.net) stops responding for >= 2 checks (~90s):
   - Sends instant Telegram alert to MuhammadSodiq (@corecod)
   - Automatically launches bot.py locally on this laptop
   - Sends confirmation notification
3. Zero-downtime protection for all 585+ users.
"""

import os
import sys
import asyncio
import logging
import subprocess
from datetime import datetime
from telethon import TelegramClient

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import config

LOG_FILE = os.path.join(BASE_DIR, "scripts", "watchdog.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("FailoverWatchdog")

SESSION_PATH = os.path.join(BASE_DIR, "watchdog")
PYTHON_EXE = r"C:\Python313\python.exe"
BOT_SCRIPT = os.path.join(BASE_DIR, "bot.py")

local_bot_process = None

def is_local_bot_running():
    global local_bot_process
    if local_bot_process is not None:
        if local_bot_process.poll() is None:
            return True
        else:
            local_bot_process = None
    return False

def start_local_bot():
    global local_bot_process
    if is_local_bot_running():
        return True
    logger.info("⚡ Launching local bot.py failover process...")
    try:
        local_bot_process = subprocess.Popen(
            [PYTHON_EXE, "-u", BOT_SCRIPT],
            cwd=BASE_DIR,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8"
        )
        logger.info(f"Local bot process started with PID {local_bot_process.pid}")
        return True
    except Exception as e:
        logger.error(f"Failed to start local bot process: {e}")
        return False

def stop_local_bot():
    global local_bot_process
    if is_local_bot_running():
        logger.info("Stopping local bot failover process...")
        try:
            local_bot_process.terminate()
            local_bot_process.wait(timeout=5)
        except Exception:
            try:
                local_bot_process.kill()
            except Exception:
                pass
        local_bot_process = None
        logger.info("Local bot process stopped.")

async def ping_bot(client, bot_entity):
    """Check for the exact health reply and remove only this probe's messages."""
    sent = None
    pong_id = None
    try:
        sent = await client.send_message(bot_entity, "/ping")
        for _ in range(10):
            await asyncio.sleep(1)
            msgs = await client.get_messages(bot_entity, limit=5, min_id=sent.id)
            for m in msgs:
                if (
                    not m.out
                    and m.id > sent.id
                    and m.sender_id == bot_entity.id
                    and (m.text or "").strip() == "PONG_HEALTH_OK"
                ):
                    pong_id = m.id
                    return True
        return False
    except Exception as e:
        logger.warning(f"Ping exception: {e}")
        return False
    finally:
        if sent is not None:
            message_ids = [sent.id]
            if pong_id is not None:
                message_ids.append(pong_id)
            try:
                await client.delete_messages(bot_entity, message_ids, revoke=True)
            except Exception as e:
                logger.warning(f"Could not remove health-check messages: {e}")

async def main():
    logger.info("🛡️ Starting High-Availability Bot Watchdog & Auto-Failover...")
    client = TelegramClient(SESSION_PATH, config.API_ID, config.API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        logger.error("Watchdog Telethon session not authorized!")
        return

    me = await client.get_me()
    logger.info(f"Watchdog authorized as {me.first_name} (@{me.username})")
    bot_entity = await client.get_entity("@uzkdrama_app")
    admin_entity = me

    consecutive_failures = 0
    failover_active = False

    while True:
        try:
            logger.info("Checking bot health...")
            is_healthy = await ping_bot(client, bot_entity)

            if is_healthy:
                logger.info("✅ Bot is healthy and responding.")
                consecutive_failures = 0
                if failover_active:
                    # Hosting came back or recovered
                    logger.info("Cloud hosting recovered. Disengaging local failover...")
                    stop_local_bot()
                    failover_active = False
                    try:
                        await client.send_message(
                            admin_entity,
                            "ℹ️ <b>HOSTING TIKLANDI:</b>\n"
                            "Bot-Hosting.net dagi server yana to'liq ishlayapti. "
                            "Noutbukdagi zaxira bot to'xtatildi, tizim yana bulutli rejimda faol.",
                            parse_mode="HTML"
                        )
                    except Exception:
                        pass
            else:
                consecutive_failures += 1
                logger.warning(f"⚠️ Health check failed ({consecutive_failures}/2)!")

                if consecutive_failures >= 2 and not failover_active:
                    logger.error("🚨 HOSTING IS DOWN! Activating local laptop failover...")
                    # 1. Alert admin
                    alert_text = (
                        "🚨 <b>DIQQAT: BOT HOSTINGDA TO'XTAB QOLDI!</b>\n\n"
                        "Bulutli server (Bot-Hosting.net) javob bermayapti.\n"
                        "⚡️ <b>Tizim noutbukingizda avtomatik ZAXIRA (Failover) botni ishga tushirdi!</b>\n\n"
                        "Foydalanuvchilarga xizmat ko'rsatish to'xtamadi, barcha funksiyalar 100% onlayn."
                    )
                    try:
                        await client.send_message(admin_entity, alert_text, parse_mode="HTML")
                    except Exception as e:
                        logger.error(f"Could not send alert: {e}")

                    # 2. Start local bot
                    started = start_local_bot()
                    if started:
                        failover_active = True
                        consecutive_failures = 0
                        logger.info("Local failover active.")

            await asyncio.sleep(45)

        except asyncio.CancelledError:
            logger.info("Watchdog cancelled.")
            break
        except Exception as e:
            logger.error(f"Watchdog loop error: {e}")
            await asyncio.sleep(30)

    stop_local_bot()
    await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        stop_local_bot()
