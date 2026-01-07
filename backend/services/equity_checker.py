"""
Equity & Bias Awareness Checker
Flags known diagnostic and treatment biases to promote equitable care.
"""

from typing import List
from ..models.patient import PatientRecord, Gender
from ..models.responses import EquityFlag, Citation


class EquityChecker:
    """Checks for health equity considerations and potential biases."""
    
    def __init__(self):
        # Equity knowledge base
        self.equity_rules = self._load_equity_rules()
    
    def _load_equity_rules(self) -> dict:
        """Load evidence-based equity guidelines."""
        return {
            "gender_specific_symptoms": {
                "conditions": ["chest pain", "myocardial infarction", "heart attack", "cardiac"],
                "gender_trigger": Gender.FEMALE,
                "flag": {
                    "category": "Gender-Specific Symptoms",
                    "title": "Atypical Cardiac Symptoms in Women",
                    "description": (
                        "Women often present with atypical cardiac symptoms (nausea, fatigue, "
                        "jaw pain) rather than classic chest pain. Consider cardiac workup even "
                        "with non-classic presentation."
                    ),
                    "educational_note": (
                        "Research shows women are more likely to be misdiagnosed or have delayed "
                        "treatment for heart attacks due to atypical symptom presentation. "
                        "This awareness can save lives."
                    ),
                    "citations": [
                        Citation(
                            source_name="American Heart Association",
                            section="Women and Heart Disease",
                            url="https://www.heart.org/en/health-topics/heart-attack/warning-signs-of-a-heart-attack/heart-attack-symptoms-in-women",
                            snippet="Women may experience different heart attack symptoms than men"
                        )
                    ]
                }
            },
            "elderly_kidney_function": {
                "age_threshold": 65,
                "lab_trigger": "creatinine",
                "flag": {
                    "category": "Age-Related Dosing",
                    "title": "Kidney Function in Elderly Patients",
                    "description": (
                        "Elderly patients may have reduced kidney function despite normal creatinine "
                        "due to decreased muscle mass. Consider using eGFR or Cockcroft-Gault equation "
                        "for medication dosing adjustments."
                    ),
                    "educational_note": (
                        "Serum creatinine alone can underestimate kidney impairment in elderly patients. "
                        "This can lead to medication overdosing and adverse effects, particularly with "
                        "renally-cleared drugs like antibiotics and anticoagulants."
                    ),
                    "citations": [
                        Citation(
                            source_name="KDIGO Guidelines",
                            section="CKD Evaluation in Elderly",
                            url="https://kdigo.org/guidelines/",
                            snippet="eGFR should be used for dosing adjustments in elderly patients"
                        )
                    ]
                }
            },
            "polypharmacy_elderly": {
                "age_threshold": 65,
                "medication_count": 5,
                "flag": {
                    "category": "Age-Related Risk",
                    "title": "Polypharmacy in Elderly Patients",
                    "description": (
                        "Patient is on multiple medications (polypharmacy). Elderly patients are at "
                        "higher risk for adverse drug interactions, falls, and cognitive impairment. "
                        "Consider medication reconciliation and deprescribing where appropriate."
                    ),
                    "educational_note": (
                        "Polypharmacy disproportionately affects elderly patients and contributes to "
                        "preventable hospitalizations. Regular medication review can improve outcomes "
                        "and reduce healthcare costs."
                    ),
                    "citations": [
                        Citation(
                            source_name="American Geriatrics Society Beers Criteria",
                            section="Potentially Inappropriate Medications",
                            url="https://www.americangeriatrics.org/",
                            snippet="Polypharmacy increases risk of adverse events in older adults"
                        )
                    ]
                }
            },
            "language_barrier": {
                "flag": {
                    "category": "Communication Equity",
                    "title": "Language and Health Literacy Considerations",
                    "description": (
                        "Ensure discharge instructions are provided in the patient's preferred language "
                        "and at an appropriate reading level. Consider using teach-back method to "
                        "confirm understanding."
                    ),
                    "educational_note": (
                        "Language barriers and low health literacy are associated with worse health "
                        "outcomes, medication errors, and higher readmission rates. Providing accessible "
                        "instructions is a matter of health equity."
                    ),
                    "citations": [
                        Citation(
                            source_name="Joint Commission",
                            section="Patient-Centered Communication Standards",
                            url="https://www.jointcommission.org/",
                            snippet="Effective communication is essential for patient safety and quality care"
                        )
                    ]
                }
            }
        }
    
    def check_equity_considerations(self, patient: PatientRecord) -> List[EquityFlag]:
        """
        Analyze patient record for equity considerations.
        Returns list of equity flags to raise clinician awareness.
        """
        flags = []
        
        # Calculate patient age
        from datetime import datetime
        try:
            dob = datetime.fromisoformat(patient.demographics.date_of_birth)
            age = (datetime.now() - dob).days // 365
        except:
            age = 0
        
        # Check gender-specific symptoms (cardiac in women)
        if patient.demographics.gender == Gender.FEMALE:
            clinical_text = " ".join([note.content.lower() for note in patient.clinical_notes])
            cardiac_keywords = self.equity_rules["gender_specific_symptoms"]["conditions"]
            
            if any(keyword in clinical_text for keyword in cardiac_keywords):
                flag_data = self.equity_rules["gender_specific_symptoms"]["flag"]
                flags.append(EquityFlag(**flag_data))
        
        # Check elderly kidney function
        if age >= self.equity_rules["elderly_kidney_function"]["age_threshold"]:
            has_creatinine = any(
                lab.test_name.lower() == "creatinine" 
                for lab in patient.lab_results
            )
            
            if has_creatinine or len(patient.medications) > 0:
                flag_data = self.equity_rules["elderly_kidney_function"]["flag"]
                flags.append(EquityFlag(**flag_data))
        
        # Check polypharmacy in elderly
        if age >= self.equity_rules["polypharmacy_elderly"]["age_threshold"]:
            if len(patient.medications) >= self.equity_rules["polypharmacy_elderly"]["medication_count"]:
                flag_data = self.equity_rules["polypharmacy_elderly"]["flag"]
                flags.append(EquityFlag(**flag_data))
        
        # Always include language/literacy reminder for discharge
        flags.append(EquityFlag(**self.equity_rules["language_barrier"]["flag"]))
        
        return flags
    
    def get_equity_summary(self, flags: List[EquityFlag]) -> str:
        """Generate a summary of equity considerations."""
        if not flags:
            return "No specific equity considerations identified."
        
        categories = set(flag.category for flag in flags)
        return f"Equity awareness: {len(flags)} considerations across {len(categories)} categories."
