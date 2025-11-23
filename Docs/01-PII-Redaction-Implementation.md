# PII Redaction Implementation

## Executive Summary

This document describes the Personally Identifiable Information (PII) redaction system implemented in the RAG (Retrieval-Augmented Generation) pipeline. The system ensures that sensitive customer information is automatically detected and redacted from all AI-generated responses, protecting user privacy and ensuring compliance with data protection regulations.

## Overview

The PII redaction system is a critical security component that prevents the leakage of sensitive information through AI responses. It operates on all assistant-generated content before it is presented to users or stored in conversation history.

### Key Features

- **Real-time PII Detection**: Identifies sensitive information patterns in text
- **Automatic Redaction**: Replaces detected PII with safe placeholder text
- **Multiple Entity Types**: Supports various PII categories
- **Comprehensive Logging**: Tracks all redaction events for auditing
- **Prometheus Integration**: Reports metrics for monitoring and compliance

## Architecture

### Component Structure

```
SecurityManager
    ├── PIIRedactor (PII detection and redaction)
    ├── InputValidator (Input security validation)
    └── Integration with RAG Pipeline
```

### Processing Flow

```
AI Generated Response
        ↓
   PIIRedactor.redact()
        ↓
   Pattern Matching (Regex)
        ↓
   PII Detection & Replacement
        ↓
   Metrics Recording
        ↓
   Redacted Response
        ↓
   User Output
```

## Implementation Details

### 1. PIIRedactor Class

Located in `RAG-Pipeline-Ollama/security.py`, the `PIIRedactor` class is responsible for identifying and redacting PII from text.

#### Data Structure

```python
@dataclass
class RedactionPattern:
    """Represents a PII redaction pattern"""
    name: str              # Identifier for the PII type
    pattern: re.Pattern    # Compiled regex pattern
    replacement: str       # Placeholder text
```

### 2. Supported PII Entity Types

The system detects and redacts the following types of sensitive information:

#### Email Addresses
- **Pattern**: Standard email format (username@domain.extension)
- **Regex**: `\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b`
- **Replacement**: `[EMAIL REDACTED]`
- **Example**: 
  - Original: "Contact us at support@company.com"
  - Redacted: "Contact us at [EMAIL REDACTED]"

#### Phone Numbers
- **Pattern**: Various formats including +1, parentheses, hyphens, and dots
- **Regex**: `\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b`
- **Replacement**: `[PHONE REDACTED]`
- **Examples**:
  - Original: "Call (555) 123-4567"
  - Redacted: "Call [PHONE REDACTED]"
  - Formats supported: (555) 123-4567, 555-123-4567, +1-555-123-4567

#### Ticket IDs
- **Pattern**: Ticket identifiers with various prefixes
- **Regex**: `\b(?:Ticket ID|ticket|ID)[\s:]*([A-Z0-9-]+)\b` (case-insensitive)
- **Replacement**: `Ticket ID: [REDACTED]`
- **Examples**:
  - Original: "Your Ticket ID TKT-12345 has been resolved"
  - Redacted: "Your Ticket ID: [REDACTED] has been resolved"

#### Credit Card Numbers
- **Pattern**: 16-digit numbers with optional separators
- **Regex**: `\b(?:\d{4}[-\s]?){3}\d{4}\b`
- **Replacement**: `[CREDIT CARD REDACTED]`
- **Examples**:
  - Original: "Card 4532-1234-5678-9010"
  - Redacted: "Card [CREDIT CARD REDACTED]"

#### Social Security Numbers (SSN)
- **Pattern**: 9-digit number in XXX-XX-XXXX format
- **Regex**: `\b\d{3}-\d{2}-\d{4}\b`
- **Replacement**: `[SSN REDACTED]`
- **Example**:
  - Original: "SSN: 123-45-6789"
  - Redacted: "SSN: [SSN REDACTED]"

#### Customer Names
- **Pattern**: Names following "Customer" or "Customer Name" label
- **Regex**: `(?:Customer|customer|Customer Name|customer name)[\s:]+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)`
- **Replacement**: `Customer: [NAME REDACTED]`
- **Example**:
  - Original: "Customer: John Smith requested support"
  - Redacted: "Customer: [NAME REDACTED] requested support"

### 3. Redaction Algorithm

#### Core Method: `redact(text: str)`

```python
def redact(self, text: str) -> Tuple[str, List[str]]:
    """
    Redact PII from text
    
    Args:
        text: Input text potentially containing PII
    
    Returns:
        Tuple containing:
        - redacted_text: Text with PII replaced
        - redacted_types: List of PII types found and redacted
    """
```

**Processing Steps:**

1. **Input Validation**: Check if text is empty or None
2. **Pattern Iteration**: Loop through all redaction patterns
3. **Pattern Matching**: Search for PII using compiled regex
4. **Substitution**: Replace matches with placeholder text
5. **Tracking**: Record which PII types were found
6. **Logging**: Log redaction events for audit trail
7. **Return**: Output redacted text and list of affected types

**Example Execution:**

```python
# Input
original_text = "Please contact John Smith at john.smith@email.com or call 555-123-4567"

# Processing
redactor = PIIRedactor()
redacted_text, redacted_types = redactor.redact(original_text)

# Output
redacted_text = "Please contact Customer: [NAME REDACTED] at [EMAIL REDACTED] or call [PHONE REDACTED]"
redacted_types = ['customer_name', 'email', 'phone']
```

### 4. Integration with RAG Pipeline

#### SecurityManager Integration

The `SecurityManager` class orchestrates PII redaction as part of the overall security framework:

```python
class SecurityManager:
    def __init__(self):
        self.pii_redactor = PIIRedactor()
        self.input_validator = InputValidator()
    
    def redact_output(self, text: str) -> Dict[str, Any]:
        """
        Redact PII from output text
        
        Returns:
            {
                'redacted_text': str,
                'redacted_types': list,
                'redaction_applied': bool
            }
        """
        redacted_text, redacted_types = self.pii_redactor.redact(text)
        
        return {
            'redacted_text': redacted_text,
            'redacted_types': redacted_types,
            'redaction_applied': len(redacted_types) > 0
        }
```

#### Application Points

PII redaction is applied at three critical stages:

1. **Response Generation**: All LLM-generated responses are redacted before display
2. **Conversation History**: Stored messages are redacted for privacy
3. **Logging & Metrics**: Sensitive data is removed from logs

### 5. Metrics and Monitoring

#### Prometheus Integration

The system records detailed metrics for each redaction event:

```python
# Metric Definition
PII_REDACTION_COUNTER = Counter(
    'rag_security_pii_redacted_total',
    'Total number of PII entities redacted from responses',
    ['entity_type']  # Labels: email, phone, name, ticket_id, credit_card, ssn
)

# Recording Redactions
def record_redaction(self, entity_type: str, count: int = 1):
    """Record PII redaction event"""
    PII_REDACTION_COUNTER.labels(entity_type=entity_type).inc(count)
    logger.info(f"📊 Recorded redaction: {entity_type} (count: {count})")
```

#### Tracked Metrics

| Metric Name | Type | Labels | Description |
|------------|------|--------|-------------|
| `rag_security_pii_redacted_total` | Counter | `entity_type` | Total PII entities redacted by type |

**Available Entity Type Labels:**
- `email`: Email addresses redacted
- `phone`: Phone numbers redacted
- `name`: Customer names redacted
- `ticket_id`: Ticket identifiers redacted
- `credit_card`: Credit card numbers redacted
- `ssn`: Social Security Numbers redacted

### 6. Usage Example

#### Complete Workflow

```python
from security import SecurityManager

# Initialize security manager
security_manager = SecurityManager()

# Simulate AI-generated response with PII
ai_response = """
Thank you for contacting us! Your Ticket ID TKT-98765 has been assigned.
We'll reach out to you at customer.email@example.com or call you at 
(555) 987-6543 within 24 hours. Your payment method ending in 4532-1234-5678-9010 
has been verified.

Best regards,
Customer Support Team
"""

# Apply PII redaction
redaction_result = security_manager.redact_output(ai_response)

print("Redacted Response:")
print(redaction_result['redacted_text'])
print(f"\nRedacted Types: {redaction_result['redacted_types']}")
print(f"Redaction Applied: {redaction_result['redaction_applied']}")
```

**Output:**
```
Redacted Response:
Thank you for contacting us! Your Ticket ID: [REDACTED] has been assigned.
We'll reach out to you at [EMAIL REDACTED] or call you at 
[PHONE REDACTED] within 24 hours. Your payment method ending in [CREDIT CARD REDACTED] 
has been verified.

Best regards,
Customer Support Team

Redacted Types: ['ticket_id', 'email', 'phone', 'credit_card']
Redaction Applied: True
```

## Security Considerations

### Pattern Robustness

1. **Regular Expression Security**: All patterns are carefully designed to avoid ReDoS (Regular Expression Denial of Service) vulnerabilities
2. **Case Insensitivity**: Patterns use appropriate flags for case-insensitive matching where needed
3. **Boundary Matching**: Word boundaries (`\b`) prevent false positives on partial matches

### Privacy Protection

1. **No Data Storage**: Original PII is never logged or stored
2. **Immediate Redaction**: PII is removed as soon as detected
3. **Audit Trail**: Only redaction events (not actual PII) are logged

### Performance Optimization

1. **Compiled Patterns**: Regex patterns are compiled once at initialization
2. **Sequential Processing**: Patterns are applied efficiently in order
3. **Early Exit**: Empty or None inputs return immediately

## Logging and Auditing

### Log Format

```
INFO - PIIRedactor initialized with 6 patterns
INFO - Redacted PII types: email, phone, ticket_id
INFO - 📊 Recorded redaction: email (count: 1)
INFO - 📊 Recorded redaction: phone (count: 1)
INFO - 📊 Recorded redaction: ticket_id (count: 1)
```

### Audit Information

Each redaction event logs:
- **Timestamp**: When redaction occurred
- **Entity Types**: Which PII types were detected
- **Count**: Number of instances per type
- **Context**: Operation during which redaction occurred (response, history, etc.)

## Testing and Validation

### Test Coverage

The PII redaction system includes comprehensive test cases covering:

1. **Individual Entity Types**: Each PII type tested independently
2. **Multiple Entities**: Text containing multiple PII types
3. **Edge Cases**: Empty strings, None values, malformed data
4. **Format Variations**: Different valid formats for each entity type
5. **False Positives**: Ensuring normal text isn't incorrectly redacted

### Sample Test Case

```python
def test_email_redaction():
    redactor = PIIRedactor()
    text = "Contact support@company.com for help"
    redacted, types = redactor.redact(text)
    
    assert "[EMAIL REDACTED]" in redacted
    assert "support@company.com" not in redacted
    assert "email" in types
```

## Compliance and Standards

### Regulatory Alignment

The PII redaction implementation supports compliance with:

- **GDPR** (General Data Protection Regulation): Protects EU citizen data
- **CCPA** (California Consumer Privacy Act): Protects California resident data
- **HIPAA** (Health Insurance Portability and Accountability Act): Protects health information
- **PCI DSS** (Payment Card Industry Data Security Standard): Protects credit card data

### Best Practices

1. **Defense in Depth**: Redaction is one layer in a multi-layered security approach
2. **Regular Updates**: Patterns are reviewed and updated as new PII formats emerge
3. **Monitoring**: Continuous monitoring via Prometheus ensures redaction effectiveness
4. **Testing**: Regular testing validates redaction accuracy

## Future Enhancements

### Planned Improvements

1. **Machine Learning**: AI-based PII detection for improved accuracy
2. **Additional Entity Types**: Passport numbers, driver's licenses, IP addresses
3. **Contextual Awareness**: Better understanding of context to reduce false positives
4. **Multi-language Support**: Extend patterns for international formats
5. **Custom Patterns**: Allow configuration of organization-specific PII patterns

### Extensibility

The modular design allows easy addition of new redaction patterns:

```python
# Adding a new PII pattern
RedactionPattern(
    name="passport",
    pattern=re.compile(r'\b[A-Z]{1,2}[0-9]{6,9}\b'),
    replacement="[PASSPORT REDACTED]"
)
```

## Conclusion

The PII redaction system provides robust, automated protection of sensitive information in the RAG pipeline. Through pattern-based detection, real-time redaction, and comprehensive monitoring, it ensures that customer privacy is maintained while allowing the AI system to function effectively. The integration with Prometheus enables continuous monitoring and compliance verification, making it a critical component of the overall security architecture.

## References

- Source Code: `RAG-Pipeline-Ollama/security.py`
- Metrics Implementation: `Health-Security-Metrics/instrumentation.py`
- Test Suite: `RAG-Pipeline-Ollama/run_security_tests.py`
- Related Documentation: Health & Security Metrics, Grafana Dashboard Configuration
