"""
API endpoints for clinical safety analysis and discharge drafting.
"""

from fastapi import APIRouter, Depends, HTTPException, Body
from ..models.patient import PatientRecord
from ..models.responses import (
    AnalysisResponse, DischargeInstructions, SimplifyRequest,
    ComprehensionScore, ClinicalFeedback
)
from ..services.orchestrator import ClinicalOrchestrator
from ..services.comprehension_analyzer import ComprehensionAnalyzer
from ..core.dependencies import get_orchestrator
from ..core.exceptions import ClinicalSafetyException

router = APIRouter(prefix="/v1/clinical", tags=["Clinical Safety"])

@router.post("/analyze", response_model=AnalysisResponse)
async def analyze_patient_safety(
    patient: PatientRecord = Body(...),
    orchestrator: ClinicalOrchestrator = Depends(get_orchestrator)
):
    """
    Analyzes a patient's record for safety risks using clinical guidelines.
    Returns categorized flags (Red/Yellow/Green/Purple) and citations.
    Includes equity awareness flags.
    """
    try:
        analysis = await orchestrator.run_analysis(patient)
        return analysis
    except Exception as e:
        raise ClinicalSafetyException(detail=str(e))

@router.post("/draft-discharge", response_model=DischargeInstructions)
async def draft_discharge_instructions(
    patient: PatientRecord = Body(...),
    analysis: AnalysisResponse = Body(..., description="The result of the /analyze endpoint"),
    orchestrator: ClinicalOrchestrator = Depends(get_orchestrator)
):
    """
    Generates structured discharge instructions for both patient and clinician.
    Includes comprehension analysis and simplified version if needed.
    Requires the analysis result to ensure continuity of safety oversight.
    """
    try:
        discharge_draft = await orchestrator.run_discharge_draft(patient, analysis)
        return discharge_draft
    except Exception as e:
        raise ClinicalSafetyException(detail=str(e))

@router.post("/simplify-text", response_model=ComprehensionScore)
async def simplify_medical_text(
    request: SimplifyRequest = Body(...)
):
    """
    Simplifies medical text for patient comprehension.
    Returns comprehension score and simplified version.
    """
    try:
        analyzer = ComprehensionAnalyzer()
        result = await analyzer.analyze_and_improve(request.text, request.language)
        
        return ComprehensionScore(
            score=result["score"],
            reading_level=result["reading_level"],
            interpretation=result["interpretation"],
            jargon_detected=result["jargon_detected"],
            simplified_version=result["simplified_version"],
            language=result["language"],
            needs_improvement=result["needs_improvement"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simplification error: {str(e)}")

@router.post("/feedback/submit")
async def submit_clinical_feedback(
    feedback: ClinicalFeedback = Body(...)
):
    """
    Submit feedback on AI suggestions (for learning loop).
    Helps the system learn from clinician decisions.
    """
    try:
        # TODO: Store feedback in database for analysis
        # For now, just acknowledge receipt
        return {
            "status": "received",
            "message": "Feedback recorded successfully",
            "feedback_id": feedback.alert_id,
            "timestamp": feedback.timestamp.isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Feedback submission error: {str(e)}")

