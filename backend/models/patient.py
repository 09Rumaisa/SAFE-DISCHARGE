"""
Pydantic models for Patient Records.
Structured to maintain clinical integrity and detailed patient state.
"""

from typing import List, Optional, Any
from datetime import datetime
from pydantic import BaseModel, Field, validator
from enum import Enum


class Gender(str, Enum):
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"
    UNKNOWN = "Unknown"


class Demographics(BaseModel):
    patient_id: str = Field(..., description="Unique medical record number (MRN)")
    first_name: str
    last_name: str
    date_of_birth: str = Field(..., description="ISO 8601 format: YYYY-MM-DD")
    gender: Gender
    weight_kg: Optional[float] = None
    height_cm: Optional[float] = None


class Medication(BaseModel):
    name: str = Field(..., description="Generic or Brand name")
    dosage: str = Field(..., description="e.g., 5mg")
    frequency: str = Field(..., description="e.g., Once daily")
    route: str = Field(default="Oral", description="e.g., Oral, IV")
    start_date: Optional[str] = None
    indication: Optional[str] = Field(None, description="Why is the patient taking this?")


class LabResult(BaseModel):
    test_name: str = Field(..., description="e.g., Creatinine, Hemoglobin")
    value: float
    unit: str
    reference_range: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    status: str = Field(default="Final", description="Final, Preliminary, etc.")

    @validator('timestamp', pre=True)
    def parse_timestamp(cls, v):
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


class ClinicalNote(BaseModel):
    note_id: str
    author_role: str = Field(..., description="e.g., Physician, Nurse")
    timestamp: datetime = Field(default_factory=datetime.now)
    content: str = Field(..., description="The full-text clinical note")
    note_type: str = Field(default="Progress Note", description="Admission, Progress, Discharge, etc.")


class VitalSigns(BaseModel):
    heart_rate: Optional[int] = Field(None, description="bpm")
    sys_bp: Optional[int] = Field(None, description="mmHg")
    dia_bp: Optional[int] = Field(None, description="mmHg")
    temperature_c: Optional[float] = Field(None, description="Celsius")
    resp_rate: Optional[int] = Field(None, description="breaths per minute")
    sp_o2: Optional[int] = Field(None, description="percentage")
    timestamp: datetime = Field(default_factory=datetime.now)


class PatientRecord(BaseModel):
    """The root model for a comprehensive patient clinical snapshot."""
    demographics: Demographics
    medications: List[Medication] = []
    lab_results: List[LabResult] = []
    clinical_notes: List[ClinicalNote] = []
    vital_signs: Optional[VitalSigns] = None
    allergies: List[str] = []
    active_problems: List[str] = []

    class Config:
        json_schema_extra = {
            "example": {
                "demographics": {
                    "patient_id": "MRN-123456",
                    "first_name": "John",
                    "last_name": "Doe",
                    "date_of_birth": "1975-05-15",
                    "gender": "Male",
                    "weight_kg": 82.5,
                    "height_cm": 178.0
                },
                "medications": [
                    {
                        "name": "Warfarin",
                        "dosage": "5mg",
                        "frequency": "Once daily",
                        "route": "Oral",
                        "start_date": "2024-01-15",
                        "indication": "Atrial Fibrillation"
                    },
                    {
                        "name": "Metoprolol",
                        "dosage": "50mg",
                        "frequency": "Twice daily",
                        "route": "Oral",
                        "start_date": "2024-01-15",
                        "indication": "Hypertension"
                    }
                ],
                "lab_results": [
                    {
                        "test_name": "INR",
                        "value": 3.8,
                        "unit": "ratio",
                        "reference_range": "2.0-3.0",
                        "timestamp": "2026-01-06T10:00:00",
                        "status": "Final"
                    },
                    {
                        "test_name": "Creatinine",
                        "value": 1.1,
                        "unit": "mg/dL",
                        "reference_range": "0.7-1.3",
                        "timestamp": "2026-01-06T10:00:00",
                        "status": "Final"
                    },
                    {
                        "test_name": "Hemoglobin",
                        "value": 13.5,
                        "unit": "g/dL",
                        "reference_range": "13.5-17.5",
                        "timestamp": "2026-01-06T10:00:00",
                        "status": "Final"
                    }
                ],
                "clinical_notes": [
                    {
                        "note_id": "N1",
                        "author_role": "ED Physician",
                        "timestamp": "2026-01-06T09:00:00",
                        "content": "Patient presents with mild shortness of breath and calf pain. Currently on anticoagulant therapy. History of atrial fibrillation. Denies chest pain. Vital signs stable.",
                        "note_type": "Progress Note"
                    }
                ],
                "vital_signs": {
                    "heart_rate": 85,
                    "sys_bp": 130,
                    "dia_bp": 80,
                    "temperature_c": 37.2,
                    "resp_rate": 16,
                    "sp_o2": 96,
                    "timestamp": "2026-01-06T09:30:00"
                },
                "allergies": ["Penicillin", "Sulfa drugs"],
                "active_problems": ["Atrial Fibrillation", "Hypertension", "Chronic Kidney Disease Stage 2"]
            }
        }
