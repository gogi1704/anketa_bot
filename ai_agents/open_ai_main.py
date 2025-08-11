import os
from openai import AsyncOpenAI
from dotenv import load_dotenv



load_dotenv()

model_gpt4o_mini = "gpt-4.1-mini-2025-04-14"
model_gpt_4o = "gpt-4o-2024-08-06"
env_path = os.path.join(os.path.dirname(__file__), "..", ".env")
client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

async def call_openai_with_auto_key(system_prompt, user_prompt,client, model = model_gpt4o_mini):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    try:
        completion = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(e)
        return "error"


async def get_gpt_answer(system_prompt, user_prompt):
    answer = await call_openai_with_auto_key(system_prompt=system_prompt, user_prompt=user_prompt, client=client)
    print(answer)
    return answer
