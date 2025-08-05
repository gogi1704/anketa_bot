def normalize_name(text: str) -> str:
    return ' '.join(word.capitalize() for word in text.strip().split())