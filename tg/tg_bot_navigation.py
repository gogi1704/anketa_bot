from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, Message
from telegram.constants import ChatAction
from ai_agents.open_ai_main import get_gpt_answer
from ai_agents import ai_utils
from db import dialogs_db
import asyncio
from pathlib import Path
import util_fins
from tg import tg_manager_chat_handlers
from tg import tg_bot_telegraph
from telegram.ext import ContextTypes
from utils.anketa_utils import *
from tg import tg_bot_reminder
from tg import tg_bot_channel_invite


image_path = Path(__file__).parent.parent / "images" / "image_andrey.jpg"
async def clear_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    user_id = update.effective_user.id
    await dialogs_db.delete_dialog(user_id)
    await dialogs_db.delete_user(user_id)
    await dialogs_db.delete_user_reply_state(user_id)
    await dialogs_db.delete_anketa(user_id)
    await dialogs_db.cancel_reminders(user_id=update.effective_user.id, application=context.application )
    await start(update, context)

async def stop_privacy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    user_data = await dialogs_db.get_user(user_id)
    await dialogs_db.add_user(user_id=update.effective_user.id,
                              name=user_data['name'],
                              is_medosomotr=user_data['is_medosomotr'],
                              phone="empty",
                              register_date=user_data['register_date'],
                              from_manager="отказ",
                              privacy_policy_date=None,
                              )
    await update.message.reply_text("Разрешения отозваны.")

BACK_BUTTON = "⬅️ Назад"
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    # Пытаемся получить пользователя из БД
    user = await dialogs_db.get_user(user_id)

    # Аргументы после команды /start — там может быть реф-код
    args = context.args
    new_ref = args[0] if args else None

    #
    # === 1. Пользователь заходит впервые ===
    #
    if user is None:
        # Если пользователь заходит по ссылке → фиксируем менеджера
        # Иначе ставим base_url
        ref_code = new_ref if new_ref else "base_url"

        await dialogs_db.add_user(
            user_id=user_id,
            name="",
            from_manager=ref_code
        )

        # Записываем в историю первого сообщения
        await dialogs_db.append_answer(
            telegram_id=user_id,
            text=f"Терапевт сказал:{resources.start_text}\n"
        )

        # Сохраняем состояние
        await dialogs_db.save_user_reply_state(
            user_id,
            manager_msg_id=resources.STATES_USERS_FINALS['start']
        )

        # Отправляем первое сообщение
        with open(image_path, "rb") as image:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=image,
                caption=resources.start_text,
                reply_markup=ReplyKeyboardRemove()
            )

        # Переводим в следующее состояние
        await dialogs_db.set_dialog_state(
            user_id,
            resources.dialog_states_dict["get_name"]
        )
        return

    #
    # === 2. Пользователь уже существует ===
    #
    current_manager = user.get("from_manager")

    # Логика обновления менеджера:
    # Если был base_url/None/"", но пользователь пришёл по реф-ссылке → обновляем
    if current_manager in (None, "", "base_url") and new_ref:
        await dialogs_db.update_user_from_manager(user_id, new_ref)

    #
    # Дальнейшее поведение для старых пользователей
    #
    anketa = await dialogs_db.get_anketa(user_id=user_id)

    if anketa is None:
        # await context.bot.send_message(
        #     chat_id=chat_id,
        #     text="Анкета не найдена. Для прохождения анкеты введите команду: /clear_and_restart"
        # )

        # Записываем в историю первого сообщения
        await dialogs_db.append_answer(
            telegram_id=user_id,
            text=f"Терапевт сказал:{resources.start_text}\n"
        )

        # Сохраняем состояние
        await dialogs_db.save_user_reply_state(
            user_id,
            manager_msg_id=resources.STATES_USERS_FINALS['start']
        )

        # Отправляем первое сообщение
        with open(image_path, "rb") as image:
            await context.bot.send_photo(
                chat_id=chat_id,
                photo=image,
                caption=resources.start_text,
                reply_markup=ReplyKeyboardRemove()
            )

        # Переводим в следующее состояние
        await dialogs_db.set_dialog_state(
            user_id,
            resources.dialog_states_dict["get_name"]
        )
        return
    else:
        reply_markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Написать менеджеру", callback_data="reply_to_manager|0")]
        ])

        await context.bot.send_message(
            chat_id=chat_id,
            text=f"Здравствуйте {user['name']}! Ожидаем вас на осмотре {anketa['osmotr_date']}!\n\n"
                 f"Если у вас есть вопросы — вы можете задать их менеджеру, нажав на кнопку под сообщением.",
            reply_markup=reply_markup
        )

# async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
#     chat_id = update.effective_chat.id
#     user = await dialogs_db.get_user(update.effective_user.id)
#     args = context.args
#
#     if user is None:
#         print(args)
#         if args and len(args) > 0:
#             ref_code = args[0]
#         else:
#             ref_code = "base_url"
#         await dialogs_db.add_user(
#             user_id=update.effective_user.id,
#             name="",
#             from_manager=ref_code
#         )
#
#         await dialogs_db.append_answer(telegram_id=update.effective_user.id, text=f"Терапевт сказал:{resources.start_text}\n")
#         await dialogs_db.save_user_reply_state(update.effective_user.id, manager_msg_id= resources.STATES_USERS_FINALS['start'])
#         with open(image_path, "rb") as image:
#             await context.bot.send_photo(chat_id=chat_id, photo=image, caption=resources.start_text,  reply_markup=ReplyKeyboardRemove())
#
#         await dialogs_db.set_dialog_state(update.effective_user.id, resources.dialog_states_dict["get_name"] )
#     else:
#         anketa = await dialogs_db.get_anketa(user_id=update.effective_user.id)
#         if anketa is None:
#             await context.bot.send_message(chat_id=chat_id, text="Анкета не найдена. Для прохождения анкеты введите команду : /clear_and_restart")
#         else:
#             await context.bot.send_message(chat_id=chat_id, text=f"Здравствуйте {user['name']}! Ожидаем вас на осмотре {anketa['osmotr_date']}!")

async def start_anketa(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['answers'] = []
    context.user_data['position'] = 0

    await dialogs_db.set_dialog_state(update.effective_user.id, resources.dialog_states_dict["anketa"])
    context.user_data['mode'] = 'anketa_osmotr'

    await ask_question(update, context)

async def ask_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pos = context.user_data['position']
    text = resources.QUESTIONS[pos]
    await dialogs_db.append_answer(telegram_id=update.effective_user.id, text=f"Терапевт сказал:{text}\n")
    keyboard = [[BACK_BUTTON]] if pos > 0 else None

    if pos == 5:
        text, keyboard = question_smoke()
    elif pos == 6:
        text, keyboard = question_alko()
    elif pos == 7:
        text, keyboard = question_physical()
    elif pos == 8:
        text, keyboard = question_hyperton()
    elif pos == 9:
        text, keyboard = question_dark_in_eyes()
    elif pos == 10:
        text, keyboard = question_sugar()
    elif pos == 11:
        text, keyboard = question_sustavi()




    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True) if keyboard else ReplyKeyboardRemove()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(1)
    await context.bot.send_message(chat_id=update.effective_chat.id, text=text, reply_markup=reply_markup)


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await dialogs_db.append_answer(telegram_id=update.effective_user.id, text=f"Пациент сказал:{text}\n")
    state = await dialogs_db.get_dialog_state(update.effective_user.id)

    manager_msg_id = await dialogs_db.get_user_answer_state(update.effective_user.id)
    if manager_msg_id is not None:
        # Получили ответ → очищаем состояние
        await dialogs_db.delete_user_answer_state(update.effective_user.id)

        # Отправляем сообщение в группу
        await tg_manager_chat_handlers.send_to_chat(
            update, context,
            message_text=f"📨 Пользователь ответил:\n\n{update.message.text}\n\n\n#Диалог_с_{update.effective_user.id}"
        )

        await update.message.reply_text("✅ Ваш ответ отправлен менеджеру.")
        return

    if state == resources.dialog_states_dict["anketa"]:
        await anketa_dialog(update, context)

    elif state == resources.dialog_states_dict['get_name']:
        await name_dialog(update, context)

    # elif state == resources.dialog_states_dict['medosmotr_in_company']:
    #     await medosmotr_in_company_dialog(update, context)

    elif state == resources.dialog_states_dict['is_has_complaint']:
        await is_has_complaint_dialog(update, context)

    elif state == resources.dialog_states_dict['terapevt_consult']:
        await terapevt_consult_dialog(update, context)

    # elif state == resources.dialog_states_dict['change_anketa']:
    #     await change_anketa_dialog(update, context)

    elif state == resources.dialog_states_dict['is_ready_to_consult']:
        await is_ready_to_consult_dialog(update, context)

    elif state == resources.dialog_states_dict['get_number']:
        await get_number_dialog(update, context)

    elif state == resources.dialog_states_dict['new_state']:
        user = await dialogs_db.get_user(update.effective_user.id)
        anketa = await  dialogs_db.get_anketa(user_id=update.effective_user.id)
        name = user["name"]
        date = anketa["osmotr_date"]

        await update.message.reply_text(f"Приветствую {name}. До встречи на осмотре {date}")

    else:
        print("handle_text_message - else")


async def name_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    user = await dialogs_db.get_user(update.effective_user.id)
    text = update.message.text
    user_id = update.effective_user.id
    name = util_fins.normalize_name(text)

    print(user)

    await dialogs_db.add_user(user_id=user_id, name=name, from_manager= user["from_manager"],register_date=user['register_date'],)
    await dialogs_db.set_dialog_state(update.effective_user.id, resources.dialog_states_dict["anketa"])
    answer = resources.second_text.format(user_name=name, user_id=user_id)

    # doc_say = answer + "\n" + resources.medosmotr_text
    # await dialogs_db.append_answer(telegram_id=update.effective_user.id,
    #                                text=f"Терапевт сказал:{doc_say}\n")

    msg = await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=answer
    )
    await context.bot.pin_chat_message(
        chat_id=msg.chat.id,
        message_id=msg.message_id
    )
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    await asyncio.sleep(1)
    await start_anketa(update, context)

async def anketa_dialog(update, context):
    text = update.message.text
    user_id = update.effective_user.id

    if context.user_data.get("mode") == "anketa_osmotr":
        questions = resources.QUESTIONS
        questions_small = resources.QUESTIONS_SMALL
    else:
        questions = resources.QUESTIONS_IF_NOT_OSMOTR
        questions_small = resources.QUESTIONS_SMALL_IF_NOT_OSMOTR

    pos = context.user_data['position']

    if text == BACK_BUTTON:
        if pos > 0:
            context.user_data['position'] -= 1
            context.user_data['answers'].pop()
        await ask_question(update, context)
        return

    result = await util_fins.validate_anketa_questions(position=pos, user_say=text, text= text, context= context, update= update)
    if result == "empty":
        await update.message.reply_text("Для ответа выберите один вариантов, нажав на соответствующую кнопку!")
        return

    if result != "complete":
        await update.message.reply_text(result)
        return


    if pos != 12:
        context.user_data['answers'].append(text)
    context.user_data['position'] += 1

    if context.user_data['position'] < len(questions):
        await ask_question(update, context)
        return
    else:
        # await update.message.reply_text("Спасибо за ответы! Анкета для прохождения осмотра заполнена.")
        # Завершение анкеты
        await dialogs_db.save_user_reply_state(update.effective_user.id, manager_msg_id=resources.STATES_USERS_FINALS['final_anketa'])

        wait_msg: Message = await update.message.reply_text("⏳ анализирую анкету...")
        try:
            anketa_answers = context.user_data['answers']
            await add_to_anketa(update, context,anketa_answers)
            context.user_data['mode'] = None

            anketa = "\n".join(
                f"{i + 1}. {q} — {a}" for i, (q, a) in enumerate(zip(questions_small, anketa_answers))
            )
            # user = await dialogs_db.get_user(update.effective_user.id)
            # user_name = user["name"]
            keyboard_yes_no = [
                [InlineKeyboardButton("Да", callback_data='dop_yes')],
                [InlineKeyboardButton("Нет", callback_data='dop_no')]
            ]

            keyboard_tests_info = InlineKeyboardMarkup([
                [InlineKeyboardButton("Ознакомиться с комплексами",
                                      url=f"https://telegra.ph/CHek-apy-po-laboratorii-OOO-CHelovek-09-10?ver={int(datetime.now().timestamp())}"
                                      )]
            ])

            reply_markup = InlineKeyboardMarkup(keyboard_yes_no)

            #TУТ ЗАПРОС К НЕЙРОНКЕ НА ПОЛУЧЕНИЕ РЕКОМЕГДАЦИЙ

            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

            user_prompt = prompts.user_prompt_new_rec_tests.format(anketa = anketa)
            recs = await get_gpt_answer(system_prompt= prompts.system_prompt_new_rec_tests, user_prompt= user_prompt, context= context)
            risks, recommendations_list, rec_text = ai_utils.extract_recs(recs)

            risk_text = f"Проанализировав ваши ответы, я выявил некоторые риски:\n{risks}\n\n"
            recomendation_text = f"На основе этого анализа, я сформировал ПЕРСОНАЛЬНУЮ РЕКОМЕНДАЦИЮ.\nВам полезно пройти комплекс исследований:\n{rec_text}"

            # user_prompt = prompts.user_prompt_rec_tests.format(anketa = f"Имя - {user_name}\n" + anketa)
            # rec_tests_json = await get_gpt_answer(system_prompt= prompts.system_prompt_rec_tests , context= context, user_prompt= user_prompt,model= "gpt-5-mini"  )
            # tests_list = ai_utils.extract_tests(rec_tests_json)

            if len(recommendations_list) > 0:
                await update.message.reply_text(risk_text, parse_mode="HTML")
                await asyncio.sleep(4)
                await update.message.reply_text(recomendation_text, parse_mode="HTML")
                await asyncio.sleep(5)
                await update.message.reply_text(text="Также, вы можете выбрать абсолютно любой из представленных комплексов услуг.\nОзнакомиться со всеми услугами можно нажав на кнопку под этим сообщением👇",reply_markup= keyboard_tests_info)

                await asyncio.sleep(6)
                # await update.message.reply_text("Вы хотели бы сдать дополнительные анализы на осмотре?", reply_markup= reply_markup )
                await update.message.reply_text(resources.by_dop_tests_or_not_text,reply_markup=reply_markup)
            else:

                await dialogs_db.append_answer(telegram_id=user_id, text=f"Терапевт сказал:{resources.is_has_complaint_text}")
                await dialogs_db.set_dialog_state(update.effective_user.id, resources.dialog_states_dict["is_has_complaint"])
                await update.message.reply_text(resources.is_has_complaint_text, reply_markup=ReplyKeyboardRemove())

        finally:
                # 4. Удаляем сообщение с часами (в любом случае)
                try:
                    await wait_msg.delete()
                except Exception as e:
                    print(f"⚠️ Не удалось удалить сообщение: {e}")



async def handle_pay(update, context):
    query = update.callback_query
    answer = query.data
    chosen = ", ".join(context.user_data["selected_tests"]) or "ничего"
    user_data = await dialogs_db.get_user(user_id=update.effective_user.id)
    anketa = await dialogs_db.get_anketa(user_id=update.effective_user.id)
    date = anketa["osmotr_date"]
    date_obj = datetime.strptime(date, "%d.%m.%Y")

    if answer == "pay_yes":
        # keyboard = InlineKeyboardMarkup([
        #     [InlineKeyboardButton("🔔 Напомнить за день до визита", callback_data=f"remind:{date_obj.isoformat()}")]
        # ])

        await query.message.reply_text("Спасибо! Оплата прошла успешно.(прислать чек)Поздравляем, Вы полностью готовы к визиту!(когда подключим платежку)")
        await asyncio.sleep(2)
        await query.message.reply_text(f"Ваша дата осмотра :{date}.\nПри себе необходимо иметь паспорт.Все вопросы Вы можете задать менеджеру лаборатории оп телефону ... \nХорошего дня и до встречи!")

        context.user_data["remind_data"] = f"remind:{date_obj.isoformat()}"
        await tg_bot_reminder.handle_remind(update, context)

        text_to_manager = f"Пользователь: {user_data['name']} (ID- {update.effective_user.id}).\nПланирует пройти дополнительные обследования на осмотре (и уже оплатил){date}.\n\nОбследования: {chosen} "
        await tg_manager_chat_handlers.send_to_chat(update, context, text_to_manager)
        await asyncio.sleep(2)

    elif answer == "pay_no":
        await query.message.reply_text(
            f"Спасибо за прохождение анкетирования! Ваша анкета передана менеджеру.\nНа приеме скажите ему Ваш ID номер {update.effective_user.id}.\nЕсли у Вас возникнут вопросы по дополнительным обследованиям, Вы всегда можете проконсультироваться с нашим менеджером в день осмотра.\nБудем ждать Вас {date} на осмотре!")
        await dialogs_db.set_dialog_state(update.effective_user.id,resources.dialog_states_dict["new_state"])

    elif answer == "pay_change":
        await choose_tests(update, context)


async def handle_dop_analizy(update, context):
    query = update.callback_query
    answer = query.data  # Получаем ответ, "yes" или "no"
    context.user_data["dop_message_id"] = query.message.message_id

    message = query.message  # Сообщение, на которое нажали
    # Удаляем сообщение с кнопками
    await message.delete()

    if answer == 'dop_yes':
        await dialogs_db.save_user_reply_state(update.effective_user.id,
                                               manager_msg_id=resources.STATES_USERS_FINALS['dop_true'])
        await choose_tests(update, context)

    elif answer == "dop_no":
        await dialogs_db.save_user_reply_state(update.effective_user.id,
                                               manager_msg_id=resources.STATES_USERS_FINALS['dop_false'])
        await dialogs_db.set_dialog_state(update.effective_user.id,
                                          resources.dialog_states_dict["new_state"])

        keyboard = [
            [InlineKeyboardButton("Хочу сдать анализы", callback_data='dopDop_yes')],
            [InlineKeyboardButton("Спасибо, но нет", callback_data='dopDop_no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        anketa = await dialogs_db.get_anketa(user_id=update.effective_user.id)
        date = anketa["osmotr_date"]

        await update.effective_message.reply_text(resources.get_tests_answer_false_text, reply_markup= reply_markup)


async def handle_dopDop_analizy(update, context):
    query = update.callback_query
    answer = query.data  # Получаем ответ, "yes" или "no"
    context.user_data["dop_message_id"] = query.message.message_id

    message = query.message  # Сообщение, на которое нажали
    await message.delete()

    if answer == 'dopDop_yes':
        await dialogs_db.save_user_reply_state(update.effective_user.id,
                                               manager_msg_id=resources.STATES_USERS_FINALS['dop_dop_true'])
        await choose_tests(update, context)

    elif answer == "dopDop_no":
        await dialogs_db.save_user_reply_state(update.effective_user.id,
                                               manager_msg_id=resources.STATES_USERS_FINALS['dop_dop_false'])
        await dialogs_db.set_dialog_state(update.effective_user.id,
                                          resources.dialog_states_dict["new_state"])

        anketa = await dialogs_db.get_anketa(user_id=update.effective_user.id)
        date = anketa["osmotr_date"]
        await update.effective_message.reply_text(f"Спасибо за ответ!Вы так же можете выбрать подходящие исследования непосредственно перед осмотром.")
        await update.effective_message.reply_text(f"Будем ждать Вас на осмотре {date}")
        await asyncio.sleep(3)
        await tg_bot_channel_invite.send_channel_invite(update, context)


# --- формируем клавиатуру ---
def get_tests_keyboard(selected_tests: set):
    keyboard = []

    for idx, test in enumerate(resources.TESTS):
        # текст кнопки
        text = test
        if test in selected_tests:
            text = f"✅ *{test}*"   # жирный + галочка

        # callback_data используем короткий ID (индекс), а не весь текст
        callback_data = f"toggle:{idx}"

        # длинные названия — в отдельном ряду, короткие можно по 2
        if len(test) > 15:
            keyboard.append([InlineKeyboardButton(text, callback_data=callback_data)])
        else:
            if not keyboard or len(keyboard[-1]) == 2 or "ГОТОВО" in keyboard[-1][0].text:
                keyboard.append([])
            keyboard[-1].append(InlineKeyboardButton(text, callback_data=callback_data))

    # кнопка "ГОТОВО" внизу
    keyboard.append([InlineKeyboardButton("ГОТОВО", callback_data="done")])
    return InlineKeyboardMarkup(keyboard)

# --- выбор тестов ---
async def choose_tests(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    context.user_data["selected_tests"] = set()  # список выбранных сбрасываем

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=resources.choose_tests_text,
        reply_markup=get_tests_keyboard(context.user_data["selected_tests"]),
        parse_mode="Markdown"
    )

# --- обработка кликов по кнопкам ---
async def handle_toggle(update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if "selected_tests" not in context.user_data:
        context.user_data["selected_tests"] = set()

    data = query.data

    if data.startswith("toggle:"):
        idx = int(data.split(":", 1)[1])  # достаём индекс
        test = resources.TESTS[idx]       # получаем название теста

        if test in context.user_data["selected_tests"]:
            context.user_data["selected_tests"].remove(test)
        else:
            context.user_data["selected_tests"].add(test)

        # обновляем клавиатуру
        await query.edit_message_reply_markup(
            reply_markup=get_tests_keyboard(context.user_data["selected_tests"])
        )

    elif data == "done":
        chosen = ", ".join(context.user_data["selected_tests"]) or "ничего"
        user_data = await dialogs_db.get_user(user_id= update.effective_user.id)
        anketa = await dialogs_db.get_anketa(user_id=update.effective_user.id)
        message = query.message  # Сообщение, на которое нажали


        await dialogs_db.add_user(user_id=update.effective_user.id,
                                  name=user_data['name'],
                                  is_medosomotr=user_data['is_medosomotr'],
                                  register_date=user_data['register_date'],
                                  from_manager = user_data['from_manager'],
                                  privacy_policy_date = user_data['privacy_policy_date'],
                                  get_dop_tests = chosen
                                  )

        text_to_manager = f"Пользователь: {user_data['name']} (ID- {update.effective_user.id}).\nПланирует пройти дополнительные обследования на осмотре.\n\nОбследования: {chosen} "
        await tg_manager_chat_handlers.send_to_chat(update, context, text_to_manager)

        if "dop_message_id" in context.user_data:
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=context.user_data["dop_message_id"]
                )
                await query.message.delete()
            except Exception as e:
                print(f"Не удалось удалить сообщение с вопросом: {e}")

        await dialogs_db.set_dialog_state(update.effective_user.id,
                                          resources.dialog_states_dict["new_state"])

        text, price = await util_fins.get_list_and_price(list_tests=context.user_data["selected_tests"] , tests_price= resources.TESTS_PRICE)
        # Удаляем сообщение с кнопками
        await message.delete()
        await dialogs_db.save_user_reply_state(update.effective_user.id,
                                               manager_msg_id=resources.STATES_USERS_FINALS['victory'])

        await query.message.reply_text(text=resources.get_final_text_tests_with_price2(tests=text, price = price), parse_mode= "HTML")

        await asyncio.sleep(2)
        await tg_bot_channel_invite.send_channel_invite(update, context)


async def is_has_complaint_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = "empty"
    user_dialog = await dialogs_db.get_dialog(update.effective_user.id)
    user_prompt = prompts.user_prompt_is_has_complaint.format(dialog = user_dialog )

    complaint_json = await get_gpt_answer(system_prompt= prompts.system_prompt_is_has_complaint, context= context, user_prompt= user_prompt)
    terapevt_state, complaints = ai_utils.parse_complaint_response(complaint_json)
    print(complaints)

    if terapevt_state == "complaint_empty":
        keyboard = [
            [InlineKeyboardButton("Да", callback_data='dop_yes')],
            [InlineKeyboardButton("Нет", callback_data='dop_no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            text=resources.no_complaints_text,
            parse_mode="HTML")

        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(2)

        # await update.message.reply_text(
        #     text="Также, перед мед-осмотром, вы можете выбрать любой из представленных комплексов услуг и сдать анализы не жертвуя личным временем (<a href='https://telegra.ph/CHek-apy-po-laboratorii-OOO-CHelovek-09-10'>ознакомиться можно тут</a>).",
        #     parse_mode="HTML")

        # await update.message.reply_text("Вы хотели бы сдать дополнительные анализы на осмотре?",
        #                                 reply_markup=reply_markup)
        await update.message.reply_text(text= resources.by_dop_tests_or_not_text,parse_mode = "HTML", reply_markup=reply_markup)


    elif terapevt_state == "complaint_true":
            await dialogs_db.set_dialog_state(update.effective_user.id,
                                          resources.dialog_states_dict["terapevt_consult"])
            # тут добавление жалоб в бд
            context.user_data['user_problem'] = str(complaints)
            await terapevt_consult_dialog(update, context)

    elif terapevt_state is None:
        await dialogs_db.append_answer(telegram_id=update.effective_user.id, text=f"Терапевт сказал:{complaint_json}\n")
        text = complaint_json

    if text != "empty":
        await context.bot.send_message(chat_id=update.effective_chat.id, text=text)

async def terapevt_consult_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    user_problem = context.user_data['user_problem']
    dialog = await dialogs_db.get_dialog(update.effective_user.id)
    user_prompt_terapevt_stop = prompts.user_prompt_stop_terapevt.format(user_problem =user_problem ,dialog = dialog)
    is_stop_terapevt = await get_gpt_answer(system_prompt= prompts.system_prompt_stop_terapevt, context= context, user_prompt= user_prompt_terapevt_stop)

    if is_stop_terapevt == "terapevt_complete":
        user_prompt_get_recs = prompts.user_prompt_get_rec.format(dialog = dialog)
        recs = await get_gpt_answer(system_prompt=prompts.system_prompt_get_rec, context= context, user_prompt= user_prompt_get_recs)
        anketa = await dialogs_db.get_anketa(update.effective_user.id)

        await update.message.reply_text(recs)
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(5)

        await update.message.reply_text(
            text=resources.yes_complaints_text,
            parse_mode="HTML")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
        await asyncio.sleep(5)

        keyboard = [
            [InlineKeyboardButton("Да", callback_data='dop_yes')],
            [InlineKeyboardButton("Нет", callback_data='dop_no')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        # await update.message.reply_text(
        #     text="Во время медосмотра, рекомендуем пройти доп обследования. Вы можете выбрать любой из представленных комплексов услуг и сдать анализы не жертвуя личным временем. (<a href='https://telegra.ph/CHek-apy-po-laboratorii-OOO-CHelovek-09-10'>ознакомиться можно тут</a>).",
        #     parse_mode="HTML")
        await update.message.reply_text(text=resources.by_dop_tests_or_not_text,
                                        reply_markup=reply_markup)


        return


    elif is_stop_terapevt == "terapevt_uncomplete":
        user_prompt_terapevt_consult = prompts.user_prompt_terapevt_consult.format(user_problem=user_problem,
                                                                                   dialog=dialog)
        terapevt_say = await get_gpt_answer(system_prompt=prompts.system_prompt_terapevt_consult, context= context,
                                            user_prompt=user_prompt_terapevt_consult)

        text = terapevt_say
        await dialogs_db.append_answer(telegram_id=update.effective_user.id, text=f"Терапевт сказал:{terapevt_say}")

    else:
        text = "error, try again"

    await update.message.reply_text(text,reply_markup=ReplyKeyboardRemove())



async def is_ready_to_consult_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    user_dialog = await dialogs_db.get_dialog(update.effective_user.id)

    user_prompt_is_ready = prompts.user_prompt_is_ready_to_consult.format(dialog = user_dialog)
    manager_say = await get_gpt_answer(system_prompt= prompts.system_prompt_is_ready_to_consult, context= context, user_prompt= user_prompt_is_ready)

    if manager_say == "user_true":
        await send_privacy_policy_message(update, context)
        return
    elif manager_say == "user_false":
        await dialogs_db.set_dialog_state(update.effective_user.id,
                                          resources.dialog_states_dict["new_state"])
        manager_say = "Спасибо за ответы. До встречи на мед осмотре. Если что - я тут👋🏻"

    await dialogs_db.append_answer(telegram_id=update.effective_user.id, text=f"Менеджер сказал:{manager_say}")
    await update.message.reply_text(manager_say)

async def get_number_dialog(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)
    user_dialog = await dialogs_db.get_dialog(update.effective_user.id)

    user_prompt_get_number = prompts.user_prompt_get_number.format(dialog = user_dialog)
    manager_say = await get_gpt_answer(system_prompt= prompts.system_prompt_get_number, context= context, user_prompt= user_prompt_get_number)

    if "get_number_false" in manager_say:
        await dialogs_db.set_dialog_state(update.effective_user.id,
                                          resources.dialog_states_dict["new_state"])
        manager_say = "В таком случае онлайн встреча с терапевтом не состоится. До встречи на мед осмотре. Если что я тут"

    elif manager_say.startswith("user_num:"):
        await dialogs_db.set_dialog_state(update.effective_user.id,
                                          resources.dialog_states_dict["new_state"])

        user_data = await dialogs_db.get_user(update.effective_user.id)
        parts = manager_say.split("user_num:")
        number = "error"
        if len(parts) > 1:
            number = parts[1].strip()
            print(number)

        await dialogs_db.add_user(user_id=update.effective_user.id,
                                  name=user_data['name'],
                                  is_medosomotr=user_data['is_medosomotr'],
                                  phone= number,
                                  register_date=user_data['register_date'],
                                  from_manager = user_data['from_manager'],
                                  privacy_policy_date = user_data['privacy_policy_date']
                                  )
        anketa = await dialogs_db.get_anketa(update.effective_user.id)
        # тут достаем жалоб из бд
        complaints = ai_utils.format_medical_risk_from_any(text = context.user_data['user_problem'])
        text_to_manager = f"Пользователь: {user_data['name']}({number}).\n{resources.get_anketa_formatted(anketa)}\n\n{complaints}\n\n\n#Диалог_с_{update.effective_user.id} "
        await tg_manager_chat_handlers.send_to_chat(update, context, text_to_manager)
        manager_say = resources.get_number_complete_text

    await dialogs_db.append_answer(telegram_id=update.effective_user.id, text=f"Менеджер сказал:{manager_say}")
    await update.message.reply_text(manager_say)
    #Отправка в чат с менеджером тут



async def add_to_anketa(update: Update, context: ContextTypes.DEFAULT_TYPE, answers ):

    if context.user_data.get("mode") == "anketa_osmotr":
        await dialogs_db.add_or_update_anketa(user_id=update.effective_user.id,
                                              organization_or_inn=answers[0],
                                              osmotr_date= answers[1],
                                              age= answers[2],
                                              weight= answers[3],
                                              height= answers[4],
                                              smoking= answers[5],
                                              alcohol= answers[6],
                                              physical_activity= answers[7],
                                              hypertension= answers[8],
                                              darkening_of_the_eyes = answers[9],
                                              sugar= answers[10],
                                              joint_pain = answers[11],
                                              chronic_diseases= answers[12])
    else:
        await dialogs_db.add_or_update_anketa(user_id=update.effective_user.id,
                                              organization_or_inn=answers[0],
                                              osmotr_date= answers[1],
                                              age= answers[2],
                                              weight= answers[3],
                                              height= answers[4],
                                              smoking= answers[5],
                                              alcohol= answers[6],
                                              physical_activity= answers[7],
                                              hypertension= answers[8],
                                              darkening_of_the_eyes = answers[9],
                                              sugar= answers[10],
                                              joint_pain = answers[11],
                                              chronic_diseases= answers[12])

async def send_privacy_policy_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_data = await dialogs_db.get_user(update.effective_user.id)
    url = await tg_bot_telegraph.make_telegraph(user_data)
    keyboard = [
        [
            InlineKeyboardButton("✅ Согласен с обработкой данных", callback_data="consent_yes"),
            InlineKeyboardButton("❌ Отказаться", callback_data="consent_no"),
        ],
        # [
        #     InlineKeyboardButton("📖 Подробнее", url= url)
        # ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = resources.privacy_text.format(url = url)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode="HTML")
