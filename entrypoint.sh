#!/bin/bash

set -e

echo "Waiting for PostgreSQL..."
while ! pg_isready -h db -U postgres; do
  sleep 1
done

echo "Running migrations..."
python3 manage.py migrate --noinput

echo "Creating superuser if not exists..."
python3 manage.py shell << EOF
from django.contrib.auth import get_user_model
from core.models import Profile

User = get_user_model()
if not User.objects.filter(username='admin').exists():
    user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    Profile.objects.create(user=user, role='admin', max_instances=10)
    print('Superuser created: username=admin, password=admin')
else:
    print('Superuser already exists')
EOF

echo "Starting application..."
exec "$@"
