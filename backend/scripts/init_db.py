"""
Initialize database with sample data.
"""

import asyncio
from datetime import date, datetime
from tortoise import Tortoise
import sys
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from backend.models.database import Clinician, Patient


async def init_sample_data():
    """Initialize database with sample clinicians and patients."""
    
    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL", "sqlite://db.sqlite3")
    
    # Initialize Tortoise
    await Tortoise.init(
        db_url=database_url,
        modules={"models": ["backend.models.database"]}
    )
    await Tortoise.generate_schemas()
    
    db_type = "PostgreSQL" if "postgres" in database_url else "SQLite"
    print(f"✅ Database schema created ({db_type})")
    print(f"📍 Connected to: {database_url.split('@')[1] if '@' in database_url else 'db.sqlite3'}")
    print()
    
    # Create sample clinicians
    clinicians_data = [
        {
            "clinician_id": "DOC001",
            "first_name": "Sarah",
            "last_name": "Johnson",
            "email": "sarah.johnson@hospital.com",
            "role": "Emergency Physician",
            "department": "Emergency Department",
            "license_number": "MD123456"
        },
        {
            "clinician_id": "DOC002",
            "first_name": "Michael",
            "last_name": "Chen",
            "email": "michael.chen@hospital.com",
            "role": "Cardiologist",
            "department": "Cardiology",
            "license_number": "MD789012"
        },
        {
            "clinician_id": "NUR001",
            "first_name": "Emily",
            "last_name": "Rodriguez",
            "email": "emily.rodriguez@hospital.com",
            "role": "Registered Nurse",
            "department": "Emergency Department",
            "license_number": "RN345678"
        }
    ]
    
    for data in clinicians_data:
        clinician, created = await Clinician.get_or_create(**data)
        if created:
            print(f"✅ Created clinician: Dr. {clinician.first_name} {clinician.last_name}")
        else:
            print(f"ℹ️  Clinician already exists: Dr. {clinician.first_name} {clinician.last_name}")
    
    # Create sample patients
    patients_data = [
        {
            "patient_id": "MRN-123456",
            "first_name": "Jane",
            "last_name": "Doe",
            "date_of_birth": date(1950, 1, 15),
            "gender": "Female",
            "email": "jane.doe@email.com",
            "phone": "+1-555-0101",
            "weight_kg": 68.0,
            "height_cm": 165.0,
            "allergies": ["Penicillin"]
        },
        {
            "patient_id": "MRN-789012",
            "first_name": "John",
            "last_name": "Smith",
            "date_of_birth": date(1975, 5, 20),
            "gender": "Male",
            "email": "john.smith@email.com",
            "phone": "+1-555-0102",
            "weight_kg": 82.5,
            "height_cm": 178.0,
            "allergies": []
        },
        {
            "patient_id": "MRN-345678",
            "first_name": "Maria",
            "last_name": "Garcia",
            "date_of_birth": date(1988, 8, 10),
            "gender": "Female",
            "email": "maria.garcia@email.com",
            "phone": "+1-555-0103",
            "weight_kg": 62.0,
            "height_cm": 160.0,
            "allergies": ["Sulfa drugs", "Latex"]
        }
    ]
    
    for data in patients_data:
        # Check if patient exists
        existing_patient = await Patient.get_or_none(patient_id=data["patient_id"])
        if existing_patient:
            print(f"ℹ️  Patient already exists: {existing_patient.first_name} {existing_patient.last_name} (MRN: {existing_patient.patient_id})")
        else:
            # Create new patient
            patient = await Patient.create(**data)
            print(f"✅ Created patient: {patient.first_name} {patient.last_name} (MRN: {patient.patient_id})")
    
    print("\n" + "="*60)
    print("✅ Database initialization complete!")
    print("="*60)
    print(f"Total Clinicians: {await Clinician.all().count()}")
    print(f"Total Patients: {await Patient.all().count()}")
    print("="*60)
    
    await Tortoise.close_connections()


if __name__ == "__main__":
    asyncio.run(init_sample_data())
