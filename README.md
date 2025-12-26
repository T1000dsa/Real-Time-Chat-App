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

# Important clarification - Bash scripts can be aborted in the future. 


1. Clone the repo.
    git clone https://github.com/T1000dsa/Real-Time-Chat-App.git  # Pulling repository


2. Installing dependencies. 

    pip install poetry  # poetry install with pip

    poetry install  # install main dependecies with poetry


3. Create migrations and new containers.

During this step, powershell/bash scripts will be executed, unless there is a critical error, and docker container will be pulled and created. Also new migration will be applied to create database, unless it exist already.

To start with the project, you need to execute next command in your terminal: 

For powershell - scripts/start_dev 
For bash - bash scripts/start_dev.sh


4. Stop all containers.

At this step, all containers will be stopped, unless there is a critical error, then you should stop containers manually. 

To stop the project, you need to execute next command in your terminal: 

For powershell - scripts/stop_dev
For bash - bash scripts/stop_dev.sh


5. Purge docker data.

At this step, if clearly necessary, all data, except volumes, will be purged, unless there is a critical error.

To purge docker data (except volumes), you need to execute next command in your terminal:

For powershell - scripts/purge_dev
For bash - bash scripts/purge_dev.sh