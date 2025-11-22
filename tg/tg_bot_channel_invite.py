from telegram import Update,InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


async def send_channel_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # Текст сообщения
    message_text = (
        "Мы хотим быть полезными не только во время медосмотра, но и каждый день. "
        "Рекомендуем обратить внимание на наш телеграм-канал.В канале:\n\n"
        "• советы и рекомендации по здоровью;\n"
        "• разбор анализов и типичных ситуаций;\n"
        "• рекомендации по профилактике и укреплению организма;\n"
        "• полезная информация от наших специалистов.\n\n"
        "Наш канал — ваш надежный помощник и советчик в заботе о здоровье.\n\n"
        "Подписывайтесь, чтобы не пропустить важное! ✅"
    )

    # Кнопка с ссылкой на канал
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Открыть канал", url="https://t.me/human3s")]
    ])

    await context.bot.send_message(
        chat_id=chat_id,
        text=message_text,
        reply_markup=keyboard
    )