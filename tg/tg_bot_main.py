import os
from dotenv import load_dotenv
from tg.tg_bot_navigation import *
from tg.tg_manager_chat_handlers import *
from tg.tg_bot_channel_funs import *
from tg.tg_error_handlers import error_handler
from db import dialogs_db
import nest_asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler
from telegram import BotCommand, BotCommandScopeDefault


load_dotenv()
TOKEN = os.environ.get("TG_TOKEN")

async def consent_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_data = await dialogs_db.get_user(user_id=update.effective_user.id)
    await query.answer()
    try:
        await context.bot.delete_message(
            chat_id=query.message.chat.id,
            message_id=query.message.message_id
        )
    except Exception as e:
        print("Ошибка при удалении сообщения:", e)

    if query.data == "consent_yes":
        await dialogs_db.set_dialog_state(update.effective_user.id, resources.dialog_states_dict["get_number"])

        await dialogs_db.add_user(user_id=update.effective_user.id,
                                  name=user_data['name'],
                                  is_medosomotr=user_data['is_medosomotr'],
                                  phone= user_data["phone"],
                                  register_date=user_data['register_date'],
                                  privacy_policy = "согласие",
                                  privacy_policy_date = datetime.datetime.now(datetime.UTC),
                                  )
        # Записать в диалог
        await dialogs_db.append_answer(telegram_id=update.effective_user.id,text=f"Менеджер сказал: {resources.get_number_text}")
        # Отправить новое сообщение в чат с выбором пользователя
        await context.bot.send_message(chat_id=update.effective_user.id, text= resources.privacy_policy_true)

        await context.bot.send_message(chat_id=update.effective_user.id,text=resources.get_number_text)

    elif query.data == "consent_no":
        await dialogs_db.set_dialog_state(update.effective_user.id, resources.dialog_states_dict["new_state"])
        await dialogs_db.add_user(user_id=update.effective_user.id,
                                  name=user_data['name'],
                                  is_medosomotr=user_data['is_medosomotr'],
                                  phone= user_data["phone"],
                                  register_date=user_data['register_date'],
                                  privacy_policy = "отказ",
                                  privacy_policy_date = datetime.datetime.now(datetime.UTC),
                                  )

        await context.bot.send_message(chat_id=update.effective_user.id,text=resources.privacy_policy_false)

        await context.bot.send_message(chat_id=update.effective_user.id, text="Спасибо за ответы. До встречи на медосмотре!")

async def main():
    await dialogs_db.init_db()
    asyncio.create_task(periodic_sync())

    application = Application.builder().token(TOKEN).concurrent_updates(True).build()
    print('Бот запущен...')
    await application.bot.set_my_commands([
        BotCommand("start", "Пуск"),
        BotCommand("clear_all", "Очистить все данные"),
        BotCommand("stop_privacy", "Отмена обработки персональных данных"),
    ], scope=BotCommandScopeDefault())

    application.add_error_handler(error_handler)

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler("clear_all", clear_all))
    application.add_handler(CommandHandler("stop_privacy", stop_privacy))
    application.add_handler(CallbackQueryHandler(consent_button_handler, pattern="^consent_"))


    # application.add_handler(MessageHandler(filters.ChatType.CHANNEL, handle_channel_post))

    application.add_handler(CallbackQueryHandler(handle_reply_button_pressed, pattern=r"^reply_to_manager\|"))
    application.add_handler(MessageHandler(filters.ChatType.GROUPS & filters.TEXT, handle_manager_reply))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))


    await application.run_polling()
    print('Бот остановлен')

if __name__ == "__main__":
    import asyncio


    nest_asyncio.apply()
    asyncio.run(main())

