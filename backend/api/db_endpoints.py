"""
API endpoints for database operations (Clinicians and Patients).
"""

from fastapi import APIRouter, HTTPException, status
from typing import List
from pydantic import BaseModel
from datetime import date, datetime
from ..models.database import Clinician, Patient, ClinicalEncounter, ClinicalFeedbackRecord

router = APIRouter(prefix="/v1/db", tags=["Database"])


# Pydantic schemas for API requests/responses
class ClinicianCreate(BaseModel):
    clinician_id: str
    first_name: str
    last_name: str
    email: str
    role: str
    department: str = None
    license_number: str = None


class ClinicianResponse(BaseModel):
    id: int
    clinician_id: str
    first_name: str
    last_name: str
    email: str
    role: str
    department: str = None
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class PatientCreate(BaseModel):
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    email: str = None
    phone: str = None
    weight_kg: float = None
    height_cm: float = None
    allergies: List[str] = []


class PatientResponse(BaseModel):
    id: int
    patient_id: str
    first_name: str
    last_name: str
    date_of_birth: date
    gender: str
    email: str = None
    phone: str = None
    weight_kg: float = None
    height_cm: float = None
    allergies: List[str] = []
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Clinician Endpoints
@router.post("/clinicians", response_model=ClinicianResponse, status_code=status.HTTP_201_CREATED)
async def create_clinician(clinician: ClinicianCreate):
    """Create a new clinician record."""
    try:
        db_clinician = await Clinician.create(**clinician.dict())
        return await ClinicianResponse.from_tortoise_orm(db_clinician)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create clinician: {str(e)}")


@router.get("/clinicians", response_model=List[ClinicianResponse])
async def list_clinicians(skip: int = 0, limit: int = 100):
    """List all clinicians."""
    clinicians = await Clinician.all().offset(skip).limit(limit)
    return [await ClinicianResponse.from_tortoise_orm(c) for c in clinicians]


@router.get("/clinicians/{clinician_id}", response_model=ClinicianResponse)
async def get_clinician(clinician_id: str):
    """Get a specific clinician by ID."""
    clinician = await Clinician.get_or_none(clinician_id=clinician_id)
    if not clinician:
        raise HTTPException(status_code=404, detail="Clinician not found")
    return await ClinicianResponse.from_tortoise_orm(clinician)


@router.delete("/clinicians/{clinician_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_clinician(clinician_id: str):
    """Delete a clinician (soft delete by setting is_active=False)."""
    clinician = await Clinician.get_or_none(clinician_id=clinician_id)
    if not clinician:
        raise HTTPException(status_code=404, detail="Clinician not found")
    clinician.is_active = False
    await clinician.save()
    return None


# Patient Endpoints
@router.post("/patients", response_model=PatientResponse, status_code=status.HTTP_201_CREATED)
async def create_patient(patient: PatientCreate):
    """Create a new patient record."""
    try:
        db_patient = await Patient.create(**patient.dict())
        return await PatientResponse.from_tortoise_orm(db_patient)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create patient: {str(e)}")


@router.get("/patients", response_model=List[PatientResponse])
async def list_patients(skip: int = 0, limit: int = 100):
    """List all patients."""
    patients = await Patient.all().offset(skip).limit(limit)
    return [await PatientResponse.from_tortoise_orm(p) for p in patients]


@router.get("/patients/{patient_id}", response_model=PatientResponse)
async def get_patient(patient_id: str):
    """Get a specific patient by MRN."""
    patient = await Patient.get_or_none(patient_id=patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return await PatientResponse.from_tortoise_orm(patient)


@router.put("/patients/{patient_id}", response_model=PatientResponse)
async def update_patient(patient_id: str, patient_update: PatientCreate):
    """Update patient information."""
    patient = await Patient.get_or_none(patient_id=patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    
    await patient.update_from_dict(patient_update.dict(exclude_unset=True))
    await patient.save()
    return await PatientResponse.from_tortoise_orm(patient)


@router.delete("/patients/{patient_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_patient(patient_id: str):
    """Delete a patient (soft delete by setting is_active=False)."""
    patient = await Patient.get_or_none(patient_id=patient_id)
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    patient.is_active = False
    await patient.save()
    return None


# Statistics Endpoint
@router.get("/stats")
async def get_database_stats():
    """Get database statistics."""
    total_clinicians = await Clinician.filter(is_active=True).count()
    total_patients = await Patient.filter(is_active=True).count()
    total_encounters = await ClinicalEncounter.all().count()
    total_feedback = await ClinicalFeedbackRecord.all().count()
    
    return {
        "total_clinicians": total_clinicians,
        "total_patients": total_patients,
        "total_encounters": total_encounters,
        "total_feedback_records": total_feedback,
        "database_type": "SQLite",
        "status": "operational"
    }
