# Grafana Dashboard Configuration

## Executive Summary

This document provides comprehensive documentation for the Grafana monitoring dashboards used in the RAG pipeline. The dashboard system provides real-time visualization of security events, performance metrics, quality indicators, and system health across four organized sections. This documentation covers dashboard structure, PromQL queries, visualization types, and configuration details suitable for inclusion in technical reports.

## Dashboard Architecture

### Overview

The Grafana dashboard system consists of a single comprehensive dashboard organized into four collapsible sections, providing a complete view of the RAG pipeline's operational status.

```
┌──────────────────────────────────────────────────────────┐
│           RAG Pipeline Monitoring Dashboard              │
├──────────────────────────────────────────────────────────┤
│  📊 Section 1: Executive Overview                        │
│     - High-level KPIs                                     │
│     - Business metrics                                    │
│     - Overall system health                               │
├──────────────────────────────────────────────────────────┤
│  🔒 Section 2: Security Operations                       │
│     - Attack monitoring                                   │
│     - PII redaction tracking                              │
│     - Threat detection                                    │
├──────────────────────────────────────────────────────────┤
│  ⚡ Section 3: Performance Metrics                        │
│     - Latency analysis                                    │
│     - Throughput monitoring                               │
│     - Resource utilization                                │
├──────────────────────────────────────────────────────────┤
│  ✨ Section 4: Quality Metrics                           │
│     - Similarity scores                                   │
│     - Refusal rates                                       │
│     - Retrieval quality                                   │
└──────────────────────────────────────────────────────────┘
```

### Dashboard Files

| File | Purpose | Location |
|------|---------|----------|
| `rag-pipeline-dashboard.json` | Complete unified dashboard | `grafana-dashboards/` |
| `1-executive-overview.json` | Standalone executive section | `grafana-dashboards/` |
| `2-security-operations.json` | Standalone security section | `grafana-dashboards/` |
| `3-performance-dashboard.json` | Standalone performance section | `grafana-dashboards/` |
| `4-quality-dashboard.json` | Standalone quality section | `grafana-dashboards/` |

## Section 1: Executive Overview

### Purpose
Provides high-level business and operational metrics for stakeholders and management. Focuses on overall system performance and critical KPIs.

### Visualizations

#### 1.1 Total Queries (24h)
**Type**: Stat Panel (Single Number)

**PromQL Query:**
```promql
sum(increase(rag_queries_total[24h]))
```

**Description**: Displays the total number of queries processed in the last 24 hours.

**Configuration:**
- **Unit**: None (count)
- **Decimal Places**: 0
- **Color**: Green → Yellow → Red
- **Thresholds**: 
  - Green: < 1000
  - Yellow: 1000-5000
  - Red: > 5000

**Use Case**: Monitor daily system usage and identify traffic patterns.

---

#### 1.2 Attack Attempts (24h)
**Type**: Stat Panel (Single Number)

**PromQL Query:**
```promql
sum(increase(rag_security_attacks_total[24h]))
```

**Description**: Total security attacks detected and blocked in the last 24 hours.

**Configuration:**
- **Unit**: None (count)
- **Decimal Places**: 0
- **Color**: Green → Yellow → Red
- **Thresholds**:
  - Green: 0-5
  - Yellow: 6-20
  - Red: > 20

**Use Case**: Security monitoring and threat assessment.

---

#### 1.3 P95 Latency
**Type**: Stat Panel (Single Number with Sparkline)

**PromQL Query:**
```promql
histogram_quantile(0.95, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))
```

**Description**: 95th percentile of request processing latency (95% of requests complete faster than this time).

**Configuration:**
- **Unit**: Seconds (s)
- **Decimal Places**: 3
- **Color**: Green → Yellow → Red
- **Thresholds**:
  - Green: < 1.0s
  - Yellow: 1.0-3.0s
  - Red: > 3.0s
- **Sparkline**: Shows trend over time

**Use Case**: Performance SLA monitoring.

**Formula Explanation:**
- `rate()`: Calculates per-second rate over 5-minute window
- `sum() by (le)`: Aggregates across buckets
- `histogram_quantile(0.95, ...)`: Calculates 95th percentile

---

#### 1.4 Success Rate Distribution
**Type**: Pie Chart

**PromQL Queries:**
```promql
# Success
sum(increase(rag_queries_total{status="success"}[24h]))

# Blocked
sum(increase(rag_queries_total{status="blocked"}[24h]))

# No Context
sum(increase(rag_queries_total{status="no_context"}[24h]))
```

**Description**: Breakdown of query outcomes over the last 24 hours.

**Configuration:**
- **Legend**: status label
- **Colors**:
  - Success: Green (#73BF69)
  - Blocked: Red (#F2495C)
  - No Context: Yellow (#FF9830)
- **Display**: Percentage and count

**Use Case**: Quick health check of system effectiveness.

---

#### 1.5 Query Rate Timeline
**Type**: Time Series Graph

**PromQL Query:**
```promql
sum(rate(rag_queries_total[5m])) * 60
```

**Description**: Queries per minute over time, showing traffic patterns.

**Configuration:**
- **Unit**: Queries per minute (qpm)
- **Y-Axis**: Auto-scale
- **Line Style**: Smooth line
- **Fill**: 20% opacity
- **Legend**: Bottom placement

**Use Case**: Identify peak usage times and traffic anomalies.

**Formula Explanation:**
- `rate(rag_queries_total[5m])`: Per-second rate over 5 minutes
- `* 60`: Convert to per-minute rate

---

#### 1.6 Top 5 Attack Types
**Type**: Bar Chart (Horizontal)

**PromQL Query:**
```promql
topk(5, sum by (attack_type) (increase(rag_security_attacks_total[24h])))
```

**Description**: Most frequent attack types in the last 24 hours.

**Labels:**
- `jailbreak`: Prompt injection attempts
- `exfiltration`: Data extraction attempts
- `pii_leak`: PII leakage attempts
- `roleplay`: Role manipulation attempts

**Configuration:**
- **Orientation**: Horizontal bars
- **Color**: Gradient (red scale)
- **Display**: Count with attack type label

**Use Case**: Identify prevalent attack vectors for security hardening.

**Formula Explanation:**
- `sum by (attack_type)`: Group by attack type
- `increase([24h])`: Total increase over 24 hours
- `topk(5, ...)`: Select top 5 values

## Section 2: Security Operations

### Purpose
Dedicated security monitoring for threat detection, attack tracking, and privacy compliance. Critical for security teams and compliance officers.

### Visualizations

#### 2.1 Real-time Attack Rate
**Type**: Time Series Graph (Multi-line)

**PromQL Query:**
```promql
sum by (attack_type) (rate(rag_security_attacks_total[1m])) * 60
```

**Description**: Attacks per minute by type, showing real-time threat landscape.

**Labels:**
- `jailbreak`: Prompt manipulation
- `exfiltration`: Data extraction
- `pii_leak`: Privacy violations
- `roleplay`: Identity impersonation

**Configuration:**
- **Unit**: Attacks per minute (apm)
- **Multiple Series**: One line per attack type
- **Colors**: Distinct colors for each type
- **Legend**: Shows current, min, max, average values
- **Alert Zone**: Highlight above threshold

**Use Case**: Real-time security incident detection.

---

#### 2.2 Attack Type Distribution
**Type**: Donut Chart

**PromQL Query:**
```promql
sum by (attack_type) (increase(rag_security_attacks_total[24h]))
```

**Description**: Proportional breakdown of attack types over 24 hours.

**Configuration:**
- **Display**: Percentage with count
- **Center Label**: Total attacks
- **Colors**: Security-themed palette
- **Threshold**: Highlight if any type > 40%

**Use Case**: Understand attack vector distribution for defense prioritization.

---

#### 2.3 PII Redaction Activity
**Type**: Stacked Bar Chart (Time Series)

**PromQL Query:**
```promql
sum by (entity_type) (increase(rag_security_pii_redacted_total[1h]))
```

**Description**: Hourly PII redactions by entity type.

**Labels:**
- `email`: Email addresses
- `phone`: Phone numbers
- `name`: Personal names
- `ticket_id`: Ticket identifiers
- `credit_card`: Credit card numbers
- `ssn`: Social Security Numbers

**Configuration:**
- **Stacking**: Enabled (cumulative view)
- **Unit**: Count per hour
- **Colors**: Privacy-themed gradient
- **Legend**: Entity types with totals

**Use Case**: Privacy compliance monitoring and PII exposure tracking.

**Formula Explanation:**
- `increase([1h])`: Total increase per hour
- `sum by (entity_type)`: Separate series for each PII type

---

#### 2.4 Security Status: Blocked vs Allowed
**Type**: Time Series Graph (Area Chart)

**PromQL Query:**
```promql
# Allowed Queries (Success)
sum(rate(rag_queries_total{status="success"}[5m])) * 60

# Blocked Queries
sum(rate(rag_queries_total{status="blocked"}[5m])) * 60

# No Context
sum(rate(rag_queries_total{status="no_context"}[5m])) * 60
```

**Description**: Real-time view of query security status.

**Configuration:**
- **Type**: Stacked area chart
- **Unit**: Queries per minute
- **Colors**:
  - Success: Green
  - Blocked: Red
  - No Context: Orange
- **Fill Opacity**: 60%

**Use Case**: Monitor security effectiveness and false positive rate.

---

#### 2.5 PII Redaction Heatmap
**Type**: Heatmap

**PromQL Query:**
```promql
sum by (entity_type) (increase(rag_security_pii_redacted_total[5m]))
```

**Description**: Intensity map showing PII redaction patterns over time.

**Configuration:**
- **Buckets**: 5-minute intervals
- **Color Scheme**: Green (low) → Yellow → Red (high)
- **Y-Axis**: Entity types
- **X-Axis**: Time

**Use Case**: Identify patterns in PII exposure attempts.

## Section 3: Performance Metrics

### Purpose
Detailed performance analysis for system optimization and SLA compliance. Essential for DevOps and performance engineering teams.

### Visualizations

#### 3.1 Latency Percentiles
**Type**: Time Series Graph (Multi-line)

**PromQL Queries:**
```promql
# P50 (Median)
histogram_quantile(0.50, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))

# P95
histogram_quantile(0.95, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))

# P99
histogram_quantile(0.99, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))
```

**Description**: Request latency at different percentiles over time.

**Percentile Meanings:**
- **P50**: Median latency (50% of requests faster)
- **P95**: 95% of requests complete within this time
- **P99**: 99% of requests complete within this time (captures outliers)

**Configuration:**
- **Unit**: Seconds (s)
- **Y-Axis**: Logarithmic scale (optional)
- **Lines**:
  - P50: Blue (thin)
  - P95: Yellow (medium)
  - P99: Red (thick)
- **Threshold Lines**:
  - SLA Target: 2.0s (dotted line)

**Use Case**: SLA monitoring and performance degradation detection.

**Why Percentiles?**
- Averages hide outliers
- P95/P99 reveal worst-case user experience
- Industry standard for SLA definitions

---

#### 3.2 Requests Per Second (RPS)
**Type**: Gauge (Speedometer)

**PromQL Query:**
```promql
sum(rate(rag_queries_total[1m]))
```

**Description**: Current request throughput.

**Configuration:**
- **Unit**: Requests per second (req/s)
- **Decimal Places**: 2
- **Gauge Range**: 0-10 (auto-adjusts)
- **Color Zones**:
  - Green: 0-5 (normal)
  - Yellow: 5-8 (high load)
  - Red: > 8 (capacity concern)

**Use Case**: Real-time load monitoring.

---

#### 3.3 Latency Heatmap
**Type**: Heatmap

**PromQL Query:**
```promql
sum(increase(rag_request_duration_seconds_bucket[1m])) by (le)
```

**Description**: Distribution of latencies over time, showing concentration patterns.

**Configuration:**
- **Buckets**: Latency ranges (0.1s, 0.5s, 1.0s, 2.0s, 5.0s, 10.0s)
- **Color Scheme**: Blue (few requests) → Yellow → Red (many requests)
- **Y-Axis**: Latency buckets
- **X-Axis**: Time

**Use Case**: Identify performance anomalies and patterns.

---

#### 3.4 Average Latency by Status
**Type**: Bar Chart

**PromQL Query:**
```promql
sum by (status) (rate(rag_request_duration_seconds_sum[5m])) / 
sum by (status) (rate(rag_request_duration_seconds_count[5m]))
```

**Description**: Average latency broken down by query status.

**Configuration:**
- **Unit**: Seconds
- **Orientation**: Vertical bars
- **Colors**: Status-based
- **Labels**: Status categories with latency values

**Use Case**: Understand if security blocking adds latency overhead.

**Formula Explanation:**
- `_sum / _count`: Calculates average from histogram data
- `sum by (status)`: Separate average for each status

---

#### 3.5 Vector Store Size
**Type**: Stat Panel with Trend

**PromQL Query:**
```promql
rag_vector_store_documents
```

**Description**: Current number of documents in the knowledge base.

**Configuration:**
- **Unit**: Documents (count)
- **Decimal Places**: 0
- **Trend**: Sparkline showing growth
- **Color**: Information (blue)

**Use Case**: Monitor knowledge base growth and capacity.

---

#### 3.6 Throughput Timeline
**Type**: Time Series Graph (Area Chart)

**PromQL Query:**
```promql
sum(rate(rag_queries_total[1m])) * 60
```

**Description**: Queries per minute over extended period.

**Configuration:**
- **Unit**: Queries per minute
- **Fill**: Gradient
- **Color**: Blue
- **Y-Axis**: Auto-scale with 0 baseline

**Use Case**: Capacity planning and traffic pattern analysis.

## Section 4: Quality Metrics

### Purpose
Monitor RAG system quality, accuracy, and effectiveness. Critical for ML engineers and quality assurance teams.

### Visualizations

#### 4.1 Average Similarity Score
**Type**: Gauge (Arc)

**PromQL Query:**
```promql
sum(rate(rag_similarity_score_sum[5m])) / 
sum(rate(rag_similarity_score_count[5m]))
```

**Description**: Average similarity score of retrieved documents (0-1 scale).

**Interpretation:**
- **0.8-1.0**: Excellent - High confidence matches
- **0.6-0.8**: Good - Relevant results
- **0.4-0.6**: Fair - Marginal relevance
- **< 0.4**: Poor - Low quality retrieval

**Configuration:**
- **Range**: 0 to 1
- **Decimal Places**: 3
- **Color Zones**:
  - Red: < 0.4
  - Yellow: 0.4-0.6
  - Light Green: 0.6-0.8
  - Dark Green: > 0.8

**Use Case**: Monitor retrieval quality and knowledge base effectiveness.

---

#### 4.2 Refusal Rate Percentage
**Type**: Stat Panel

**PromQL Query:**
```promql
sum(rate(rag_content_refusals_total[5m])) / 
sum(rate(rag_queries_total[5m])) * 100
```

**Description**: Percentage of queries where the system refused to answer.

**Configuration:**
- **Unit**: Percent (%)
- **Decimal Places**: 2
- **Color**: Reverse scale (low is good)
- **Thresholds**:
  - Green: < 5%
  - Yellow: 5-15%
  - Red: > 15%

**Use Case**: Identify knowledge gaps and context limitations.

**Formula Explanation:**
- Refusals / Total Queries * 100
- Lower is better (indicates good knowledge coverage)

---

#### 4.3 Query Status Breakdown
**Type**: Stacked Bar Chart (Time Series)

**PromQL Query:**
```promql
sum by (status) (increase(rag_queries_total[1h]))
```

**Description**: Hourly distribution of query outcomes.

**Configuration:**
- **Stacking**: 100% (normalized view)
- **Unit**: Count
- **Colors**:
  - Success: Green
  - Blocked: Red
  - No Context: Orange
- **Legend**: Percentage of each status

**Use Case**: Track system effectiveness over time.

---

#### 4.4 Similarity Score Distribution
**Type**: Histogram

**PromQL Query:**
```promql
sum(increase(rag_similarity_score_bucket[5m])) by (le)
```

**Description**: Distribution of similarity scores showing concentration.

**Configuration:**
- **Buckets**: 0.0, 0.1, 0.2, ..., 1.0
- **Type**: Vertical bars
- **Color**: Gradient (blue scale)
- **X-Axis**: Similarity score ranges
- **Y-Axis**: Count of queries

**Use Case**: Understand typical retrieval quality distribution.

---

#### 4.5 Similarity Score Timeline
**Type**: Time Series Graph

**PromQL Query:**
```promql
sum(rate(rag_similarity_score_sum[5m])) / 
sum(rate(rag_similarity_score_count[5m]))
```

**Description**: Average similarity score trend over time.

**Configuration:**
- **Unit**: Score (0-1)
- **Line**: Smooth, medium thickness
- **Fill**: 20% opacity
- **Reference Line**: 0.6 (minimum acceptable threshold)

**Use Case**: Monitor quality degradation or improvement trends.

---

#### 4.6 P95 Similarity Score
**Type**: Stat Panel

**PromQL Query:**
```promql
histogram_quantile(0.95, sum(rate(rag_similarity_score_bucket[5m])) by (le))
```

**Description**: 95th percentile of similarity scores (95% of retrievals score higher than this).

**Configuration:**
- **Unit**: Score (0-1)
- **Decimal Places**: 3
- **Color**: Green → Yellow → Red
- **Thresholds**:
  - Red: < 0.5
  - Yellow: 0.5-0.7
  - Green: > 0.7

**Use Case**: Ensure consistently high retrieval quality.

---

#### 4.7 Vector Store Growth
**Type**: Time Series Graph (Line)

**PromQL Query:**
```promql
rag_vector_store_documents
```

**Description**: Document count trend over time.

**Configuration:**
- **Unit**: Documents
- **Line**: Step (shows discrete changes)
- **Color**: Blue
- **Y-Axis**: Start at 0

**Use Case**: Track knowledge base expansion.

---

#### 4.8 Conversation Length Trend
**Type**: Time Series Graph

**PromQL Query:**
```promql
rag_conversation_history_length
```

**Description**: Current conversation history size over time.

**Configuration:**
- **Unit**: Messages (count)
- **Line**: Smooth
- **Color**: Purple
- **Alert**: If consistently > 20 (memory concern)

**Use Case**: Monitor conversation memory usage.

## PromQL Query Reference

### Understanding PromQL

PromQL (Prometheus Query Language) is the functional query language for Prometheus. It allows for powerful aggregation and analysis of time-series data.

### Key Functions

#### Rate Functions

```promql
# rate() - Per-second rate over time window
rate(rag_queries_total[5m])

# irate() - Instant rate (for volatile metrics)
irate(rag_queries_total[1m])

# increase() - Total increase over time window
increase(rag_queries_total[24h])
```

**When to Use:**
- `rate()`: Smooth rates for alerting and graphing
- `irate()`: Spiky metrics needing instant values
- `increase()`: Total counts over period

#### Aggregation Functions

```promql
# sum() - Add all values
sum(rag_queries_total)

# avg() - Average across series
avg(rag_request_duration_seconds)

# min() / max() - Minimum/Maximum values
max(rag_similarity_score)

# count() - Count of series
count(rag_queries_total)
```

#### Percentile Calculations

```promql
# histogram_quantile() - Calculate percentiles from histograms
histogram_quantile(0.95, 
  sum(rate(rag_request_duration_seconds_bucket[5m])) by (le)
)
```

**Parameters:**
- `0.95`: The percentile (95th)
- `sum() by (le)`: Aggregation preserving bucket label
- `[5m]`: Time window for rate calculation

#### Filtering and Selection

```promql
# Filter by label value
rag_queries_total{status="success"}

# Regex matching
rag_security_attacks_total{attack_type=~"jailbreak|exfiltration"}

# Negative matching
rag_queries_total{status!="blocked"}

# Top K results
topk(5, sum by (attack_type) (rag_security_attacks_total))
```

### Time Windows

| Window | Use Case |
|--------|----------|
| `[1m]` | Real-time/instant metrics |
| `[5m]` | Standard monitoring (default) |
| `[1h]` | Hourly aggregations |
| `[24h]` | Daily summaries |
| `[7d]` | Weekly trends |

## Dashboard Configuration

### Global Settings

#### Time Range
- **Default**: Last 6 hours
- **Refresh**: 30 seconds (auto-refresh)
- **Options**: 5m, 15m, 30m, 1h, 3h, 6h, 12h, 24h, 7d, 30d

#### Variables

The dashboard supports variables for dynamic filtering:

```json
{
  "name": "instance",
  "type": "query",
  "query": "label_values(rag_queries_total, instance)",
  "multi": false,
  "includeAll": false
}
```

**Purpose**: Filter metrics by specific RAG instance (useful for multi-instance deployments).

#### Theme

- **Default**: Dark theme
- **Supported**: Light theme, High contrast
- **Customizable**: Colors, fonts, spacing

### Panel Configuration Standards

#### Common Settings

```json
{
  "transparent": false,
  "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
  "options": {
    "legend": {
      "displayMode": "list",
      "placement": "bottom",
      "showLegend": true
    },
    "tooltip": {
      "mode": "multi",
      "sort": "none"
    }
  }
}
```

#### Threshold Configuration

```json
{
  "thresholds": {
    "mode": "absolute",
    "steps": [
      {"value": null, "color": "green"},
      {"value": 0.5, "color": "yellow"},
      {"value": 0.8, "color": "red"}
    ]
  }
}
```

### Alerting Rules

#### Example: High Attack Rate Alert

```json
{
  "alert": "HighAttackRate",
  "expr": "sum(rate(rag_security_attacks_total[5m])) * 60 > 10",
  "for": "5m",
  "labels": {
    "severity": "warning"
  },
  "annotations": {
    "summary": "High attack rate detected",
    "description": "Attack rate is {{ $value }} attacks/min"
  }
}
```

#### Example: High Latency Alert

```json
{
  "alert": "HighLatencyP95",
  "expr": "histogram_quantile(0.95, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le)) > 3",
  "for": "10m",
  "labels": {
    "severity": "critical"
  },
  "annotations": {
    "summary": "P95 latency exceeds SLA",
    "description": "P95 latency is {{ $value }}s (SLA: 3s)"
  }
}
```

## Dashboard Import and Export

### Importing Dashboard

#### Method 1: Via UI
1. Navigate to Grafana: `http://localhost:3000`
2. Click **Dashboards** → **Import**
3. Click **Upload JSON file**
4. Select `rag-pipeline-dashboard.json`
5. Select Prometheus data source
6. Click **Import**

#### Method 2: Via API
```powershell
curl -X POST `
  http://admin:admin@localhost:3000/api/dashboards/db `
  -H "Content-Type: application/json" `
  -d "@grafana-dashboards/rag-pipeline-dashboard.json"
```

### Exporting Dashboard

#### Via UI
1. Open dashboard
2. Click dashboard settings (gear icon)
3. Select **JSON Model**
4. Copy JSON or **Save to file**

#### Via API
```powershell
curl http://admin:admin@localhost:3000/api/dashboards/uid/rag-pipeline `
  > rag-pipeline-backup.json
```

## Customization Guide

### Adding New Panels

1. **Edit Mode**: Click **Edit** (pencil icon) in top-right
2. **Add Panel**: Click **Add panel** button
3. **Select Visualization**: Choose chart type
4. **Configure Query**:
   - Data source: Prometheus
   - Query: PromQL expression
   - Legend: Label template
5. **Configure Panel Options**:
   - Title, description
   - Colors, thresholds
   - Legend, tooltip
6. **Apply**: Save panel changes
7. **Save Dashboard**: Save entire dashboard

### Modifying Existing Panels

1. Click panel title → **Edit**
2. Modify query, visualization, or options
3. **Apply** changes
4. **Save dashboard**

### Creating Custom Sections

To add a new collapsible section:

```json
{
  "collapsed": true,
  "gridPos": {"h": 1, "w": 24, "x": 0, "y": 0},
  "id": 5,
  "panels": [],
  "title": "📈 Custom Section Title",
  "type": "row"
}
```

## Best Practices

### Dashboard Design

1. **Information Hierarchy**: Most critical metrics at top
2. **Visual Consistency**: Use consistent colors across similar metrics
3. **Appropriate Visualizations**: 
   - Time series for trends
   - Gauges for current values
   - Pie/donut for distributions
   - Heatmaps for pattern detection
4. **Avoid Clutter**: Maximum 12-15 panels per section
5. **Meaningful Names**: Clear, descriptive panel titles

### Query Optimization

1. **Time Windows**: Use appropriate ranges
   - Short windows (1m, 5m) for real-time
   - Longer windows (1h, 24h) for trends
2. **Aggregation**: Aggregate before filtering when possible
3. **Rate vs Increase**: Use `rate()` for per-second rates, `increase()` for totals
4. **Avoid High Cardinality**: Don't group by unbounded labels

### Performance Considerations

1. **Refresh Interval**: 
   - Real-time: 10-30s
   - Historical: 1-5m
2. **Time Range**: Shorter ranges load faster
3. **Query Complexity**: Simplify complex queries
4. **Panel Count**: Limit to 20-30 panels total

## Troubleshooting

### Common Issues

#### "No Data" in Panels

**Causes:**
- Prometheus not scraping metrics
- Wrong data source selected
- Time range doesn't include data
- PromQL query error

**Solutions:**
```powershell
# 1. Verify metrics exist
curl http://localhost:8000/metrics | grep rag_

# 2. Check Prometheus targets
# Navigate to: http://localhost:9090/targets

# 3. Test query in Prometheus
# Navigate to: http://localhost:9090/graph
# Enter query and execute

# 4. Check time range in Grafana
```

#### Incorrect Values

**Cause:** Wrong PromQL query

**Debug:**
1. Use Grafana's **Query Inspector** (panel menu → Inspect → Query)
2. Copy query to Prometheus UI for testing
3. Verify units and calculations
4. Check label filtering

#### Slow Dashboard Loading

**Solutions:**
- Increase refresh interval
- Reduce time range
- Simplify complex queries
- Use recording rules in Prometheus

### Query Testing

Test queries before adding to dashboard:

```powershell
# Test via Prometheus API
curl 'http://localhost:9090/api/v1/query?query=rag_queries_total'

# Test with time range
curl 'http://localhost:9090/api/v1/query_range?query=rate(rag_queries_total[5m])&start=2024-01-01T00:00:00Z&end=2024-01-01T23:59:59Z&step=15s'
```

## Report Integration

### Screenshot Recommendations

For including in reports:

1. **Dashboard Overview**: Full dashboard view at 1920x1080
2. **Individual Sections**: Each section expanded
3. **Critical Metrics**: Close-up of key panels
4. **Time Ranges**: Use relevant periods (last 24h, last 7d)
5. **Annotations**: Add descriptions in image captions

### Export Options

#### PDF Export
1. Install Grafana Image Renderer
2. Dashboard menu → **Share** → **Export as PDF**

#### PNG Export
1. Panel menu → **Share** → **Export as PNG**
2. Configure dimensions
3. Download

### Data Export

#### CSV Export
1. Panel menu → **Inspect** → **Data**
2. Click **Download CSV**

#### JSON Export
```powershell
# Export panel data via API
curl -G 'http://localhost:9090/api/v1/query' `
  --data-urlencode 'query=rag_queries_total' `
  | jq . > metrics_data.json
```

## Maintenance

### Regular Tasks

```powershell
# Backup dashboard weekly
$date = Get-Date -Format "yyyyMMdd"
curl http://admin:admin@localhost:3000/api/dashboards/uid/rag-pipeline `
  > "backups/rag-dashboard-$date.json"

# Update dashboard from file
curl -X POST http://admin:admin@localhost:3000/api/dashboards/db `
  -H "Content-Type: application/json" `
  -d "@rag-pipeline-dashboard.json"
```

### Version Control

Store dashboard JSON files in version control:

```
grafana-dashboards/
├── rag-pipeline-dashboard.json
├── README.md
└── backups/
    ├── 20250123-dashboard.json
    └── 20250120-dashboard.json
```

## Conclusion

The Grafana dashboard system provides comprehensive visibility into the RAG pipeline's security, performance, and quality metrics. Through organized sections, carefully designed visualizations, and optimized PromQL queries, it enables effective monitoring, troubleshooting, and reporting. The modular structure allows for easy customization and extension based on evolving monitoring requirements.

## References

- **Dashboard Files**: `grafana-dashboards/rag-pipeline-dashboard.json`
- **Configuration**: `grafana-dashboards/README.md`, `TESTING-GUIDE.md`
- **Source Documentation**: `grafana-dashboards/README.md`
- **Related Docs**: Health & Security Metrics, PII Redaction Implementation
- **External Resources**:
  - [Grafana Documentation](https://grafana.com/docs/)
  - [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
  - [Dashboard Best Practices](https://grafana.com/docs/grafana/latest/dashboards/dashboard-best-practices/)
  - [Prometheus Functions](https://prometheus.io/docs/prometheus/latest/querying/functions/)
