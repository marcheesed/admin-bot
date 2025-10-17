import os
import ssl
import tempfile
import discord
import asyncio
import aiohttp
import certifi
from dotenv import load_dotenv
from pastryfunctions import PastryClient
from modfunctions import load_banned_words, add_banned_word

# --- load environment variables ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("BACKUP_DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("No Discord token available in environment variables!")

# ---prepare SSL context ---
pem_content = os.getenv("PEM_KEY")
if pem_content:
    pem_content = pem_content.replace("\\n", "\n")
    pem_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pem")
    pem_file.write(pem_content.encode())
    pem_file.close()
    pem_cert_path = pem_file.name
    ssl_context = ssl.create_default_context(cafile=pem_cert_path)
else:
    ssl_context = ssl.create_default_context(cafile=certifi.where())

# --- Discord bot setup ---
intents = discord.Intents.default()
intents.message_content = True
bot = discord.Client(intents=intents)
banned_words = load_banned_words()

pastry_client = None


# --- Test aiohttp request ---
async def test_request():
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(
                "https://pastry.diy/admin/pastes", ssl=ssl_context
            ) as resp:
                print(f"Test request status code: {resp.status}")
        except Exception as e:
            print(f"Warning: Test request failed → {e}")


# --- Discord helpers ---
def get_channel(guild):
    return discord.utils.get(guild.text_channels, name="general") or (
        guild.text_channels[0] if guild.text_channels else None
    )


async def check_and_alert(channel):
    await pastry_client.refresh_database()
    flagged = pastry_client.check_for_banned_urls()
    if flagged:
        await channel.send(
            "\n".join(
                [
                    f"**BANNED WORD DETECTED** in `{url}`, owned by `{owner}`"
                    for url, owner in flagged
                ]
            )
        )
    else:
        await channel.send("No banned URLs detected.")


# --- Discord events ---
@bot.event
async def on_ready():
    global pastry_client
    print(f"Logged in as {bot.user}")

    # Pass ssl_context to PastryClient
    pastry_client = await PastryClient(
        verify_ssl=True, cert_path=pem_cert_path if pem_content else None
    ).__aenter__()

    await test_request()
    await pastry_client.refresh_database()
    print("Database preloaded!")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip()
    channel = get_channel(message.guild)

    # --- Admin-only PastryClient commands ---
    if (
        content.startswith(
            ("!ping", "!refresh", "!checkbanned", "!searchuser", "!searchurl")
        )
        and channel
    ):
        if not message.author.guild_permissions.administrator:
            await channel.send("You don't have permissions for this!")
            return

        if content.startswith("!ping"):
            await channel.send(f"Pong! **Latency: {bot.latency * 1000:.2f}ms**")
        elif content.startswith("!refresh"):
            await pastry_client.refresh_database()
            await channel.send("Database refreshed!")
        elif content.startswith("!checkbanned"):
            await check_and_alert(channel)
        elif content.startswith("!searchuser"):
            username = content[len("!searchuser") :].strip()
            await channel.send(pastry_client.search_by_username(username))
        elif content.startswith("!searchurl"):
            url = content[len("!searchurl") :].strip()
            await channel.send(pastry_client.search_by_url(url))

    # --- Banned word commands ---
    elif content.startswith("!addword") and channel:
        if not message.author.guild_permissions.administrator:
            await channel.send("You don't have permissions for this!")
            return
        new_word = content[len("!addword") :].strip()
        add_banned_word(new_word)
        global banned_words
        banned_words = load_banned_words()
        await channel.send(f"Added banned word: {new_word}")

    # --- Word filter ---
    for word in banned_words:
        if word in content.lower() and channel:
            await message.delete()
            await channel.send("You can't say that here!")
            break


@bot.event
async def on_disconnect():
    global pastry_client
    if pastry_client:
        await pastry_client.__aexit__(None, None, None)
        print("Closed PastryClient session cleanly.")


# --- Run bot ---
if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
