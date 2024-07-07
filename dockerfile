# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-fontforge \
    libfontforge-dev \
    libspiro-dev \
    libuninameslist-dev

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV NAME World

# Run the application
CMD ["gunicorn", "-b", "0.0.0.0:5000", "app:app"]
