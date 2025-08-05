import os
from dotenv import load_dotenv

import resources
from tg.tg_bot_navigation import *
from tg.tg_manager_chat_handlers import *
from db import dialogs_db
import nest_asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import BotCommand, BotCommandScopeDefault


load_dotenv()
TOKEN = os.environ.get("TG_TOKEN")

async def consent_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    # Удалить старое сообщение с кнопками (опционально)
    try:
        await context.bot.delete_message(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id
        )
    except Exception as e:
        print("Ошибка при удалении сообщения:", e)

    if query.data == "consent_yes":
        context.user_data['dialog_state'] = resources.dialog_states['get_number']
        # Записать в диалог
        await dialogs_db.append_answer(telegram_id=update.effective_user.id,text=f"Менеджер сказал: {resources.get_number_text}")
        # Отправить новое сообщение в чат с выбором пользователя
        await context.bot.send_message(chat_id=update.effective_user.id, text= resources.privacy_policy_true)
        await context.bot.send_message(chat_id=update.effective_user.id,text=resources.get_number_text)

    elif query.data == "consent_no":
        context.user_data['dialog_state'] = resources.dialog_states['new_state']

        await context.bot.send_message(chat_id=update.effective_user.id,text=resources.privacy_policy_false)

        await context.bot.send_message(chat_id=update.effective_user.id, text="Спасибо за ответы. До встречи на медосмотре!")

async def main():
    await dialogs_db.init_db()

    application = Application.builder().token(TOKEN).concurrent_updates(True).build()
    print('Бот запущен...')
    await application.bot.set_my_commands([
        BotCommand("start", "Пуск"),
        BotCommand("clear_all", "Очистить все данные"),
    ], scope=BotCommandScopeDefault())

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("clear_all", clear_all))
    application.add_handler(CallbackQueryHandler(consent_button_handler, pattern="^consent_"))



    application.add_handler(CallbackQueryHandler(handle_reply_button_pressed, pattern=r"^reply_to_manager\|"))
    application.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT, handle_manager_reply))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))


    await application.run_polling()
    print('Бот остановлен')

if __name__ == "__main__":
    nest_asyncio.apply()
    import asyncio
    asyncio.run(main())
