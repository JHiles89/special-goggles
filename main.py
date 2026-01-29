import os
import aiohttp
import discord
from discord.ext import commands, tasks
from bs4 import BeautifulSoup

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = 1466161739547807795
PRODUCT_URL = "https://www.lego.com/en-gb/product/tom-jerry-figures-40793"

CHECK_INTERVAL_MINUTES = 1

HEADERS = {
    "User-Agent": "Mozilla/5.0 (LEGOStockChecker/1.0)"
}

# =========================
# DISCORD SETUP
# =========================

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

last_status = None  # remembers previous stock state


@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    check_stock.start()

# =========================
# STOCK CHECK TASK
# =========================

@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_stock():
    from datetime import datetime
    global last_status

    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            async with session.get(PRODUCT_URL, timeout=10) as response:
                html = await response.text()

        soup = BeautifulSoup(html, "html.parser")

        # LEGO usually disables the Add to Bag button when unavailable
        add_to_bag_button = soup.select_one("button[data-test='add-to-bag']")

        if add_to_bag_button and not add_to_bag_button.has_attr("disabled"):
            current_status = "available"
        else:
            current_status = "unavailable"

        # First run: set baseline, no alert
        if last_status is None:
            last_status = current_status
            print(f"Initial stock state: {current_status}")

        if current_status == "available":
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send("🧪 Test alert: item is available")

        # Log status changes
        if current_status != last_status:
            print(f"Stock changed: {last_status} → {current_status}")

        # Alert only when item becomes available
        if current_status == "available" and last_status != "available":
            channel = bot.get_channel(CHANNEL_ID)
            if channel:
                await channel.send(
                    "🚨 **LEGO ALERT!** 🚨\n"
                    "**Tom & Jerry Figures** are now **AVAILABLE** 🧱🔥\n"
                    f"{PRODUCT_URL}"
                )

        last_status = current_status

    except Exception as e:
        print(f"❌ Error checking stock: {e}")

# =========================
# RUN BOT
# =========================

bot.run(BOT_TOKEN)
