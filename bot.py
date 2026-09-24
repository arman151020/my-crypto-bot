import os
import asyncio
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8987965329:AAHmAtlhKTjQt58rVy6pHD4YQSy2bSOnFhg"
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

seen_tokens = set()

# Background task to check new ARC chain tokens
async def check_new_arc_tokens(app: Application):
    while True:
        try:
            url = "https://api.dexscreener.com/latest/dex/search?q=arc"
            response = requests.get(url, timeout=10).json()
            pairs = response.get('pairs', [])
            
            if pairs:
                for pair in pairs:
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
                            
                            await app.bot.send_message(
                                chat_id=MY_CHAT_ID,
                                text=msg,
                                parse_mode="Markdown"
                            )
        except Exception as e:
            print(f"Error checking ARC tokens: {e}")
            
        await asyncio.sleep(60)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ARC Chain Alert Bot is Active!")

async def post_init(app: Application):
    asyncio.create_task(check_new_arc_tokens(app))

def main():
    Thread(target=run_http_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is starting...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
