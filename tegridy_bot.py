import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
from supabase import create_client
from datetime import datetime

BOT_TOKEN   = "8965770810:AAFNM9WQy0eMNkr24b7TmIkL0Gln-xdruDw"
MINIAPP_URL = "https://tegridy.netlify.app/"
SB_URL      = "https://qcmanyxzgnxypensibqt.supabase.co"
SB_KEY      = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjbWFueXh6Z254eXBlbnNpYnF0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc1NTgzNjcsImV4cCI6MjEwMzEzNDM2N30.YnVyBmWw60frN2YdGreElMs3hQAW-E_ThfaqVCxcFM4"
LOGO_URL    = "https://stashmemedia.b-cdn.net/1788183519196_qfq7kfz0elb.png"
ADMIN_IDS   = []

WELCOME_TEXT = """🌿 *Bienvenue sur TEGRIDY*

Premium · Discret · Fiable

Découvrez notre sélection de produits premium.

Appuyez sur le bouton ci-dessous 👇"""

supabase = create_client(SB_URL, SB_KEY)

def log_visit(user):
    try:
        supabase.table("bot_visits").insert({
            "telegram_id": user.id,
            "username": user.username or "",
            "first_name": user.first_name or "",
            "visited_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        logging.error(f"log_visit: {e}")

class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK")
    def log_message(self, *args):
        pass

def run_health():
    HTTPServer(('0.0.0.0', 8080), HealthHandler).serve_forever()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_visit(user)
    kb = [[InlineKeyboardButton("🌿 Ouvrir la boutique", web_app=WebAppInfo(url=MINIAPP_URL))]]
    try:
        await update.message.reply_photo(
            photo=LOGO_URL,
            caption=WELCOME_TEXT,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )
    except Exception:
        await update.message.reply_text(
            WELCOME_TEXT,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(kb)
        )

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_IDS and update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Accès refusé.")
        return
    if not context.args:
        await update.message.reply_text("Usage : /broadcast Votre message")
        return
    msg = " ".join(context.args)
    visits = supabase.table("bot_visits").select("telegram_id").execute()
    ids = list(set([v["telegram_id"] for v in visits.data]))
    sent = 0
    for tid in ids:
        try:
            await context.bot.send_message(chat_id=tid, text=msg, parse_mode="Markdown")
            sent += 1
        except Exception:
            pass
    await update.message.reply_text(f"✅ Envoyé à {sent} utilisateurs.")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if ADMIN_IDS and update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Accès refusé.")
        return
    visits = supabase.table("bot_visits").select("telegram_id").execute()
    ids = list(set([v["telegram_id"] for v in visits.data]))
    await update.message.reply_text(
        f"📊 *Stats TEGRIDY*\n\n👥 Uniques : {len(ids)}\n📬 Total visites : {len(visits.data)}",
        parse_mode="Markdown"
    )

def main():
    logging.basicConfig(level=logging.INFO)
    threading.Thread(target=run_health, daemon=True).start()
    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    print("✅ Bot TEGRIDY lancé")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
