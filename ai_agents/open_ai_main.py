import os
from openai import AsyncOpenAI
from dotenv import load_dotenv



load_dotenv()

model_gpt4o_mini = "gpt-4.1-mini-2025-04-14"
model_gpt_5_mini = "gpt-5-mini"
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

ADMIN_CHAT_ID = 1106334332  # сюда твой Telegram ID

async def call_openai_with_auto_key(system_prompt, user_prompt, client, context, model):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        completion = await client.chat.completions.create(
            model=model,
            messages=messages,
        )
        return completion.choices[0].message.content

    except Exception as e:
        err = str(e)

        # проверяем, что это ошибка лимита токенов
        if "insufficient_quota" in err or "exceeded your current quota" in err:
            print("❌ Закончились токены / баланс OpenAI API.")

            # уведомляем админа
            try:
                await context.bot.send_message(
                    chat_id=ADMIN_CHAT_ID,
                    text="⚠️ Внимание! У бота закончились токены / баланс OpenAI API."
                )
            except Exception as notify_err:
                print(f"Не удалось отправить уведомление админу: {notify_err}")

            return "Извините, закончились средства на API. Попробуйте позже."

        else:
            print(f"Другая ошибка: {err}")
            return "error"


async def get_gpt_answer(system_prompt, user_prompt, context, model = model_gpt4o_mini):
    answer = await call_openai_with_auto_key(system_prompt=system_prompt, user_prompt=user_prompt, context= context, client=client, model=model)
    print(answer)
    return answer
