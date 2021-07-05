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

import os
from config import Config
from datetime import datetime, timedelta
from pyrogram import Client, filters, emoji
from pyrogram.methods.messages.download_media import DEFAULT_DOWNLOAD_DIR
from pyrogram.types import Message
from utils.vc import mp
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

ADMINS=Config.ADMINS
CHAT=Config.CHAT
LOG_GROUP=Config.LOG_GROUP


async def current_vc_filter(_, __, m: Message):
    group_call = mp.group_call
    if group_call.is_connected:
        return True
    else:
        return False


current_vc = filters.create(current_vc_filter)


@Client.on_message((current_vc & filters.command("play") | (current_vc & filters.audio & filters.private))
)
async def play_track(client, m: Message):
    group_call = mp.group_call
    playlist = mp.playlist
    if m.audio:
        m_audio = m
    elif m.reply_to_message and m.reply_to_message.audio:
        m_audio = m.reply_to_message
    else:
        chat_id=m.from_user.id
        await client.send_message(text="You Didn't Gave Me Anything To Play. Send Me An Audio File or Reply /play To An Audio File!", chat_id=chat_id)
        if LOG_GROUP:
            await mp.send_playlist()
        return
    if playlist and playlist[-1].audio.file_unique_id \
            == m_audio.audio.file_unique_id:
        await m.reply_text(f"{emoji.ROBOT} **Already Added!**")
        return
    # add to playlist
    playlist.append(m_audio)
    if len(playlist) == 1:
        m_status = await m.reply_text(
            f"{emoji.INBOX_TRAY} **Downloading & Transcoding...**"
        )
        await mp.download_audio(playlist[0])
        group_call.input_filename = os.path.join(
            client.workdir,
            DEFAULT_DOWNLOAD_DIR,
            f"{playlist[0].audio.file_unique_id}.raw"
        )
        await mp.update_start_time()
        await m_status.delete()
        print(f"- START PLAYING: {playlist[0].audio.title}")
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
    await m.reply_text(pl)
    for track in playlist[:2]:
        await mp.download_audio(track)
    if not m.audio:
        await m.delete()
    if LOG_GROUP:
        await mp.send_playlist()


@Client.on_message(current_vc & filters.command("current"))
async def show_current_playing_time(_, m: Message):
    start_time = mp.start_time
    playlist = mp.playlist
    if not start_time:
        await m.reply_text(f"{emoji.PLAY_BUTTON} **Nothing Playing!**")
        return
    utcnow = datetime.utcnow().replace(microsecond=0)
    #if mp.msg.get('current') is not None:
        #await mp.msg['current'].delete()
    await m.reply_text(
        f"{emoji.PLAY_BUTTON}  {utcnow - start_time} / "
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

@Client.on_message(current_vc & filters.command("skip") & filters.user(ADMINS))
async def skip_track(_, m: Message):
    playlist = mp.playlist
    if len(m.command) == 1:
        await mp.skip_current_playing()
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
        await m.reply_text(pl)
    else:
        try:
            items = list(dict.fromkeys(m.command[1:]))
            items = [int(x) for x in items if x.isdigit()]
            items.sort(reverse=True)
            text = []
            for i in items:
                if 2 <= i <= (len(playlist) - 1):
                    audio = f"{playlist[i].audio.title}"
                    playlist.pop(i)
                    text.append(f"{emoji.WASTEBASKET} {i}. **{audio}**")
                else:
                    text.append(f"{emoji.CROSS_MARK} {i}")
            await m.reply_text("\n".join(text))
            if not playlist:
                pl = f"{emoji.NO_ENTRY} **Empty Playlist!**"
            else:
                if len(playlist) == 1:
                    pl = f"{emoji.REPEAT_SINGLE_BUTTON} **Playlist**:\n"
                else:
                    pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n"
                pl += "\n".join([
                    f"**{i}**. **{x.audio.title}**"
                    for i, x in enumerate(playlist)])
            await m.reply_text(pl)
            if LOG_GROUP:
                await mp.send_playlist()
        except (ValueError, TypeError):
            await m.reply_text(f"{emoji.NO_ENTRY} **Invalid Input!**",
                                       disable_web_page_preview=True)


@Client.on_message(filters.command("join") & filters.user(ADMINS))
async def join_group_call(client, m: Message):
    group_call = mp.group_call
    if group_call.is_connected:
        await m.reply_text(f"{emoji.ROBOT} **Already Joined To The Voice Chat!**")
        return
    await mp.start_call()
    #await group_call.start(CHAT)
    chat = await client.get_chat(CHAT)
    await m.reply_text(f"{emoji.CHECK_MARK_BUTTON} **Joined The Voice Chat In {chat.title} Successfully!**")


@Client.on_message(current_vc
                   & filters.command("leave") & filters.user(ADMINS))
async def leave_voice_chat(_, m: Message):
    group_call = mp.group_call
    mp.playlist.clear()
    group_call.input_filename = ''
    await group_call.stop()
    await m.reply_text(f"{emoji.CROSS_MARK_BUTTON} **Left From The Voice Chat Successfully!**")


@Client.on_message(filters.command("vc") & filters.user(ADMINS))
async def list_voice_chat(client, m: Message):
    group_call = mp.group_call
    if group_call.is_connected:
        chat_id = int("-100" + str(group_call.full_chat.id))
        chat = await client.get_chat(chat_id)
        await m.reply_text(
            f"{emoji.MUSICAL_NOTES} **Currently Joined In**:\n"
            f"- **{chat.title}**"
        )
    else:
        await m.reply_text(emoji.NO_ENTRY
                                   + "**Didn't Joined Any Voice Chat Yet!**")


@Client.on_message(current_vc
                   & filters.command("stop") & filters.user(ADMINS))
async def stop_playing(_, m: Message):
    group_call = mp.group_call
    group_call.stop_playout()
    await m.reply_text(f"{emoji.STOP_BUTTON} **Stopped Playing!**")
    await mp.update_start_time(reset=True)
    mp.playlist.clear()


@Client.on_message(current_vc
                   & filters.command("replay") & filters.user(ADMINS))
async def restart_playing(_, m: Message):
    group_call = mp.group_call
    if not mp.playlist:
        return
    group_call.restart_playout()
    await mp.update_start_time()
    await m.reply_text(
        f"{emoji.COUNTERCLOCKWISE_ARROWS_BUTTON}  "
        "**Playing From The Beginning...**"
    )


@Client.on_message(current_vc
                   & filters.command("pause") & filters.user(ADMINS))
async def pause_playing(_, m: Message):
    mp.group_call.pause_playout()
    await mp.update_start_time(reset=True)
    reply = await m.reply_text(f"{emoji.PLAY_OR_PAUSE_BUTTON} **Paused Playing!**",
                               quote=False)
    mp.msg['pause'] = reply



@Client.on_message(current_vc
                   & filters.command("resume") & filters.user(ADMINS))
async def resume_playing(_, m: Message):
    mp.group_call.resume_playout()
    await m.reply_text(f"{emoji.PLAY_OR_PAUSE_BUTTON} **Resumed Playing!**",
                               quote=False)
    if mp.msg.get('pause') is not None:
        await mp.msg['pause'].delete()

@Client.on_message(current_vc
                   & filters.command("clean") & filters.user(ADMINS))
async def clean_raw_pcm(client, m: Message):
    download_dir = os.path.join(client.workdir, DEFAULT_DOWNLOAD_DIR)
    all_fn: list[str] = os.listdir(download_dir)
    for track in mp.playlist[:2]:
        track_fn = f"{track.audio.file_unique_id}.raw"
        if track_fn in all_fn:
            all_fn.remove(track_fn)
    count = 0
    if all_fn:
        for fn in all_fn:
            if fn.endswith(".raw"):
                count += 1
                os.remove(os.path.join(download_dir, fn))
    await m.reply_text(f"{emoji.WASTEBASKET} **Cleaned {count} Files!**")


@Client.on_message(current_vc
                   & filters.command("mute") & filters.user(ADMINS))
async def mute(_, m: Message):
    group_call = mp.group_call
    group_call.set_is_mute(True)
    await m.reply_text(f"{emoji.MUTED_SPEAKER} **User Muted!**")


@Client.on_message(current_vc
                   & filters.command("unmute") & filters.user(ADMINS))
async def unmute(_, m: Message):
    group_call = mp.group_call
    group_call.set_is_mute(False)
    await m.reply_text(f"{emoji.SPEAKER_MEDIUM_VOLUME} **User Unmuted!**")

@Client.on_message(filters.command("playlist"))
async def playlist(_, m: Message):
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
    await m.reply_text(pl)
