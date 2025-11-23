# Health & Security Metrics System

## Executive Summary

This document describes the comprehensive health and security metrics collection system implemented for the RAG (Retrieval-Augmented Generation) pipeline. The system uses **Prometheus** for metrics collection and storage, and **Grafana** for visualization, providing real-time monitoring of security events, performance, and quality metrics.

## System Architecture

### Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     RAG Pipeline Application                 │
│                    (Python + instrumentation.py)             │
│                         Port 8000                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │        RAGMonitor (Prometheus Client)              │    │
│  │  - Exposes /metrics endpoint                       │    │
│  │  - Records security events                         │    │
│  │  - Records performance data                        │    │
│  │  - Records quality metrics                         │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────┬───────────────────────────────────────────┘
                  │ HTTP Scrape (every 5s)
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                      Prometheus Server                       │
│                         Port 9090                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Time-Series Database                              │    │
│  │  - Scrapes metrics from /metrics                   │    │
│  │  - Stores historical data                          │    │
│  │  - Provides PromQL query interface                 │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────┬───────────────────────────────────────────┘
                  │ PromQL Queries
                  ↓
┌─────────────────────────────────────────────────────────────┐
│                       Grafana Dashboard                      │
│                         Port 3000                            │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │  Visualization Layer                               │    │
│  │  - Queries Prometheus via PromQL                   │    │
│  │  - Renders charts and graphs                       │    │
│  │  - Provides alerting capabilities                  │    │
│  └────────────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────────┘
```

### Component Roles

| Component | Role | Port | Technology |
|-----------|------|------|------------|
| **RAG Application** | Metrics generation | 8000 | Python + prometheus_client |
| **Prometheus** | Metrics collection & storage | 9090 | Prometheus TSDB |
| **Grafana** | Visualization & alerting | 3000 | Grafana |

## Metrics Collection with Prometheus

### 1. Python Instrumentation

#### RAGMonitor Class

Located in `Health-Security-Metrics/instrumentation.py`, this class implements the Prometheus client for the RAG pipeline.

```python
from prometheus_client import start_http_server, Counter, Histogram, Gauge, Info

class RAGMonitor:
    """Prometheus monitoring for RAG Pipeline"""
    
    def __init__(self, port=8000, host='0.0.0.0'):
        """Initialize the monitor and start the metrics server"""
        start_http_server(port, addr=host)
        logger.info(f"✅ Prometheus metrics exposed on http://{host}:{port}/metrics")
```

**Initialization Steps:**

1. **HTTP Server Start**: Launches an HTTP server on the specified port
2. **Host Binding**: Binds to `0.0.0.0` to allow Docker container access
3. **System Info**: Records metadata about the system version and configuration
4. **Logging**: Confirms successful startup with access URLs

### 2. Metric Types and Definitions

#### Security Metrics

##### Attack Counter
```python
ATTACK_COUNTER = Counter(
    'rag_security_attacks_total', 
    'Total number of prompt injection attempts blocked',
    ['attack_type']
)
```
- **Type**: Counter (monotonically increasing)
- **Purpose**: Track security attack attempts
- **Labels**: `attack_type` - jailbreak, pii_leak, roleplay, exfiltration
- **Recording**: `monitor.record_attack('jailbreak')`

##### PII Redaction Counter
```python
PII_REDACTION_COUNTER = Counter(
    'rag_security_pii_redacted_total',
    'Total number of PII entities redacted from responses',
    ['entity_type']
)
```
- **Type**: Counter
- **Purpose**: Track PII entities removed from responses
- **Labels**: `entity_type` - email, phone, name, ticket_id, credit_card, ssn
- **Recording**: `monitor.record_redaction('email', count=3)`

#### Performance Metrics

##### Request Latency Histogram
```python
REQUEST_LATENCY = Histogram(
    'rag_request_duration_seconds',
    'Time spent processing RAG requests',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]
)
```
- **Type**: Histogram
- **Purpose**: Measure request processing time
- **Buckets**: 0.1s, 0.5s, 1.0s, 2.0s, 5.0s, 10.0s
- **Recording**: `monitor.record_latency(start_time)`
- **Output Metrics**: 
  - `rag_request_duration_seconds_bucket{le="0.5"}` - Count ≤ 0.5s
  - `rag_request_duration_seconds_sum` - Total duration
  - `rag_request_duration_seconds_count` - Total requests

##### Similarity Score Histogram
```python
SIMILARITY_SCORE = Histogram(
    'rag_similarity_score',
    'Distribution of similarity scores for retrieved documents',
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)
```
- **Type**: Histogram
- **Purpose**: Track quality of document retrieval
- **Buckets**: 0.0 to 1.0 in 0.1 increments
- **Recording**: `monitor.record_similarity_score(0.85)`

#### Quality Metrics

##### Query Counter
```python
QUERY_COUNTER = Counter(
    'rag_queries_total',
    'Total number of queries processed',
    ['status']
)
```
- **Type**: Counter
- **Purpose**: Track query outcomes
- **Labels**: `status` - success, blocked, no_context
- **Recording**: `monitor.record_query('success')`

##### Refusal Counter
```python
REFUSAL_COUNTER = Counter(
    'rag_content_refusals_total',
    'Total times the model refused to answer due to lack of context or security'
)
```
- **Type**: Counter
- **Purpose**: Track when system refuses to answer
- **Recording**: `monitor.record_refusal()`

#### System Metrics

##### Vector Store Size
```python
VECTOR_STORE_SIZE = Gauge(
    'rag_vector_store_documents',
    'Number of documents in the vector store'
)
```
- **Type**: Gauge (can go up or down)
- **Purpose**: Track knowledge base size
- **Recording**: `monitor.update_vector_store_size(1500)`

##### Conversation History Length
```python
CONVERSATION_LENGTH = Gauge(
    'rag_conversation_history_length',
    'Current length of conversation history'
)
```
- **Type**: Gauge
- **Purpose**: Track conversation context size
- **Recording**: `monitor.update_conversation_length(10)`

##### System Information
```python
SYSTEM_INFO = Info('rag_system', 'RAG Pipeline System Information')
```
- **Type**: Info (metadata)
- **Purpose**: Static system metadata
- **Data**: version, component, security_enabled

### 3. Metrics Recording Pattern

#### Integration in RAG Pipeline

```python
# Initialize monitor
monitor = RAGMonitor(port=8000, host='0.0.0.0')

# Update system metrics
monitor.update_vector_store_size(len(vector_store.documents))

# Record query processing
start_time = time.time()
try:
    # Process query
    response = process_query(user_input)
    
    # Record success
    monitor.record_query('success')
    monitor.record_latency(start_time)
    
    # Record PII redactions
    if redaction_result['redaction_applied']:
        for entity_type in redaction_result['redacted_types']:
            monitor.record_redaction(entity_type)
            
except SecurityException as e:
    # Record security event
    monitor.record_attack(e.attack_type)
    monitor.record_query('blocked')
```

## Prometheus Configuration

### 1. Prometheus Configuration File

Located at `Health-Security-Metrics/prometheus.yml`:

```yaml
global:
  scrape_interval: 5s      # Scrape metrics every 5 seconds
  evaluation_interval: 5s   # Evaluate rules every 5 seconds

scrape_configs:
  - job_name: 'rag_pipeline'
    static_configs:
      - targets: ['host.docker.internal:8000']
    
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        replacement: 'rag_pipeline'
    
    scrape_interval: 5s
    scrape_timeout: 4s
```

**Configuration Breakdown:**

| Parameter | Value | Description |
|-----------|-------|-------------|
| `scrape_interval` | 5s | How often Prometheus scrapes metrics |
| `evaluation_interval` | 5s | How often Prometheus evaluates alerting rules |
| `job_name` | rag_pipeline | Identifier for this scrape job |
| `targets` | host.docker.internal:8000 | Where to scrape metrics from |
| `scrape_timeout` | 4s | Maximum time to wait for scrape |

**Important:** `host.docker.internal` allows Docker containers to access the host machine's localhost.

### 2. Docker Compose Setup

Located at `Health-Security-Metrics/docker-compose.yml`:

```yaml
version: '3.8'

services:
  prometheus:
    image: prom/prometheus:latest
    container_name: prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.enable-lifecycle'
    networks:
      - monitoring

  grafana:
    image: grafana/grafana:latest
    container_name: grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    depends_on:
      - prometheus
    networks:
      - monitoring

volumes:
  prometheus_data:
  grafana_data:

networks:
  monitoring:
    driver: bridge
```

**Service Definitions:**

#### Prometheus Service
- **Image**: Official Prometheus image
- **Port**: 9090 (host) → 9090 (container)
- **Volumes**:
  - Config file: `./prometheus.yml` → `/etc/prometheus/prometheus.yml`
  - Data persistence: `prometheus_data` volume
- **Command**: Specifies config file and storage location
- **Network**: Connected to `monitoring` network

#### Grafana Service
- **Image**: Official Grafana image
- **Port**: 3000 (host) → 3000 (container)
- **Environment**:
  - Default admin password: `admin`
  - Sign-up disabled for security
- **Volumes**:
  - Data persistence: `grafana_data` volume
  - Provisioning: Auto-configure datasources
- **Dependencies**: Waits for Prometheus to start
- **Network**: Connected to `monitoring` network

### 3. Data Flow

#### Step-by-Step Process

1. **Application Start**: RAG pipeline starts with `RAGMonitor(port=8000)`
2. **Metrics Exposure**: HTTP endpoint `/metrics` becomes available
3. **Prometheus Scrape**: Every 5 seconds, Prometheus queries `http://host.docker.internal:8000/metrics`
4. **Data Storage**: Prometheus stores time-series data in TSDB
5. **Grafana Query**: Grafana queries Prometheus using PromQL
6. **Visualization**: Data is rendered in dashboards

#### Sample Metrics Endpoint Output

When accessing `http://localhost:8000/metrics`:

```prometheus
# HELP rag_security_attacks_total Total number of prompt injection attempts blocked
# TYPE rag_security_attacks_total counter
rag_security_attacks_total{attack_type="jailbreak"} 5.0
rag_security_attacks_total{attack_type="exfiltration"} 2.0

# HELP rag_security_pii_redacted_total Total number of PII entities redacted from responses
# TYPE rag_security_pii_redacted_total counter
rag_security_pii_redacted_total{entity_type="email"} 12.0
rag_security_pii_redacted_total{entity_type="phone"} 8.0

# HELP rag_request_duration_seconds Time spent processing RAG requests
# TYPE rag_request_duration_seconds histogram
rag_request_duration_seconds_bucket{le="0.1"} 45.0
rag_request_duration_seconds_bucket{le="0.5"} 120.0
rag_request_duration_seconds_bucket{le="1.0"} 180.0
rag_request_duration_seconds_sum 156.8
rag_request_duration_seconds_count 200.0

# HELP rag_queries_total Total number of queries processed
# TYPE rag_queries_total counter
rag_queries_total{status="success"} 193.0
rag_queries_total{status="blocked"} 5.0
rag_queries_total{status="no_context"} 2.0

# HELP rag_vector_store_documents Number of documents in the vector store
# TYPE rag_vector_store_documents gauge
rag_vector_store_documents 1500.0
```

## Data Visualization with Grafana

### 1. Grafana Data Source Configuration

Grafana connects to Prometheus to query metrics.

**Configuration Steps:**

1. Access Grafana: `http://localhost:3000`
2. Navigate to **Configuration** → **Data Sources**
3. Click **Add data source**
4. Select **Prometheus**
5. Configure settings:
   - **Name**: Prometheus
   - **URL**: `http://prometheus:9090` (Docker network)
   - **Access**: Server (default)
6. Click **Save & Test**

### 2. PromQL Queries

Grafana uses PromQL (Prometheus Query Language) to retrieve and aggregate metrics.

#### Common Query Patterns

##### Rate Calculations
```promql
# Queries per minute
sum(rate(rag_queries_total[5m])) * 60

# Attacks per minute by type
sum by (attack_type) (rate(rag_security_attacks_total[1m])) * 60
```

##### Percentile Calculations
```promql
# P95 latency
histogram_quantile(0.95, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))

# P50 similarity score
histogram_quantile(0.50, sum(rate(rag_similarity_score_bucket[5m])) by (le))
```

##### Aggregations
```promql
# Total queries in last 24 hours
sum(increase(rag_queries_total[24h]))

# Success rate percentage
sum(rate(rag_queries_total{status="success"}[5m])) / sum(rate(rag_queries_total[5m])) * 100
```

### 3. Dashboard Organization

Grafana dashboards are organized into logical sections for easy monitoring (see Grafana Dashboard Documentation for details).

## System Deployment

### 1. Installation Steps

```powershell
# 1. Navigate to metrics directory
cd "c:\Tejas\BE Project\CODEBASE\BE-Project\Health-Security-Metrics"

# 2. Install Python dependencies
pip install prometheus-client

# 3. Start Prometheus and Grafana
docker-compose up -d

# 4. Verify services are running
docker ps

# 5. Check Prometheus targets
# Open browser: http://localhost:9090/targets
```

### 2. Starting the RAG Pipeline

```powershell
# Navigate to RAG pipeline directory
cd "c:\Tejas\BE Project\CODEBASE\BE-Project\RAG-Pipeline-Ollama"

# Run the secure pipeline (includes monitoring)
python rag_pipeline_secure.py
```

### 3. Verification

**Check Metrics Exposure:**
```powershell
# View raw metrics
curl http://localhost:8000/metrics

# Should see Prometheus format output
```

**Check Prometheus Scraping:**
```powershell
# Query Prometheus API
curl 'http://localhost:9090/api/v1/query?query=rag_queries_total'
```

**Access Grafana:**
```
URL: http://localhost:3000
Username: admin
Password: admin
```

## Monitoring Best Practices

### 1. Metric Selection

**What to Monitor:**
- ✅ **Security Events**: Attacks, PII redactions
- ✅ **Performance**: Latency percentiles, throughput
- ✅ **Quality**: Refusal rates, similarity scores
- ✅ **System Health**: Vector store size, errors

**What Not to Monitor:**
- ❌ Individual user queries (privacy)
- ❌ Actual PII content (security)
- ❌ Excessive granularity (performance impact)

### 2. Data Retention

**Prometheus Storage:**
- Default: 15 days retention
- Configurable via `--storage.tsdb.retention.time` flag
- Adjust based on compliance requirements

### 3. Performance Considerations

**Scrape Interval:**
- Current: 5 seconds (real-time monitoring)
- Production: Consider 15-30 seconds for high-scale systems
- Balance: freshness vs. system load

**Metric Cardinality:**
- Keep label values bounded
- Avoid high-cardinality labels (user IDs, timestamps)
- Current implementation: Low cardinality (attack_type, status, entity_type)

## Troubleshooting

### Common Issues

#### Metrics Not Appearing

**Symptom**: Grafana shows "No data"

**Diagnosis:**
```powershell
# 1. Check if metrics are exposed
curl http://localhost:8000/metrics

# 2. Check Prometheus targets
# Navigate to: http://localhost:9090/targets
# Verify target is "UP"

# 3. Check Prometheus logs
docker logs prometheus
```

**Solutions:**
- Ensure RAG application is running
- Verify port 8000 is not blocked
- Check `host.docker.internal` resolves correctly

#### Connection Refused

**Symptom**: Prometheus can't reach application

**Solutions:**
```yaml
# For Windows/Mac with Docker Desktop, use:
targets: ['host.docker.internal:8000']

# For Linux, use:
targets: ['172.17.0.1:8000']  # Docker bridge IP
# Or add network_mode: host to docker-compose.yml
```

## Security Considerations

### 1. Metrics Endpoint Protection

**Current**: Exposed on `0.0.0.0:8000` for development

**Production Recommendations:**
- Use authentication for `/metrics` endpoint
- Restrict access to monitoring network
- Consider TLS/SSL encryption

### 2. Sensitive Data

**What's Safe:**
- ✅ Aggregated counts
- ✅ Statistical measures (percentiles, averages)
- ✅ Event types and categories

**What's Not Logged:**
- ❌ Actual user queries
- ❌ PII content
- ❌ User identifiers

### 3. Grafana Security

**Access Control:**
- Change default admin password immediately
- Disable sign-up: `GF_USERS_ALLOW_SIGN_UP=false`
- Use RBAC for team access

## Conclusion

The Health & Security Metrics system provides comprehensive, real-time visibility into the RAG pipeline's operation. Through Prometheus's efficient time-series storage and Grafana's powerful visualization capabilities, teams can monitor security events, track performance, ensure quality, and maintain system health effectively. The modular architecture allows for easy extension and customization based on evolving monitoring needs.

## References

- **Source Code**: `Health-Security-Metrics/instrumentation.py`
- **Configuration**: `Health-Security-Metrics/prometheus.yml`, `docker-compose.yml`
- **Documentation**: `Health-Security-Metrics/README.md`, `Health-Security-Metrics/QUICKSTART.md`
- **Related Docs**: PII Redaction Implementation, Grafana Dashboard Configuration
- **External Resources**:
  - [Prometheus Documentation](https://prometheus.io/docs/)
  - [Prometheus Python Client](https://github.com/prometheus/client_python)
  - [PromQL Guide](https://prometheus.io/docs/prometheus/latest/querying/basics/)
