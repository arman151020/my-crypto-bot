import os
import asyncio
import requests
from threading import Thread
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8987965329:AAGHuyL6mo4N0JBRHjowZ_1hPKC-bo153JM"
MY_CHAT_ID = "5490622725"

web_app = Flask('')

@web_app.route('/')
def home():
    return "Bot is running 24/7!"

def run_web_server():
    port = int(os.environ.get("PORT", 8080))
    web_app.run(host='0.0.0.0', port=port)

seen_tokens = set()

async def check_new_arc_tokens(app: Application):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
    }
    
    # 🔔 Instant Startup Test Message
    try:
        await app.bot.send_message(
            chat_id=MY_CHAT_ID, 
            text="✅ **ARC Alert Bot System Initialized!**\nScanning DexScreener & BasedBot every 60s...",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"Startup message error: {e}")

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
    Thread(target=run_web_server, daemon=True).start()
    
    app = Application.builder().token(TOKEN).post_init(post_init).build()
    app.add_handler(CommandHandler("start", start))
    
    print("Bot is starting polling...")
    app.run_polling(drop_pending_updates=True, close_loop=False)

if __name__ == "__main__":
    main()
