from telegram.ext import ContextTypes
from telegram import Update
from db import dialogs_db

async def update_db(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await dialogs_db.sync_to_google_sheets()
    chat_id = update.effective_chat.id
    await context.bot.send_message(chat_id=chat_id,
                                   text= "База данных обновлена")
