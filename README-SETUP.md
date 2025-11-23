# RAG Chatbot - Frontend & Backend Setup Guide

## 🚀 Quick Start

This guide will help you set up and run the complete RAG Chatbot application with frontend, backend, and monitoring.

## 📋 Prerequisites

### Required Software
- **Docker Desktop** (Windows/Mac) or Docker + Docker Compose (Linux)
- **Node.js** 18+ (for local development)
- **Python** 3.11+ (for local development)
- **Ollama** with Llama 3.2 model
- **Git**

### Verify Installations
```powershell
docker --version          # Should be 20.10+
docker-compose --version  # Should be 2.0+
node --version           # Should be 18+
python --version         # Should be 3.11+
ollama --version         # Should be installed
```

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────────┐
│                    Frontend (React)                       │
│                   http://localhost:3000                   │
└────────────────────┬─────────────────────────────────────┘
                     │
┌────────────────────┴─────────────────────────────────────┐
│                  Backend (FastAPI)                        │
│                  http://localhost:8000                    │
│  ┌─────────────────────────────────────────────────┐    │
│  │         RAG Pipeline (rag_pipeline_secure.py)    │    │
│  │  - Security Layer (PII Redaction)                │    │
│  │  - Vector Store (FAISS)                          │    │
│  │  - LLM Integration (Ollama/Llama 3.2)            │    │
│  └─────────────────────────────────────────────────┘    │
└────────────────────┬─────────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
┌────────▼─────────┐   ┌────────▼─────────┐
│   Prometheus     │   │     Grafana      │
│ localhost:9090   │   │  localhost:3001  │
│ (Metrics)        │   │ (Dashboards)     │
└──────────────────┘   └──────────────────┘
```

## 📦 Installation Steps

### Step 1: Clone and Navigate to Project

```powershell
cd "c:\Tejas\BE Project\CODEBASE\BE-Project"
```

### Step 2: Install Ollama and Download Model

```powershell
# Download and install Ollama from https://ollama.ai
# Then pull the Llama 3.2 model
ollama pull llama3.2

# Verify it's running
ollama list
```

### Step 3: Setup Environment Variables

#### Backend Environment
```powershell
# Copy example env file
cd backend
copy .env.example .env

# Edit .env with your settings (use notepad or VS Code)
notepad .env
```

#### Frontend Environment
```powershell
# Copy example env file
cd ../frontend
copy .env.example .env

# Edit .env if needed
notepad .env
```

### Step 4: Build and Run with Docker Compose

```powershell
# Return to project root
cd ..

# Build and start all services
docker-compose up --build -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

Expected output:
```
NAME              STATUS    PORTS
rag-frontend      Up        0.0.0.0:3000->80/tcp
rag-backend       Up        0.0.0.0:8000->8000/tcp
rag-prometheus    Up        0.0.0.0:9090->9090/tcp
rag-grafana       Up        0.0.0.0:3001->3000/tcp
```

### Step 5: Verify Services

Open your browser and check:
- ✅ **Frontend**: http://localhost:3000
- ✅ **Backend API Docs**: http://localhost:8000/api/docs
- ✅ **Prometheus**: http://localhost:9090
- ✅ **Grafana**: http://localhost:3001 (admin/admin)

## 🛠️ Development Setup (Without Docker)

### Backend Development

```powershell
# Create virtual environment
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
pip install -r ../requirements.txt

# Copy environment file
copy .env.example .env

# Run backend
python main.py
```

Backend will be available at http://localhost:8000

### Frontend Development

```powershell
# Install dependencies
cd frontend
npm install

# Copy environment file
copy .env.example .env

# Start development server
npm start
```

Frontend will be available at http://localhost:3000

## 🔧 Configuration

### Backend Configuration (backend/.env)

```env
# API Settings
API_PORT=8000
API_HOST=0.0.0.0

# Ollama Configuration
OLLAMA_URL=http://localhost:11434

# Model Settings
MODEL_NAME=llama3.2
EMBEDDING_MODEL=all-MiniLM-L6-v2
TEMPERATURE=0.7
MAX_TOKENS=1024
TOP_K_RESULTS=5

# Monitoring
METRICS_PORT=8001
PROMETHEUS_URL=http://prometheus:9090

# Logging
LOG_LEVEL=INFO
```

### Frontend Configuration (frontend/.env)

```env
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000
REACT_APP_GRAFANA_URL=http://localhost:3001
```

## 📚 API Documentation

### REST API Endpoints

#### Chat Endpoints
```
POST   /api/chat/message          - Send a message and get response
POST   /api/chat/new              - Start new conversation
GET    /api/chat/history          - Get all conversations
GET    /api/chat/history/{id}     - Get specific conversation
DELETE /api/chat/{id}             - Delete conversation
GET    /api/chat/export/{id}      - Export conversation (JSON/TXT)
```

#### Metrics Endpoints
```
GET    /api/metrics/summary       - Get metrics summary
GET    /api/metrics/live          - Get live metrics
GET    /api/metrics/security      - Get security metrics
GET    /api/metrics/performance   - Get performance metrics
```

#### System Endpoints
```
GET    /api/health                - Health check
GET    /api/system/config         - Get system configuration
POST   /api/system/config         - Update configuration
```

#### WebSocket Endpoints
```
WS     /api/ws/chat              - Real-time chat streaming
WS     /api/ws/metrics           - Real-time metrics updates
```

### API Examples

#### Send a Chat Message
```bash
curl -X POST http://localhost:8000/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are your return policies?",
    "conversation_id": null
  }'
```

Response:
```json
{
  "conversation_id": "conv_1700000000000",
  "response": "Our return policy allows...",
  "sources": [...],
  "security_info": {...},
  "pii_redacted": ["email"],
  "similarity_scores": [0.85, 0.82],
  "processing_time": 1.23
}
```

#### Get Health Status
```bash
curl http://localhost:8000/api/health
```

## 🎨 Frontend Features

### Chat Interface
- **Real-time messaging** with WebSocket support
- **PII redaction indicators** showing protected data
- **Security alerts** for blocked attacks
- **Conversation history** with sidebar navigation
- **Markdown rendering** for formatted responses
- **Export conversations** as JSON or text

### Dashboard
- **Metrics summary cards** showing key KPIs
- **Embedded Grafana dashboards** with 4 sections:
  - Executive Overview
  - Security Operations
  - Performance Metrics
  - Quality Metrics
- **Real-time updates** every 5 seconds

## 🔒 Security Features

### Automatic PII Protection
- Email addresses redacted
- Phone numbers redacted
- Social Security Numbers redacted
- Credit card numbers redacted
- Ticket IDs redacted
- Customer names redacted

### Attack Detection
- Prompt injection attempts blocked
- Data exfiltration attempts blocked
- Jailbreak attempts blocked
- Role manipulation attempts blocked

### Visual Indicators
- 🟢 **Green** - Secure, no issues
- 🟡 **Yellow** - PII redacted
- 🔴 **Red** - Attack blocked

## 📊 Monitoring & Metrics

### Prometheus Metrics
Access raw metrics at http://localhost:8000/metrics

Key metrics:
- `rag_queries_total` - Total queries processed
- `rag_security_attacks_total` - Security attacks blocked
- `rag_security_pii_redacted_total` - PII items redacted
- `rag_request_duration_seconds` - Request latency
- `rag_similarity_score` - Retrieval quality

### Grafana Dashboards
Access dashboards at http://localhost:3001

Default credentials: `admin` / `admin`

Four dashboard sections:
1. **Executive Overview** - High-level KPIs
2. **Security Operations** - Attack monitoring
3. **Performance Metrics** - Latency and throughput
4. **Quality Metrics** - Retrieval quality

## 🐛 Troubleshooting

### Common Issues

#### 1. Frontend can't connect to backend
```powershell
# Check backend is running
curl http://localhost:8000/api/health

# Check CORS settings in backend/main.py
# Ensure frontend URL is in allow_origins list
```

#### 2. Ollama connection failed
```powershell
# Check Ollama is running
ollama list

# Check Ollama URL in backend/.env
# For Docker: http://host.docker.internal:11434
# For local: http://localhost:11434
```

#### 3. Prometheus not scraping metrics
```powershell
# Check targets in Prometheus
# Open: http://localhost:9090/targets

# Verify backend metrics endpoint
curl http://localhost:8000/metrics
```

#### 4. Docker build fails
```powershell
# Clean up and rebuild
docker-compose down -v
docker system prune -a
docker-compose up --build
```

#### 5. Port already in use
```powershell
# Check what's using the port
netstat -ano | findstr :3000

# Kill the process or change ports in docker-compose.yml
```

### Viewing Logs

```powershell
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f prometheus
docker-compose logs -f grafana
```

## 🧪 Testing

### Backend API Tests
```powershell
cd backend
pytest tests/ -v
```

### Frontend Tests
```powershell
cd frontend
npm test
```

### Load Testing
```powershell
# Using k6 (install from https://k6.io)
k6 run load-test.js
```

## 🚀 Deployment

### Production Checklist
- [ ] Change default passwords (Grafana admin)
- [ ] Set up proper SSL/TLS certificates
- [ ] Configure firewall rules
- [ ] Set up database for conversation storage
- [ ] Enable authentication and authorization
- [ ] Set up log aggregation
- [ ] Configure backup strategy
- [ ] Set up monitoring alerts
- [ ] Enable rate limiting
- [ ] Review security settings

### Docker Production Build
```powershell
# Build for production
docker-compose -f docker-compose.prod.yml up --build -d
```

## 📖 Additional Resources

- **API Documentation**: http://localhost:8000/api/docs
- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **React Docs**: https://react.dev/

## 🆘 Support

For issues or questions:
1. Check the troubleshooting section above
2. Review logs: `docker-compose logs -f`
3. Check API health: `curl http://localhost:8000/api/health`
4. Verify Ollama: `ollama list`

## 📝 Project Structure

```
BE-Project/
├── backend/                    # FastAPI backend
│   ├── main.py                # API endpoints
│   ├── requirements.txt       # Python dependencies
│   ├── Dockerfile            # Backend Docker config
│   └── .env                  # Environment variables
├── frontend/                  # React frontend
│   ├── src/
│   │   ├── pages/            # React pages
│   │   ├── components/       # React components
│   │   └── App.tsx           # Main app component
│   ├── package.json          # Node dependencies
│   ├── Dockerfile            # Frontend Docker config
│   └── nginx.conf            # Nginx configuration
├── RAG-Pipeline-Ollama/       # RAG pipeline code
│   ├── rag_pipeline_secure.py # Secure RAG implementation
│   └── security.py           # Security layer
├── Health-Security-Metrics/   # Monitoring setup
│   ├── instrumentation.py    # Prometheus metrics
│   └── prometheus.yml        # Prometheus config
├── grafana-dashboards/        # Grafana dashboards
├── docker-compose.yml         # Docker orchestration
└── README-SETUP.md           # This file
```

## 🎯 Next Steps

1. **Start the application**: `docker-compose up -d`
2. **Open the frontend**: http://localhost:3000
3. **Try chatting**: Ask about customer support topics
4. **View dashboards**: http://localhost:3001
5. **Monitor security**: Watch for PII redaction and blocked attacks
6. **Explore API**: http://localhost:8000/api/docs

Happy chatting! 🤖💬
