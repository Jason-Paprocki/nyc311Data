#!/bin/bash

# Check if an argument is provided
if [ -z "$1" ]; then
    echo "Usage: $0 --up | --down | --populate"
    exit 1
fi

# Main command logic
if [ "$1" == "--up" ]; then
    echo "🚀 Starting up services..."
    # Start all services defined in docker-compose.yml in the background
    docker-compose up -d --build
    echo "✅ Services are up and running."

elif [ "$1" == "--down" ]; then
    echo "🛑 Shutting down services..."
    # Stop and remove all services defined in docker-compose.yml
    docker-compose down
    echo "✅ Services have been shut down."

elif [ "$1" == "--populate" ]; then
    echo "🔄 Rebuilding the populator image to ensure latest changes..."
    # Explicitly build the image first to pick up any code changes.
    docker-compose build populate_db

    echo "🔄 Populating the database with the latest 311 data..."
    # Run the one-off populate_db service. --rm cleans up the container afterward.
    docker-compose run --rm populate_db
    echo "✅ Database population script finished."

else
    echo "Error: Invalid command '$1'"
    echo "Usage: $0 --up | --down | --populate"
    exit 1
fi
