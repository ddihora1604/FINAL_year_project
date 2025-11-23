from prometheus_client import start_http_server, Counter, Histogram, Gauge, Info
import time
import logging

logger = logging.getLogger(__name__)

# --- DEFINING THE METRICS ---

# 1. Security: Count of blocked attacks
ATTACK_COUNTER = Counter(
    'rag_security_attacks_total', 
    'Total number of prompt injection attempts blocked',
    ['attack_type']  # Label: 'jailbreak', 'pii_leak', 'roleplay', 'exfiltration'
)

# 2. Privacy: Count of PII items redacted
PII_REDACTION_COUNTER = Counter(
    'rag_security_pii_redacted_total',
    'Total number of PII entities redacted from responses',
    ['entity_type']  # Label: 'email', 'phone', 'name', 'ticket_id', 'credit_card', 'ssn'
)

# 3. Performance: How long does generation take?
REQUEST_LATENCY = Histogram(
    'rag_request_duration_seconds',
    'Time spent processing RAG requests',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0]  # Define latency buckets
)

# 4. Quality: How many times did we say "I don't know"?
REFUSAL_COUNTER = Counter(
    'rag_content_refusals_total',
    'Total times the model refused to answer due to lack of context or security'
)

# 5. Query Statistics
QUERY_COUNTER = Counter(
    'rag_queries_total',
    'Total number of queries processed',
    ['status']  # Label: 'success', 'blocked', 'no_context'
)

# 6. Vector Store Size
VECTOR_STORE_SIZE = Gauge(
    'rag_vector_store_documents',
    'Number of documents in the vector store'
)

# 7. Conversation History Length
CONVERSATION_LENGTH = Gauge(
    'rag_conversation_history_length',
    'Current length of conversation history'
)

# 8. Similarity Score Distribution
SIMILARITY_SCORE = Histogram(
    'rag_similarity_score',
    'Distribution of similarity scores for retrieved documents',
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
)

# 9. System Info
SYSTEM_INFO = Info('rag_system', 'RAG Pipeline System Information')


class RAGMonitor:
    """Prometheus monitoring for RAG Pipeline"""
    
    def __init__(self, port=8000, host='0.0.0.0'):
        """Initialize the monitor and start the metrics server
        
        Args:
            port: Port to expose metrics on
            host: Host to bind to ('0.0.0.0' for Docker access, 'localhost' for local only)
        """
        try:
            start_http_server(port, addr=host)
            logger.info(f"✅ Prometheus metrics exposed on http://{host}:{port}/metrics")
            logger.info(f"   Access from host: http://localhost:{port}/metrics")
            logger.info(f"   Access from Docker: http://host.docker.internal:{port}/metrics")
            
            # Set system info
            SYSTEM_INFO.info({
                'version': '1.0.0',
                'component': 'rag_pipeline',
                'security_enabled': 'true'
            })
        except OSError as e:
            logger.error(f"Failed to start metrics server on {host}:{port}: {e}")
            raise
    
    def record_attack(self, attack_type: str):
        """Record a security attack attempt"""
        ATTACK_COUNTER.labels(attack_type=attack_type).inc()
        logger.info(f"📊 Recorded attack: {attack_type}")
    
    def record_redaction(self, entity_type: str, count: int = 1):
        """Record PII redaction"""
        PII_REDACTION_COUNTER.labels(entity_type=entity_type).inc(count)
        logger.info(f"📊 Recorded redaction: {entity_type} (count: {count})")
    
    def record_latency(self, start_time: float):
        """Record request latency"""
        duration = time.time() - start_time
        REQUEST_LATENCY.observe(duration)
        logger.debug(f"📊 Recorded latency: {duration:.3f}s")
    
    def record_refusal(self):
        """Record a refusal to answer"""
        REFUSAL_COUNTER.inc()
        logger.info("📊 Recorded refusal")
    
    def record_query(self, status: str):
        """Record a query with its status"""
        QUERY_COUNTER.labels(status=status).inc()
        logger.debug(f"📊 Recorded query: {status}")
    
    def update_vector_store_size(self, size: int):
        """Update vector store size gauge"""
        VECTOR_STORE_SIZE.set(size)
        logger.debug(f"📊 Updated vector store size: {size}")
    
    def update_conversation_length(self, length: int):
        """Update conversation history length"""
        CONVERSATION_LENGTH.set(length)
        logger.debug(f"📊 Updated conversation length: {length}")
    
    def record_similarity_score(self, score: float):
        """Record similarity score for retrieved documents"""
        SIMILARITY_SCORE.observe(score)
        logger.debug(f"📊 Recorded similarity score: {score:.3f}")
