#!/usr/bin/env bash
# Exit on error
set -o errexit

# Build commands
python manage.py collectstatic --noinput
python manage.py migrate

