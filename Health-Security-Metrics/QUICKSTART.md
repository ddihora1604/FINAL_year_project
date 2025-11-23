# Quick Start Guide - Phase 3 Monitoring

## Prerequisites

1. **Docker Desktop must be running**
   - Open Docker Desktop application
   - Wait for it to fully start (green icon in system tray)
   - Test: Run `docker ps` in terminal

## Setup Steps

### Option 1: Automated (Windows)

```bash
# Run the startup script
start_monitoring.bat
```

### Option 2: Manual

```bash
# 1. Verify Docker is running
docker ps

# 2. Start monitoring stack
docker-compose up -d

# 3. Check status
docker-compose ps
```

## Starting the RAG Pipeline

```bash
cd "c:\Tejas\BE Project\CODEBASE\BE-Project\RAG-Pipeline-Ollama"
python rag_pipeline_secure.py
```

## Verification

Run the verification script:

```bash
cd "c:\Tejas\BE Project\CODEBASE\BE-Project\Health-Security-Metrics"
pip install requests
python verify_setup.py
```

## Access Points

- **RAG Metrics**: http://localhost:8000/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (login: admin/admin)

## Common Issues

### "Docker Desktop is not running"

**Solution:**
1. Open Docker Desktop application
2. Wait 30-60 seconds for it to start completely
3. Try again when the Docker icon is solid in system tray

### "Port already in use"

**Solution:**
```bash
# Check what's using the ports
netstat -ano | findstr ":8000"
netstat -ano | findstr ":9090"
netstat -ano | findstr ":3000"

# Stop containers and restart
docker-compose down
docker-compose up -d
```

### "Cannot find file specified" error

**Solution:**
- This means Docker Desktop is not running
- Start Docker Desktop and wait for it to fully initialize
- The Docker whale icon in system tray should be still (not animating)

### Prometheus shows target is DOWN

**Solution:**
1. Ensure RAG pipeline is running: `python rag_pipeline_secure.py`
2. Test metrics endpoint: `curl http://localhost:8000/metrics`
3. Check prometheus.yml uses `host.docker.internal:8000`

## Quick Commands

```bash
# View logs
docker-compose logs prometheus
docker-compose logs grafana

# Restart services
docker-compose restart

# Stop services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v
```

## Testing the Setup

1. **Start everything:**
   ```bash
   docker-compose up -d
   cd ..\RAG-Pipeline-Ollama
   python rag_pipeline_secure.py
   ```

2. **Generate some traffic:**
   In the RAG chat interface, ask:
   - "How do I reset my password?"
   - "Tell me about billing issues"

3. **Check Prometheus:**
   - Visit: http://localhost:9090/targets
   - Should see "rag_pipeline" target with status UP (green)

4. **View metrics:**
   - Visit: http://localhost:9090/graph
   - Query: `rag_queries_total`
   - Click "Execute"
   - Should see data points

5. **Setup Grafana:**
   - Visit: http://localhost:3000
   - Login: admin/admin
   - Add Prometheus data source: `http://prometheus:9090`
   - Create dashboard with query: `rate(rag_queries_total[5m])`

## Troubleshooting Script

Run this to diagnose all issues:

```bash
python verify_setup.py
```

The script will check:
- ✅ Metrics endpoint accessible
- ✅ Prometheus running
- ✅ Prometheus can reach the app
- ✅ Grafana running
- ✅ Metrics are updating

Any failures will show specific error messages and solutions.
