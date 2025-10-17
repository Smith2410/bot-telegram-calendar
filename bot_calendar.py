import json
import base64
import logging
import datetime
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters

# 📜 Configuración de logs
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# 🔑 Token del bot de Telegram
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
if not TELEGRAM_TOKEN:
    raise ValueError("❌ No se encontró TELEGRAM_TOKEN en las variables de entorno.")

# 🔐 Permiso de lectura de Google Calendar
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]

# 🧩 Reconstruye token.json si viene como base64 (Render)
if not os.path.exists("token.json"):
    token_data = os.getenv("TOKEN_JSON_BASE64")
    if token_data:
        with open("token.json", "wb") as f:
            f.write(base64.b64decode(token_data))
        logging.info("✅ token.json reconstruido desde variable de entorno.")
    else:
        logging.warning("⚠️ No se encontró TOKEN_JSON_BASE64. Asegúrate de configurarlo en Render.")

def get_calendar_service():
    """Inicializa y devuelve el servicio de Google Calendar"""
    creds = None

    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    else:
        creds_json = os.getenv("GOOGLE_CREDENTIALS")
        if not creds_json:
            raise ValueError("❌ No se encontró GOOGLE_CREDENTIALS en las variables de entorno.")

        # Guardar credenciales en un archivo temporal
        with open("credentials.json", "w") as f:
            json.dump(json.loads(creds_json), f)

        # ⚠️ No podemos usar InstalledAppFlow en Render (sin navegador)
        raise RuntimeError("❌ Debes subir token.json en Render o usar TOKEN_JSON_BASE64.")

    service = build("calendar", "v3", credentials=creds)
    return service

# 🧠 Comando de inicio con botones
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["📅 Hoy", "👋 Saludar"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)
    await update.message.reply_text(
        "¡Hola! Selecciona una opción 👇",
        reply_markup=reply_markup
    )

# Función para ver clases de hoy
async def hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = get_calendar_service()

    now = datetime.datetime.utcnow()
    inicio_dia = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    fin_dia = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=inicio_dia,
        timeMax=fin_dia,
        singleEvents=True,
        orderBy="startTime"
    ).execute()

    events = events_result.get("items", [])

    if not events:
        await update.message.reply_text("😎 Hoy no tienes clases.")
        return

    msg = "📚 *Clases de hoy:*\n\n"
    for event in events:
        start = event["start"].get("dateTime", event["start"].get("date"))
        hora = datetime.datetime.fromisoformat(start.replace("Z", "+00:00")).strftime("%H:%M")
        curso = event.get("summary", "Sin título")
        salon = event.get("location", "No especificado")
        msg += f"🧾 *Curso:* {curso}\n⏰ *Hora:* {hora}\n🏫 *Salón:* {salon}\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

# Maneja mensajes de los botones
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "📅 Hoy":
        await hoy(update, context)
    elif text == "👋 Saludar":
        await update.message.reply_text("¡Hola! 😎 ¿Listo para tus clases de hoy?")
    else:
        await update.message.reply_text("No entendí eso 😅, usa los botones.")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.run_polling()

if __name__ == "__main__":
    main()
