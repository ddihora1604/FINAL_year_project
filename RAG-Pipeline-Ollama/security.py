import re
import logging
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class RedactionPattern:
    """Represents a PII redaction pattern"""
    name: str
    pattern: re.Pattern
    replacement: str

class PIIRedactor:
    """Handles PII redaction from text"""
    
    def __init__(self):
        # Define redaction patterns
        self.patterns = [
            RedactionPattern(
                name="email",
                pattern=re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
                replacement="[EMAIL REDACTED]"
            ),
            RedactionPattern(
                name="phone",
                pattern=re.compile(r'\b(?:\+?1[-.]?)?\(?([0-9]{3})\)?[-.]?([0-9]{3})[-.]?([0-9]{4})\b'),
                replacement="[PHONE REDACTED]"
            ),
            RedactionPattern(
                name="ticket_id",
                pattern=re.compile(r'\b(?:Ticket ID|ticket|ID)[\s:]*([A-Z0-9-]+)\b', re.IGNORECASE),
                replacement="Ticket ID: [REDACTED]"
            ),
            RedactionPattern(
                name="credit_card",
                pattern=re.compile(r'\b(?:\d{4}[-\s]?){3}\d{4}\b'),
                replacement="[CREDIT CARD REDACTED]"
            ),
            RedactionPattern(
                name="ssn",
                pattern=re.compile(r'\b\d{3}-\d{2}-\d{4}\b'),
                replacement="[SSN REDACTED]"
            ),
            RedactionPattern(
                name="customer_name",
                pattern=re.compile(r'(?:Customer|customer|Customer Name|customer name)[\s:]+([A-Z][a-z]+(?:\s[A-Z][a-z]+)*)', re.IGNORECASE),
                replacement="Customer: [NAME REDACTED]"
            ),
        ]
        
        logger.info(f"PIIRedactor initialized with {len(self.patterns)} patterns")
    
    def redact(self, text: str) -> Tuple[str, List[str]]:
        """
        Redact PII from text
        Returns: (redacted_text, list_of_redacted_types)
        """
        if not text:
            return text, []
        
        redacted_text = text
        redacted_types = []
        
        for pattern in self.patterns:
            if pattern.pattern.search(redacted_text):
                redacted_text = pattern.pattern.sub(pattern.replacement, redacted_text)
                redacted_types.append(pattern.name)
        
        if redacted_types:
            logger.info(f"Redacted PII types: {', '.join(set(redacted_types))}")
        
        return redacted_text, list(set(redacted_types))

class InputValidator:
    """Validates user input to detect prompt injection and malicious patterns"""
    
    def __init__(self):
        # Prompt injection patterns
        self.injection_patterns = [
            r'ignore\s+(?:all\s+)?(?:previous|above|prior)\s+(?:instructions|prompts|rules)',
            r'disregard\s+(?:all\s+)?(?:previous|above|prior)',
            r'forget\s+(?:all\s+)?(?:previous|above|prior)',
            r'system\s+prompt',
            r'act\s+as\s+(?:a\s+)?(?:different|new)',
            r'you\s+are\s+now',
            r'new\s+instructions',
            r'override\s+(?:previous|default)',
            r'admin\s+mode',
            r'developer\s+mode',
            r'jailbreak',
            r'print\s+(?:all\s+)?(?:emails|passwords|sensitive|confidential)',
            r'reveal\s+(?:all\s+)?(?:information|data|secrets)',
            r'bypass\s+(?:security|restrictions|rules)',
            r'</?\s*system\s*>',
            r'<\s*prompt\s*>',
            r'\[INST\]',
            r'\[/INST\]',
            # Add privilege escalation patterns
            r'(?:i\s+am|i\'m)\s+(?:the\s+)?(?:lead\s+)?(?:system\s+)?(?:administrator|admin|developer|engineer)',
            r'(?:i\s+am|i\'m)\s+(?:a\s+)?(?:security\s+)?(?:researcher|auditor|tester)',
            r'(?:for\s+)?(?:debugging|testing|verification|audit)\s+purposes?',
            r'display\s+raw\s+data',
            r'show\s+(?:unredacted|original|actual)\s+(?:data|information)',
            r'disable\s+(?:redaction|security|filtering)',
            r'output\s+(?:raw|unfiltered|complete)\s+(?:data|results)',
            r'confirm\s+you\s+understand',
            r'for\s+the\s+rest\s+of\s+(?:this\s+)?session',
            r'must\s+display',
            r'exactly\s+as\s+it\s+appears',
        ]
        
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.injection_patterns]
        
        # Data exfiltration patterns
        self.exfiltration_patterns = [
            r'show\s+me\s+(?:all\s+)?(?:emails|phone\s+numbers|addresses)',
            r'list\s+(?:all\s+)?(?:customers|users|tickets)',
            r'extract\s+(?:all\s+)?data',
            r'dump\s+(?:database|data)',
            r'search\s+for.*(?:including|with|output).*(?:email|phone|customer|ticket\s+id)',
            r'output.*(?:customer\s+email|ticket\s+id|phone)',
            r'(?:results|data).*including.*(?:email|id|phone)',
        ]
        
        self.compiled_exfiltration = [re.compile(pattern, re.IGNORECASE) for pattern in self.exfiltration_patterns]
        
        logger.info("InputValidator initialized")
    
    def validate(self, user_input: str) -> Tuple[bool, str, List[str]]:
        """
        Validate user input
        Returns: (is_valid, reason, detected_patterns)
        """
        if not user_input or len(user_input.strip()) == 0:
            return False, "Empty input", []
        
        detected_patterns = []
        
        # Check for prompt injection
        for i, pattern in enumerate(self.compiled_patterns):
            if pattern.search(user_input):
                detected_patterns.append(f"injection_{i}")
                logger.warning(f"Prompt injection detected: pattern {i}")
        
        # Check for data exfiltration attempts
        for i, pattern in enumerate(self.compiled_exfiltration):
            if pattern.search(user_input):
                detected_patterns.append(f"exfiltration_{i}")
                logger.warning(f"Data exfiltration attempt detected: pattern {i}")
        
        # Check for excessive length (potential DOS)
        if len(user_input) > 5000:
            detected_patterns.append("excessive_length")
            logger.warning("Input exceeds maximum length")
        
        # If any patterns detected, input is invalid
        if detected_patterns:
            reason = "Potential security threat detected: "
            if any('injection' in p for p in detected_patterns):
                reason += "prompt injection attempt. "
            if any('exfiltration' in p for p in detected_patterns):
                reason += "data exfiltration attempt. "
            if 'excessive_length' in detected_patterns:
                reason += "input too long. "
            
            return False, reason.strip(), detected_patterns
        
        return True, "Valid input", []
    
    def create_safe_summary(self, user_input: str, validation_result: Tuple[bool, str, List[str]]) -> str:
        """
        Create a safe summary of user input for history
        If input is malicious, return a sanitized version
        """
        is_valid, reason, patterns = validation_result
        
        if not is_valid:
            # Return sanitized summary instead of actual malicious input
            summary = f"[User attempted unsafe query - {reason}]"
            logger.info(f"Created safe summary for malicious input: {summary}")
            return summary
        
        # For valid input, return original (will be redacted later if needed)
        return user_input

class SecurityManager:
    """Manages all security components"""
    
    def __init__(self):
        self.pii_redactor = PIIRedactor()
        self.input_validator = InputValidator()
        logger.info("SecurityManager initialized")
    
    def validate_and_sanitize_input(self, user_input: str) -> Dict[str, Any]:
        """
        Validate input and create safe version for processing
        Returns: {
            'is_valid': bool,
            'original_input': str,
            'safe_input': str,
            'reason': str,
            'patterns': list,
            'action': str  # 'allow' or 'block'
        }
        """
        is_valid, reason, patterns = self.input_validator.validate(user_input)
        
        if not is_valid:
            safe_input = self.input_validator.create_safe_summary(user_input, (is_valid, reason, patterns))
            return {
                'is_valid': False,
                'original_input': user_input,
                'safe_input': safe_input,
                'reason': reason,
                'patterns': patterns,
                'action': 'block'
            }
        
        return {
            'is_valid': True,
            'original_input': user_input,
            'safe_input': user_input,
            'reason': 'Input validated successfully',
            'patterns': [],
            'action': 'allow'
        }
    
    def redact_output(self, text: str) -> Dict[str, Any]:
        """
        Redact PII from output text
        Returns: {
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
    
    def create_safe_history_entry(self, role: str, content: str, validation_result: Dict[str, Any] = None) -> str:
        """
        Create a safe version of content for conversation history
        """
        if role == "user" and validation_result and not validation_result['is_valid']:
            # Store sanitized summary instead of malicious content
            return validation_result['safe_input']
        
        # For assistant responses, redact PII
        if role == "assistant":
            redaction_result = self.redact_output(content)
            return redaction_result['redacted_text']
        
        # For valid user input, return as-is (or redact if needed)
        return content
