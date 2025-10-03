#!/bin/bash

echo "==================================="
echo "Docker Manager - Setup Script"
echo "==================================="

# Check if running with Docker Compose
if [ "$1" = "--docker" ]; then
    echo "Starting with Docker Compose..."
    docker-compose up --build -d
    echo ""
    echo "Application is starting..."
    echo "Web interface: http://localhost:8000"
    echo "Admin panel: http://localhost:8000/admin"
    echo "Default credentials: admin / admin"
    echo ""
    echo "To view logs: docker-compose logs -f"
    echo "To stop: docker-compose down"
    exit 0
fi

# Local development setup
echo "Setting up for local development..."
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

# Check Docker
if ! command -v docker &> /dev/null; then
    echo "Warning: Docker is not installed or not in PATH"
    echo "Docker is required to manage containers"
fi

# Check Redis
if ! command -v redis-cli &> /dev/null; then
    echo "Warning: Redis is not installed"
    echo "You'll need to install and start Redis for Celery tasks"
fi

echo "Installing Python dependencies..."
python3 -m pip install --user -r requirements.txt

echo ""
echo "Running database migrations..."
python3 manage.py migrate

echo ""
echo "Creating static directories..."
mkdir -p static staticfiles

echo ""
echo "Creating superuser..."
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

echo ""
echo "==================================="
echo "Setup complete!"
echo "==================================="
echo ""
echo "To start the application:"
echo "1. Start Redis: redis-server"
echo "2. Start Celery worker: celery -A dockermanager worker --loglevel=info"
echo "3. Start Django: python3 manage.py runserver"
echo ""
echo "Then visit: http://localhost:8000"
echo "Admin panel: http://localhost:8000/admin"
echo "Default credentials: admin / admin"
echo ""
echo "Or use Docker Compose:"
echo "./setup.sh --docker"
