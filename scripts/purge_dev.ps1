.\stop_dev.ps1
docker system prune -f\
docker rm -f $(docker ps -aq) \
docker rmi -f $(docker images -aq) \