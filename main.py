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

PRODUCTS = {
    "Tom & Jerry Figures": {
        "url": "https://www.lego.com/en-gb/product/tom-jerry-figures-40793",
        "last_status": None,
    },
    "Time Machine (Back to the Future)": {
        "url": "https://www.lego.com/en-gb/product/time-machine-from-back-to-the-future-77256",
        "last_status": None,
    },
    "Lightning McQueen": {
        "url": "https://www.lego.com/en-gb/product/lightning-mcqueen-77255",
        "last_status": None,
    },
}

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

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    check_stock.start()

# =========================
# STOCK CHECK TASK
# =========================

@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_stock():
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            for product_name, product in PRODUCTS.items():
                url = product["url"]
                last_status = product["last_status"]

                async with session.get(url, timeout=10) as response:
                    html = await response.text()

                soup = BeautifulSoup(html, "html.parser")

                add_to_bag_button = soup.select_one(
                    "button[data-test='add-to-bag']"
                )

                if add_to_bag_button and not add_to_bag_button.has_attr("disabled"):
                    current_status = "available"
                else:
                    current_status = "unavailable"

                # First run: set baseline only
                if last_status is None:
                    product["last_status"] = current_status
                    print(f"Initial state for {product_name}: {current_status}")
                    continue

                # Log status changes
                if current_status != last_status:
                    print(
                        f"{product_name} stock changed: "
                        f"{last_status} → {current_status}"
                    )

                # Alert only when it becomes available
                if current_status == "available" and last_status != "available":
                    channel = bot.get_channel(CHANNEL_ID)
                    if channel:
                        await channel.send(
                            "🚨 **LEGO ALERT!** 🚨\n"
                            f"**{product_name}** is now **AVAILABLE** 🧱🔥\n"
                            f"{url}"
                        )

                product["last_status"] = current_status

    except Exception as e:
        print(f"❌ Error checking stock: {e}")


# =========================
# RUN BOT
# =========================

bot.run(BOT_TOKEN)
