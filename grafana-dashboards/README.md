# RAG Pipeline Grafana Dashboard

This directory contains a comprehensive single-page Grafana dashboard for monitoring your RAG Pipeline system with organized sections.

## 📊 Dashboard Overview

**File:** `rag-pipeline-dashboard.json`

The dashboard is organized into 4 collapsible sections:
1. **📊 Executive Overview** - High-level KPIs and business metrics
2. **🔒 Security Operations** - Security monitoring and attack tracking
3. **⚡ Performance Metrics** - Latency and throughput analysis
4. **✨ Quality Metrics** - RAG quality and accuracy monitoring

## 🚀 Quick Start

### 1. Import Dashboard into Grafana

**Via UI:**
1. Open Grafana (http://localhost:3000)
2. Navigate to **Dashboards** → **Import**
3. Click **Upload JSON file**
4. Select `rag-pipeline-dashboard.json`
5. Select your Prometheus data source
6. Click **Import**

**Via API:**
```bash
curl -X POST \
  http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @grafana-dashboards/rag-pipeline-dashboard.json
```

### 2. Configure Data Source

1. Go to **Configuration** → **Data Sources**
2. Add Prometheus data source
3. URL: `http://prometheus:9090` (Docker) or `http://localhost:9090` (local)
4. Click **Save & Test**

### 3. Verify Metrics

```bash
# View raw metrics
curl http://localhost:8000/metrics

# Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=rag_queries_total'
```

## 📈 Dashboard Sections & PromQL Queries

### 📊 Section 1: Executive Overview

| Visualization | PromQL Query | Description |
|--------------|--------------|-------------|
| **Total Queries (24h)** | `sum(increase(rag_queries_total[24h]))` | Total queries in last 24 hours |
| **Attack Attempts (24h)** | `sum(increase(rag_security_attacks_total[24h]))` | Security attacks detected |
| **P95 Latency** | `histogram_quantile(0.95, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))` | 95th percentile latency |
| **Success Rate (Pie)** | `sum(increase(rag_queries_total{status="success\|blocked\|no_context"}[24h]))` | Query status distribution |
| **Query Rate Timeline** | `sum(rate(rag_queries_total[5m])) * 60` | Queries per minute over time |
| **Top 5 Attack Types** | `topk(5, sum by (attack_type) (increase(rag_security_attacks_total[24h])))` | Most frequent attack types |

### 🔒 Section 2: Security Operations

| Visualization | PromQL Query | Description |
|--------------|--------------|-------------|
| **Real-time Attacks** | `sum by (attack_type) (rate(rag_security_attacks_total[1m])) * 60` | Attacks per minute by type |
| **Attack Distribution** | `sum by (attack_type) (increase(rag_security_attacks_total[24h]))` | Attack type breakdown |
| **PII Redactions** | `sum by (entity_type) (increase(rag_security_pii_redacted_total[1h]))` | PII entities redacted |
| **Blocked vs Allowed** | `sum(rate(rag_queries_total{status="success\|blocked\|no_context"}[5m])) * 60` | Query status over time |

### ⚡ Section 3: Performance Metrics

| Visualization | PromQL Query | Description |
|--------------|--------------|-------------|
| **P50 Latency** | `histogram_quantile(0.50, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))` | Median latency |
| **P95 Latency** | `histogram_quantile(0.95, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))` | 95th percentile latency |
| **P99 Latency** | `histogram_quantile(0.99, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))` | 99th percentile latency |
| **Requests Per Second** | `sum(rate(rag_queries_total[1m]))` | Current RPS |
| **Latency Heatmap** | `sum(increase(rag_request_duration_seconds_bucket[1m])) by (le)` | Latency distribution over time |
| **Avg Latency by Status** | `sum by (status) (rate(rag_request_duration_seconds_sum[5m])) / sum by (status) (rate(rag_request_duration_seconds_count[5m]))` | Average latency per status |
| **Vector Store Size** | `rag_vector_store_documents` | Current document count |

### ✨ Section 4: Quality Metrics

| Visualization | PromQL Query | Description |
|--------------|--------------|-------------|
| **Avg Similarity Score** | `sum(rate(rag_similarity_score_sum[5m])) / sum(rate(rag_similarity_score_count[5m]))` | Average retrieval similarity |
| **Refusal Rate %** | `sum(rate(rag_content_refusals_total[5m])) / sum(rate(rag_queries_total[5m])) * 100` | Percentage of refusals |
| **Conversation Length** | `rag_conversation_history_length` | Current conversation size |
| **Query Status Breakdown** | `sum by (status) (increase(rag_queries_total[1h]))` | Status distribution |
| **Similarity Distribution** | `sum(increase(rag_similarity_score_bucket[5m])) by (le)` | Score distribution histogram |
| **Similarity Timeline** | `sum(rate(rag_similarity_score_sum[5m])) / sum(rate(rag_similarity_score_count[5m]))` | Score trend over time |
| **P95 Similarity** | `histogram_quantile(0.95, sum(rate(rag_similarity_score_bucket[5m])) by (le))` | 95th percentile similarity |
| **Vector Store Growth** | `rag_vector_store_documents` | Document count trend |
| **Conversation Trend** | `rag_conversation_history_length` | Conversation length over time |

## 📊 Complete PromQL Reference

### Counters (use with `rate()` or `increase()`)

```promql
# Query metrics
rag_queries_total                          # Labels: status
rag_security_attacks_total                 # Labels: attack_type
rag_security_pii_redacted_total           # Labels: entity_type
rag_content_refusals_total                # No labels

# Rate calculations
rate(rag_queries_total[5m])               # Per-second rate
increase(rag_queries_total[24h])          # Total increase over period
```

### Histograms (use with `histogram_quantile()`)

```promql
# Latency histogram
rag_request_duration_seconds_bucket       # Buckets: 0.1, 0.5, 1.0, 2.0, 5.0, 10.0
rag_request_duration_seconds_sum          # Sum of all latencies
rag_request_duration_seconds_count        # Count of requests

# Similarity score histogram
rag_similarity_score_bucket               # Buckets: 0.0 to 1.0 (step 0.1)
rag_similarity_score_sum                  # Sum of all scores
rag_similarity_score_count                # Count of scores

# Calculate percentiles
histogram_quantile(0.50, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))  # P50
histogram_quantile(0.95, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))  # P95
histogram_quantile(0.99, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))  # P99

# Calculate averages
sum(rate(rag_request_duration_seconds_sum[5m])) / sum(rate(rag_request_duration_seconds_count[5m]))
```

### Gauges (use directly)

```promql
# Current values
rag_vector_store_documents                # Current document count
rag_conversation_history_length           # Current conversation length
```

### Aggregations & Filtering

```promql
# Sum across all labels
sum(rag_queries_total)

# Sum by specific label
sum by (status) (rag_queries_total)

# Filter by label value
rag_queries_total{status="success"}

# Multiple label filters
rag_security_attacks_total{attack_type=~"jailbreak|pii_leak"}

# Top K results
topk(5, sum by (attack_type) (increase(rag_security_attacks_total[24h])))
```

### Time Windows

```promql
[5m]    # 5 minutes
[1h]    # 1 hour  
[24h]   # 24 hours
[7d]    # 7 days
```

### Useful Calculations

```promql
# Convert rate to per-minute
sum(rate(rag_queries_total[5m])) * 60

# Calculate percentage
sum(rate(rag_queries_total{status="success"}[5m])) / sum(rate(rag_queries_total[5m])) * 100

# Calculate growth/delta
increase(rag_vector_store_documents[1h])
```

## 🎨 Dashboard Features

### Auto-Refresh
- Default: 30 seconds
- Configurable in top-right corner

### Time Ranges
- Default: Last 6 hours
- Can be changed to: 5m, 15m, 1h, 6h, 12h, 24h, 7d, 30d

### Collapsible Sections
- Click section headers to collapse/expand
- Useful for focusing on specific areas

### Color Thresholds
- **Green**: Healthy/good values
- **Yellow**: Warning range
- **Red**: Critical/alert range

### Interactive Features
- Click legend items to show/hide series
- Hover for detailed tooltips
- Zoom by clicking and dragging
- Double-click to reset zoom

## 🔧 Customization

### Modify Panel Queries
1. Click panel title → **Edit**
2. Modify PromQL query in **Query** tab
3. Adjust visualization in **Panel** tab
4. Click **Apply** to save

### Adjust Thresholds
Find threshold configuration in JSON:
```json
"thresholds": {
  "mode": "absolute",
  "steps": [
    {"value": null, "color": "green"},
    {"value": 2, "color": "yellow"},
    {"value": 3, "color": "red"}
  ]
}
```

### Add New Panels
1. Click **Add panel** in dashboard
2. Select visualization type
3. Add PromQL query
4. Configure display options
5. Save dashboard

### Export Dashboard
1. Dashboard settings (gear icon)
2. **JSON Model**
3. Copy JSON or save to file

## 🔍 Troubleshooting

### No Data Showing

```bash
# 1. Check if metrics are exposed
curl http://localhost:8000/metrics | grep rag_

# 2. Verify Prometheus is scraping
curl http://localhost:9090/api/v1/targets

# 3. Test PromQL query in Prometheus
curl 'http://localhost:9090/api/v1/query?query=rag_queries_total'

# 4. Check Grafana data source
# UI: Configuration → Data Sources → Prometheus → Save & Test
```

### Common Issues

| Issue | Solution |
|-------|----------|
| "No data" message | Check time range, verify app is running |
| "Bad gateway" error | Verify Prometheus URL in data source |
| Wrong values | Check PromQL syntax, verify metric names |
| Missing metrics | Ensure instrumentation.py is recording data |

### Query Testing

Test queries in Prometheus before adding to Grafana:
```bash
# Prometheus query API
curl 'http://localhost:9090/api/v1/query?query=rag_queries_total'

# Query with time range
curl 'http://localhost:9090/api/v1/query_range?query=rate(rag_queries_total[5m])&start=2024-01-01T00:00:00Z&end=2024-01-01T23:59:59Z&step=15s'
```

## 📝 Maintenance

### Regular Tasks

```bash
# Backup dashboard
curl http://admin:admin@localhost:3000/api/dashboards/uid/rag-pipeline \
  > backup-$(date +%Y%m%d).json

# Update dashboard
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -d @rag-pipeline-dashboard.json
```

### Performance Optimization

For better performance with large datasets:
1. Use recording rules in Prometheus for complex queries
2. Increase refresh interval (e.g., 1m instead of 30s)
3. Reduce time range for heavy queries
4. Use downsampling for long-term data

## 📚 Resources

- [Grafana Documentation](https://grafana.com/docs/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [PromQL Functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)
- [Prometheus Client Python](https://github.com/prometheus/client_python)
- [Histogram Quantiles](https://prometheus.io/docs/practices/histograms/)

## 🆘 Support

For issues:
1. Check Grafana logs: `docker logs grafana`
2. Check Prometheus logs: `docker logs prometheus`
3. Verify metrics: `curl http://localhost:8000/metrics`
4. Use Grafana's Query Inspector (panel menu → Inspect → Query)
