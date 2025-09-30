from datetime import datetime
import resources
from ai_agents import prompts, open_ai_main

BACK_BUTTON = "⬅️ Назад"

def validate_date_input(date_text: str):
    date_text = (date_text or "").strip()
    if not date_text:
        return False, "Пустая строка. Введите дату в формате ДД.ММ.ГГГГ (пример: 11.11.2025)."

    # Приводим все разделители к точке
    normalized = date_text.replace("-", ".").replace("/", ".")

    try:
        user_date = datetime.strptime(normalized, "%d.%m.%Y").date()
    except ValueError:
        return False, "Введите дату в формате ДД.ММ.ГГГГ (пример: 12.12.2025)."

    today = datetime.today().date()
    if user_date < today:
        return False, "Возможно, вы случайно ввели прошедшую дату. Введите корректное значение, в формате ДД.ММ.ГГГГ (пример: 12.12.2025). "

    return True, None

def is_valid_inn(inn: str) -> bool:
    if not inn.isdigit():
        return False

    length = len(inn)

    def check_digit(digits, coefficients):
        s = sum(int(d) * c for d, c in zip(digits, coefficients))
        return str((s % 11) % 10)

    if length == 10:
        coefficients = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        return inn[-1] == check_digit(inn[:9], coefficients)
    elif length == 12:
        coefficients1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
        coefficients2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8, 0]
        return (inn[-2] == check_digit(inn[:11], coefficients1) and
                inn[-1] == check_digit(inn[:11], coefficients2))
    return False

def validate_inn(inn_text):
    if not inn_text.isdigit() or len(inn_text) not in (10, 12):
        return "❌ ИНН должен состоять только из 10 или 12 цифр. Попробуйте ещё раз."


    if not is_valid_inn(inn_text):
        return "❌ Неверный ИНН. Проверьте и введите снова."


    return "complete"

def validate_age(value: str) -> str:
    if not value.isdigit():
        return "Пожалуйста, введите только цифру равную вашему возрасту (пример ввода : 33)"
    age = int(value)
    if age < 18:
        return "Возраст не может быть меньше 18 лет. Пожалуйста, введите корректное значение."
    if age > 100:
        return "Скорее всего, вы допустили ошибку при введении данных возраста.Но, если вам реально больше 100 лет, то мы безумно рады за вас и желаем вам крепкого здоровья. Если вам больше 100 лет, то введите просто цифру 100. "

    return "complete"  # Всё хорошо

def validate_weight(value: str) -> str:
    if not value.isdigit():
        return "Пожалуйста, введите только цифру равную вашему весу (пример ввода : 84)"
    weight = int(value)
    if weight < 20:
        return "Указан слишком маленький вес. Возможно вы ошиблись при вводе данных. Пожалуйста, введите корректное значение."
    if weight > 250:
        return "Указан слишком большой вес. Возможно вы ошиблись при вводе данных. Пожалуйста, введите корректное значение."

    return "complete"  # Всё хорошо

def validate_height(value: str) -> str:
    if not value.isdigit():
        return "Пожалуйста, введите только цифру равную вашему росту в сантиметрах (пример ввода : 184)"
    height = int(value)
    if height < 140:
        return "Указан слишком маленький рост. Возможно вы ошиблись при вводе данных. Пожалуйста, введите корректное значение."
    if height > 250:
        return "Указан слишком большой рост. Возможно вы ошиблись при вводе данных. Пожалуйста, введите корректное значение."

    return "complete"  # Всё хорошо

def question_smoke():
    keyboard = [
        ["Да", "Нет"],
        [BACK_BUTTON]
    ]
    # reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    return resources.QUESTIONS[5], keyboard

def question_alko():
    keyboard = [
        ["Не употребляю","По праздникам"],
        ["Раз в неделю", "Раз в месяц"],
        [BACK_BUTTON]
    ]
    # reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    return resources.QUESTIONS[6], keyboard

def question_physical():
    keyboard = [
        ["Высокая","Средняя"],
        ["Низкая"],
        [BACK_BUTTON]
    ]
    # reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    return resources.QUESTIONS[7], keyboard

def question_dark_in_eyes():
    keyboard = [
        ["Да","Нет"],
        [BACK_BUTTON]
    ]
    # reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    return resources.QUESTIONS[9], keyboard

def question_sugar():
    keyboard = [
        ["Сахар всегда в норме"],
        ["Повышенный","Пониженный"],
        ["Не мониторю"],
        [BACK_BUTTON]
    ]
    # reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    return resources.QUESTIONS[10], keyboard

def question_sustavi():
    keyboard = [
        ["Да","Нет"],
        [BACK_BUTTON]
    ]
    # reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    return resources.QUESTIONS[11], keyboard

async def question_hyperton(dialog, context):
    user_prompt = prompts.user_prompt_check_hyperton_question.format(dialog=dialog)
    agent_check = await open_ai_main.get_gpt_answer(system_prompt= prompts.system_prompt_check_hyperton_question, user_prompt=user_prompt, context= context)
    return agent_check

async def question_hronic(dialog, context):
    user_prompt = prompts.user_prompt_check_hronic_question.format(dialog=dialog)
    agent_check = await open_ai_main.get_gpt_answer(system_prompt= prompts.system_prompt_check_hronic_question, user_prompt=user_prompt, context= context)
    return agent_check
