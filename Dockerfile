# syntax=docker/dockerfile:1.6
FROM python:3.11-slim

# Безопасность: не запускаем приложение от root.
# Создаём отдельного пользователя для нашего сервиса.
RUN useradd -r -u 1000 -m -d /home/mlservice mlservice

WORKDIR /app

# Переменные окружения для Python:
# - PYTHONUNBUFFERED: stdout не буферизуется (логи появляются сразу)
# - PYTHONDONTWRITEBYTECODE: не создавать .pyc файлы (мусора меньше)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Сначала ставим зависимости отдельным слоем.
# Docker кеширует слои - пока requirements.txt не меняется,
# pip install не будет запускаться повторно при rebuild.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Теперь копируем код
COPY ml_pipeline.py app.py ./

# Тренируем модель при сборке - артефакты попадают в /app/artifacts
# внутри образа. Образ становится самодостаточным.
RUN python ml_pipeline.py

# Передаём владение всем содержимым /app непривилегированному пользователю
RUN chown -R mlservice:mlservice /app
USER mlservice

EXPOSE 8000

# Docker-level healthcheck - сам Docker будет периодически проверять,
# что контейнер жив. Полезно для оркестраторов (docker-compose, k8s).
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()" || exit 1

# В production используем gunicorn вместо flask dev server.
# 2 worker процесса достаточно для учебной нагрузки.
# --access-logfile - выводит каждый запрос в stdout (видно в docker logs)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "2", "--access-logfile", "-", "app:app"]