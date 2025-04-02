# (c) 2025 Christoffer Wittchen
# Released under the MIT License.

import interactions

import os
from dotenv import load_dotenv
load_dotenv()

client = interactions.Client(intents = interactions.Intents.DEFAULT | interactions.Intents.GUILD_MEMBERS | interactions.Intents.GUILDS
| interactions.Intents.MESSAGE_CONTENT, status = interactions.Status.ONLINE)

import datetime
from utils.database import DatabaseManager
_db = DatabaseManager()

#region - STARTUP
@interactions.listen()
async def on_startup():
    """ Runs when the bot is starting up. """
    await client.wait_until_ready()
    now = datetime.datetime.now()
    print(f"[{now:%d/%m/%Y - %H:%M:%S}] '{client.user.username}' is now online!")
    await _db.create_pool()
#endregion

#region - SHUTDOWN
@interactions.listen()
async def on_shutdown():
    """ Runs when the bot is shutting down. """
    print(f"'{client.user.username}' is shutting down...")
    await _db.close_pool()
#endregion

def load_extensions(folder_name):
    for filename in os.listdir(f"./{folder_name}"):
        if filename.endswith(".py"):
            client.load_extension(f"{folder_name}.{filename[:-3]}")
load_extensions("cogs")

client.start(os.getenv("CLIENT_TOKEN"))
