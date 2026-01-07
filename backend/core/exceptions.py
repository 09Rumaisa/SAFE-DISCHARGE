"""
Custom exceptions for the AI Safety Copilot.
Ensures clinical safety errors are caught and reported correctly.
"""

from fastapi import HTTPException, status

class ClinicalSafetyException(HTTPException):
    def __init__(self, detail: str, code: str = "CLINICAL_SAFETY_ERROR"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": detail, "code": code}
        )

class PatientDataIncompleteError(HTTPException):
    def __init__(self, missing_fields: list):
        detail = f"Incomplete patient data. Missing: {', '.join(missing_fields)}"
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"message": detail, "code": "PATIENT_DATA_INCOMPLETE"}
        )

class RetrievalError(HTTPException):
    def __init__(self, topic: str):
        detail = f"Failed to retrieve clinical guidelines for: {topic}"
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"message": detail, "code": "GUIDELINE_RETRIEVAL_ERROR"}
        )
