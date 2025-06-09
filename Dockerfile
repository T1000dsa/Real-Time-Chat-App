FROM python:latest

ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y wait-for-it
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

COPY .env .env

EXPOSE 8000

RUN echo "Environment variables in container:" && \
    printenv

COPY db_init.py .

# Entrypoint that runs migrations then starts the app
CMD ["sh", "-c", "python db_init.py && uvicorn src.main:app --host 0.0.0.0 --port 8000"]