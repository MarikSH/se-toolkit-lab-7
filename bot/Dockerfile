FROM python:3.12-slim

WORKDIR /app

# Установить uv
RUN pip install --no-cache-dir uv

# Скопировать файлы проекта
COPY pyproject.toml uv.lock ./
RUN uv sync --no-editable --frozen

COPY . .

ENV PYTHONUNBUFFERED=1

# Переменные окружения для LLM и backend
ENV LLM_API_BASE_URL=http://qwen:42005/v1 \
    LLM_API_KEY=changeme \
    LLM_API_MODEL=qwen2.5-coder-32b-instruct

# Команда запуска бота
CMD ["uv", "run", "bot.py"]
