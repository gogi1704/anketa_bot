import ast
import json
from typing import List, Dict
import html
import resources

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

def extract_tests(agent_response: str):
    if isinstance(agent_response, str):
        try:
            data = json.loads(agent_response)
        except json.JSONDecodeError:
            raise ValueError("Ответ агента не является корректным JSON")
    elif isinstance(agent_response, dict):
        data = agent_response
    else:
        raise TypeError("Ответ агента должен быть строкой JSON или dict")

    return data.get("tests", [])

def extract_recs(response_str: str):
        try:
            data = json.loads(response_str)

            risks: List[str] = data.get("risks", [])
            risks_text = "🔺" + "\n🔺".join(risks)
            recommendations: List[Dict[str, str]] = data.get("recommendations", [])
            if len(recommendations) > 3:
                recommendations = recommendations[:3]

            rec_text = ""
            for rec in recommendations:
                rec_text += "✅ комплекс "
                rec_text += bold_html(rec['test'])
                rec_text += bold_html(f" {resources.TESTS_PRICE[rec['test']]}₽")
                rec_text += " - "
                rec_text += rec['reason']
                rec_text += "\n"

            return bold_html(risks_text), recommendations, rec_text

        except json.JSONDecodeError:
            raise ValueError("Некорректный формат JSON от агента")

def bold_html(text: str) -> str:
    """
    Экранирует текст для HTML и оборачивает его в <b>...</b>
    """
    safe_text = html.escape(text)
    return f"<b>{safe_text}</b>"