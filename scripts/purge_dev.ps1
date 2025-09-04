.\stop_dev.ps1
docker system prune  \
docker rm -f $(docker ps -aq) \
docker rmi -f $(docker images -aq) \
docker volume rm $(docker volume ls -q)