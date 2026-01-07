"""
Security utilities for clinical data.
Provides de-identification (PII scrubbing) to protect patient privacy.
"""

import re
from typing import Dict, Any

def scrub_pii(text: str) -> str:
    """
    Simpler regex-based PII scrubber.
    In production, this would use Presidio or a dedicated de-identification service.
    """
    if not text:
        return text
        
    # Scrub MRNs/IDs (e.g., MRN-123456)
    text = re.sub(r'[A-Z]{2,3}-\d{4,10}', '[REDACTED_ID]', text)
    
    # Scrub potential names (simplified approach for mock)
    # This is a placeholder for more robust NER
    # For this phase, we explicitly redact 'first_name' and 'last_name' values in the orchestrator
    return text

def deidentify_patient_data(patient_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Creates a copy of the patient data with PII removed for LLM processing.
    """
    scrubbed = patient_dict.copy()
    
    if "demographics" in scrubbed:
        demo = scrubbed["demographics"].copy()
        demo["first_name"] = "[FIRST_NAME]"
        demo["last_name"] = "[LAST_NAME]"
        demo["patient_id"] = "[REDACTED_ID]"
        scrubbed["demographics"] = demo
        
    return scrubbed
