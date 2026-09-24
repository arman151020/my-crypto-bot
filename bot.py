import os
import asyncio
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from threading import Thread
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Updated Revoked Bot Token & Chat ID
TOKEN = "8987965329:AAFQVt4M5_wt7ofyB80QfbAza5PK1XFsr0g"
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

# Scanner for DexScreener & BasedBot
async def check_new_arc_tokens(app: Application):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    while True:
        # 1. Check DexScreener
        try:
            url_dex = "https://api.dexscreener.com/latest/dex/search?q=arc"
            res_dex = requests.get(url_dex, timeout=10, headers=headers).json()
            pairs = res_dex.get('pairs', [])
            
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
                                f"🚨 **New ARC Chain Token Detected! (DexScreener)** 🚨\n\n"
                                f"🪙 **Name:** {token_name} ({token_symbol})\n"
                                f"💰 **Price:** ${price}\n"
                                f"🔗 **Pair Address:** `{pair_address}`\n\n"
                                f"📈 [View on DexScreener]({dex_url})"
                            )
                            
                            await app.bot.send_message(chat_id=MY_CHAT_ID, text=msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Error checking DexScreener: {e}")

        # 2. Check BasedBot
        try:
            url_based = "https://api.basedbot.app/v1/tokens?chain=arc" 
            res_based = requests.get(url_based, timeout=10, headers=headers)
            
            if res_based.status_code == 200:
                data = res_based.json()
                tokens = data.get('tokens', []) if isinstance(data, dict) else []
                
                for token in tokens:
                    address = token.get('address') or token.get('pairAddress')
                    if address and address not in seen_tokens:
                        seen_tokens.add(address)
                        
                        name = token.get('name', 'Unknown')
                        symbol = token.get('symbol', 'Unknown')
                        
                        msg = (
                            f"🚨 **New ARC Chain Token Detected! (BasedBot)** 🚨\n\n"
                            f"🪙 **Name:** {name} ({symbol})\n"
                            f"🔗 **Contract:** `{address}`\n\n"
                            f"🌐 [View on BasedBot](https://basedbot.app/token/{address})"
                        )
                        
                        await app.bot.send_message(chat_id=MY_CHAT_ID, text=msg, parse_mode="Markdown")
        except Exception as e:
            print(f"Error checking BasedBot: {e}")

        await asyncio.sleep(60)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("ARC Chain Alert Bot is Active! Monitoring DexScreener & BasedBot.")

async def post_init(app: Application):
    asyncio.create_task(check_new_arc_tokens(app))

def main():
    Thread(target=run_http_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is starting polling...")
    app.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == "__main__":
    main()
