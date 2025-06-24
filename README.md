This is a real-time implementation of FastApi / Это реализация чата в реальном времени на FastApi

Technology stack / Стек технологий :
FastAPI
SQLAlchemy
poetry
alembic
jwt
pydantic
websockets
jinja2
redis

How to launch this project? / Как запустить этот проект?

1. Clone the repo.
    git clone https://github.com/T1000dsa/Real-Time-Chat-App.git  # Pulling repository / скачиваем репозиторий

2. Installing dependencies. 

    pip install poetry  # poetry install with pip / скачиваем poetry с pip

    poetry install  # install main dependecies with poetry / скачиваем основные зависимости с poetry 

3. Set the environment vars.
    rename .env.example into .env
    If you want to change some variables just follow sctructure where: FAST - is the begin of the var, __ - is a delimeter. So it's should looks like that:
    FAST__DB__NAME

    Переименуй .env.example в .env
    Если ты хочешь изменить какие-либо параметры, просто следуй структуре, где: FAST - начало переменной, __ - разделитель. Это должно выглядеть примерно так:
    FAST__DB__NAME

4. Migrations.
    alembic revision --autogenerate -m "init"
    alembic upgrade head

5. poetry run uvicorn main:app --reload