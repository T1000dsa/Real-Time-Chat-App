#!/bin/bash  
# "Alembic Docker Hack Attack"  

echo "🔥 Spinning up temp DB..."  
docker run --rm --name temp_db -e POSTGRES_PASSWORD=temp -d postgres  

echo "😴 Waiting for DB to wake up..."  
while ! docker exec temp_db pg_isready -U postgres; do  
  sleep 1  
done  

echo "📦 Generating revision..."  
alembic revision --autogenerate -m "Initial tables (Docker-proofed)"  

echo "💀 Killing temp DB..."  
docker stop temp_db  

echo "✅ Done. Now rebuild your *real* Docker setup."  