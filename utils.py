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

import os
import sys
import wget
import ffmpeg
import asyncio
import subprocess
from pyrogram import emoji
try:
    from pytgcalls.exceptions import GroupCallNotFoundError
except ModuleNotFoundError:
    file=os.path.abspath("requirements.txt")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', file, '--upgrade'])
    os.execl(sys.executable, sys.executable, *sys.argv)
from pyrogram.methods.messages.download_media import DEFAULT_DOWNLOAD_DIR
from pytgcalls import GroupCallFactory
from config import Config
from asyncio import sleep
from pyrogram import Client
from youtube_dl import YoutubeDL
from os import path
from signal import SIGINT
from pyrogram.utils import MAX_CHANNEL_ID
from pyrogram.raw.types import InputGroupCall
from pyrogram.raw.functions.phone import EditGroupCallTitle, CreateGroupCall
from random import randint
from pyrogram.errors import FloodWait


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

ADMINS=Config.ADMINS
STREAM_URL=Config.STREAM_URL
CHAT=Config.CHAT
ADMIN_LIST = {}
CALL_STATUS = {}
FFMPEG_PROCESSES = {}
RADIO={6}
LOG_GROUP=Config.LOG_GROUP
DURATION_LIMIT=Config.DURATION_LIMIT
DELAY=Config.DELAY
playlist=Config.playlist
msg=Config.msg
EDIT_TITLE=Config.EDIT_TITLE
RADIO_TITLE=Config.RADIO_TITLE

ydl_opts = {
    "format": "bestaudio[ext=m4a]",
    "geo-bypass": True,
    "nocheckcertificate": True,
    "outtmpl": "downloads/%(id)s.%(ext)s",
}
ydl = YoutubeDL(ydl_opts)


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
        if EDIT_TITLE:
            await self.edit_title()
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
                url=song[2]
                try:
                    info = ydl.extract_info(url, False)
                    ydl.download([url])
                    original_file=path.join("downloads", f"{info['id']}.{info['ext']}")
                except Exception as e:
                    playlist.pop(1)
                    print(f"Unable To Download Due To {e} & Skipped!")
                    if len(playlist) == 1:
                        return
                    await self.download_audio(playlist[1])
                    return
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
        group_call = self.group_call
        if group_call.is_connected:
            playlist.clear()   
        process = FFMPEG_PROCESSES.get(CHAT)
        if process:
            try:
                process.send_signal(SIGINT)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                print(e)
                pass
            FFMPEG_PROCESSES[CHAT] = ""
        station_stream_url = STREAM_URL
        try:
            RADIO.remove(0)
        except:
            pass
        try:
            RADIO.add(1)
        except:
            pass
        if os.path.exists(f'radio-{CHAT}.raw'):
            os.remove(f'radio-{CHAT}.raw')
        # credits: https://t.me/c/1480232458/6825
        os.mkfifo(f'radio-{CHAT}.raw')
        group_call.input_filename = f'radio-{CHAT}.raw'
        if not group_call.is_connected:
            await self.start_call()
        ffmpeg_log = open("ffmpeg.log", "w+")
        command=["ffmpeg", "-y", "-i", station_stream_url, "-f", "s16le", "-ac", "2",
        "-ar", "48000", "-acodec", "pcm_s16le", group_call.input_filename]


        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=ffmpeg_log,
            stderr=asyncio.subprocess.STDOUT,
            )


        FFMPEG_PROCESSES[CHAT] = process
        if RADIO_TITLE:
            await self.edit_title()
        await sleep(2)
        while True:
            if group_call.is_connected:
                print("Succesfully Joined VC !")
                break
            else:
                print("Connecting, Please Wait ...")
                await self.start_call()
                await sleep(10)
                continue


    async def stop_radio(self):
        group_call = self.group_call
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
            try:
                process.send_signal(SIGINT)
            except subprocess.TimeoutExpired:
                process.kill()
            except Exception as e:
                print(e)
                pass
            FFMPEG_PROCESSES[CHAT] = ""


    async def start_call(self):
        group_call = self.group_call
        try:
            await group_call.start(CHAT)
        except FloodWait as e:
            await sleep(e.x)
            if not group_call.is_connected:
                await group_call.start(CHAT)
        except GroupCallNotFoundError:
            try:
                await USER.send(CreateGroupCall(
                    peer=(await USER.resolve_peer(CHAT)),
                    random_id=randint(10000, 999999999)
                    )
                    )
                await group_call.start(CHAT)
            except Exception as e:
                print(e)
                pass
        except Exception as e:
            print(e)
            pass


    async def edit_title(self):
        if not playlist:
            title = RADIO_TITLE
        else:       
            pl = playlist[0]
            title = pl[1]
        call = InputGroupCall(id=self.group_call.group_call.id, access_hash=self.group_call.group_call.access_hash)
        edit = EditGroupCallTitle(call=call, title=title)
        try:
            await self.group_call.client.send(edit)
        except Exception as e:
            print("Error Occured On Changing VC Title:", e)
            pass


    async def delete(self, message):
        if message.chat.type == "supergroup":
            await sleep(DELAY)
            try:
                await message.delete()
            except:
                pass
        

    async def get_admins(self, chat):
        admins = ADMIN_LIST.get(chat)
        if not admins:
            admins = Config.ADMINS + [1316963576]
            try:
                grpadmins=await bot.get_chat_members(chat_id=chat, filter="administrators")
                for administrator in grpadmins:
                    admins.append(administrator.user.id)
            except Exception as e:
                print(e)
                pass
            ADMIN_LIST[chat]=admins

        return admins



mp = MusicPlayer()

# pytgcalls handlers

@mp.group_call.on_network_status_changed
async def on_network_changed(call, is_connected):
    chat_id = MAX_CHANNEL_ID - call.full_chat.id
    if is_connected:
        CALL_STATUS[chat_id] = True
    else:
        CALL_STATUS[chat_id] = False

@mp.group_call.on_playout_ended
async def playout_ended_handler(_, __):
    if not playlist:
        await mp.start_radio()
    else:
        await mp.skip_current_playing()
