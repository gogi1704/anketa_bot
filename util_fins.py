import random
from utils.anketa_utils import *
from db import dialogs_db
import resources


def normalize_name(text: str) -> str:
    return ' '.join(word.capitalize() for word in text.strip().split())

async def get_info_by_tests(tests_list, test_info):
    text = ""
    for test in tests_list:
        text += f"{test_info[test]}\n\n"
    return text

async def get_list_and_price(list_tests,tests_price ):
    text = ""
    price = 0
    for test in list_tests:
        text += f"{test} - {tests_price[test]}\n"
        price += tests_price[test]

    return text, price

def pick_first_and_two_random(items):
    if len(items) < 3:
        return items
    first = items[0]
    rand_two = random.sample(items[1:], 2)  # берём 2 разных случайных
    return [first] + rand_two

async def validate_anketa_questions(position, user_say, text,update = None,context = None):
    # Вопросы которые проверяются на формат
    # ИНН
    if position == 0:
        result = validate_inn(user_say)
        return result
    # ДАТА ОСМОТРА
    elif position == 1:
        ok, err = validate_date_input(user_say)
        if not ok:
            # Отправляем конкретную ошибку и не продвигаем позицию — остаёмся на том же вопросе
            return err
        else:
            return "complete"
    # ВОЗРАСТ
    elif position == 2:
        result = validate_age(user_say)
        return result
    # ВЕС
    elif position == 3:
        result = validate_weight(user_say)
        return result
    # РОСТ
    elif position == 4:
        result = validate_height(user_say)
        return result

    # Вопросы с кнопками
    # ВОПРОС С КНОПКАМИ- КУРЕНИЕ
    elif position == 5:
       if text in ["Да", "Нет", BACK_BUTTON]:
           return "complete"
       else:
           return "empty"
    # ВОПРОС С КНОПКАМИ- Алкоголь
    elif position == 6:
        if text in ["Не употребляю", "По праздникам","Раз в неделю","Раз в месяц", BACK_BUTTON]:
            return "complete"
        else:
            return "empty"
    # ВОПРОС С КНОПКАМИ- Физическая активность
    elif position == 7:
       if text in ["Высокая", "Средняя", "Низкая", BACK_BUTTON]:
           return "complete"
       else:
           return "empty"
    # ВОПРОС С КНОПКАМИ- Давление
    elif position == 8:
       if text in ["В норме", "Повышенное", "Не мониторю", "Ниже 120/80", BACK_BUTTON]:
           return "complete"
       else:
           return "empty"
    # ВОПРОС С КНОПКАМИ - Потемнения в глазах
    elif position == 9:
        if text in ["Да", "Нет", BACK_BUTTON]:
            return "complete"
        else:
            return "empty"
    # ВОПРОС С КНОПКАМИ - Сахар
    elif position == 10:
        if text in ["Сахар всегда в норме", "Встречались случаи повышенного","Повышенный","Пониженный","Не мониторю", BACK_BUTTON]:
            return "complete"
        else:
            return "empty"
    # ВОПРОС С КНОПКАМИ - Бывает ли боль в суставах
    elif position == 11:
        if text in ["Да","Нет", BACK_BUTTON]:
            return "complete"
        else:
            return "empty"

    #Вопросы с нейро-проверкой
    # elif position == 8:
    #     dialog = await dialogs_db.get_dialog(update.effective_user.id)
    #     result = await question_hyperton(dialog, context)
    #     if "complete" in result:
    #         context.user_data['answers'].append(result)
    #         await dialogs_db.delete_dialog(update.effective_user.id)
    #         return "complete"
    #     else:
    #         await dialogs_db.append_answer(telegram_id=update.effective_user.id, text=f"Терапевт сказал:{result}\n")
    #         return result

    elif position == 12:
        dialog = await dialogs_db.get_dialog(update.effective_user.id)
        result = await question_hronic(dialog, context)
        if "complete" in result:
            context.user_data['answers'].append(result)
            await dialogs_db.delete_dialog(update.effective_user.id)
            return "complete"
        else:
            await dialogs_db.append_answer(telegram_id=update.effective_user.id, text=f"Терапевт сказал:{result}\n")
            return result

    else:
        return  "complete"
