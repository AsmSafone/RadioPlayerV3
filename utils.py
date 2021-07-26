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

import os
import signal
import wget
import ffmpeg
from pyrogram import emoji
from pyrogram.methods.messages.download_media import DEFAULT_DOWNLOAD_DIR
from pytgcalls import GroupCallFactory
from config import Config
from asyncio import sleep
from pyrogram import Client
from youtube_dl import YoutubeDL
from os import path

bot = Client(
    "RadioPlayerVC",
    Config.API_ID,
    Config.API_HASH,
    bot_token=Config.BOT_TOKEN
)
bot.start()
e=bot.get_me()
USERNAME=e.username

from user import USER

STREAM_URL=Config.STREAM_URL
CHAT=Config.CHAT
GROUP_CALLS = {}
FFMPEG_PROCESSES = {}
RADIO={6}
LOG_GROUP=Config.LOG_GROUP
DURATION_LIMIT=Config.DURATION_LIMIT
DELAY=Config.DELAY
playlist=Config.playlist
msg=Config.msg


ydl_opts = {
    "format": "bestaudio[ext=m4a]",
    "geo-bypass": True,
    "nocheckcertificate": True,
    "outtmpl": "downloads/%(id)s.%(ext)s",
}
ydl = YoutubeDL(ydl_opts)
def youtube(url: str) -> str:
    info = ydl.extract_info(url, False)
    duration = round(info["duration"] / 60)
    try:
        ydl.download([url])
    except Exception as e:
        print(e)
        pass
    return path.join("downloads", f"{info['id']}.{info['ext']}")

class MusicPlayer(object):
    def __init__(self):
        self.group_call = GroupCallFactory(USER, GroupCallFactory.MTPROTO_CLIENT_TYPE.PYROGRAM).get_file_group_call()

    async def send_playlist(self):
        if not playlist:
            pl = f"{emoji.NO_ENTRY} **Empty Playlist!**"
        else:       
            pl = f"{emoji.PLAY_BUTTON} **Playlist**:\n" + "\n".join([
                f"**{i}**. **{x[1]}**\n  - **Requested By:** {x[4]}\n"
                for i, x in enumerate(playlist)
            ])
        if msg.get('playlist') is not None:
            await msg['playlist'].delete()
        msg['playlist'] = await self.send_text(pl)

    async def skip_current_playing(self):
        group_call = self.group_call
        if not playlist:
            return
        if len(playlist) == 1:
            await mp.start_radio()
            return
        client = group_call.client
        download_dir = os.path.join(client.workdir, DEFAULT_DOWNLOAD_DIR)
        group_call.input_filename = os.path.join(
            download_dir,
            f"{playlist[1][1]}.raw"
        )
        # remove old track from playlist
        old_track = playlist.pop(0)
        print(f"- START PLAYING: {playlist[0][1]}")
        if LOG_GROUP:
            await self.send_playlist()
        os.remove(os.path.join(
            download_dir,
            f"{old_track[1]}.raw")
        )
        if len(playlist) == 1:
            return
        await self.download_audio(playlist[1])

    async def send_text(self, text):
        group_call = self.group_call
        client = group_call.client
        chat_id = LOG_GROUP
        message = await bot.send_message(
            chat_id,
            text,
            disable_web_page_preview=True,
            disable_notification=True
        )
        return message

    async def download_audio(self, song):
        group_call = self.group_call
        client = group_call.client
        raw_file = os.path.join(client.workdir, DEFAULT_DOWNLOAD_DIR,
                                f"{song[1]}.raw")
        #if os.path.exists(raw_file):
            #os.remove(raw_file)
        if not os.path.isfile(raw_file):
            # credits: https://t.me/c/1480232458/6825
            #os.mkfifo(raw_file)
            if song[3] == "telegram":
                original_file = await bot.download_media(f"{song[2]}")
            elif song[3] == "youtube":
                original_file = youtube(song[2])
            else:
                original_file=wget.download(song[2])
            ffmpeg.input(original_file).output(
                raw_file,
                format='s16le',
                acodec='pcm_s16le',
                ac=2,
                ar='48k',
                loglevel='error'
            ).overwrite_output().run()
            os.remove(original_file)


    async def start_radio(self):
        group_call = mp.group_call
        if group_call.is_connected:
            playlist.clear()   
            group_call.input_filename = ''
            await group_call.stop()
        process = FFMPEG_PROCESSES.get(CHAT)
        if process:
            process.send_signal(signal.SIGTERM)
        station_stream_url = STREAM_URL
        group_call.input_filename = f'radio-{CHAT}.raw'
        try:
            RADIO.remove(0)
        except:
            pass
        try:
            RADIO.add(1)
        except:
            pass
        if os.path.exists(group_call.input_filename):
            os.remove(group_call.input_filename)
        # credits: https://t.me/c/1480232458/6825
        #os.mkfifo(group_call.input_filename)
        process = ffmpeg.input(station_stream_url).output(
            group_call.input_filename,
            format='s16le',
            acodec='pcm_s16le',
            ac=2,
            ar='48k'
        ).overwrite_output().run_async()
        FFMPEG_PROCESSES[CHAT] = process
        while True:
            await sleep(5)
            if os.path.isfile(group_call.input_filename):
                await group_call.start(CHAT)
                break
            else:
                print("No File Found!\nSleeping ...")
                process = FFMPEG_PROCESSES.get(CHAT)
                if process:
                    process.send_signal(signal.SIGTERM)
                await sleep(2)
                process = ffmpeg.input(station_stream_url).output(
                    group_call.input_filename,
                    format='s16le',
                    acodec='pcm_s16le',
                    ac=2,
                    ar='48k'
                    ).overwrite_output().run_async()
                FFMPEG_PROCESSES[CHAT] = process
                await sleep(5)
                continue

    async def stop_radio(self):
        group_call = mp.group_call
        if group_call:
            playlist.clear()   
            group_call.input_filename = ''
            try:
                RADIO.remove(1)
            except:
                pass
            try:
                RADIO.add(0)
            except:
                pass
        process = FFMPEG_PROCESSES.get(CHAT)
        if process:
            process.send_signal(signal.SIGTERM)

    async def start_call(self):
        group_call = mp.group_call
        await group_call.start(CHAT)
    
    async def delete(self, message):
        if message.chat.type == "supergroup":
            await sleep(DELAY)
            try:
                await message.delete()
            except:
                pass
        



mp = MusicPlayer()


# pytgcalls handlers


@mp.group_call.on_playout_ended
async def playout_ended_handler(_, __):
    if not playlist:
        await mp.start_radio()
    else:
        await mp.skip_current_playing()
