import os
import asyncio
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Telegram Bot Token & Chat ID
TOKEN = "8987965329:AAFFzejNz8dqmL2cdKwMVejFwQ94fDP4XvY"
MY_CHAT_ID = "5490622725"

# Dummy HTTP Server for Render Port Binding
class SimpleHTTPRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot is alive!")

def run_http_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), SimpleHTTPRequestHandler)
    server.serve_forever()

# Track seen pair addresses to avoid duplicate alerts
seen_tokens = set()

# Job function to check new tokens on ARC chain
async def check_new_arc_tokens(context: ContextTypes.DEFAULT_TYPE):
    try:
        url = "https://api.dexscreener.com/latest/dex/search?q=arc"
        response = requests.get(url, timeout=10).json()
        pairs = response.get('pairs', [])
        
        for pair in pairs:
            # Check if pair belongs to ARC chain
            if pair.get('chainId') == 'arc':
                pair_address = pair.get('pairAddress')
                
                if pair_address and pair_address not in seen_tokens:
                    seen_tokens.add(pair_address)
                    
                    token_name = pair.get('baseToken', {}).get('name', 'Unknown')
                    token_symbol = pair.get('baseToken', {}).get('symbol', 'Unknown')
                    price = pair.get('priceUsd', 'N/A')
                    dex_url = pair.get('url', '')
                    
                    msg = (
                        f"🚨 **New ARC Chain Token Detected!** 🚨\n\n"
                        f"🪙 **Name:** {token_name} ({token_symbol})\n"
                        f"💰 **Price:** ${price}\n"
                        f"🔗 **Pair Address:** `{pair_address}`\n\n"
                        f"📈 [View on DexScreener]({dex_url})"
                    )
                    
                    await context.bot.send_message(
                        chat_id=MY_CHAT_ID,
                        text=msg,
                        parse_mode="Markdown"
                    )
    except Exception as e:
        print(f"Error checking ARC tokens: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ARC Chain Price & Alert Bot is Active! Send any token CA to get details.")

def main():
    # Start Dummy HTTP Server in background thread
    Thread(target=run_http_server, daemon=True).start()
    
    # Initialize Bot Application
    app = Application.builder().token(TOKEN).build()
    
    # Register Commands
    app.add_handler(CommandHandler("start", start))
    
    # Schedule repeating job (runs every 60 seconds)
    if app.job_queue:
        app.job_queue.run_repeating(check_new_arc_tokens, interval=60, first=5)
        
    print("Bot is starting...")
    app.run_polling()

if __name__ == "__main__":
    main()
