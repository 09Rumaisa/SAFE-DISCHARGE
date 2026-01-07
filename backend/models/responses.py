"""
Pydantic models for API responses and Clinical Content.
"""

from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime


class FlagSeverity(str, Enum):
    RED = "Red"       # Critical risk, immediate action required
    YELLOW = "Yellow" # Moderate risk, review needed
    GREEN = "Green"   # General info or low risk
    PURPLE = "Purple" # Equity/bias awareness flag


class Citation(BaseModel):
    source_name: str = Field(..., description="e.g., NICE Guidelines, BNF, NHS")
    section: Optional[str] = None
    url: Optional[str] = None
    snippet: Optional[str] = Field(None, description="Relevant text excerpt from source")


class SafetyFlag(BaseModel):
    severity: FlagSeverity
    title: str
    description: str
    action_required: Optional[str] = None
    citations: List[Citation] = []


class EquityFlag(BaseModel):
    """Flags for bias awareness and health equity considerations."""
    category: str = Field(..., description="e.g., 'Gender-specific symptoms', 'Age-related dosing'")
    title: str
    description: str
    educational_note: str = Field(..., description="Why this matters for equitable care")
    citations: List[Citation] = []


class ClinicalProtocol(BaseModel):
    title: str
    summary: str
    source: str


class ComprehensionScore(BaseModel):
    """Patient comprehension analysis for discharge instructions."""
    score: int = Field(..., ge=0, le=100, description="0-100, higher is better")
    reading_level: float = Field(..., description="Flesch-Kincaid Grade Level")
    interpretation: str = Field(..., description="Easy/Moderate/Difficult")
    jargon_detected: List[str] = []
    simplified_version: str = Field(..., description="AI-simplified patient-friendly version")
    language: str = Field(default="en", description="ISO language code")
    needs_improvement: bool = Field(..., description="True if score < 70")


class RiskCategory(str, Enum):
    CRITICAL = "Critical"      # Immediate life-threatening
    HIGH = "High"              # Significant risk, urgent action
    MODERATE = "Moderate"      # Notable risk, review needed
    LOW = "Low"                # Minimal risk, monitoring sufficient


class RiskStratification(BaseModel):
    """Categorizes patient into overall risk level."""
    overall_risk: RiskCategory
    critical_count: int = Field(default=0, description="Number of critical/RED flags")
    high_count: int = Field(default=0, description="Number of high/YELLOW flags")
    moderate_count: int = Field(default=0, description="Number of moderate/GREEN flags")
    equity_count: int = Field(default=0, description="Number of equity/PURPLE flags")
    risk_score: float = Field(..., ge=0, le=100, description="Weighted risk score 0-100")
    clinical_reasoning: str = Field(..., description="Why this risk category was assigned")


class DetailedAnalysis(BaseModel):
    """Detailed breakdown of clinical findings."""
    presenting_problem: str = Field(..., description="Primary reason for visit")
    relevant_history: List[str] = Field(default=[], description="Relevant past medical history")
    current_vital_signs_assessment: str = Field(..., description="Interpretation of vitals")
    medication_review_findings: List[str] = Field(default=[], description="Drug interactions, contraindications")
    laboratory_interpretation: List[str] = Field(default=[], description="Abnormal results and significance")
    infection_risk_assessment: Optional[str] = Field(None, description="Sepsis/infection risk evaluation")
    thromboembolism_risk: Optional[str] = Field(None, description="VTE/bleeding risk assessment")


class AnalysisMetadata(BaseModel):
    """Metadata about the analysis."""
    analysis_duration_seconds: Optional[float] = None
    models_used: List[str] = Field(default=["GPT-4", "NEWS2", "EquityChecker", "ComprehensionAnalyzer"])
    protocols_retrieved: int = Field(default=0, description="Number of clinical guidelines referenced")
    deidentified: bool = Field(default=True, description="PII removed before analysis")


class AnalysisResponse(BaseModel):
    """The main safety analysis output - enhanced with risk stratification."""
    summary: str = Field(..., description="High-level clinical safety summary")
    risk_stratification: RiskStratification = Field(..., description="Overall risk category and score")
    detailed_analysis: DetailedAnalysis = Field(..., description="Structured clinical findings")
    flags: List[SafetyFlag] = []
    equity_flags: List[EquityFlag] = Field(default=[], description="Bias awareness insights")
    relevant_protocols: List[ClinicalProtocol] = []
    metadata: AnalysisMetadata = Field(default_factory=AnalysisMetadata)
    analysis_timestamp: str


class DischargeInstructions(BaseModel):
    """Model for discharge documentation."""
    clinician_facing: str = Field(..., description="Highly technical briefing for the outpatient team")
    patient_facing: str = Field(..., description="Simple, clear, easy-to-read instructions for the patient")
    comprehension_analysis: Optional[ComprehensionScore] = Field(None, description="Patient comprehension metrics")
    patient_facing_translations: Dict[str, str] = Field(default={}, description="Translations: {'es': '...', 'ur': '...'}")
    medication_changes: List[str] = []
    follow_up_required: str
    safety_netting: str = Field(..., description="Emergency 'what to watch for' red flags for the patient")
    citations: List[Citation] = []


class ClinicalFeedback(BaseModel):
    """Feedback from clinicians on AI suggestions (for learning loop)."""
    alert_id: str = Field(..., description="Unique ID of the flag/suggestion")
    action: str = Field(..., description="'accepted', 'rejected', 'modified'")
    clinician_note: Optional[str] = Field(None, description="Optional explanation")
    patient_outcome: Optional[str] = Field(None, description="Follow-up outcome if available")
    timestamp: datetime = Field(default_factory=datetime.now)
    clinician_id: Optional[str] = Field(None, description="De-identified clinician ID")


class SimplifyRequest(BaseModel):
    """Request model for text simplification endpoint."""
    text: str = Field(..., description="Medical text to simplify")
    target_grade_level: int = Field(default=6, ge=1, le=12, description="Target reading level")
    language: str = Field(default="en", description="Output language")
