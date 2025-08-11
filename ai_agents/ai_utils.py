import json
import ast

def filter_by_threat_level(data: dict, threshold: int = 6) -> dict:
    """
    Фильтрует элементы из словаря по уровню угрозы (evaluation).
    Оставляет только те, у которых значение evaluation > threshold.

    :param data: Входной JSON-словарь с полями evaluation.
    :param threshold: Порог угрозы (по умолчанию 6).
    :return: Отфильтрованный словарь.
    """
    return {
        key: value
        for key, value in data.items()
        if value.get("evaluation", 0) > threshold
    }

def parse_complaint_response(json_str):
    try:
        data = json.loads(json_str)
        state = data.get("state", "")
        complaints = data.get("complaints", [])
        return state, complaints
    except json.JSONDecodeError:
        return None, None

def format_medical_risk_from_any(text: str) -> str:
    try:
        # Пытаемся как JSON
        data = json.loads(text)
    except json.JSONDecodeError:
        try:
            # Пробуем как Python-словарь
            data = ast.literal_eval(text)
        except (ValueError, SyntaxError):
            return "❌ Ошибка: не удалось распарсить строку как JSON или dict."

    if not isinstance(data, dict) or not data:
        # return "❌ Ошибка: данные не являются словарём."
        return data
    _, value = next(iter(data.items()))
    if not isinstance(value, dict):
        return "❌ Ошибка: структура вложенных данных неверна."

    description = value.get("description", "—")
    # comment = value.get("comment", "—")

    return f"\nОписание: {description}"
