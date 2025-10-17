import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

# Función para formatear cada evento
def formatear_evento(event):
    # Parsear summary en código, curso y NRC
    summary = event.get("summary", "Sin título")
    match = re.match(r"(.+?)\s+(.+)\s+(\(.+\))", summary)
    if match:
        codigo = match.group(1)
        curso = match.group(2)
        nrc = match.group(3)
    else:
        codigo = "No especificado"
        curso = summary
        nrc = ""

    # Hora
    start = event["start"].get("dateTime", event["start"].get("date"))
    end = event["end"].get("dateTime", event["end"].get("date"))
    start_time = datetime.datetime.fromisoformat(start.replace("Z", "+00:00")).strftime("%H:%M")
    end_time = datetime.datetime.fromisoformat(end.replace("Z", "+00:00")).strftime("%H:%M")
    hora = f"{start_time} - {end_time}"

    # Salón y link
    salon = "Google Meet"
    link = "No disponible"
    if "conferenceData" in event and "entryPoints" in event["conferenceData"]:
        for ep in event["conferenceData"]["entryPoints"]:
            if ep.get("entryPointType") == "video":
                link = ep.get("uri")

    msg = (
        f"🧾 *Curso:* {curso}\n"
        f"⏰ *Hora:* {hora}\n"
        f"🏫 *Salón:* {salon}\n"
        f"🔗 *Link de la clase:* {link}\n"
        f"📌 *Código:* {codigo}\n"
        f"📚 *NRC:* {nrc}\n\n"
    )
    return msg

# Nuevo handler para botones
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📅 Hoy", callback_data="hoy")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("👋 ¡Hola! Selecciona una opción:", reply_markup=reply_markup)

# Callback de botones
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "hoy":
        await mostrar_clases_hoy(update, context)

# Función que reemplaza /hoy usando botón
async def mostrar_clases_hoy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    service = get_calendar_service()

    now = datetime.datetime.utcnow()
    inicio_dia = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat() + "Z"
    fin_dia = now.replace(hour=23, minute=59, second=59, microsecond=0).isoformat() + "Z"

    events_result = service.events().list(
        calendarId="primary",
        timeMin=inicio_dia,
        timeMax=fin_dia,
        singleEvents=True,
        orderBy="startTime",
        conferenceDataVersion=1
    ).execute()

    events = events_result.get("items", [])
    if not events:
        await update.callback_query.message.edit_text("😎 Hoy no tienes clases.")
        return

    msg = "📚 *Clases de hoy:*\n\n"
    for event in events:
        msg += formatear_evento(event)

    await update.callback_query.message.edit_text(msg, parse_mode="Markdown")

# En main, reemplazar CommandHandler("hoy", hoy) por botón
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button))
    app.run_polling()
