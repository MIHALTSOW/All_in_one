FROM python:3.11-slim

WORKDIR /code

# Устанавливаем Poetry
RUN pip install --no-cache-dir poetry

# Копируем файлы зависимостей
COPY ./pyproject.toml ./poetry.lock /code/

# Устанавливаем зависимости без создания виртуального окружения
RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root


COPY . /code/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]

# Если используете прокси-сервер, такой как Nginx или Traefik, добавьте --proxy-headers
# CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80", "--proxy-headers"]