#!/bin/bash
set -e

# Load environment variables from .env file
if [ -f .env ]; then
  export $(grep -v '^#' .env | xargs)
fi

echo "🚀 Starting PostgreSQL container..."
docker-compose up -d db

echo "😴 Waiting for PostgreSQL to be ready..."
while ! docker-compose exec db pg_isready -U ${FAST__DB__USER} -d ${FAST__DB__NAME}; do
  sleep 1
done

echo "🔍 Checking for existing migrations..."
if [ ! -d "alembic/versions" ] || [ -z "$(ls -A alembic/versions)" ]; then
  echo "📦 Generating initial migration..."
  docker-compose run --rm backend alembic revision --autogenerate -m "initial tables"
fi

echo "🔄 Applying migrations..."
docker-compose run --rm backend alembic upgrade head

echo "✅ Database initialization complete!"
sleep 1