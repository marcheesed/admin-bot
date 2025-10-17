import os
import threading
import ssl
import tempfile
import discord
import asyncio
import aiohttp
import certifi
from flask import Flask, render_template_string
from dotenv import load_dotenv
from pastryfunctions import PastryClient
from modfunctions import load_banned_words, add_banned_word

# --- Load environment ---
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN") or os.getenv("BACKUP_DISCORD_TOKEN")
if not DISCORD_TOKEN:
    raise ValueError("No Discord token found in environment variables!")

# --- SSL setup for PastryClient ---
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

# --- Flask app ---
app = Flask(__name__)


@app.route("/")
def index():
    # Get bot name safely
    bot_name = getattr(bot.user, "name", "Loading...")

    # Get URLs from PastryClient
    urls = []
    if pastry_client:
        urls = [f"{url} (owner: {owner})" for url, owner in pastry_client.arr]

    # Render HTML
    html = """
    <html>
    <head>
        <title>Admin Bot Dashboard</title>
        <style>
            body {
                display: flex;
                justify-content: center;
                align-items: center;
                flex-direction: column;
                font-family: Arial, sans-serif;
                padding: 20px;
            }
            h1 { color: #2c3e50; }
            ul { max-height: 400px; overflow-y: scroll; width: 600px; }
            li { margin-bottom: 5px; }
        </style>
    </head>
    <body>
        <h1>Admin Bot Dashboard</h1>
        <p>Status: Running</p>
        <p>Bot: {{ bot_name }}</p>
        <h2>Tracked URLs:</h2>
        {% if urls %}
            <ul>
                {% for u in urls %}
                    <li>{{ u }}</li>
                {% endfor %}
            </ul>
        {% else %}
            <p>No URLs loaded yet.</p>
        {% endif %}
    </body>
    </html>
    """
    return render_template_string(html, bot_name=bot_name, urls=urls)


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
    pastry_client = await PastryClient(
        verify_ssl=True, cert_path=pem_cert_path if pem_content else None
    ).__aenter__()
    await pastry_client.refresh_database()
    print("Database preloaded!")


@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    content = message.content.strip()
    channel = get_channel(message.guild)

    # Admin-only commands
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

    # Add banned word
    elif content.startswith("!addword") and channel:
        if not message.author.guild_permissions.administrator:
            await channel.send("You don't have permissions for this!")
            return
        new_word = content[len("!addword") :].strip()
        add_banned_word(new_word)
        global banned_words
        banned_words = load_banned_words()
        await channel.send(f"Added banned word: {new_word}")

    # Word filter
    for word in banned_words:
        if word in content.lower() and channel:
            await message.delete()
            await channel.send("You can't say that here!")
            break


# --- Run Discord bot in background ---
def run_bot():
    asyncio.run(bot.start(DISCORD_TOKEN))


threading.Thread(target=run_bot).start()

# --- Run Flask app ---
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
