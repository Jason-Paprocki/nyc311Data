#!/bin/bash

# This script starts the database using Docker Compose,
# then builds and runs the Docker container to import the data.

echo "--- Starting database service ---"
docker-compose up -d

echo "--- Building and running data import container ---"
# Change to the GetData directory to access its Dockerfile
cd GetData

# Build the docker image
docker build -t get_data .

# Run the container, mounting the current directory
# The :z flag is for SELinux compatibility
docker run --rm --network="host" -v $(pwd):/app:z get_data

# Change back to the root directory
cd ..
echo "--- Data import finished ---"
