from telegram.ext import ContextTypes
from telegram import Update
from db import dialogs_db

async def handle_channel_post(update: Update, context: ContextTypes.DEFAULT_TYPE):
    post = update.channel_post

    # Получи всех пользователей из своей БД
    user_ids = await dialogs_db.get_all_user_ids()

    # Рассылка текста (или пересылка)
    for user_id in user_ids:
        try:
            if post.text:
                await context.bot.send_message(chat_id=user_id, text=post.text)
            elif post.photo:
                await context.bot.send_photo(
                    chat_id=user_id,
                    photo=post.photo[-1].file_id,
                    caption=post.caption or ""
                )
            elif post.document:
                await context.bot.send_document(
                    chat_id=user_id,
                    document=post.document.file_id,
                    caption=post.caption or ""
                )
            else:
                await context.bot.forward_message(chat_id=user_id, from_chat_id=post.chat_id, message_id=post.message_id)
        except Exception as e:
            print(f"Не удалось отправить сообщение пользователю {user_id}: {e}")
