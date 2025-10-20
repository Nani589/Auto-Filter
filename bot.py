import logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logging.getLogger('hydrogram').setLevel(logging.ERROR)
logger = logging.getLogger(name)

import os
import time
import asyncio
import uvloop
from hydrogram import types
from hydrogram import Client
from hydrogram.errors import FloodWait
from aiohttp import web
from typing import Union, Optional, AsyncGenerator
from web import web_app
from info import (
    INDEX_CHANNELS, SUPPORT_GROUP, LOG_CHANNEL, API_ID, DATA_DATABASE_URL,
    API_HASH, BOT_TOKEN, PORT, BIN_CHANNEL, ADMINS,
    SECOND_FILES_DATABASE_URL, FILES_DATABASE_URL
)
from utils import temp, get_readable_time, check_premium
from database.users_chats_db import db
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi


class Bot(Client):
    def init(self):
        super().init(
            name='Auto_Filter_Bot',
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            plugins={"root": "plugins"}
        )

    async def start(self):
        await super().start()
        temp.START_TIME = time.time()
        b_users, b_chats = await db.get_banned()
        temp.BANNED_USERS = b_users
        temp.BANNED_CHATS = b_chats

        if os.path.exists('restart.txt'):
            with open("restart.txt") as file:
                chat_id, msg_id = map(int, file)
            try:
                await self.edit_message_text(chat_id=chat_id, message_id=msg_id, text='Restarted Successfully!')
            except Exception:
                pass
            os.remove('restart.txt')

        temp.BOT = self
        me = await self.get_me()
        temp.ME = me.id
        temp.U_NAME = me.username
        temp.B_NAME = me.first_name
        
        # Start web server for Koyeb or other platforms
        runner = web.AppRunner(web_app)
        await runner.setup()
        await web.TCPSite(runner, "0.0.0.0", PORT).start()

        # Background tasks
        asyncio.create_task(check_premium(self))
        try:
            await self.send_message(chat_id=LOG_CHANNEL, text=f"<b>{me.mention} Restarted! 🤖</b>")
        except Exception:
            logger.error("Make sure bot admin in LOG_CHANNEL, exiting now")
            exit()
        logger.info(f"@{me.username} is started now ✓")

    async def stop(self, *args):
        await super().stop()
        logger.info("Bot Stopped! Bye...")

    async def iter_messages(
        self: Client,
        chat_id: Union[int, str],
        limit: int,
        offset: int = 0
    ) -> Optional[AsyncGenerator["types.Message", None]]:
        """
        Iterate through a chat sequentially.
        Example:
            async for message in app.iter_messages("HA_Bots", 1000, 100):
                print(message.text)
        """
        current = offset
        while True:
            new_diff = min(200, limit - current)
            if new_diff <= 0:
                return
            messages = await self.get_messages(chat_id, list(range(current, current + new_diff + 1)))
            for message in messages:
                yield message
                current += 1


# --- Main Entry Point ---
if name == "main":
    # ✅ Safe uvloop initialization (fixes "no current event loop" error)
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())

    app = Bot()
    app.run()
