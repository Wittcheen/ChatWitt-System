# (c) 2024 Christoffer Wittchen
# Released under the MIT License.

import interactions

import os
from dotenv import load_dotenv
load_dotenv()

client = interactions.Client(intents = interactions.Intents.DEFAULT | interactions.Intents.GUILD_MEMBERS | interactions.Intents.GUILDS
| interactions.Intents.MESSAGE_CONTENT, status = interactions.Status.ONLINE)

import datetime

@interactions.listen()
async def on_startup():
    await client.wait_until_ready()
    now = datetime.datetime.now()
    print(f"[{now:%d/%m/%Y - %H:%M:%S}] '{client.user.username}' is now online!")

def load_extensions(folder_name):
    for filename in os.listdir(f"./{folder_name}"):
        if filename.endswith(".py"):
            client.load_extension(f"{folder_name}.{filename[:-3]}")

load_extensions("cogs")

client.start(os.getenv("client_token"))