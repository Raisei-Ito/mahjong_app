#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Build commands
python manage.py collectstatic --noinput
python manage.py migrate

