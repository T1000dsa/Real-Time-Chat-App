#!/bin/bash

# Load environment variables
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

# Set defaults (container name is now required)
CONTAINER_NAME=${FAST__DB__CONTAINER:?"Missing FAST__DB__CONTAINER in .env"}
DB_USER=${FAST__DB__USER:-"postgres"}
DB_NAME=${FAST__DB__NAME:-"fastapi_db"}

# Check if container exists and is running
if ! docker ps --format '{{.Names}}' | grep -qw "$CONTAINER_NAME"; then
    echo "Error: Container '$CONTAINER_NAME' not found or not running."
    echo "Available containers:"
    docker ps --format '{{.Names}}'
    echo "Please:"
    echo "1. Start your containers: docker-compose up -d"
    echo "2. Verify the correct container name in .env"
    exit 1
fi

# Database creation (now with password support)
echo "Creating database '$DB_NAME' if not exists..."
docker exec "$CONTAINER_NAME" psql -U "$DB_USER" -c "CREATE DATABASE $DB_NAME;" 2>/dev/null || \
    echo "Database already exists or creation failed (might need password?)"

# Run migrations
echo "Running migrations..."
python.exe -m alembic revision --autogenerate -m "init"
python.exe -m alembic upgrade head

if [ $? -eq 0 ]; then
    echo "Migrations completed successfully!"
else
    echo "Migration failed!"
    exit 1
fi