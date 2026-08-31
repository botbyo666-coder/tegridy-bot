import logging
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
from supabase import create_client
from datetime import datetime

# ══════════════════════════════════
# CONFIG
# ══════════════════════════════════
BOT_TOKEN    = "8965770810:AAFNM9WQy0eMNkr24b7TmIkL0Gln-xdruDw"  # ⚠️ À remplacer !
MINIAPP_URL  = "https://tegridy.netlify.app/"
SB_URL       = "https://qcmanyxzgnxypensibqt.supabase.co"
SB_KEY       = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InFjbWFueXh6Z254eXBlbnNpYnF0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODc1NTgzNjcsImV4cCI6MjEwMzEzNDM2N30.YnVyBmWw60frN2YdGreElMs3hQAW-E_ThfaqVCxcFM4"
LOGO_URL     = "https://avecamour.b-cdn.net/file_038_image.png"
ADMIN_IDS    = []

WELCOME_TEXT = """🌿 *Bienvenue sur TEGRIDY*

Produits Premium · Discret · Fiable

Découvrez notre sélection de produits premium directement depuis notre boutique.

Appuyez sur le bouton ci-dessous pour ouvrir la boutique 👇"""

# ══════════════════════════════════
# SUPABASE
# ══════════════════════════════════
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
        logging.error(f"log_visit error: {e}")

# ══════════════════════════════════
# PETIT SERVEUR HTTP (requis par Render)
# ══════════════════════════════════
class HealthHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"TEGRIDY BOT OK")
    def log_message(self, format, *args):
        pass  # Silence les logs HTTP

def run_health_server():
    server = HTTPServer(('0.0.0.0', 8080), HealthHandler)
    server.serve_forever()

# ══════════════════════════════════
# HANDLERS
# ══════════════════════════════════
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    log_visit(user)

    keyboard = [[
        InlineKeyboardButton(
            "🌿 Ouvrir la boutique",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )
    ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await update.message.reply_photo(
            photo=LOGO_URL,
            caption=WELCOME_TEXT,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )
    except Exception:
        await update.message.reply_text(
            WELCOME_TEXT,
            parse_mode="Markdown",
            reply_markup=reply_markup
        )

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if ADMIN_IDS and user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Accès refusé.")
        return
    if not context.args:
        await update.message.reply_text("Usage : /broadcast Votre message ici")
        return
    message = " ".join(context.args)
    await update.message.reply_text("📢 Envoi en cours...")
    try:
        visits = supabase.table("bot_visits").select("telegram_id").execute()
        ids = list(set([v["telegram_id"] for v in visits.data]))
        sent = 0
        for tid in ids:
            try:
                await context.bot.send_message(chat_id=tid, text=message, parse_mode="Markdown")
                sent += 1
            except Exception:
                pass
        await update.message.reply_text(f"✅ Envoyé à {sent} utilisateurs.")
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {e}")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if ADMIN_IDS and user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ Accès refusé.")
        return
    try:
        visits = supabase.table("bot_visits").select("telegram_id").execute()
        ids = list(set([v["telegram_id"] for v in visits.data]))
        await update.message.reply_text(
            f"📊 *Stats TEGRIDY*\n\n👥 Utilisateurs uniques : {len(ids)}\n📬 Total visites : {len(visits.data)}",
            parse_mode="Markdown"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Erreur : {e}")

# ══════════════════════════════════
# MAIN
# ══════════════════════════════════
def main():
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        level=logging.INFO
    )
    # Lancer le serveur HTTP dans un thread séparé
    t = threading.Thread(target=run_health_server, daemon=True)
    t.start()
    print("✅ Serveur health démarré sur port 8080")

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    print("✅ Bot TEGRIDY démarré — en attente de messages...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
