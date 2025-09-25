#!/bin/bash

# Check if an argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 --up | --down [args] | --populate"
    exit 1
fi

# Store the main command
COMMAND=$1
# Shift the first argument off, so $@ contains the rest
shift

# Main command logic
if [ "$COMMAND" == "--up" ]; then
    echo "🚀 Starting up services..."
    # Start all services defined in docker-compose.yml in the background
    docker compose up -d --build
    echo "✅ Services are up and running."

elif [ "$COMMAND" == "--down" ]; then
    echo "🛑 Shutting down services..."
    # Stop and remove all services, passing along any extra flags like -v
    docker compose down "$@"
    echo "✅ Services have been shut down."

elif [ "$COMMAND" == "--populate" ]; then
    echo "🔄 Rebuilding the populator image to ensure latest changes..."
    docker compose build populate_db

    echo "🔄 Populating the database with the latest 311 data..."
    docker compose run --rm populate_db
    echo "✅ Database population script finished."

else
    echo "Error: Invalid command '$COMMAND'"
    echo "Usage: $0 --up | --down [args] | --populate"
    exit 1
fi
