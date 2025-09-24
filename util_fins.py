from datetime import datetime
import random

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



def validate_date_input(date_text: str):
    """
    Проверяет формат ДД.ММ.ГГГГ (допускает . / - как разделители).
    Проверяет, что дата >= сегодня.
    Возвращает (True, None) если всё ок, иначе (False, error_message).
    """
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

def pick_first_and_two_random(items):
    if len(items) < 3:
        return items
    first = items[0]
    rand_two = random.sample(items[1:], 2)  # берём 2 разных случайных
    return [first] + rand_two
