from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.ext import ContextTypes
import resources
from db.dialogs_db import *

REPLY_TO_MANAGER = 1


async def send_to_chat(update: Update, context: ContextTypes.DEFAULT_TYPE, message_text: str):
    user = update.effective_user
    sent: Message = await context.bot.send_message(chat_id=resources.GROUP_CHAT_ID, text=message_text)
    await save_message_link(sent.message_id, user.id)

async def handle_reply_button_pressed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    _, manager_msg_id = query.data.split("|")
    manager_msg_id = int(manager_msg_id)
    user_id = query.from_user.id

    # Удаляем inline-кнопку (красиво)
    try:
        await context.bot.edit_message_reply_markup(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id,
            reply_markup=None
        )
    except Exception as e:
        print(f"⚠ Не удалось удалить кнопку: {e}")

    # Если пользователь нажал "Написать менеджеру"
    if manager_msg_id == 0:
        await save_user_answer_state(user_id, 0)
        await context.bot.send_message(
            chat_id=user_id,
            text="✍️ Напишите ваш вопрос менеджеру одним сообщением."
        )
        return REPLY_TO_MANAGER

    # Если это реальный ответ на сообщение менеджера
    await save_user_answer_state(user_id, manager_msg_id)

    await context.bot.send_message(
        chat_id=user_id,
        text="✍️ Введите ваш ответ менеджеру:"
    )

    return REPLY_TO_MANAGER


async def handle_manager_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("handle_manager_reply")
    if not update.message.reply_to_message:
        await update.message.reply_text("⚠️ Это не ответ на сообщение пользователя.")
        return

    group_message_id = update.message.reply_to_message.message_id
    user_id = await get_user_id_by_group_message(group_message_id)

    if user_id:
        reply_markup = InlineKeyboardMarkup(
            [[InlineKeyboardButton("✉ Нажми чтобы ввести ответ", callback_data=f"reply_to_manager|{update.message.message_id}")]]
        )

        await context.bot.send_message(
            chat_id=user_id,
            text=f"📩 Сообщение от менеджера:\n\n{update.message.text}\n\n Для ответа нажмите кнопку ниже и введите весь необходимый текст в одном сообщении.",
            reply_markup=reply_markup
        )
        await update.message.reply_text("✅ Ответ отправлен пользователю.")
    else:
        await update.message.reply_text("⚠️ Не удалось найти пользователя по сообщению.")


