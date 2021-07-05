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

from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from pyrogram import Client, emoji
from datetime import datetime, timedelta
from utils.vc import mp

@Client.on_callback_query()
async def cb_handler(client: Client, query: CallbackQuery):
    if query.data == "replay":
        group_call = mp.group_call
        if not mp.playlist:
            return
        group_call.restart_playout()
        await mp.update_start_time()
        start_time = mp.start_time
        playlist = mp.playlist
        if not start_time:
            await query.edit_message_text(f"{emoji.PLAY_BUTTON} **Nothing Playing!**")
            return
        utcnow = datetime.utcnow().replace(microsecond=0)
        if mp.msg.get('current') is not None:
            playlist=mp.playlist
            if not playlist:
                pl = f"{emoji.NO_ENTRY} **Empty Playlist!**"
            else:
                if len(playlist) == 1:
                    pl = f"{emoji.REPEAT_SINGLE_BUTTON} **Playlist**:\n"
                else:
                    pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n"
                pl += "\n".join([
                    f"**{i}**. **{x.audio.title}**"
                    for i, x in enumerate(playlist)
                    ])
            await mp.msg['current'].delete()
            mp.msg['current'] = await playlist[0].reply_text(
                f"{pl}\n\n{emoji.PLAY_BUTTON}  {utcnow - start_time} / "
                f"{timedelta(seconds=playlist[0].audio.duration)}",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("🔄", callback_data="replay"),
                            InlineKeyboardButton("⏸", callback_data="pause"),
                            InlineKeyboardButton("⏭", callback_data="skip")
                            
                        ],
                    ]
                )
            )

    elif query.data == "pause":
        mp.group_call.pause_playout()
        await mp.update_start_time(reset=True)
        playlist = mp.playlist
        if not playlist:
            pl = f"{emoji.NO_ENTRY} **Empty Playlist!**"
        else:
            if len(playlist) == 1:
                pl = f"{emoji.REPEAT_SINGLE_BUTTON} **Playlist**:\n"
            else:
                pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n"
            pl += "\n".join([
                f"**{i}**. **{x.audio.title}**"
                for i, x in enumerate(playlist)
                ])
        reply = await query.edit_message_text(f"{emoji.PLAY_OR_PAUSE_BUTTON} **Paused Playing!**\n\n{pl}",
        reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("🔄", callback_data="replay"),
                            InlineKeyboardButton("▶️", callback_data="resume"),
                            InlineKeyboardButton("⏭", callback_data="skip")
                            
                        ],
                    ]
                )
            )

    
    elif query.data == "resume":
        mp.group_call.resume_playout()
        playlist=mp.playlist
        if not playlist:
            pl = f"{emoji.NO_ENTRY} **Empty Playlist!**"
        else:
            if len(playlist) == 1:
                pl = f"{emoji.REPEAT_SINGLE_BUTTON} **Playlist**:\n"
            else:
                pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n"
            pl += "\n".join([
                f"**{i}**. **{x.audio.title}**"
                for i, x in enumerate(playlist)
                ])
        await query.edit_message_text(f"{emoji.PLAY_OR_PAUSE_BUTTON} **Resumed Playing!**\n\n{pl}",
        reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton("🔄", callback_data="replay"),
                            InlineKeyboardButton("⏸", callback_data="pause"),
                            InlineKeyboardButton("⏭", callback_data="skip")
                            
                        ],
                    ]
                )
            )

    elif query.data=="skip":
        playlist = mp.playlist
        await mp.skip_current_playing()
        if not playlist:
            pl = f"{emoji.NO_ENTRY} **Empty Playlist!**"
        else:
            if len(playlist) == 1:
                pl = f"{emoji.REPEAT_SINGLE_BUTTON} **Playlist**:\n"
            else:
                pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n"
            pl += "\n".join([
                f"**{i}**. **{x.audio.title}**"
                for i, x in enumerate(playlist)
                ])

        try:
            await query.edit_message_text(f"⏭ **Skipped Track!**\n\n{pl}",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("🔄", callback_data="replay"),
                        InlineKeyboardButton("⏸", callback_data="pause"),
                        InlineKeyboardButton("⏭", callback_data="skip")
                            
                    ],
                ]
            )
        )
        except:
            pass
    elif query.data=="help":
        await query.edit_message_text("🙋‍♂️ **Hi Bruh**, \nJust Send Me An Audio File To Play. You Can Use @SafoneMusicBot To Get Audio Files! 😌\n\nCheck /help To Know More ...",
        reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Close 🔐", callback_data="close"),
                    ],
                ]
            )
        )
        
    elif query.data=="close":
        await query.message.delete()

