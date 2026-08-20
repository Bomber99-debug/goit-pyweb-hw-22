FROM python:3.14-slim
LABEL authors="bomber"

WORKDIR /app

RUN pip install --no-cache-dir "poetry>=2,<3"

ENV POETRY_VIRTUALENVS_CREATE=false

COPY pyproject.toml poetry.lock ./

RUN poetry install --no-root \
    && python -m pip install --no-cache-dir --force-reinstall "redis==8.0.1"

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]