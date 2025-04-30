#!/usr/bin/env bash
# exit on error
set -o errexit

# Make script executable
chmod +x build.sh

# Install dependencies
pip install -r requirements.txt

# Create directories for static and media files
mkdir -p staticfiles
mkdir -p media

# Run migrations
python manage.py migrate

# Collect static files
python manage.py collectstatic --no-input 