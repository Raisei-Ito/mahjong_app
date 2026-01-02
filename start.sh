#!/bin/bash
set -e

# マイグレーションを実行
python manage.py migrate --noinput

# Gunicornを起動
exec gunicorn mahjong_project.wsgi --bind 0.0.0.0:8080 --workers 2 --timeout 120


