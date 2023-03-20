import interactions

import yaml,os 
with open("botconfig.yaml") as config_file:
    data = yaml.safe_load(config_file)

client = interactions.Client(token = data["client_token"], intents = interactions.Intents.DEFAULT 
| interactions.Intents.GUILD_MEMBERS | interactions.Intents.GUILD_MESSAGE_CONTENT, status = interactions.StatusType("online"))

import datetime

@client.event
async def on_start():
    await client.wait_until_ready()
    now = datetime.datetime.now()
    print(f"[{now.day}/{now.month}/{now.year} - {now.hour}:{now.minute}:{now.second}] '{client.me.name}' is now online!")

for filename in os.listdir("./cogs"):
    if filename.endswith(".py"):
        client.load(f"cogs.{filename[:-3]}")

client.start()