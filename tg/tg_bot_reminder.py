from datetime import datetime, timedelta, time
from db import dialogs_db

async def handle_remind(update, context):
    query = update.callback_query
    await query.answer()

    # ✅ Безопасность
    if not context.job_queue:
        print("⚠️ JobQueue is not initialized!")
        await query.edit_message_text("⚠️ Ошибка: напоминания временно недоступны.")
        return

    data = query.data.split(":")
    if data[0] == "remind":
        visit_date = datetime.fromisoformat(data[1])
        reminder_time = datetime.combine((visit_date - timedelta(days=1)).date(), time(hour=10, minute=0))

        job_name = f"reminder_{query.from_user.id}_{visit_date.date()}"

        # ✅ Убираем предыдущую задачу, если она была
        existing_jobs = context.job_queue.get_jobs_by_name(job_name)
        if existing_jobs:
            for job in existing_jobs:
                job.schedule_removal()

        # ✅ Сохраняем в базу
        await dialogs_db.save_reminder(query.from_user.id, visit_date, reminder_time)

        # ✅ Ставим новую задачу
        context.job_queue.run_once(send_reminder, reminder_time, chat_id=query.from_user.id, name=job_name)
        dt = datetime.fromisoformat(data[1])
        formatted_date = dt.strftime("%d.%m.%Y")
        await query.edit_message_text(f"✅ Напоминание установлено! Осмотр запланирован на {formatted_date}.\nЯ напомню за день до визита в 10:00.")

async def send_reminder(context):
    await context.bot.send_message(
        chat_id=context.job.chat_id,
        text="🔔 Напоминаем, у вас завтра визит в лабораторию. Не забудьте взять паспорт!"
    )
