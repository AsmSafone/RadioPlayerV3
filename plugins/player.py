"""
RadioPlayer, Telegram Voice Chat Bot
Copyright (c) 2021  Asm Safone

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
import re
import signal
from youtube_dl import YoutubeDL
from config import Config
from pyrogram import Client, filters, emoji
from pyrogram.methods.messages.download_media import DEFAULT_DOWNLOAD_DIR
from pyrogram.types import Message
from utils import mp, RADIO, USERNAME, FFMPEG_PROCESSES
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from youtube_search import YoutubeSearch
from pyrogram import Client

LOG_GROUP=Config.LOG_GROUP
ADMIN_ONLY=Config.ADMIN_ONLY
DURATION_LIMIT = Config.DURATION_LIMIT
playlist=Config.playlist
msg = Config.msg
ADMINS=Config.ADMINS
CHAT=Config.CHAT
LOG_GROUP=Config.LOG_GROUP
playlist=Config.playlist

@Client.on_message(filters.command(["play", f"play@{USERNAME}"]) & (filters.chat(CHAT) | filters.private) | filters.audio & filters.private)
async def yplay(_, message: Message):
    if ADMIN_ONLY == "Y":
        admins=[1316963576]
        grpadmins=await _.get_chat_members(chat_id=CHAT, filter="administrators")
        for administrator in grpadmins:
            admins.append(administrator.user.id)
        if message.from_user.id not in admins:
            m=await message.reply_text("**You're Not Allowed To Play** 🤣!")
            await mp.delete(m)
            await message.delete()
            return
    type=""
    yturl=""
    ysearch=""
    if message.audio:
        type="audio"
        m_audio = message
    elif message.reply_to_message and message.reply_to_message.audio:
        type="audio"
        m_audio = message.reply_to_message
    else:
        if message.reply_to_message:
            link=message.reply_to_message.text
            regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
            match = re.match(regex,link)
            if match:
                type="youtube"
                yturl=link
        elif " " in message.text:
            text = message.text.split(" ", 1)
            query = text[1]
            regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
            match = re.match(regex,query)
            if match:
                type="youtube"
                yturl=query
            else:
                type="query"
                ysearch=query
        else:
            d=await message.reply_text("❗️ __You Didn't Gave Me Anything To Play, Send Me An Audio File or Reply /play To An Audio File!__")
            await mp.delete(d)
            await message.delete()
            return
    user=f"[{message.from_user.first_name}](tg://user?id={message.from_user.id})"
    group_call = mp.group_call
    if type=="audio":
        if round(m_audio.audio.duration / 60) > DURATION_LIMIT:
            d=await message.reply_text(f"❌ __Audios Longer Than {DURATION_LIMIT} Minute(s) Aren't Allowed, The Provided Audio Is {round(m_audio.audio.duration/60)} Minute(s)!__")
            await mp.delete(d)
            await message.delete()
            return
        if playlist and playlist[-1][2] \
                == m_audio.audio.file_id:
            d=await message.reply_text(f"{emoji.ROBOT} **Already Added To Playlist!**")
            await mp.delete(d)
            await message.delete()
            return
        data={1:m_audio.audio.title, 2:m_audio.audio.file_id, 3:"telegram", 4:user}
        playlist.append(data)
        if len(playlist) == 1:
            m_status = await message.reply_text(
                f"{emoji.INBOX_TRAY} **Downloading & Transcoding** ..."
            )
            await mp.download_audio(playlist[0])
            if 1 in RADIO:
                if group_call:
                    group_call.input_filename = ''
                    RADIO.remove(1)
                    RADIO.add(0)
                process = FFMPEG_PROCESSES.get(CHAT)
                if process:
                    process.send_signal(signal.SIGTERM)
            if not group_call.is_connected:
                await mp.start_call()
            file=playlist[0][1]
            group_call.input_filename = os.path.join(
                _.workdir,
                DEFAULT_DOWNLOAD_DIR,
                f"{file}.raw"
            )

            await m_status.delete()
            print(f"- START PLAYING: {playlist[0][1]}")
        if not playlist:
            pl = f"{emoji.NO_ENTRY} **Empty Playlist!**"
        else:   
            pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n" + "\n".join([
                f"**{i}**. **{x[1]}**\n  **Requested By:** {x[4]}"
                for i, x in enumerate(playlist)
                ])
        for track in playlist[:2]:
            await mp.download_audio(track)
        if message.chat.type == "private":
            await message.reply_text(pl)        
        elif LOG_GROUP:
            await mp.send_playlist()
        else:
            k=await message.reply_text(pl)
            await mp.delete(k)
    if type=="youtube" or type=="query":
        if type=="youtube":
            msg = await message.reply_text("**Searching On YouTube** ...🔍")
            url=yturl
        elif type=="query":
            try:
                msg = await message.reply_text("**Searching On YouTube** ...🔍")
                ytquery=ysearch
                results = YoutubeSearch(ytquery, max_results=1).to_dict()
                url = f"https://youtube.com{results[0]['url_suffix']}"
                title = results[0]["title"][:40]
            except Exception as e:
                await msg.edit(
                    "**Literary Found Noting**!\nTry Searching On Inline 😉!"
                )
                print(str(e))
                return
        else:
            return
        ydl_opts = {
            "geo-bypass": True,
            "nocheckcertificate": True
        }
        ydl = YoutubeDL(ydl_opts)
        info = ydl.extract_info(url, False)
        duration = round(info["duration"] / 60)
        title= info["title"]
        if int(duration) > DURATION_LIMIT:
            k=await message.reply_text(f"❌ __Videos Longer Than {DURATION_LIMIT} Minute(s) Aren't Allowed, The Provided Video Is {duration} Minute(s)!__")
            await mp.delete(k)
            await message.delete()
            return

        data={1:title, 2:url, 3:"youtube", 4:user}
        playlist.append(data)
        group_call = mp.group_call
        client = group_call.client
        if len(playlist) == 1:
            m_status = await msg.edit(
                f"{emoji.INBOX_TRAY} **Downloading & Transcoding** ..."
            )
            await mp.download_audio(playlist[0])
            if 1 in RADIO:
                if group_call:
                    group_call.input_filename = ''
                    RADIO.remove(1)
                    RADIO.add(0)
                process = FFMPEG_PROCESSES.get(CHAT)
                if process:
                    process.send_signal(signal.SIGTERM)
            if not group_call.is_connected:
                await mp.start_call()
            file=playlist[0][1]
            group_call.input_filename = os.path.join(
                client.workdir,
                DEFAULT_DOWNLOAD_DIR,
                f"{file}.raw"
            )

            await m_status.delete()
            print(f"- START PLAYING: {playlist[0][1]}")
        else:
            await msg.delete()
        if not playlist:
            pl = f"{emoji.NO_ENTRY} **Empty Playlist!**"
        else:
            pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n" + "\n".join([
                f"**{i}**. **{x[1]}**\n  **Requested By:** {x[4]}"
                for i, x in enumerate(playlist)
                ])
        for track in playlist[:2]:
            await mp.download_audio(track)
        if message.chat.type == "private":
            await message.reply_text(pl)
        if LOG_GROUP:
            await mp.send_playlist()
        else:
            k=await message.reply_text(pl)
            await mp.delete(k)
    await message.delete()


@Client.on_message(filters.command(["current", f"current@{USERNAME}"]) & (filters.chat(CHAT) | filters.private))
async def current(_, m: Message):
    if not playlist:
        k=await m.reply_text(f"{emoji.NO_ENTRY} **Nothing Is Playing!**")
        await mp.delete(k)
        await m.delete()
        return
    else:
        pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n" + "\n".join([
            f"**{i}**. **{x[1]}**\n  **Requested By:** {x[4]}"
            for i, x in enumerate(playlist)
            ])
    if m.chat.type == "private":
        await m.reply_text(
            pl,
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
    else:
        if msg.get('playlist') is not None:
            await msg['playlist'].delete()
        msg['playlist'] = await m.reply_text(
            pl,
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
    await m.delete()

@Client.on_message(filters.command(["skip", f"skip@{USERNAME}"]) & filters.user(ADMINS) & (filters.chat(CHAT) | filters.private))
async def skip_track(_, m: Message):
    group_call = mp.group_call
    if not group_call.is_connected:
        k=await m.reply_text(f"{emoji.NO_ENTRY} **Nothing Is Playing To Skip!**")
        await mp.delete(k)
        await m.delete()
        return
    if len(m.command) == 1:
        await mp.skip_current_playing()
        if not playlist:
            pl = f"{emoji.NO_ENTRY} **Empty Playlist!**"
        else:
            pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n" + "\n".join([
            f"**{i}**. **{x[1]}**\n  **Requested By:** {x[4]}"
            for i, x in enumerate(playlist)
            ])
        if m.chat.type == "private":
            await m.reply_text(pl)
        if LOG_GROUP:
            await mp.send_playlist()
        else:
            k=await m.reply_text(pl)
            await mp.delete(k)
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
            k=await m.reply_text("\n".join(text))
            await mp.delete(k)
            if not playlist:
                pl = f"{emoji.NO_ENTRY} **Empty Playlist!**"
            else:
                pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n" + "\n".join([
                    f"**{i}**. **{x[1]}**\n  **Requested By:** {x[4]}"
                    for i, x in enumerate(playlist)
                    ])
            if m.chat.type == "private":
                await m.reply_text(pl)
            if LOG_GROUP:
                await mp.send_playlist()
            else:
                k=await m.reply_text(pl)
                await mp.delete(k)
        except (ValueError, TypeError):
            k=await m.reply_text(f"{emoji.NO_ENTRY} **Invalid Input!**",
                                       disable_web_page_preview=True)
            await mp.delete(k)
    await m.delete()


@Client.on_message(filters.command(["join", f"join@{USERNAME}"]) & filters.user(ADMINS) & (filters.chat(CHAT) | filters.private))
async def join_group_call(client, m: Message):
    group_call = mp.group_call
    if group_call.is_connected:
        k=await m.reply_text(f"{emoji.ROBOT} **Already Joined To The Voice Chat!**")
        await mp.delete(k)
        await m.delete()
        return
    await mp.start_call()
    chat = await client.get_chat(CHAT)
    k=await m.reply_text(f"{emoji.CHECK_MARK_BUTTON} **Joined The Voice Chat In {chat.title} Successfully!**")
    await mp.delete(k)
    await m.delete()


@Client.on_message(filters.command(["leave", f"leave@{USERNAME}"]) & filters.user(ADMINS))
async def leave_voice_chat(_, m: Message):
    group_call = mp.group_call
    if not group_call.is_connected:
        k=await m.reply_text(f"{emoji.ROBOT} **Didn't Joined Any Voice Chat!**")
        await mp.delete(k)
        await m.delete()
        return
    playlist.clear()
    if 1 in RADIO:
        await mp.stop_radio()
    group_call.input_filename = ''
    await group_call.stop()
    k=await m.reply_text(f"{emoji.CROSS_MARK_BUTTON} **Left From The Voice Chat Successfully!**")
    await mp.delete(k)
    await m.delete()



@Client.on_message(filters.command(["stop", f"stop@{USERNAME}"]) & filters.user(ADMINS) & (filters.chat(CHAT) | filters.private))
async def stop_playing(_, m: Message):
    group_call = mp.group_call
    if not group_call.is_connected:
        k=await m.reply_text(f"{emoji.NO_ENTRY} **Nothing Is Playing To Stop!**")
        await mp.delete(k)
        await m.delete()
        return
    if 1 in RADIO:
        await mp.stop_radio()
    group_call.stop_playout()
    k=await m.reply_text(f"{emoji.STOP_BUTTON} **Stopped Playing!**")
    playlist.clear()
    await mp.delete(k)
    await m.delete()


@Client.on_message(filters.command(["replay", f"replay@{USERNAME}"]) & filters.user(ADMINS) & (filters.chat(CHAT) | filters.private))
async def restart_playing(_, m: Message):
    group_call = mp.group_call
    if not group_call.is_connected:
        k=await m.reply_text(f"{emoji.NO_ENTRY} **Nothing Is Playing To Replay!**")
        await mp.delete(k)
        await m.delete()
        return
    if not playlist:
        k=await m.reply_text(f"{emoji.NO_ENTRY} **Empty Playlist!**")
        await mp.delete(k)
        await m.delete()
        return
    group_call.restart_playout()
    k=await m.reply_text(
        f"{emoji.COUNTERCLOCKWISE_ARROWS_BUTTON}  "
        "**Playing From The Beginning...**"
    )
    await mp.delete(k)
    await m.delete()


@Client.on_message(filters.command(["pause", f"pause@{USERNAME}"]) & filters.user(ADMINS) & (filters.chat(CHAT) | filters.private))
async def pause_playing(_, m: Message):
    group_call = mp.group_call
    if not group_call.is_connected:
        k=await m.reply_text(f"{emoji.NO_ENTRY} **Nothing Is Playing To Pause!**")
        await mp.delete(k)
        await m.delete()
        return
    mp.group_call.pause_playout()
    k=await m.reply_text(f"{emoji.PLAY_OR_PAUSE_BUTTON} **Paused Playing!**",
                               quote=False)
    await mp.delete(k)
    await m.delete()



@Client.on_message(filters.command(["resume", f"resume@{USERNAME}"]) & filters.user(ADMINS) & (filters.chat(CHAT) | filters.private))
async def resume_playing(_, m: Message):
    if not mp.group_call.is_connected:
        k=await m.reply_text(f"{emoji.NO_ENTRY} **Nothing Is Paused To Resume!**")
        await mp.delete(k)
        await m.delete()
        return
    mp.group_call.resume_playout()
    k=await m.reply_text(f"{emoji.PLAY_OR_PAUSE_BUTTON} **Resumed Playing!**",
                               quote=False)
    await mp.delete(k)
    await m.delete()

@Client.on_message(filters.command(["clean", f"clean@{USERNAME}"]) & filters.user(ADMINS) & (filters.chat(CHAT) | filters.private))
async def clean_raw_pcm(client, m: Message):
    download_dir = os.path.join(client.workdir, DEFAULT_DOWNLOAD_DIR)
    all_fn: list[str] = os.listdir(download_dir)
    for track in playlist[:2]:
        track_fn = f"{track[1]}.raw"
        if track_fn in all_fn:
            all_fn.remove(track_fn)
    count = 0
    if all_fn:
        for fn in all_fn:
            if fn.endswith(".raw"):
                count += 1
                os.remove(os.path.join(download_dir, fn))
    k=await m.reply_text(f"{emoji.WASTEBASKET} **Cleaned {count} Files!**")
    await mp.delete(k)
    await m.delete()


@Client.on_message(filters.command(["mute", f"mute@{USERNAME}"]) & filters.user(ADMINS) & (filters.chat(CHAT) | filters.private))
async def mute(_, m: Message):
    group_call = mp.group_call
    if not group_call.is_connected:
        k=await m.reply_text(f"{emoji.NO_ENTRY} **Nothing Is Playing To Mute!**")
        await mp.delete(k)
        await m.delete()
        return
    group_call.set_is_mute(True)
    k=await m.reply_text(f"{emoji.MUTED_SPEAKER} **User Muted!**")
    await mp.delete(k)
    await m.delete()

@Client.on_message(filters.command(["unmute", f"unmute@{USERNAME}"]) & filters.user(ADMINS) & (filters.chat(CHAT) | filters.private))
async def unmute(_, m: Message):
    group_call = mp.group_call
    if not group_call.is_connected:
        k=await m.reply_text(f"{emoji.NO_ENTRY} **Nothing Is Muted To Unmute!**")
        await mp.delete(k)
        await m.delete()
        return
    group_call.set_is_mute(False)
    k=await m.reply_text(f"{emoji.SPEAKER_MEDIUM_VOLUME} **User Unmuted!**")
    await mp.delete(k)
    await m.delete()

@Client.on_message(filters.command(["playlist", f"playlist@{USERNAME}"]) & (filters.chat(CHAT) | filters.private))
async def show_playlist(_, m: Message):
    if not playlist:
        k=await m.reply_text(f"{emoji.NO_ENTRY} **Nothing Is Playing!**")
        await mp.delete(k)
        await m.delete()
        return
    else:
        pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n" + "\n".join([
            f"**{i}**. **{x[1]}**\n  **Requested By:** {x[4]}"
            for i, x in enumerate(playlist)
            ])
    if m.chat.type == "private":
        await m.reply_text(pl)
    else:
        if msg.get('playlist') is not None:
            await msg['playlist'].delete()
        msg['playlist'] = await m.reply_text(pl)
    await m.delete()

admincmds=["join", "unmute", "mute", "leave", "clean", "pause", "resume", "stop", "skip", "radio", "stopradio", "replay", "restart", f"join@{USERNAME}", f"unmute@{USERNAME}", f"mute@{USERNAME}", f"leave@{USERNAME}", f"clean@{USERNAME}", f"pause@{USERNAME}", f"resume@{USERNAME}", f"stop@{USERNAME}", f"skip@{USERNAME}", f"radio@{USERNAME}", f"stopradio@{USERNAME}", f"replay@{USERNAME}", f"restart@{USERNAME}"]

@Client.on_message(filters.command(admincmds) & ~filters.user(ADMINS) & (filters.chat(CHAT) | filters.private))
async def notforu(_, m: Message):
    k=await m.reply_sticker("CAACAgUAAxkBAAIN3GDlcLBuKEONOFSNt_Hdnf0kyeDYAALNAgACNJ70McB9A_E8NCvZHgQ")
    await mp.delete(k)
    await m.delete()

