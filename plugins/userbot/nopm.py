"""
RadioPlayerV3, Telegram Voice Chat Bot
Copyright (c) 2021  Asm Safone <https://github.com/AsmSafone>

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

import asyncio
from pyrogram import Client, filters
from utils import USERNAME
from config import Config
from pyrogram.errors import BotInlineDisabled

REPLY_MESSAGE=Config.REPLY_MESSAGE

@Client.on_message(filters.private & filters.incoming & ~filters.bot & ~filters.service & ~filters.me & ~filters.edited)
async def reply(client, message): 
    try:
        inline = await client.get_inline_bot_results(USERNAME, "SAF_ONE")
        await client.send_inline_bot_result(
            message.chat.id,
            query_id=inline.query_id,
            result_id=inline.results[0].id,
            hide_via=True
            )
    except BotInlineDisabled:
            print(f"Inline Mode for @{USERNAME} is not enabled. Enable it from @Botfather to turn on PM Guard !")
            await message.reply_text(f"{REPLY_MESSAGE}\n\n<b>© Powered By : \n@AsmSafone | @AsmSupport 👑</b>")
    except Exception as e:
        print(e)
        pass
