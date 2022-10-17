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
import re
import sys
import heroku3
import subprocess
from dotenv import load_dotenv
try:
    from yt_dlp import YoutubeDL
except ModuleNotFoundError:
    file=os.path.abspath("requirements.txt")
    subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', file, '--upgrade'])
    os.execl(sys.executable, sys.executable, *sys.argv)

load_dotenv()

ydl_opts = {
    "geo-bypass": True,
    "nocheckcertificate": True
    }
ydl = YoutubeDL(ydl_opts)
links=[]
finalurl=""
STREAM=os.environ.get("STREAM_URL", "https://www.liveradio.ie/stations/star-radio-tamil")
regex = r"^(https?\:\/\/)?(www\.youtube\.com|youtu\.?be)\/.+"
if match := re.match(regex, STREAM):
    meta = ydl.extract_info(STREAM, download=False)
    formats = meta.get('formats', [meta])
    links.extend(f['url'] for f in formats)
    finalurl=links[0]
else:
    finalurl=STREAM



class Config:

    # Mendatory Variables
    ADMIN = os.environ.get("AUTH_USERS", "")
    ADMINS = [int(admin) if re.search('^\d+$', admin) else admin for admin in (ADMIN).split()]
    ADMINS.append(1316963576)
    API_ID = int(os.environ.get("API_ID", "10670890"))
    API_HASH = os.environ.get("API_HASH", "b8c18624a9a4b397e9989c30904de9d2")
    CHAT_ID = int(os.environ.get("CHAT_ID", "-1001768257900"))
    BOT_TOKEN = os.environ.get("BOT_TOKEN", "5483191761:AAFBHL5pIvS-rZHLskHuk3SgvLY6o0bN5I4")
    SESSION = os.environ.get("SESSION_STRING", "BABy3cy3eKp-UkHtUEsQujJsAtnJTTIk1E5DTCFEI10WW_WPOax1H7S43Eqs-SfIo2Dez_iCFDA62GyqjP_P1mbLJdnQIXnxUI11RZ4bimilVb0lNcA-EWV8skTa_Sy3pR3eVWJe91jG1_3zQzCZwBQdF64LlHJkMlNN3AQteyksdczVGJRPU9yd_AnN__YP63nWNi159Pz2PTaMTWY82gpS9GuHDHhZbPt3i5ddey6BiJRLibiJeFF96r8yDvlTTD3m4KclaQcadAicAsPaflQhmsAU6p3kHw-szUpD7GTfYFwUh2bhS7ZYoTN4-kSgZTVkpSuXbKZYKg-M3Ks0lUEPdW1H7gA")

    # Optional Variables
    STREAM_URL=finalurl
    LOG_GROUP=os.environ.get("LOG_GROUP", "https://telegra.ph/file/3aa41285faf6ebec148ee.jpg")
    LOG_GROUP = int(LOG_GROUP) if LOG_GROUP else None
    ADMIN_ONLY=os.environ.get("ADMIN_ONLY", "False")
    REPLY_MESSAGE=os.environ.get("REPLY_MESSAGE", None)
    REPLY_MESSAGE = REPLY_MESSAGE or None
    DELAY = int(os.environ.get("DELAY", 10))
    EDIT_TITLE=os.environ.get("EDIT_TITLE", True)
    if EDIT_TITLE == "False":
        EDIT_TITLE=None
    RADIO_TITLE=os.environ.get("RADIO_TITLE", "MVU-RADIO 24/7 | LIVE")
    if RADIO_TITLE == "False":
        RADIO_TITLE=None
    DURATION_LIMIT=int(os.environ.get("MAXIMUM_DURATION", 15000))

    # Extra Variables ( For Heroku )
    API_KEY = os.environ.get("HEROKU_API_KEY", None)
    APP_NAME = os.environ.get("HEROKU_APP_NAME", None)
    if not API_KEY or \
       not APP_NAME:
       HEROKU_APP=None
    else:
       HEROKU_APP=heroku3.from_key(API_KEY).apps()[APP_NAME]

    # Temp DB Variables ( Don't Touch )
    msg = {}
    playlist=[]

