# Базовый образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта
COPY . /app

# Устанавливаем зависимости
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Указываем команду запуска бота
CMD ["python", "-m", "tg.tg_bot_main"]

# запускаем так
#docker run -d \
#--name anketa_container \
#-e PYTHONPATH=/app \
#anketa_bot_image \
#python -m tg.tg_bot_main