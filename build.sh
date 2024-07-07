#!/usr/bin/env bash
# Create a writable directory for APT lists
mkdir -p /var/lib/apt/lists/partial

# Update the package lists
apt-get update

# Install packages from apt.txt
apt-get install -y $(cat apt.txt)

# Install Python dependencies
pip install -r requirements.txt
