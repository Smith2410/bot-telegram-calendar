import logging
import re
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

# Configuración de logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

# Función para obtener los eventos de Google Calendar
def obtener_eventos(service):
    from datetime import datetime, timedelta
    now = datetime.utcnow().isoformat() + 'Z'
    end_of_day = (datetime.utcnow().replace(hour=23, minute=59, second=59)).isoformat() + 'Z'

    events_result = service.events().list(
        calendarId='primary',
        timeMin=now,
        timeMax=end_of_day,
        singleEvents=True,
        orderBy='startTime',
        conferenceDataVersion=1
    ).execute()
    return events_result.get('items', [])

# Función para formatear los eventos
def formatear_evento(event):
    summary = event.get('summary', 'No especificado')
    match = re.match(r"(.+?)\s+(.+)\s+(\(.+\))", summary)
    if match:
        codigo = match.group(1)
        curso = match.group(2)
        nrc = match.group(3)
    else:
        codigo = "No especificado"
        curso = summary
        nrc = ""

    start = event['start'].get('dateTime', event['start'].get('date'))
    end = event['end'].get('dateTime', event['end'].get('date'))

    start_time = datetime.fromisoformat(start).strftime('%H:%M')
    end_time = datetime.fromisoformat(end).strftime('%H:%M')
    hora = f"{start_time} - {end_time}"

    link = "No disponible"
    if 'conferenceData' in event and 'entryPoints' in event['conferenceData']:
        for ep in event['conferenceData']['entryPoints']:
            if ep.get('entryPointType') == 'video':
                link = ep.get('uri')

    mensaje = f"🧾 Curso: {curso}\n"
    mensaje += f"⏰ Hora: {hora}\n"
    mensaje += f"🏫 Salón: Google Meet\n"
    mensaje += f"🔗 Link de la clase: {link}\n"
    mensaje += f"📌 Código: {codigo}\n"
    mensaje += f"📚 NRC: {nrc}\n\n"

    return mensaje

# Función que maneja el botón "Hoy"
async def mostrar_clases_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Cargar credenciales de Google (ajusta según tu proyecto)
    creds = Credentials.from_authorized_user_file('token.json', ['https://www.googleapis.com/auth/calendar.readonly'])
    service = build('calendar', 'v3', credentials=creds)

    eventos = obtener_eventos(service)
    if not eventos:
        await update.callback_query.message.edit_text("No tienes clases hoy 😴")
        return

    mensaje = "📚 Clases de hoy:\n\n"
    for event in eventos:
        mensaje += formatear_evento(event)

    await update.callback_query.message.edit_text(mensaje)

# Función que maneja /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📅 Hoy", callback_data='hoy')],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text('¡Hola! Selecciona una opción:', reply_markup=reply_markup)

# Callback para los botones
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == 'hoy':
        await mostrar_clases_hoy(update, context)

# Crear aplicación del bot
app = ApplicationBuilder().token("TU_TOKEN_AQUI").build()

# Agregar handlers
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

# Ejecutar bot
app.run_polling()
