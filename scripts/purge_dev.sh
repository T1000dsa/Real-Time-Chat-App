#!/bin/bash
bash stop_dev.sh
docker system prune -a --volumes --force && docker rm -f $(docker ps -aq) && docker rmi -f $(docker images -aq) && docker volume rm $(docker volume ls -q)