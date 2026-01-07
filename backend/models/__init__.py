"""
Pydantic models for the AI Safety Copilot.
"""

from .patient import (
    PatientRecord,
    Medication,
    LabResult,
    ClinicalNote,
    Demographics,
    VitalSigns
)

from .responses import (
    SafetyFlag,
    FlagSeverity,
    AnalysisResponse,
    DischargeInstructions,
    Citation,
    ClinicalProtocol
)

__all__ = [
    # Patient models
    "PatientRecord",
    "Medication", 
    "LabResult",
    "ClinicalNote",
    "Demographics",
    "VitalSigns",
    # Response models
    "SafetyFlag",
    "FlagSeverity",
    "AnalysisResponse",
    "DischargeInstructions",
    "Citation",
    "ClinicalProtocol"
]
