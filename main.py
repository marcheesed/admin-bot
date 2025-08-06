import discord
import pastryfunctions
import json
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("DISCORD_TOKEN")

global arr


def refresh():
    with open("banned.json", "r") as f:
        data = json.load(f)

    words = [entry["word"] for entry in data]
    return words


arr = refresh()

# Initialize the bot client with default intents
intents = discord.Intents.default()
intents.message_content = True  # Enable the message content intent
client = discord.Client(intents=intents)


# Event: Bot is ready
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')


@client.event
async def on_message(message):

    if message.author == client.user:
        return

    if message.content.startswith('!searchuser'):
        req = message.content[12:]
        ans = pastryfunctions.searchURL(req)
        await message.channel.send(ans)

    if message.content.startswith('!addword'):
        req = message.content[9:]

        with open("banned.json", "r") as file:
            data = json.load(file)

        data.append({"word": req})

        with open("banned.json", "w") as file:
            json.dump(data, file, indent=4)
        arr = refresh()

    if message.content.startswith('!searchurl'):
        req = message.content[11:]
        ans = pastryfunctions.searchOwner(req)
        await message.channel.send(ans)

    if message.content.startswith("!ping"):
        await message.channel.send("Pong!\n\n**Latency is " +
                                   str(client.latency) + " ms**")

    if message.author != client.user:
        arr = refresh()
        for i in arr:
            if i.lower() in message.content.lower():
                await message.delete()
                await message.channel.send("YOU CAN'T SAY THAT!!!")


client.run(TOKEN)
