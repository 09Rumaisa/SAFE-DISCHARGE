"""
Azure OpenAI service using LangChain for clinical logic.
"""

import logging
from typing import List, Optional
from langchain_openai import ChatOpenAI, AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import PydanticOutputParser
from ..config import get_settings
from ..models.responses import AnalysisResponse, DischargeInstructions

logger = logging.getLogger(__name__)
settings = get_settings()

class LLMClient:
    """Wrapper for Azure OpenAI calls using LangChain patterns."""
    
    def __init__(self):
        if settings.use_azure_openai:
            logger.info("🔷 Using Azure OpenAI")
            self.llm = AzureChatOpenAI(
                azure_endpoint=settings.azure_openai_endpoint,
                api_key=settings.azure_openai_api_key,
                deployment_name=settings.azure_openai_deployment,
                api_version=settings.azure_openai_api_version,
                temperature=1
            )
        else:
            logger.info("Using OpenAI API")
            self.llm = ChatOpenAI(
                api_key=settings.openai_api_key,
                model=settings.openai_model,
                temperature=1
            )

    async def analyze_safety(self, patient_data: str, protocols: str, clinical_alerts: str = "") -> AnalysisResponse:
        """Execute safety analysis using RAG context and clinical alerts."""
        
        # DEBUG: Validate the data being sent
        print("\n" + "="*80)
        print("🔍 DATA VALIDATION:")
        print(f"📊 Patient data length: {len(patient_data)} chars")
        print(f"📚 Protocols length: {len(protocols)} chars")
        
        # Check if patient_data is valid JSON
        try:
            import json
            parsed = json.loads(patient_data)
            print(f"✅ Patient data is valid JSON")
            print(f"   - Has demographics: {bool(parsed.get('demographics'))}")
            print(f"   - Has medications: {bool(parsed.get('medications'))} ({len(parsed.get('medications', []))} meds)")
            print(f"   - Has lab_results: {bool(parsed.get('lab_results'))} ({len(parsed.get('lab_results', []))} labs)")
        except Exception as e:
            print(f"❌ Patient data is INVALID JSON: {e}")
        
        print("="*80 + "\n")
        
        # Enhanced prompt for comprehensive risk stratification
        system_prompt = (
            "You are an Expert Clinical Safety AI analyzing a patient for discharge safety.\n\n"
            "CORE TASK:\n"
            "Perform a comprehensive, structured clinical analysis of the patient data against evidence-based guidelines.\n"
            "Identify ALL safety risks and categorize them by severity (CRITICAL → HIGH → MODERATE → LOW).\n\n"
            "PATIENT DATA: Provided below in structured JSON format\n"
            "CLINICAL GUIDELINES: Reference these for evidence-based recommendations\n"
            "AUTOMATED ALERTS: Clinical deterministic checks (NEWS2 score, drug interactions, etc.)\n\n"
            "ANALYSIS FRAMEWORK:\n"
            "1. PRESENTING PROBLEM: What is the primary diagnosis/reason for admission?\n"
            "2. VITAL SIGNS: Assess NEWS2 score and hemodynamic stability\n"
            "3. MEDICATIONS: Identify drug interactions, contraindications, dosing appropriateness\n"
            "4. LABS: Interpret abnormal results in clinical context\n"
            "5. INFECTION RISK: Evaluate fever, WBC, vital signs for sepsis (NEWS2 ≥5 = concerning)\n"
            "6. THROMBOEMBOLISM RISK: Check anticoagulation status, VTE symptoms, INR\n"
            "7. RENAL/HEPATIC: Any organ dysfunction affecting drug clearance?\n\n"
            "CRITICAL SAFETY PRINCIPLES:\n"
            "• SUPRATHERAPEUTIC INR + NSAID = CRITICAL RISK (severe bleeding)\n"
            "• Anticoagulation + VTE symptoms = CRITICAL (need urgent investigation)\n"
            "• NEWS2 ≥7 = CRITICAL sepsis risk (Sepsis Six protocol)\n"
            "• NEWS2 5-6 = HIGH sepsis risk (frequent monitoring)\n"
            "• Elderly (>65) + 5+ medications = MODERATE polypharmacy risk\n"
            "• Renal impairment + renally-cleared drugs = HIGH dosing error risk\n\n"
            "FLAG SEVERITY DEFINITIONS:\n"
            "RED (Critical): Immediate life-threatening risk, intervention required within hours\n"
            "YELLOW (High): Significant risk, requires urgent review and likely intervention\n"
            "GREEN (Moderate-Low): Important but less urgent, routine monitoring adequate\n\n"
            "RETURN ONLY VALID JSON with this exact structure:\n"
            "{\n"
            '  "summary": "Executive summary of patient status and key safety concerns",\n'
            '  "risk_stratification": {\n'
            '    "overall_risk": "Critical|High|Moderate|Low",\n'
            '    "critical_count": 0,\n'
            '    "high_count": 0,\n'
            '    "moderate_count": 0,\n'
            '    "equity_count": 0,\n'
            '    "risk_score": 0.0,\n'
            '    "clinical_reasoning": "Why this risk level was assigned"\n'
            '  },\n'
            '  "detailed_analysis": {\n'
            '    "presenting_problem": "Primary diagnosis",\n'
            '    "relevant_history": ["past medical history items"],\n'
            '    "current_vital_signs_assessment": "Interpretation of vitals",\n'
            '    "medication_review_findings": ["drug interactions, contraindications"],\n'
            '    "laboratory_interpretation": ["abnormal lab results and significance"],\n'
            '    "infection_risk_assessment": "Sepsis risk evaluation",\n'
            '    "thromboembolism_risk": "VTE/bleeding risk assessment"\n'
            '  },\n'
            '  "flags": [\n'
            '    {"severity": "Red|Yellow|Green", "title": "Risk title", "description": "Full explanation", "action_required": "Recommended action", "citations": [{"source_name": "Guideline source"}]}\n'
            '  ],\n'
            '  "relevant_protocols": [\n'
            '    {"title": "Protocol name", "summary": "Summary", "source": "Source"}\n'
            '  ],\n'
            '  "analysis_timestamp": "ISO 8601 timestamp"\n'
            "}\n\n"
            "CRITICAL REQUIREMENTS:\n"
            "• Severity MUST be exactly: Red, Yellow, or Green (NOT 'Amber')\n"
            "• Include citations from the guidelines provided\n"
            "• risk_score must be numeric 0-100\n"
            "• Include at least one detailed explanation for each critical/high risk\n"
            "• If patient has anticoagulation + elevated INR, FLAG AS CRITICAL\n"
            "• If patient has anticoagulation + NSAID use, FLAG AS CRITICAL\n"
            "• If patient has VTE symptoms despite anticoagulation, FLAG AS CRITICAL\n"
            "• Return ONLY valid JSON, absolutely NO other text"
        )
        
        human_prompt = f"""PATIENT DATA (must analyze):
{patient_data}

CLINICAL GUIDELINES (must reference):
{protocols}

AUTOMATED CLINICAL ALERTS:
{clinical_alerts if clinical_alerts else 'No specific deterministic alerts'}

ANALYSIS INSTRUCTIONS:
1. Review patient data systematically (demographics, vitals, medications, labs, notes)
2. Cross-reference against clinical guidelines provided
3. Apply the safety principles outlined in system prompt
4. Identify ALL risks and categorize by severity
5. Provide structured JSON output with detailed clinical reasoning
6. Ensure flags address BOTH high-risk AND low-risk conditions
7. Include specific evidence-based citations

Now perform the analysis and return ONLY the JSON structure specified above."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]
        
        try:
            print("🤖 Calling OpenAI API...")
            response = await self.llm.ainvoke(messages)
            print(f"✅ Got response: {len(response.content)} chars")
            print(f"Response preview: {response.content[:200]}...")
            
            # Parse the JSON response
            import json
            import re
            from datetime import datetime
            
            # Try to extract JSON if wrapped in markdown
            content = response.content.strip()
            if content.startswith("```json"):
                content = content[7:]
            if content.startswith("```"):
                content = content[3:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()
            
            # Clean up common LLM JSON errors (trailing commas)
            # Remove trailing commas before } or ]
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            
            result_json = json.loads(content)
            print("✅ Successfully parsed JSON response")
            
            # Convert to AnalysisResponse with new structure
            from ..models.responses import (
                SafetyFlag, ClinicalProtocol, Citation, FlagSeverity, 
                RiskStratification, DetailedAnalysis, AnalysisMetadata
            )
            
            # Parse flags
            flags = []
            for f in result_json.get("flags", []):
                severity = f["severity"]
                if severity == "Amber":
                    severity = "Yellow"
                
                flags.append(SafetyFlag(
                    severity=FlagSeverity(severity),
                    title=f["title"],
                    description=f["description"],
                    action_required=f.get("action_required"),
                    citations=[Citation(source_name=c.get("source_name", "Unknown")) for c in f.get("citations", [])]
                ))
            
            # Parse protocols
            protocols_list = []
            for p in result_json.get("relevant_protocols", []):
                protocols_list.append(ClinicalProtocol(
                    title=p["title"],
                    summary=p["summary"],
                    source=p["source"]
                ))
            
            # Parse risk stratification
            rs_data = result_json.get("risk_stratification", {})
            risk_stratification = RiskStratification(
                overall_risk=rs_data.get("overall_risk", "Low"),
                critical_count=rs_data.get("critical_count", 0),
                high_count=rs_data.get("high_count", 0),
                moderate_count=rs_data.get("moderate_count", 0),
                equity_count=rs_data.get("equity_count", 0),
                risk_score=float(rs_data.get("risk_score", 0)),
                clinical_reasoning=rs_data.get("clinical_reasoning", "Risk assessment completed")
            )
            
            # Parse detailed analysis
            da_data = result_json.get("detailed_analysis", {})
            detailed_analysis = DetailedAnalysis(
                presenting_problem=da_data.get("presenting_problem", "Unknown"),
                relevant_history=da_data.get("relevant_history", []),
                current_vital_signs_assessment=da_data.get("current_vital_signs_assessment", "See flags"),
                medication_review_findings=da_data.get("medication_review_findings", []),
                laboratory_interpretation=da_data.get("laboratory_interpretation", []),
                infection_risk_assessment=da_data.get("infection_risk_assessment"),
                thromboembolism_risk=da_data.get("thromboembolism_risk")
            )
            
            # Parse metadata
            metadata = AnalysisMetadata(
                protocols_retrieved=len(protocols_list),
                deidentified=True
            )
            
            print(f"✅ Created AnalysisResponse with {len(flags)} flags, risk: {risk_stratification.overall_risk}")
            
            return AnalysisResponse(
                summary=result_json["summary"],
                risk_stratification=risk_stratification,
                detailed_analysis=detailed_analysis,
                flags=flags,
                relevant_protocols=protocols_list,
                metadata=metadata,
                analysis_timestamp=result_json.get("analysis_timestamp", datetime.now().isoformat())
            )
            
        except Exception as e:
            logger.error(f"Failed to parse AI response: {str(e)}")
            print(f"❌ ERROR: {e}")
            print(f"Response content: {response.content if 'response' in locals() else 'No response'}")
            
            # Return a fallback response
            from datetime import datetime
            from ..models.responses import (
                SafetyFlag, FlagSeverity, Citation, ClinicalProtocol,
                RiskStratification, DetailedAnalysis, AnalysisMetadata
            )
            return AnalysisResponse(
                summary="Unable to complete analysis due to parsing error. Please review patient data manually.",
                risk_stratification=RiskStratification(
                    overall_risk="High",
                    critical_count=0,
                    high_count=1,
                    risk_score=50.0,
                    clinical_reasoning="Analysis failed - manual review required"
                ),
                detailed_analysis=DetailedAnalysis(
                    presenting_problem="Unable to determine",
                    current_vital_signs_assessment="Manual review needed"
                ),
                flags=[
                    SafetyFlag(
                        severity=FlagSeverity.YELLOW,
                        title="AI Analysis Error",
                        description=f"The AI system encountered an error: {str(e)}",
                        action_required="Review patient record manually",
                        citations=[Citation(source_name="System Error")]
                    )
                ],
                relevant_protocols=[],
                metadata=AnalysisMetadata(deidentified=True),
                analysis_timestamp=datetime.now().isoformat()
            )

    async def generate_discharge(self, patient_data: str, analysis: str, protocols: str) -> DischargeInstructions:
        """Generate risk-stratified discharge documentation with personalized safety netting."""
        
        parser = PydanticOutputParser(pydantic_object=DischargeInstructions)
        
        system_prompt = (
            "You are an Expert Clinical Discharge Writer. Your task is to generate PERSONALIZED, RISK-STRATIFIED discharge instructions.\n\n"
            "CRITICAL REQUIREMENTS:\n"
            "1. Output ONLY valid JSON matching this exact schema:\n"
            "{\n"
            '  "clinician_facing": "string - technical, comprehensive briefing for outpatient team",\n'
            '  "patient_facing": "string - simple, Grade 6-8 reading level, patient-friendly",\n'
            '  "medication_changes": ["string - specific medication actions"],\n'
            '  "follow_up_required": "string - specific timing and specialty",\n'
            '  "safety_netting": "string - RED FLAG symptoms that require ER/911",\n'
            '  "citations": [{"source_name": "string"}]\n'
            "}\n\n"
            "DISCHARGE GENERATION FRAMEWORK:\n\n"
            "🔴 FOR HIGH-RISK/CRITICAL PATIENTS:\n"
            "• Be EXTREMELY SPECIFIC about what to watch for\n"
            "• Include EXACT red flag symptoms (not vague language)\n"
            "• Recommend SHORTER follow-up windows (hours/days, not weeks)\n"
            "• Call out CRITICAL interactions or contraindications explicitly\n"
            "• Example: 'STOP IBUPROFEN immediately - dangerous with your blood thinner'\n"
            "• Include multiple emergency trigger symptoms\n"
            "• Safety netting should be 5-10 specific warning signs\n\n"
            "🟡 FOR MODERATE-RISK PATIENTS:\n"
            "• Provide clear monitoring instructions\n"
            "• List moderate symptoms to watch for\n"
            "• Recommend follow-up within 3-7 days\n"
            "• Include medication adjustment guidance\n\n"
            "🟢 FOR LOW-RISK PATIENTS:\n"
            "• Standard discharge instructions appropriate\n"
            "• Routine follow-up windows (1-2 weeks)\n"
            "• General safety warnings\n\n"
            "MEDICATION SECTION:\n"
            "• List ALL changes (stops, starts, dose adjustments) with REASONS\n"
            "• If patient is on anticoagulation + NSAID: CRITICAL - must say STOP NSAID\n"
            "• If INR elevated: CRITICAL - must mention INR monitoring timeline\n"
            "• Include relevant drug interaction warnings\n\n"
            "SAFETY NETTING:\n"
            "• MUST include 'Call 911 or go to ER if...' section\n"
            "• For HIGH-RISK: 5-10 specific emergency symptoms\n"
            "• For MODERATE-RISK: 3-5 concerning symptoms\n"
            "• Include timeframes ('within 24 hours', 'immediately', etc.)\n"
            "• Be specific: not 'bleeding' but 'blood in stool, nosebleeds, bruising'\n\n"
            "FOLLOW-UP:\n"
            "• High-risk: Follow-up within 24-72 hours OR same-day if critical\n"
            "• Moderate-risk: Follow-up within 3-5 days\n"
            "• Include specific tests if needed (e.g., 'INR test within 3-5 days')\n"
            "• Name the specialty (cardiology, ID, etc.) if applicable\n\n"
            "PATIENT-FACING TEXT REQUIREMENTS:\n"
            "• Use SIMPLE, EVERYDAY LANGUAGE - write for a 5th-6th grade reading level\n"
            "• CONTEXT-SPECIFIC opening - Reference the ACTUAL chief complaint and symptoms (not generic 'surgery')\n"
            "• NEVER use complex medical terms - replace with simple words:\n"
            "  - 'anticoagulant' → 'blood thinner medicine'\n"
            "  - 'INR' → 'blood test to check how thin your blood is'\n"
            "  - 'thromboembolism' → 'blood clot'\n"
            "  - 'hypertension' → 'high blood pressure'\n"
            "  - 'dyspnea' → 'trouble breathing'\n"
            "  - 'hemorrhage' → 'bleeding'\n"
            "  - 'DVT/PE' → 'dangerous blood clot in your leg or lung'\n"
            "• Make it DETAILED and LENGTHY - patient needs complete information\n"
            "• Break down complex concepts into multiple simple sentences\n"
            "• Use newlines and paragraph breaks for clarity - DO NOT use markdown asterisks or special formatting\n"
            "• Include SPECIFIC examples and clear actions\n"
            "• Explain WHY they need to do something (e.g., 'This is important because...')\n"
            "• Use 'Call your doctor if...' and 'Go to ER if...'\n"
            "• For high-risk: Use CAPITAL LETTERS for emphasis (e.g., STOP, IMPORTANT, CRITICAL), NOT asterisks or bold\n"
            "• AIM FOR 200-400 WORDS - thorough is better than brief\n"
            "• PROFESSIONAL APPEARANCE - clean text, no asterisks, no markdown formatting\n"
            "• NEVER MENTION 'DISCHARGE' OR 'GOING HOME' - just give the instructions. The context is already understood.\n\n"
            "CLINICIAN-FACING TEXT:\n"
            "• Technical details and clinical reasoning\n"
            "• Medication doses and adjustments\n"
            "• Any special precautions or monitoring\n"
            "• Reference to guidelines and protocols\n\n"
            "ABSOLUTE RULES:\n"
            "• Return ONLY JSON, NO other text\n"
            "• NO markdown formatting (no asterisks, no bold, no underscores, no code blocks)\n"
            "• NO special characters or emoji for formatting\n"
            "• Use CAPITAL LETTERS instead of bold/asterisks for emphasis\n"
            "• Use newlines and paragraphs for organization\n"
            "• All fields must be populated\n"
            "• Safety netting must be comprehensive\n"
            "• Match the risk level in the analysis provided\n"
            "• Final text should look clean and professional\n"
        )
        
        human_prompt = (
            "PATIENT DATA:\n{patient_data}\n\n"
            "CLINICAL ANALYSIS AND RISK ASSESSMENT:\n{analysis}\n\n"
            "CLINICAL GUIDELINES:\n{protocols}\n\n"
            "INSTRUCTIONS:\n"
            "1. Analyze the patient's chief complaint and presenting symptoms from the patient data\n"
            "2. Generate discharge instructions that are SPECIFIC to THEIR CONDITION - not generic\n"
            "3. Do NOT use phrases like 'after your surgery' unless surgery is actually mentioned in their records\n"
            "4. Base the opening on their actual chief complaint (e.g., if calf pain + shortness of breath, mention these)\n"
            "5. Ensure all recommendations directly address THEIR specific medical situation\n"
            "6. If the patient is HIGH-RISK or CRITICAL, ensure safety netting is EXTREMELY SPECIFIC\n"
            "7. If anticoagulation + elevated INR: CRITICAL FLAG - discharge must specifically address blood thinner management\n"
            "8. If VTE symptoms despite anticoagulation: CRITICAL FLAG - needs urgent follow-up\n\n"
            "Generate discharge instructions as JSON ONLY."
        )

        prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=system_prompt),
            HumanMessage(content=human_prompt)
        ]).partial(format_instructions=parser.get_format_instructions())

        formatted_prompt = prompt.format_messages(
            protocols=protocols if protocols else "Use the analysis provided",
            analysis=analysis,
            patient_data=patient_data
        )
        
        try:
            logger.info("🔄 Generating risk-stratified discharge instructions...")
            response = await self.llm.ainvoke(formatted_prompt)
            logger.info(f"✅ Received discharge response ({len(response.content)} chars)")
            
            # Clean up the response content before parsing
            import re
            content = response.content.strip()
            
            # Remove trailing commas before } or ]
            content = re.sub(r',(\s*[}\]])', r'\1', content)
            
            return parser.parse(content)
        except Exception as e:
            logger.error(f"❌ Discharge generation failed: {str(e)}")
            logger.error(f"Raw response: {response.content if 'response' in locals() else 'No response'}")
            # Return a fallback discharge
            from datetime import datetime
            from ..models.responses import Citation
            return DischargeInstructions(
                clinician_facing="Unable to generate discharge instructions due to parsing error. Manual review required.",
                patient_facing="Please follow up with your doctor as instructed. Seek emergency care if symptoms worsen.",
                medication_changes=["Review medications with your doctor"],
                follow_up_required="Follow up with primary care physician within 1 week",
                safety_netting="Seek immediate medical attention (call 911 or go to ER) if you experience new or worsening symptoms, chest pain, difficulty breathing, or any emergency symptoms.",
            )
