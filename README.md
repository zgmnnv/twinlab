# TwinLab Development Environment

A complete development setup with Docker Compose featuring Apache Superset, Jupyter Lab, and a simple webapp, all accessible through direct port access.

## 🚀 Quick Start

1. **Run the setup script:**
   ```bash
   ./setup.sh
   ```

2. **Access your services:**
   - **TwinLab Homepage**: http://localhost/
   - **Apache Superset**: http://localhost:8088/
   - **Jupyter Lab**: http://localhost:8888/

## 📋 Services

### Apache Superset (Port 8088)
- **Purpose**: Business intelligence and data visualization
- **Login**: admin / admin123
- **Features**: 
  - Pre-loaded with sample datasets
  - Full functionality without subpath issues
  - PostgreSQL metadata store

### Jupyter Lab (Port 8888)
- **Purpose**: Interactive notebooks and data analysis
- **Features**:
  - Multiple Python kernels (Generic, Data Analysis)
  - Pre-installed data science libraries
  - WebSocket support for terminals and kernels

### Webapp (Port 80)
- **Purpose**: Service navigator and homepage
- **Features**: Modern UI with direct links to all services

## 🛠️ Manual Setup

If you prefer to set up manually:

1. **Start services:**
   ```bash
   docker-compose up -d
   ```

2. **Check status:**
   ```bash
   docker-compose ps
   ```

## 🔧 Configuration

### Environment Variables
All configuration is in `.env`:
- Superset admin credentials
- Database settings
- Jupyter configuration

### Superset Configuration
- Located in `config/superset/superset_config.py`
- Configured for direct access (no subpath)
- Includes sample database connections

## 📊 Sample Data

Superset comes pre-loaded with:
- Sample datasets for testing
- Example dashboards and charts
- Various data source connections

## 🐛 Troubleshooting

### Services not starting
```bash
docker-compose logs -f [service_name]
```

### Can't access services
1. Verify services are running: `docker-compose ps`
2. Check if ports are available: `netstat -tulpn | grep :8088`

### Superset issues
1. Check database connection: `docker-compose logs postgres`
2. Reset Superset: `docker-compose down && docker-compose up -d`

### Jupyter issues
1. Check if notebooks directory is accessible
2. Verify WebSocket connections in browser dev tools

## 🛑 Stopping Services

```bash
docker-compose down
```

To remove all data:
```bash
docker-compose down -v
```

## 📁 Project Structure

```
twinlab/
├── docker-compose.yml          # Main orchestration
├── .env                        # Environment variables
├── setup.sh                    # Quick setup script
├── config/
│   └── superset/superset_config.py
├── docker/
│   ├── superset/Dockerfile.superset
│   ├── jupyter/Dockerfile.jupyter
│   └── webapp/Dockerfile.webapp
├── webapp/
│   └── index.html              # Homepage
└── notebooks/                  # Jupyter notebooks
```

## 🔒 Security Notes

This is a **development-only** setup. For production:
- Change all default passwords
- Use HTTPS
- Configure proper security headers
- Use environment-specific secrets management
