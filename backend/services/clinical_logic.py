"""
Clinical logic and deterministic safety checks.
Implements NEWS2-style sepsis risk scoring and comprehensive risk stratification.
"""

from typing import Dict, Optional, List, Tuple
from ..models.patient import PatientRecord
from ..models.responses import RiskCategory

def calculate_news2_score(patient: PatientRecord) -> int:
    """
    Calculates a simplified NEWS2 (National Early Warning Score) for sepsis risk.
    Score: 0-4 (Low), 5-6 (Medium), 7+ (High/Sepsis Red Flag)
    """
    score = 0
    vitals = patient.vital_signs
    
    if not vitals:
        return 0
        
    # Resp Rate
    if vitals.resp_rate:
        if vitals.resp_rate >= 25 or vitals.resp_rate <= 8:
            score += 3
        elif 21 <= vitals.resp_rate <= 24:
            score += 2
        elif 9 <= vitals.resp_rate <= 11:
            score += 1

    # SpO2
    if vitals.sp_o2:
        if vitals.sp_o2 <= 91:
            score += 3
        elif 92 <= vitals.sp_o2 <= 93:
            score += 2
        elif 94 <= vitals.sp_o2 <= 95:
            score += 1

    # Systolic BP
    if vitals.sys_bp:
        if vitals.sys_bp <= 90 or vitals.sys_bp >= 220:
            score += 3
        elif 91 <= vitals.sys_bp <= 100:
            score += 2
        elif 101 <= vitals.sys_bp <= 110:
            score += 1

    # Heart Rate
    if vitals.heart_rate:
        if vitals.heart_rate >= 131 or vitals.heart_rate <= 40:
            score += 3
        elif 111 <= vitals.heart_rate <= 130 or 41 <= vitals.heart_rate <= 50:
            score += 1

    # Temp
    if vitals.temperature_c:
        if vitals.temperature_c <= 35.0:
            score += 3
        elif vitals.temperature_c >= 39.1:
            score += 2
        elif 38.1 <= vitals.temperature_c <= 39.0 or 35.1 <= vitals.temperature_c <= 36.0:
            score += 1

    return score

def check_sepsis_risk(patient: PatientRecord) -> Optional[str]:
    """
    Checks if the patient meets Sepsis Red Alert criteria.
    Returns a warning string if high risk, else None.
    """
    score = calculate_news2_score(patient)
    
    if score >= 7:
        return (
            "!!! CLINICAL RED ALERT: SEPSIS RISK HIGH !!!\n"
            f"NEWS2 Score: {score}. Immediate clinical review required. "
            "Suspect sepsis and initiate Sepsis Six protocol if infection suspected."
        )
    elif score >= 5:
        return f"CLINICAL WARNING: Moderate Sepsis Risk (NEWS2 Score: {score})."
        
    return None


def detect_anticoagulation_risks(patient: PatientRecord) -> List[Dict[str, str]]:
    """
    Detects anticoagulation-related risks (bleeding, INR abnormalities).
    Returns list of high-risk conditions.
    """
    risks = []
    
    # Check for anticoagulation use
    anticoag_meds = ["warfarin", "apixaban", "rivaroxaban", "dabigatran", "edoxaban", "enoxaparin", "heparin"]
    is_anticoagulated = any(
        med.name.lower() in anticoag_meds 
        for med in patient.medications
    )
    
    if is_anticoagulated:
        # Check INR abnormalities
        for lab in patient.lab_results:
            if lab.test_name.lower() == "inr":
                if lab.value > 4.0:
                    risks.append({
                        "type": "CRITICAL",
                        "condition": "Severely Elevated INR (>4.0)",
                        "value": str(lab.value),
                        "implication": "Major bleeding risk"
                    })
                elif lab.value > 3.0:
                    risks.append({
                        "type": "HIGH",
                        "condition": "Supratherapeutic INR",
                        "value": str(lab.value),
                        "implication": "Increased bleeding risk"
                    })
                elif lab.value < 1.5:
                    risks.append({
                        "type": "HIGH",
                        "condition": "Subtherapeutic INR",
                        "value": str(lab.value),
                        "implication": "Thromboembolism risk"
                    })
        
        # Check for NSAID use (dangerous interaction)
        nsaid_meds = ["ibuprofen", "naproxen", "diclofenac", "ketoprofen", "indomethacin"]
        nsaid_use = any(
            med.name.lower() in nsaid_meds 
            for med in patient.medications
        )
        
        if nsaid_use:
            risks.append({
                "type": "CRITICAL",
                "condition": "NSAID + Anticoagulation",
                "value": "Active",
                "implication": "Significantly increased GI and systemic bleeding risk"
            })
    
    return risks


def detect_vte_risks(patient: PatientRecord) -> List[Dict[str, str]]:
    """
    Detects VTE (DVT/PE) risk factors and symptoms.
    Returns list of VTE-related concerns.
    """
    risks = []
    
    # Check active problems
    vte_conditions = ["dvt", "pe", "pulmonary embolism", "deep vein thrombosis", "afib", "atrial fibrillation"]
    has_vte_risk = any(
        condition.lower() in " ".join(patient.active_problems).lower()
        for condition in vte_conditions
    )
    
    if has_vte_risk:
        # Check for VTE symptoms
        vte_symptoms = ["calf pain", "dyspnea", "shortness of breath", "chest pain", "leg swelling"]
        symptom_text = " ".join(
            note.content.lower() 
            for note in patient.clinical_notes
        )
        
        detected_symptoms = [
            symptom for symptom in vte_symptoms 
            if symptom in symptom_text
        ]
        
        if detected_symptoms:
            risks.append({
                "type": "CRITICAL",
                "condition": "VTE Risk with Concerning Symptoms",
                "value": ", ".join(detected_symptoms),
                "implication": "Potential thromboembolism despite anticoagulation"
            })
        else:
            risks.append({
                "type": "MODERATE",
                "condition": "VTE Risk Factor Present",
                "value": "History of AFib/VTE",
                "implication": "Requires monitoring and therapeutic anticoagulation"
            })
    
    return risks


def detect_renal_risks(patient: PatientRecord) -> List[Dict[str, str]]:
    """
    Detects renal impairment and drug dosing implications.
    """
    risks = []
    
    for lab in patient.lab_results:
        if lab.test_name.lower() in ["creatinine", "egfr"]:
            if lab.test_name.lower() == "creatinine":
                if lab.value > 2.5:
                    risks.append({
                        "type": "HIGH",
                        "condition": "Severe Renal Impairment",
                        "value": f"{lab.value} {lab.unit}",
                        "implication": "Requires careful drug dosing/clearance review"
                    })
                elif lab.value > 1.5:
                    risks.append({
                        "type": "MODERATE",
                        "condition": "Mild-Moderate Renal Impairment",
                        "value": f"{lab.value} {lab.unit}",
                        "implication": "Monitor renal-cleared drugs (e.g., antibiotics)"
                    })
            
            elif lab.test_name.lower() == "egfr":
                if lab.value < 30:
                    risks.append({
                        "type": "HIGH",
                        "condition": "Severe Kidney Disease (eGFR <30)",
                        "value": f"{lab.value} mL/min/1.73m²",
                        "implication": "Significant medication dosing adjustments needed"
                    })
    
    return risks


def calculate_comprehensive_risk_score(patient: PatientRecord) -> Tuple[RiskCategory, float, str]:
    """
    Calculates overall risk category based on multiple clinical factors.
    Returns: (RiskCategory, risk_score_0_to_100, clinical_reasoning)
    """
    risk_score = 0
    findings = []
    
    # NEWS2 Score (0-20 possible, normalize to 0-30 points)
    news2 = calculate_news2_score(patient)
    risk_score += min(30, news2 * 3)
    if news2 >= 7:
        findings.append("CRITICAL sepsis risk (NEWS2 ≥7)")
    elif news2 >= 5:
        findings.append("HIGH sepsis risk (NEWS2 5-6)")
    
    # Anticoagulation risks (0-35 points)
    anticoag_risks = detect_anticoagulation_risks(patient)
    critical_anticoag = [r for r in anticoag_risks if r["type"] == "CRITICAL"]
    high_anticoag = [r for r in anticoag_risks if r["type"] == "HIGH"]
    
    if critical_anticoag:
        risk_score += 35
        findings.append(f"CRITICAL anticoagulation issue: {', '.join(r['condition'] for r in critical_anticoag)}")
    elif high_anticoag:
        risk_score += 20
        findings.append(f"HIGH anticoagulation concern: {', '.join(r['condition'] for r in high_anticoag)}")
    
    # VTE risks (0-20 points)
    vte_risks = detect_vte_risks(patient)
    critical_vte = [r for r in vte_risks if r["type"] == "CRITICAL"]
    
    if critical_vte:
        risk_score += 20
        findings.append(f"CRITICAL VTE risk: {critical_vte[0]['condition']}")
    elif vte_risks:
        risk_score += 10
        findings.append(f"MODERATE VTE concern present")
    
    # Renal risks (0-15 points)
    renal_risks = detect_renal_risks(patient)
    if renal_risks:
        severity = renal_risks[0]["type"]
        if severity == "HIGH":
            risk_score += 15
            findings.append(f"Severe renal impairment")
        elif severity == "MODERATE":
            risk_score += 8
            findings.append(f"Moderate renal impairment")
    
    # Normalize to 0-100
    risk_score = min(100, risk_score)
    
    # Determine risk category
    if risk_score >= 75:
        category = RiskCategory.CRITICAL
    elif risk_score >= 50:
        category = RiskCategory.HIGH
    elif risk_score >= 25:
        category = RiskCategory.MODERATE
    else:
        category = RiskCategory.LOW
    
    reasoning = (
        f"Risk Score: {risk_score}/100. "
        f"Key factors: {'; '.join(findings) if findings else 'No major risk factors identified'}. "
        f"Category: {category.value}"
    )
    
    return category, float(risk_score), reasoning
