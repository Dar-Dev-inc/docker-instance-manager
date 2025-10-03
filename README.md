# Docker Manager

A Django-based web platform for managing Dockerized development environments (VSCode, Jupyter, etc.) with dynamic port assignment and user isolation.

## Features

- **Launch Docker containers** from predefined templates
- **Persistent volumes** for data that survives container restarts (essential for VSCode, Jupyter, databases)
- **Random port assignment** to avoid conflicts (port range: 49152-65535)
- **Manage instances**: start, stop, restart, delete
- **Real-time logs** and status monitoring
- **Admin template management** via Django admin
- **Async tasks** for container operations (via Celery + Redis)
- **Security and user isolation** with role-based access control
- **Audit logging** for tracking user actions
- **Optional volume preservation** when deleting instances

## Technology Stack

- **Backend**: Django 4.x
- **Database**: PostgreSQL / SQLite (dev)
- **Frontend**: Django Templates + Bootstrap 5
- **Docker Management**: Docker SDK for Python
- **Task Queue**: Celery + Redis
- **Deployment**: Docker Compose

## Quick Start

### Prerequisites

- Docker and Docker Compose installed
- Python 3.10+ (for local development)

### Using Docker Compose (Recommended)

1. **Clone the repository and navigate to the project directory**

2. **Create environment file** (optional, defaults are set):
   ```bash
   cp .env.example .env
   ```

3. **Build and start services**:
   ```bash
   docker-compose up --build
   ```

4. **Access the application**:
   - Web interface: http://localhost:8000
   - Admin panel: http://localhost:8000/admin
   - Default credentials: `admin` / `admin`

### Local Development (Without Docker Compose)

1. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Create .env file**:
   ```bash
   cp .env.example .env
   ```

3. **Run migrations**:
   ```bash
   python3 manage.py migrate
   ```

4. **Create superuser**:
   ```bash
   python3 manage.py createsuperuser
   ```

5. **Run development server**:
   ```bash
   python3 manage.py runserver
   ```

6. **In separate terminal, start Celery worker**:
   ```bash
   celery -A dockermanager worker --loglevel=info
   ```

7. **In another terminal, start Redis** (if not running):
   ```bash
   redis-server
   ```

## Usage

### Creating Templates (Admin Only)

1. Log in to the admin panel at `/admin`
2. Navigate to **Templates** and click **Add Template**
3. Fill in the required fields:
   - **Name**: Template display name
   - **Docker Image**: e.g., `codercom/code-server:latest`
   - **Default Ports**: JSON format, e.g., `{"vscode": 8080}`
   - **Volume Mounts** (optional): JSON format for persistent storage, e.g., `{"workspace": "/home/coder/project"}`
   - **CPU Limit**: Number of CPU cores (e.g., 1.0)
   - **Memory Limit**: RAM in MB (e.g., 1024)
   - **Environment Vars** (optional): JSON format for default env variables
   - **Description**: Optional description

**Note**: If you specify `volume_mounts`, a persistent Docker volume will be automatically created for each instance, ensuring data persists across container restarts.

### Creating Instances (Users)

1. Log in to the dashboard
2. Click **New Instance** or browse **Templates**
3. Select a template and click **Create Instance**
4. Optionally provide an instance name
5. Wait for the container to start (status will change from "Pending" to "Running")
6. Access your instance via the provided URL(s)

### Managing Instances

- **View Details**: Click the info button on an instance card to see logs, URLs, and volume information
- **Stop**: Stop a running instance (data in persistent volumes is preserved)
- **Restart**: Restart a stopped instance (reconnects to the same persistent volume)
- **Delete**: Remove an instance with option to preserve or delete the data volume
  - By default, volumes are **preserved** so you can reattach them later
  - Check "Also delete the data volume permanently" to remove all data

### Persistent Volume Benefits

When a template has `volume_mounts` configured:
- **Data persists** across container restarts and stops
- **Files are preserved** even if the container crashes
- **Volumes can be reused** - delete an instance but keep the volume for later
- Perfect for:
  - **VSCode**: Preserve your project files and extensions
  - **Jupyter**: Keep notebooks and data files
  - **Databases**: Maintain database files across restarts

## Architecture

```
User Request → Django View → Celery Task → Docker Manager → Docker Engine
                                ↓
                          Port Manager (assigns random ports)
                                ↓
                          Database (stores instance info)
```

### Key Components

- **Django App**: Handles authentication, CRUD operations, dashboard
- **Docker Manager Service**: Manages container lifecycle via Docker SDK
- **Port Manager**: Allocates random ports from configured range
- **Celery Tasks**: Async operations for starting/stopping containers
- **Redis**: Message broker for Celery
- **PostgreSQL**: Production database

## Configuration

### Environment Variables

Edit `.env` file:

```env
DEBUG=True
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:pass@localhost/dbname
REDIS_URL=redis://localhost:6379/0
ALLOWED_HOSTS=localhost,127.0.0.1
PORT_RANGE_START=49152
PORT_RANGE_END=65535
```

### User Roles and Admin Dashboard

- **Admin**: Full access to admin dashboard, can manage all users and instances
  - Access admin dashboard at `/admin-dashboard/`
  - View platform-wide statistics
  - Manage user quotas and roles
  - View all instances across all users
- **Developer**: Can create and manage own instances (up to quota limit)
- **Viewer**: Read-only access to own instances

The admin dashboard provides:
- Platform statistics (total users, running instances, templates)
- User management with quota controls
- Instance overview with filtering by status and user
- Activity logs and recent instance tracking

## Security

- User authentication required for all operations
- Container resource limits (CPU/memory)
- Port range isolation
- CSRF protection on all forms
- Audit logging for tracking actions
- Role-based access control

## Troubleshooting

### Container fails to start

- Check Docker image name is correct
- Verify Docker daemon is running
- Check container logs in instance detail page
- Ensure sufficient ports are available

### Celery tasks not processing

- Verify Redis is running: `redis-cli ping`
- Check Celery worker logs
- Restart Celery worker

### Permission denied accessing Docker

- Ensure user is in `docker` group: `sudo usermod -aG docker $USER`
- For Docker Compose, socket is mounted as volume


## Development


```bash
# Run tests
python3 manage.py test

# Create migrations
python3 manage.py makemigrations
python3 manage.py migrate

# Collect static files
python3 manage.py collectstatic
```


