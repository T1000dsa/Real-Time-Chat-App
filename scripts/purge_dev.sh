#!/bin/bash
bash stop_dev.sh
docker system prune -f -a --volumes --force && docker rm -f $(docker ps -aq) && docker rmi -f $(docker images -aq)