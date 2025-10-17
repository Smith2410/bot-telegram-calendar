import logging
import datetime
import os.path
import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# 🔑 Tu token del bot de Telegram
TOKEN = os.getenv("TELEGRAM_TOKEN")
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

# 🔐 Permiso para leer tu Google Calendar
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# 📜 Logs para depuración
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

def get_calendar_service():
    creds = None
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
    return build('calendar', 'v3', credentials=creds)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hola, usa /hoy para ver si tienes clases hoy.")

async def hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = get_calendar_service()

    # Fecha actual (UTC)
    now = datetime.datetime.utcnow()
    inicio_dia = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + 'Z'
    fin_dia = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + 'Z'

    # Buscar eventos solo de hoy
    events_result = service.events().list(
        calendarId='primary',
        timeMin=inicio_dia,
        timeMax=fin_dia,
        singleEvents=True,
        orderBy='startTime'
    ).execute()

    events = events_result.get('items', [])

    if not events:
        await update.message.reply_text("😎 Hoy no tienes clases.")
        return

    msg = "📚 *Clases de hoy:*\n\n"
    for event in events:
        # Intenta obtener hora y lugar si existen
        start = event['start'].get('dateTime', event['start'].get('date'))
        hora = datetime.datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%H:%M')
        curso = event.get('summary', 'Sin título')
        salon = event.get('location', 'No especificado')
        msg += f"🧾 *Curso:* {curso}\n⏰ *Hora:* {hora}\n🏫 *Salón:* {salon}\n\n"

    await update.message.reply_text(msg, parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("hoy", hoy))
    app.run_polling()

if __name__ == "__main__":
    main()
