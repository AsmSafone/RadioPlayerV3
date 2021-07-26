"""
RadioPlayer, Telegram Voice Chat Bot
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

from datetime import datetime
from time import time
from config import Config
from pyrogram import Client, filters, emoji
from pyrogram.types import Message

START_TIME = datetime.utcnow()
START_TIME_ISO = START_TIME.replace(microsecond=0).isoformat()
TIME_DURATION_UNITS = (
    ('week', 60 * 60 * 24 * 7),
    ('day', 60 * 60 * 24),
    ('hour', 60 * 60),
    ('min', 60),
    ('sec', 1)
)

self_or_contact_filter = filters.create(
    lambda _, __, message:
    (message.from_user and message.from_user.is_contact) or message.outgoing
)


async def _human_time_duration(seconds):
    if seconds == 0:
        return 'inf'
    parts = []
    for unit, div in TIME_DURATION_UNITS:
        amount, seconds = divmod(int(seconds), div)
        if amount > 0:
            parts.append('{} {}{}'
                         .format(amount, unit, "" if amount == 1 else "s"))
    return ', '.join(parts)


@Client.on_message(filters.text & self_or_contact_filter & ~filters.edited & ~filters.bot & filters.regex("^.ping$"))
async def ping_pong(_, m: Message):
    start = time()
    m_reply = await m.reply_text("Pong!")
    delta_ping = time() - start
    await m_reply.edit_text(
        f"{emoji.ROBOT} **Ping** : `{delta_ping * 1000:.3f} ms`"
    )


@Client.on_message(filters.text & self_or_contact_filter & ~filters.edited & ~filters.bot & filters.regex("^.uptime$"))
async def get_uptime(_, m: Message):
    current_time = datetime.utcnow()
    uptime_sec = (current_time - START_TIME).total_seconds()
    uptime = await _human_time_duration(int(uptime_sec))
    await m.reply_text(
        f"{emoji.ROBOT} Radio Player V3.0\n"
        f"- Uptime: `{uptime}`\n"
        f"- Restarted: `{START_TIME_ISO}`"
    )
