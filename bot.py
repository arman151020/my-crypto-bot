import os
import logging
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# Render Web Service-এর জন্য ফেক এইচটিটিপি সার্ভার
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is running!")

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# আপনার Telegram Bot API Key
TELEGRAM_BOT_TOKEN = "8987965329:AAFFzejNz8dqmL2cdKwMVejFwQ94fDP4XvY"

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 স্বাগতম! যেকোনো টোকেনের Contract Address (CA) পাঠান, আমি প্রাইস ও মার্কেটক্যাপ জানিয়ে দেব।")

async def check_token(update: Update, context: ContextTypes.DEFAULT_TYPE):
    token_address = update.message.text.strip()
    msg = await update.message.reply_text("🔍 তথ্য খোঁজা হচ্ছে...")
    
    url = f"https://api.dexscreener.com/latest/dex/tokens/{token_address}"
    try:
        response = requests.get(url, timeout=10).json()
        pairs = response.get("pairs")
        
        if not pairs:
            await msg.edit_text("❌ কোনো টোকেন পাওয়া যায়নি! সঠিক CA দিয়েছেন তো?")
            return
            
        pair = pairs[0]
        name = pair.get("baseToken", {}).get("name", "N/A")
        symbol = pair.get("baseToken", {}).get("symbol", "N/A")
        price = pair.get("priceUsd", "0")
        market_cap = pair.get("fdv", 0)
        liquidity = pair.get("liquidity", {}).get("usd", 0)
        chain = pair.get("chainId", "N/A").upper()
        
        alert_msg = (
            f"🚨 **TOKEN DETAILS** 🚨\n\n"
            f"🪙 **Name:** {name} (${symbol})\n"
            f"⛓️ **Chain:** {chain}\n"
            f"💰 **Price:** ${price}\n"
            f"📊 **Market Cap:** ${market_cap:,.2f}\n"
            f"💧 **Liquidity:** ${liquidity:,.2f}\n"
            f"📝 **CA:** `{token_address}`"
        )
        await msg.edit_text(alert_msg, parse_mode="Markdown")
    except Exception:
        await msg.edit_text("⚠️ সমস্যা হয়েছে, আবার চেষ্টা করুন।")

if __name__ == "__main__":
    # ব্যাকগ্রাউন্ডে ওয়েব সার্ভার স্টার্ট
    threading.Thread(target=run_web_server, daemon=True).start()
    
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), check_token))
    print("🤖 বট চালু হয়েছে...")
    app.run_polling()
