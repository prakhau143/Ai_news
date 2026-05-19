#!/bin/bash
# AI News Dashboard — one-shot setup script
set -e
cd "$(dirname "$0")"

echo "==> Creating virtual environment..."
python3 -m venv venv

echo "==> Installing dependencies..."
venv/bin/pip install --upgrade pip -q
venv/bin/pip install -r requirements.txt -q

echo "==> Creating .env from example (edit it with your API keys)..."
if [ ! -f .env ]; then
  cp .env.example .env
  echo "     ⚠  Open .env and add your ANTHROPIC_API_KEY and GNEWS_API_KEY"
fi

echo "==> Running migrations..."
venv/bin/python manage.py makemigrations
venv/bin/python manage.py migrate

echo "==> Creating superuser (admin / admin123)..."
venv/bin/python manage.py shell -c "
from django.contrib.auth import get_user_model
U = get_user_model()
if not U.objects.filter(username='admin').exists():
    U.objects.create_superuser('admin','admin@ainews.local','admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
"

echo ""
echo "✅  Setup complete!"
echo "    1. Edit .env → add ANTHROPIC_API_KEY and GNEWS_API_KEY"
echo "    2. Run:  venv/bin/python manage.py runserver"
echo "    3. Open: http://127.0.0.1:8000  (login: admin / admin123)"
