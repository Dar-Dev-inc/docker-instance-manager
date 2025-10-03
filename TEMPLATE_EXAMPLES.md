# Template Examples

This file contains example template configurations for common development environments with persistent volumes.

## VSCode Server (code-server)

**Docker Image**: `codercom/code-server:latest`

**Default Ports**:
```json
{"vscode": 8080}
```

**Volume Mounts**:
```json
{"workspace": "/home/coder/project"}
```

**Environment Variables**:
```json
{"PASSWORD": "your-password-here"}
```

**Description**: VS Code in the browser with persistent workspace

---

## Jupyter Notebook

**Docker Image**: `jupyter/scipy-notebook:latest`

**Default Ports**:
```json
{"jupyter": 8888}
```

**Volume Mounts**:
```json
{"notebooks": "/home/jovyan/work"}
```

**Environment Variables**:
```json
{"JUPYTER_ENABLE_LAB": "yes"}
```

**Description**: Jupyter Lab with SciPy stack and persistent notebooks

---

## PostgreSQL Database

**Docker Image**: `postgres:15`

**Default Ports**:
```json
{"postgres": 5432}
```

**Volume Mounts**:
```json
{"data": "/var/lib/postgresql/data"}
```

**Environment Variables**:
```json
{
  "POSTGRES_USER": "admin",
  "POSTGRES_PASSWORD": "changeme",
  "POSTGRES_DB": "myapp"
}
```

**Description**: PostgreSQL 15 with persistent database storage

---

## MongoDB

**Docker Image**: `mongo:6`

**Default Ports**:
```json
{"mongo": 27017}
```

**Volume Mounts**:
```json
{
  "data": "/data/db",
  "config": "/data/configdb"
}
```

**Environment Variables**:
```json
{
  "MONGO_INITDB_ROOT_USERNAME": "admin",
  "MONGO_INITDB_ROOT_PASSWORD": "changeme"
}
```

**Description**: MongoDB 6 with persistent data and config

---

## Redis

**Docker Image**: `redis:7-alpine`

**Default Ports**:
```json
{"redis": 6379}
```

**Volume Mounts**:
```json
{"data": "/data"}
```

**Description**: Redis 7 with persistent storage (lightweight alpine image)

---

## MySQL Database

**Docker Image**: `mysql:8`

**Default Ports**:
```json
{"mysql": 3306}
```

**Volume Mounts**:
```json
{"data": "/var/lib/mysql"}
```

**Environment Variables**:
```json
{
  "MYSQL_ROOT_PASSWORD": "changeme",
  "MYSQL_DATABASE": "myapp",
  "MYSQL_USER": "appuser",
  "MYSQL_PASSWORD": "userpass"
}
```

**Description**: MySQL 8 with persistent database storage

---

## Node.js Development

**Docker Image**: `node:18`

**Default Ports**:
```json
{"app": 3000}
```

**Volume Mounts**:
```json
{"project": "/usr/src/app"}
```

**Description**: Node.js 18 development environment with persistent project files

---

## Python Development

**Docker Image**: `python:3.11`

**Default Ports**:
```json
{"app": 8000}
```

**Volume Mounts**:
```json
{"project": "/app"}
```

**Description**: Python 3.11 development environment with persistent project files

---

## Notes

- **Security**: Always change default passwords in production environments
- **Resource Limits**: Adjust CPU and memory limits based on your workload
- **Multiple Mounts**: You can specify multiple volume mount points for different data types
- **Port Conflicts**: The system automatically assigns random host ports, so container ports can be the same across templates

## Creating Templates in Admin

1. Go to `/admin` → Templates → Add Template
2. Copy the values from these examples
3. Adjust resource limits (CPU: 1.0 cores, Memory: 1024 MB recommended for most)
4. Save and users can start creating instances!
