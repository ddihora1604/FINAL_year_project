# Grafana Dashboard Panels Reference

## Overview

This document provides a comprehensive reference for all panels in the RAG Pipeline Grafana Dashboard. The dashboard is organized into four sections, each focusing on a specific aspect of system monitoring.

---

## Section 1: Executive Overview 📊

High-level business and operational metrics for stakeholders and management.

### Panel 1.1: Total Queries (24h)

**What it Means**: The total number of user queries processed by the RAG system in the last 24 hours.

**Query**:
```promql
sum(increase(rag_queries_total[24h]))
```

**Use Case**: Monitor daily system usage, track user engagement, and identify traffic patterns or anomalies over a 24-hour period.

---

### Panel 1.2: Attack Attempts (24h)

**What it Means**: The total number of security attacks (prompt injections, data exfiltration attempts) that were detected and blocked in the last 24 hours.

**Query**:
```promql
sum(increase(rag_security_attacks_total[24h]))
```

**Use Case**: Security threat assessment, identifying attack trends, and evaluating the effectiveness of security measures.

---

### Panel 1.3: P95 Latency

**What it Means**: The 95th percentile of request processing time, meaning 95% of all requests complete faster than this duration. This metric captures typical performance while accounting for some outliers.

**Query**:
```promql
histogram_quantile(0.95, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))
```

**Use Case**: SLA monitoring, performance benchmarking, and ensuring the system meets response time requirements for the majority of requests.

---

### Panel 1.4: Success Rate Distribution

**What it Means**: A breakdown of query outcomes showing the proportion of successful queries, blocked queries (security threats), and queries with no context available.

**Query**:
```promql
# Success
sum(increase(rag_queries_total{status="success"}[24h]))

# Blocked
sum(increase(rag_queries_total{status="blocked"}[24h]))

# No Context
sum(increase(rag_queries_total{status="no_context"}[24h]))
```

**Use Case**: Quick health check of overall system effectiveness, identifying if too many queries are being blocked or failing due to lack of context.

---

### Panel 1.5: Query Rate Timeline

**What it Means**: The number of queries processed per minute over time, showing traffic patterns and usage trends.

**Query**:
```promql
sum(rate(rag_queries_total[5m])) * 60
```

**Use Case**: Identify peak usage hours, detect traffic spikes or drops, and support capacity planning decisions.

---

### Panel 1.6: Top 5 Attack Types

**What it Means**: The five most frequently occurring types of security attacks in the last 24 hours, ranked by frequency.

**Query**:
```promql
topk(5, sum by (attack_type) (increase(rag_security_attacks_total[24h])))
```

**Use Case**: Identify the most common attack vectors to prioritize security hardening efforts and understand evolving threat patterns.

---

## Section 2: Security Operations 🔒

Dedicated security monitoring for threat detection, attack tracking, and privacy compliance.

### Panel 2.1: Real-time Attack Rate

**What it Means**: The current rate of security attacks per minute, broken down by attack type (jailbreak, exfiltration, PII leak, roleplay).

**Query**:
```promql
sum by (attack_type) (rate(rag_security_attacks_total[1m])) * 60
```

**Use Case**: Real-time security incident detection, enabling immediate response to ongoing attack campaigns or suspicious activity patterns.

---

### Panel 2.2: Attack Type Distribution

**What it Means**: The proportional breakdown of different attack types over the last 24 hours, showing which attack methods are most prevalent.

**Query**:
```promql
sum by (attack_type) (increase(rag_security_attacks_total[24h]))
```

**Use Case**: Understand the distribution of attack methods to allocate security resources effectively and prioritize defense mechanisms.

---

### Panel 2.3: PII Redaction Activity

**What it Means**: Hourly count of PII (Personally Identifiable Information) entities that were detected and redacted from responses, categorized by entity type (email, phone, name, ticket_id, credit_card, SSN).

**Query**:
```promql
sum by (entity_type) (increase(rag_security_pii_redacted_total[1h]))
```

**Use Case**: Privacy compliance monitoring, tracking PII exposure risks, and ensuring data protection measures are functioning correctly.

---

### Panel 2.4: Security Status: Blocked vs Allowed

**What it Means**: Real-time comparison of queries that were allowed to proceed (successful), blocked due to security threats, or had no context available.

**Query**:
```promql
# Allowed Queries (Success)
sum(rate(rag_queries_total{status="success"}[5m])) * 60

# Blocked Queries
sum(rate(rag_queries_total{status="blocked"}[5m])) * 60

# No Context
sum(rate(rag_queries_total{status="no_context"}[5m])) * 60
```

**Use Case**: Monitor the balance between security and usability, detect if security measures are too restrictive (high block rate) or too lenient.

---

### Panel 2.5: PII Redaction Heatmap

**What it Means**: A time-based intensity map showing when and which types of PII are being redacted most frequently.

**Query**:
```promql
sum by (entity_type) (increase(rag_security_pii_redacted_total[5m]))
```

**Use Case**: Identify patterns in PII exposure attempts, detect potential data leakage risks, and understand when privacy measures are most active.

---

## Section 3: Performance Metrics ⚡

Detailed performance analysis for system optimization and SLA compliance.

### Panel 3.1: Latency Percentiles (P50, P95, P99)

**What it Means**: Request processing time at different percentiles - P50 (median), P95 (95% of requests), and P99 (99% of requests). These show typical performance and capture worst-case scenarios.

**Query**:
```promql
# P50 (Median)
histogram_quantile(0.50, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))

# P95
histogram_quantile(0.95, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))

# P99
histogram_quantile(0.99, sum(rate(rag_request_duration_seconds_bucket[5m])) by (le))
```

**Use Case**: SLA compliance monitoring, performance degradation detection, and understanding user experience across different service quality levels.

---

### Panel 3.2: Requests Per Second (RPS)

**What it Means**: The current throughput of the system measured in queries processed per second.

**Query**:
```promql
sum(rate(rag_queries_total[1m]))
```

**Use Case**: Real-time load monitoring, capacity planning, and detecting sudden traffic changes that might impact performance.

---

### Panel 3.3: Latency Heatmap

**What it Means**: A visualization showing the concentration of requests across different latency ranges over time, revealing performance patterns.

**Query**:
```promql
sum(increase(rag_request_duration_seconds_bucket[1m])) by (le)
```

**Use Case**: Identify performance anomalies, detect when most requests fall into slower latency buckets, and understand temporal performance patterns.

---

### Panel 3.4: Average Latency by Status

**What it Means**: The average processing time for requests, broken down by their final status (success, blocked, no_context).

**Query**:
```promql
sum by (status) (rate(rag_request_duration_seconds_sum[5m])) / 
sum by (status) (rate(rag_request_duration_seconds_count[5m]))
```

**Use Case**: Understand if security blocking or context failures add latency overhead, and optimize processing paths accordingly.

---

### Panel 3.5: Vector Store Size

**What it Means**: The current number of documents stored in the vector database (knowledge base).

**Query**:
```promql
rag_vector_store_documents
```

**Use Case**: Monitor knowledge base growth, track when new documents are added, and plan for storage capacity needs.

---

### Panel 3.6: Throughput Timeline

**What it Means**: Queries per minute over an extended time period, showing sustained throughput trends.

**Query**:
```promql
sum(rate(rag_queries_total[1m])) * 60
```

**Use Case**: Long-term capacity planning, identifying usage growth trends, and detecting sustained load changes.

---

## Section 4: Quality Metrics ✨

Monitor RAG system quality, accuracy, and effectiveness.

### Panel 4.1: Average Similarity Score

**What it Means**: The mean similarity score (0-1 scale) of documents retrieved from the vector store, where higher scores indicate better matches to user queries.

**Query**:
```promql
sum(rate(rag_similarity_score_sum[5m])) / 
sum(rate(rag_similarity_score_count[5m]))
```

**Use Case**: Monitor retrieval quality, detect if the knowledge base is becoming less relevant, and evaluate the effectiveness of the embedding model.

---

### Panel 4.2: Refusal Rate Percentage

**What it Means**: The percentage of queries where the system refused to answer due to lack of relevant context or security concerns.

**Query**:
```promql
sum(rate(rag_content_refusals_total[5m])) / 
sum(rate(rag_queries_total[5m])) * 100
```

**Use Case**: Identify knowledge gaps in the vector store, assess if the system is being too conservative, and guide content addition priorities.

---

### Panel 4.3: Query Status Breakdown

**What it Means**: Hourly distribution showing how queries are resolved - successfully answered, blocked by security, or failed due to missing context.

**Query**:
```promql
sum by (status) (increase(rag_queries_total[1h]))
```

**Use Case**: Track system effectiveness trends over time, identify shifts in query patterns, and measure overall system health.

---

### Panel 4.4: Similarity Score Distribution

**What it Means**: A histogram showing how retrieved documents are distributed across similarity score ranges (0.0 to 1.0).

**Query**:
```promql
sum(increase(rag_similarity_score_bucket[5m])) by (le)
```

**Use Case**: Understand typical retrieval quality distribution, identify if most retrievals are high-quality or marginal matches.

---

### Panel 4.5: Similarity Score Timeline

**What it Means**: The trend of average similarity scores over time, showing if retrieval quality is improving or degrading.

**Query**:
```promql
sum(rate(rag_similarity_score_sum[5m])) / 
sum(rate(rag_similarity_score_count[5m]))
```

**Use Case**: Monitor long-term quality trends, detect degradation after system changes, and validate improvements from knowledge base updates.

---

### Panel 4.6: P95 Similarity Score

**What it Means**: The 95th percentile of similarity scores, indicating that 95% of retrieved documents have a similarity score above this value.

**Query**:
```promql
histogram_quantile(0.95, sum(rate(rag_similarity_score_bucket[5m])) by (le))
```

**Use Case**: Ensure consistently high retrieval quality for the vast majority of queries, set quality benchmarks, and catch quality regressions.

---

### Panel 4.7: Vector Store Growth

**What it Means**: The trend of document count in the vector store over time, showing knowledge base expansion.

**Query**:
```promql
rag_vector_store_documents
```

**Use Case**: Track knowledge base expansion efforts, verify document additions, and plan for future storage needs.

---

### Panel 4.8: Conversation Length Trend

**What it Means**: The current size of conversation history (number of messages) being maintained for context.

**Query**:
```promql
rag_conversation_history_length
```

**Use Case**: Monitor conversation memory usage, detect memory leaks or unbounded growth, and optimize context window management.

---

## Summary

### Panel Count by Section

| Section | Number of Panels | Focus Area |
|---------|-----------------|------------|
| Executive Overview | 6 | High-level KPIs and business metrics |
| Security Operations | 5 | Threat detection and privacy compliance |
| Performance Metrics | 6 | Latency and throughput analysis |
| Quality Metrics | 8 | Retrieval quality and accuracy |
| **Total** | **25** | **Complete system monitoring** |

### Metric Types Used

- **Counters**: Track cumulative events (queries, attacks, redactions)
- **Histograms**: Measure distributions (latency, similarity scores)
- **Gauges**: Show current values (vector store size, conversation length)

### Query Patterns

- **rate()**: Calculate per-second rates for counters
- **increase()**: Calculate total increase over time windows
- **histogram_quantile()**: Extract percentiles from histogram data
- **sum by (label)**: Aggregate and group by specific labels
- **topk()**: Select top K series by value

---

## References

- **Dashboard File**: `grafana-dashboards/rag-pipeline-dashboard.json`
- **Full Documentation**: `Docs/03-Grafana-Dashboard-Configuration.md`
- **Metrics Implementation**: `Health-Security-Metrics/instrumentation.py`
- **Related Docs**: Health & Security Metrics, PII Redaction Implementation
