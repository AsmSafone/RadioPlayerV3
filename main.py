"""
RadioPlayerV2, Telegram Voice Chat Userbot
Copyright (C) 2021  Asm Safone
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.
This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.
You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>
"""

from pyrogram import Client, idle, filters
import os
from threading import Thread
import sys
from config import Config
from utils.vc import mp
import asyncio


CHAT=Config.CHAT
bot = Client(
    "RadioPlayer",
    Config.API_ID,
    Config.API_HASH,
    bot_token=Config.BOT_TOKEN,
    plugins=dict(root="plugins")
)
async def main():
    async with bot:
        await mp.startupradio()
        await asyncio.sleep(5)
        await mp.startupradio()

def stop_and_restart():
        bot.stop()
        os.execl(sys.executable, sys.executable, *sys.argv)
    
bot.run(main())
bot.start()
@bot.on_message(filters.command("restart") & filters.user(Config.ADMINS))
def restart(client, message):
    message.reply_text("**Restarting... Join @AsmSafone!**")
    Thread(
        target=stop_and_restart
        ).start()

idle()
bot.stop()
