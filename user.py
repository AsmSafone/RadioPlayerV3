from config import Config
from pyrogram import Client

USER = Client(
    Config.SESSION,
    Config.API_ID,
    Config.API_HASH
)
USER.start()
