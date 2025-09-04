This is a real-time chat implementation of FastApi

Technology stack :
FastAPI
SQLAlchemy
poetry
alembic
jwt
pydantic
websockets
jinja2
redis
taskiq

How to launch this project?

1. Clone the repo.
    git clone https://github.com/T1000dsa/Real-Time-Chat-App.git  # Pulling repository

2. Installing dependencies. 

    pip install poetry  # poetry install with pip

    poetry install  # install main dependecies with poetry

3. scripts/start_dev | bash scripts/start_dev.sh - creating migrations and new containers. 

4. scripts/stop_dev | bash scripts/stop_dev.sh - stopping all containers.

5. scripts/purge_dev | scripts/purge_dev.sh - purging all docker data, except images.