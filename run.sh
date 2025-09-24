#!/bin/bash

# A simple script to manage the Docker Compose environment for the NYC 311 Data Explorer.
# It provides commands to bring the services up or take them down.

# --- Helper Functions ---
# Prints a usage message explaining how to use the script.
usage() {
  echo "Usage: $0 [--up | --down]"
  echo "  --up    Builds images and starts all services in the background."
  echo "  --down  Stops and removes all services."
  exit 1
}

# --- Main Logic ---
# Check if an argument was provided. If not, show usage.
if [ -z "$1" ]; then
  echo "Error: No command specified."
  usage
fi

# Process the command provided by the user.
case "$1" in
  --up)
    echo "🚀 Bringing services up..."
    # The '--build' flag rebuilds images if their source files have changed.
    # The '-d' flag runs the containers in detached mode (in the background).
    docker-compose up --build -d
    echo "✅ Services are up and running."
    ;;
  --down)
    echo "🛑 Bringing services down..."
    # This command stops containers and removes containers, networks, and volumes created by 'up'.
    docker-compose down
    echo "✅ Services have been shut down."
    ;;
  *)
    echo "Error: Invalid command '$1'."
    usage
    ;;
esac
