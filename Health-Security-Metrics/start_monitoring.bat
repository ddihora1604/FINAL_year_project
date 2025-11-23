@echo off
echo ============================================
echo RAG Pipeline Monitoring Setup
echo ============================================
echo.

echo [1/4] Checking Docker Desktop...
docker ps >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Docker Desktop is not running!
    echo Please start Docker Desktop and try again.
    echo.
    pause
    exit /b 1
)
echo ✓ Docker is running

echo.
echo [2/4] Starting Prometheus and Grafana...
docker-compose up -d

if %errorlevel% neq 0 (
    echo ERROR: Failed to start containers
    pause
    exit /b 1
)

echo ✓ Containers started

echo.
echo [3/4] Waiting for services to be ready...
timeout /t 5 /nobreak >nul

echo.
echo [4/4] Checking service status...
docker-compose ps

echo.
echo ============================================
echo Setup Complete!
echo ============================================
echo.
echo Services available at:
echo   - Metrics:     http://localhost:8000/metrics (start RAG pipeline first)
echo   - Prometheus:  http://localhost:9090
echo   - Grafana:     http://localhost:3000 (admin/admin)
echo.
echo Next steps:
echo   1. Start the RAG pipeline: python rag_pipeline_secure.py
echo   2. Run verification: python verify_setup.py
echo   3. Configure Grafana dashboard
echo.
pause
