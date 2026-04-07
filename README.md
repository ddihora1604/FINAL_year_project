# DataSentinel: A Whitebox LLMOps Framework for Secure PII Redaction in RAG Pipelines

> A comprehensive, production-ready Retrieval-Augmented Generation (RAG) chatbot system integrated with enterprise-grade security, monitoring, and administration capabilities for secure customer support interactions.

---

## ❓ Problem Statement

### Challenge

Customer support teams face critical challenges in delivering fast, accurate, and secure responses to customer inquiries:

1. **Information Retrieval Bottleneck**: Finding relevant support information quickly from vast knowledge bases is time-consuming and error-prone
2. **Privacy Concerns**: Traditional chatbots risk exposing Personally Identifiable Information (PII) in responses, leading to compliance violations and security breaches
3. **Transparency Gap**: Lack of visibility into system behavior, security incidents, and performance metrics makes it difficult to maintain reliability and compliance
4. **Security Risks**: Vulnerability to prompt injection attacks and adversarial inputs that could manipulate the AI to behave unexpectedly

---

## 🎯 Project Overview

**DataSentinel** is a full-stack Retrieval-Augmented Generation (RAG) system designed for secure customer support automation. It combines:

- **Backend Intelligence**: A secure RAG pipeline that retrieves relevant support information and generates contextually accurate responses
- **Frontend Experience**: An intuitive React dashboard for real-time chat interactions
- **Security Layer**: PII redaction engine preventing sensitive data exposure
- **Observability Infrastructure**: Prometheus and Grafana monitoring for real-time health and security insights

### Use Case

A customer visits your support portal and asks: *"I can't log in with my email john.doe@example.com and phone 555-1234"*

The system:
1. 🔍 Retrieves relevant troubleshooting guides from the vector knowledge base
2. 🤖 Generates a personalized response using Ollama LLM
3. 🔐 Automatically redacts email and phone number with `[EMAIL_ADDRESS]` and `[PHONE_NUMBER]`
4. 📊 Records metrics: response time, security alerts, token usage
5. 💾 Stores conversation with PII-safe history

---

## ⭐ Key Features

### 🧠 RAG Pipeline
- **Semantic Search**: Powered by FAISS vector store with sentence transformers
- **Intelligent Retrieval**: Top-K similarity matching with configurable thresholds
- **LLM Integration**: Ollama Llama 3.2 local inference (no cloud dependencies)
- **Context Awareness**: Maintains conversation history for contextual responses
- **Configurable Parameters**: Easily adjust embedding models, chunk sizes, and similarity thresholds

### 🔐 Security & Privacy
- **PII Redaction Engine**: Real-time detection and masking of:
  - Email addresses, phone numbers, credit card numbers
  - Social Security Numbers, passport numbers
  - Account IDs, API keys, and tokens
- **Input Validation**: Prevents malicious payloads and injection attacks
- **Prompt Injection Detection**: Identifies and blocks suspicious input patterns
- **Conversation Sanitization**: All stored conversations have PII automatically redacted

### 📊 Enterprise Monitoring
- **Prometheus Metrics**: 
  - Query volume and processing times
  - Security events and attack attempts
  - Model performance and latency distributions
  - Token usage and cost tracking
- **Grafana Dashboards**: 
  - Executive Overview (business KPIs)
  - Security Operations (threat monitoring)
  - Performance Analytics (latency & throughput)
  - Quality Metrics (response quality and accuracy)

### 💬 User Interface
- **Real-time Chat**: WebSocket-powered live conversation
- **Conversation Management**: Create, view, and export conversations
- **Message Export**: Download conversation history as JSON
- **Security Alerts**: Visual indicators for PII redaction events
- **Responsive Design**: Works on desktop and mobile devices

---

### Data Flow During a Query

```
User Input
    ↓
[Input Validation & Logging]
    ↓
[Embedding Generation]
    ↓
[FAISS Vector Search]
    ↓
[Prompt Assembly with Context]
    ↓
[LLM Inference (Ollama)]
    ↓
[PII Redaction]
    ↓
[Metrics Recording]
    ↓
[Response + Sources + Security Info] → User
```
---

## 🔐 PII Redaction System

### Supported Entities

| Entity | Example | Replacement |
|--------|---------|-------------|
| Email | `john@example.com` | `[EMAIL_ADDRESS]` |
| Phone | `555-1234` | `[PHONE_NUMBER]` |
| Credit Card | `4532-1234-5678-9010` | `[CREDIT_CARD]` |
| SSN | `123-45-6789` | `[SSN]` |

---

## 🔑 Key Concepts & Technologies

### RAG (Retrieval-Augmented Generation)

**Definition**: A technique that combines document retrieval with language model generation to produce accurate, context-aware responses.

**Why RAG?**
- Reduces hallucinations by grounding responses in actual documents
- Enables knowledge base integration without retraining
- Improves response relevance and accuracy
- Supports multiple documents and up-to-date information

**Process**:
1. **Query Embedding**: Convert user query to vector representation
2. **Semantic Search**: Find similar documents in FAISS index
3. **Context Assembly**: Combine top-K documents for LLM context
4. **Generation**: Use LLM to generate response with retrieved context

### Vector Embeddings

**Technology**: Sentence Transformers (`all-MiniLM-L6-v2`)
- **Dimension**: 384-dimensional vectors
- **Model Size**: 22MB (lightweight)
- **Speed**: <5ms per document
- **Advantage**: Better semantic understanding than keyword matching

### FAISS (Facebook AI Similarity Search)

**Purpose**: Efficient similarity search in high-dimensional vector spaces

**Why FAISS?**
- Sub-linear search time: O(log n) instead of O(n)
- Handles millions of vectors
- Available locally (no cloud dependency)
- Battle-tested at Facebook/Meta scale

### Local LLM Integration (Ollama)

**Model**: Llama 3.2 (13B or 7B variants)
- **Privacy**: No data sent to external servers
- **Cost**: Zero API costs
- **Speed**: Instant inference (no latency from network)
- **Customization**: Can fine-tune on your data

### PII Redaction

**Entities Detected**:
- Email addresses: `user@example.com` → `[EMAIL_ADDRESS]`
- Phone numbers: `555-1234` → `[PHONE_NUMBER]`
- Credit cards: `4532-1234-5678-9010` → `[CREDIT_CARD]`
- SSN: `123-45-6789` → `[SSN]`
- API Keys, tokens, account IDs

**Detection Method**: Regex patterns with machine learning fallback

### Prometheus Metrics

**Key Metrics**:
```
- rag_queries_total: Total queries processed
- rag_request_duration_seconds: Query processing latency (histogram)
- rag_security_attacks_total: Security incidents detected
- rag_pii_redactions_total: PII redactions applied
- rag_tokens_used_total: LLM token consumption
```

---

## 📁 Directory Structure

```
FINAL_year_project-rag/
│
├── README.md                              # Main project documentation
├── README-SETUP.md                        # Detailed setup guide
├── IMPLEMENTATION-SUMMARY.md              # Technical implementation details
├── requirements.txt                       # Root dependencies
├── docker-compose.yml                     # Full stack orchestration
│
├── 📂 backend/                            # FastAPI application
│   ├── main.py                           # FastAPI server definition
│   ├── requirements.txt                  # Python dependencies
│   ├── Dockerfile                        # Container definition
│   ├── .env.example                      # Environment template
│   └── conversations/                    # Stored conversation logs
│
├── 📂 frontend/                           # React TypeScript application
│   ├── src/
│   │   ├── App.tsx                       # Main app component
│   │   ├── index.tsx                     # Entry point
│   │   ├── components/Navbar.tsx         # Navigation bar
│   │   └── pages/
│   │       ├── ChatPage.tsx             # Chat interface
│   │       └── DashboardPage.tsx        # Monitoring dashboard
│   ├── package.json                     # npm dependencies
│   ├── tsconfig.json                    # TypeScript config
│   ├── Dockerfile                       # Container definition
│   └── nginx.conf                       # Reverse proxy config
│
├── 📂 RAG-Pipeline/                       # Basic RAG implementation
│   ├── rag_pipeline.py                  # Core RAG logic
│   ├── example_usage.py                 # Demo script
│   └── customer_support_sample_1500_balanced.csv
│
├── 📂 RAG-Pipeline-Ollama/                # Production RAG with Ollama
│   ├── rag_pipeline_secure.py           # Secure RAG with PII redaction
│   ├── security.py                      # Security & PII redaction module
│   ├── customer_support_kb.faiss        # Pre-built vector index
│   └── test_prompts.md                  # Test cases
│
├── 📂 Health-Security-Metrics/            # Prometheus monitoring
│   ├── instrumentation.py               # RAGMonitor implementation
│   ├── prometheus.yml                   # Prometheus config
│   ├── QUICKSTART.md                    # Quick setup guide
│   └── verify_setup.py                  # Verification script
│
├── 📂 grafana-dashboards/                 # Pre-built dashboards
│   ├── 1-executive-overview.json        # Business metrics
│   ├── 2-security-operations.json       # Security monitoring
│   ├── 3-performance-dashboard.json     # Performance metrics
│   └── 4-quality-dashboard.json         # Quality metrics
│
├── 📂 Docs/                               # Documentation
│   ├── 01-PII-Redaction-Implementation.md
│   ├── 02-Health-Security-Metrics.md
│   └── 03-Grafana-Dashboard-Panels.md
│
└── 📂 Dataset/                            # Data processing utilities
    ├── customer_support_tickets_4330.csv
    └── dataset_operations.py
```

---

## 🔧 Installation Prerequisites & Setup

### System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **OS** | Windows 10, macOS 10.14, Ubuntu 18.04 | Windows 11, macOS 12, Ubuntu 22.04 |
| **CPU** | 4 cores | 8+ cores |
| **RAM** | 8 GB | 16+ GB |
| **Disk** | 20 GB | 50+ GB |

### Software Prerequisites

#### 1. **Python 3.11+**
```bash
python --version  # Should be 3.11+
```

#### 2. **Docker Desktop**
- Download: https://www.docker.com/products/docker-desktop/
```bash
docker --version      # Should be 20.10+
docker-compose --version  # Should be 2.0+
```

#### 3. **Ollama with Llama 3.2**
```bash
# Download from https://ollama.ai
ollama pull llama3.2
ollama list
```

#### 4. **Node.js 18+** (for frontend)
```bash
node --version   # Should be 18+
npm --version
```

### Setup Instructions

#### Option A: Automated Setup
```bash
cd "c:\path\to\FINAL_year_project-rag"
.\setup.ps1              # Windows
# or
chmod +x setup.sh && ./setup.sh  # macOS/Linux
```

#### Option B: Manual Setup

**Step 1: Install Dependencies**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install --upgrade pip
pip install -r requirements.txt
pip install -r backend/requirements.txt
```

**Step 2: Configure Environment Variables**

Create `.env` files in backend and frontend directories with appropriate configuration.

**Step 3: Start Services**
```bash
# Terminal 1: Ollama
ollama serve

# Terminal 2: Docker services
docker-compose up -d

# Terminal 3: Monitor
docker-compose logs -f
```

---

## 🚀 Quick Start

### 1. Start Everything
```bash
ollama serve                    # Terminal 1
docker-compose up -d            # Terminal 2
```

### 2. Access Applications

| Service | URL |
|---------|-----|
| Chat Interface | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Prometheus | http://localhost:9090 |
| Grafana | http://localhost:3001 |

### 3. Send First Query
```bash
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How do I reset my password?"}'
```

---

## 📊 Monitoring with Prometheus & Grafana

### Key Metrics
```promql
rag_queries_total{status="success"}
histogram_quantile(0.95, rag_request_duration_seconds_bucket)
rag_security_attacks_total
rag_pii_redactions_total
```

### Four Dashboards
1. **Executive Overview**: Business KPIs
2. **Security Operations**: Threat monitoring
3. **Performance Analytics**: Latency & throughput
4. **Quality Metrics**: Response accuracy

### Access Grafana
1. Open http://localhost:3001
2. Login: `admin` / `admin`
3. Go to Dashboards → RAG Pipeline

---

### Setup Monitoring Stack

**IMPORTANT: Start Docker Desktop first!**

1. **Verify Docker is running:**
   ```bash
   docker ps
   ```
   If this fails, open Docker Desktop and wait for it to start.

2. **Start monitoring (Windows):**
   ```bash
   cd "Health-Security-Metrics"
   start_monitoring.bat
   ```

3. **Start monitoring (Manual):**
   ```bash
   cd "Health-Security-Metrics"
   docker-compose up -d
   ```

4. **Verify setup:**
   ```bash
   python verify_setup.py
   ```

5. **Start RAG pipeline with monitoring:**
   ```bash
   cd "RAG-Pipeline-Ollama"
   python rag_pipeline_secure.py
   ```

#### Access Points

- **Metrics**: http://localhost:8000/metrics
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)

---

### 💡 Usage Examples

#### Example 1: Basic Chat
```python
import requests

response = requests.post(
    "http://localhost:8000/api/chat",
    json={"message": "How do I update my payment method?"}
)

data = response.json()
print(f"Response: {data['response']}")
```

#### Example 2: Export Conversation
```bash
curl http://localhost:8000/api/conversations/{id}/export -o chat.json
```

#### Example 3: Monitor Metrics
```bash
curl http://localhost:8000/metrics | head -20
```

---