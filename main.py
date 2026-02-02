import os
import aiohttp
import discord
from discord.ext import commands, tasks

# =========================
# CONFIG
# =========================

BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
CHANNEL_ID = 1466161739547807795

CHECK_INTERVAL_MINUTES = 1
COUNTRY_CODE = "GB"

GRAPHQL_URL = "https://www.lego.com/api/graphql/StockAvailability"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (LEGOStockChecker/1.0)",
    "Content-Type": "application/json",
}

PRODUCTS = {
    "Tom & Jerry Figures": {
        "sku": "40793",
        "url": "https://www.lego.com/en-gb/product/tom-jerry-figures-40793",
        "last_status": None,
    },
    "Time Machine (Back to the Future)": {
        "sku": "77256",
        "url": "https://www.lego.com/en-gb/product/time-machine-from-back-to-the-future-77256",
        "last_status": None,
    },
    "Lightning McQueen": {
        "sku": "77255",
        "url": "https://www.lego.com/en-gb/product/lightning-mcqueen-77255",
        "last_status": None,
    },
}

# =========================
# DISCORD SETUP
# =========================

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    if not check_stock.is_running():
        check_stock.start()

# =========================
# LEGO STOCK API
# =========================

async def fetch_stock_status(session, sku):
    payload = {
        "query": """
        query StockAvailability($sku: String!, $country: String!) {
          product(sku: $sku) {
            availability(country: $country) {
              available
              availabilityStatus
            }
          }
        }
        """,
        "variables": {
            "sku": sku,
            "country": COUNTRY_CODE,
        },
    }

    async with session.post(GRAPHQL_URL, json=payload, timeout=10) as response:
        data = await response.json()

    availability = data["data"]["product"]["availability"]
    return availability["available"]

# =========================
# STOCK CHECK TASK
# =========================

@tasks.loop(minutes=CHECK_INTERVAL_MINUTES)
async def check_stock():
    try:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            for product_name, product in PRODUCTS.items():
                sku = product["sku"]
                url = product["url"]
                last_status = product["last_status"]

                is_available = await fetch_stock_status(session, sku)
                current_status = "available" if is_available else "unavailable"

                # First run: establish baseline
                if last_status is None:
                    product["last_status"] = current_status
                    print(f"Initial state for {product_name}: {current_status}")
                    continue

                # Log any change
                if current_status != last_status:
                    print(
                        f"{product_name} stock changed: "
                        f"{last_status} → {current_status}"
                    )

                # Alert only when it becomes available
                if current_status == "available" and last_status != "available":
                    channel = await bot.get_channel(CHANNEL_ID)
                    if channel:
                        await channel.send(
                            "🚨 **LEGO ALERT!** 🚨\n"
                            f"**{product_name}** is now **AVAILABLE** 🧱🔥\n"
                            f"{url}"
                        )

                product["last_status"] = current_status

    except Exception as e:
        print(f"❌ Error checking stock: {e}")

print(f"Sending alert for {product_name} to channel {CHANNEL_ID}")


# =========================
# RUN BOT
# =========================

bot.run(BOT_TOKEN)
