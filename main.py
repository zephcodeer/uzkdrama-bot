import os
import sys

# Ensure current directory is in sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import bot

if __name__ == "__main__":
    asyncio.run(bot.main())
