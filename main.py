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
    print(f"[{now.day}/{now.month}/{now.year} - {now.hour}:{now.minute}:{now.second}] '{client.user.username}' is now online!")

client.start(os.getenv('client_token'))