# Use a slim, official Python image as the base
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the main script into the container
COPY calculate_stats.py .

# Command to run when the container starts
CMD ["python", "calculate_stats.py"]
