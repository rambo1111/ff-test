# Use an official Python runtime as a parent image
FROM ubuntu:20.04

# Install dependencies
RUN apt-get update && apt-get install -y python3 python3-fontforge libjpeg-dev libtiff5-dev libpng-dev libfreetype6-dev libgif-dev libgtk-3-dev libxml2-dev libpango1.0-dev libcairo2-dev libspiro-dev libwoff-dev python3-dev ninja-build cmake build-essential gettext

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Run app.py when the container launches
CMD ["python", "app.py"]
