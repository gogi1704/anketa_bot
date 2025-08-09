from telegraph import Telegraph
import os

telegraph = Telegraph()
telegraph.create_account(short_name='bot')

async def make_telegraph(user_data:dict):

    username = user_data['name']
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    html_path = os.path.join(base_dir, "images", "telegraph_privacy.html")

    with open(html_path, "r", encoding="utf-8") as f:
        html_template = f.read()

    # Подставляем имя пользователя
    html_content = html_template.replace("ФИО / Псевдоним пользователя", f"<b>{username}</b>")

    # Создаём страницу в Telegraph
    response = telegraph.create_page(
        title="Согласие на обработку данных",
        html_content=html_content
    )

    url = "https://telegra.ph/" + response["path"]

    return url
