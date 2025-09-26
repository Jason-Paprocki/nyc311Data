# Use a slim, official Python image as the base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# [cite_start]Install the Python dependencies [cite: 3]
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main scripts and data file into the container
COPY populate.py .
COPY load_districts.py .
COPY community_districts.geojson .

# [cite_start]Command to run when the container starts [cite: 4]
# First, run the one-time district loading script.
# If it succeeds (&&), then run the main data population script.
CMD python load_districts.py && python populate.py
