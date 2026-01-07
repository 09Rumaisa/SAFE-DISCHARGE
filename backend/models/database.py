"""
Database models using Tortoise ORM.
Stores clinician and patient information.
"""

from tortoise import fields
from tortoise.models import Model
from datetime import datetime
from typing import Optional


class Clinician(Model):
    """Clinician/Healthcare Provider model."""
    
    id = fields.IntField(pk=True)
    clinician_id = fields.CharField(max_length=50, unique=True, index=True)
    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100)
    email = fields.CharField(max_length=255, unique=True)
    role = fields.CharField(max_length=100)  # e.g., "Physician", "Nurse", "Pharmacist"
    department = fields.CharField(max_length=100, null=True)
    license_number = fields.CharField(max_length=100, null=True)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "clinicians"
    
    def __str__(self):
        return f"Dr. {self.first_name} {self.last_name} ({self.role})"


class Patient(Model):
    """Patient model for storing patient records."""
    
    id = fields.IntField(pk=True)
    patient_id = fields.CharField(max_length=50, unique=True, index=True)  # MRN
    first_name = fields.CharField(max_length=100)
    last_name = fields.CharField(max_length=100)
    date_of_birth = fields.DateField()
    gender = fields.CharField(max_length=20)  # Male, Female, Other, Unknown
    email = fields.CharField(max_length=255, null=True)
    phone = fields.CharField(max_length=20, null=True)
    address = fields.TextField(null=True)
    
    # Medical information
    weight_kg = fields.FloatField(null=True)
    height_cm = fields.FloatField(null=True)
    blood_type = fields.CharField(max_length=5, null=True)
    allergies = fields.JSONField(default=list)  # List of allergies
    
    # System fields
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "patients"
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} (MRN: {self.patient_id})"


class ClinicalEncounter(Model):
    """Records of clinical encounters/visits."""
    
    id = fields.IntField(pk=True)
    encounter_id = fields.CharField(max_length=50, unique=True, index=True)
    
    # Foreign keys
    patient = fields.ForeignKeyField("models.Patient", related_name="encounters")
    clinician = fields.ForeignKeyField("models.Clinician", related_name="encounters")
    
    # Encounter details
    encounter_type = fields.CharField(max_length=50)  # "Emergency", "Outpatient", "Inpatient"
    admission_date = fields.DatetimeField()
    discharge_date = fields.DatetimeField(null=True)
    chief_complaint = fields.TextField(null=True)
    diagnosis = fields.JSONField(default=list)  # List of diagnoses
    
    # AI Analysis results
    ai_analysis_performed = fields.BooleanField(default=False)
    ai_analysis_result = fields.JSONField(null=True)  # Stores AnalysisResponse
    comprehension_score = fields.IntField(null=True)  # 0-100
    
    # Status
    status = fields.CharField(max_length=20, default="active")  # active, discharged, transferred
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    
    class Meta:
        table = "clinical_encounters"
    
    def __str__(self):
        return f"Encounter {self.encounter_id} - {self.patient.first_name} {self.patient.last_name}"


class Medication(Model):
    """Medication records for patients."""
    
    id = fields.IntField(pk=True)
    encounter = fields.ForeignKeyField("models.ClinicalEncounter", related_name="medications")
    
    name = fields.CharField(max_length=200)
    dosage = fields.CharField(max_length=100)
    frequency = fields.CharField(max_length=100)
    route = fields.CharField(max_length=50, default="Oral")
    start_date = fields.DateField()
    end_date = fields.DateField(null=True)
    indication = fields.TextField(null=True)
    prescribing_clinician = fields.ForeignKeyField("models.Clinician", related_name="prescribed_medications", null=True)
    
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "medications"
    
    def __str__(self):
        return f"{self.name} {self.dosage} - {self.frequency}"


class LabResult(Model):
    """Laboratory test results."""
    
    id = fields.IntField(pk=True)
    encounter = fields.ForeignKeyField("models.ClinicalEncounter", related_name="lab_results")
    
    test_name = fields.CharField(max_length=200)
    value = fields.FloatField()
    unit = fields.CharField(max_length=50)
    reference_range = fields.CharField(max_length=100, null=True)
    status = fields.CharField(max_length=20, default="Final")  # Preliminary, Final, Corrected
    abnormal_flag = fields.BooleanField(default=False)
    
    test_date = fields.DatetimeField()
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "lab_results"
    
    def __str__(self):
        return f"{self.test_name}: {self.value} {self.unit}"


class ClinicalFeedbackRecord(Model):
    """Stores clinician feedback for the learning loop."""
    
    id = fields.IntField(pk=True)
    feedback_id = fields.CharField(max_length=50, unique=True, index=True)
    
    # Foreign keys
    encounter = fields.ForeignKeyField("models.ClinicalEncounter", related_name="feedback")
    clinician = fields.ForeignKeyField("models.Clinician", related_name="feedback_given")
    
    # Feedback details
    alert_id = fields.CharField(max_length=100)  # ID of the AI flag/suggestion
    alert_type = fields.CharField(max_length=50)  # "safety_flag", "equity_flag", "comprehension"
    action = fields.CharField(max_length=20)  # "accepted", "rejected", "modified"
    clinician_note = fields.TextField(null=True)
    patient_outcome = fields.TextField(null=True)
    
    # Metadata
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "clinical_feedback"
    
    def __str__(self):
        return f"Feedback {self.feedback_id} - {self.action}"


class DischargeRecord(Model):
    """Discharge documentation records."""
    
    id = fields.IntField(pk=True)
    encounter = fields.OneToOneField("models.ClinicalEncounter", related_name="discharge_record")
    
    # Discharge instructions
    clinician_facing_instructions = fields.TextField()
    patient_facing_instructions = fields.TextField()
    simplified_instructions = fields.TextField(null=True)
    
    # Comprehension analysis
    original_comprehension_score = fields.IntField(null=True)
    simplified_comprehension_score = fields.IntField(null=True)
    jargon_detected = fields.JSONField(default=list)
    
    # Follow-up
    follow_up_required = fields.TextField(null=True)
    follow_up_date = fields.DateField(null=True)
    safety_netting = fields.TextField(null=True)
    
    # Metadata
    discharge_date = fields.DatetimeField()
    created_by = fields.ForeignKeyField("models.Clinician", related_name="discharges_created")
    created_at = fields.DatetimeField(auto_now_add=True)
    
    class Meta:
        table = "discharge_records"
    
    def __str__(self):
        return f"Discharge for {self.encounter.patient.first_name} {self.encounter.patient.last_name}"
