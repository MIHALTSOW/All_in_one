FROM python:3.11-slim

WORKDIR /code


RUN pip install --no-cache-dir poetry


COPY ./pyproject.toml ./poetry.lock /code/


RUN poetry config virtualenvs.create false \
    && poetry install --no-interaction --no-ansi --no-root


COPY . /code/

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
