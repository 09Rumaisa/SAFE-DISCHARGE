"""
Clinical Orchestrator using LangGraph.
Manages the state and flow of clinical safety analysis with risk stratification.
"""

import logging
from typing import Dict, List, Annotated, TypedDict, Union
from datetime import datetime

from langgraph.graph import StateGraph
from ..models.patient import PatientRecord
from ..models.responses import AnalysisResponse, ClinicalProtocol, DischargeInstructions
from .knowledge_base import ClinicalRetriever
from .llm_client import LLMClient
from .clinical_logic import (
    check_sepsis_risk,
    detect_anticoagulation_risks,
    detect_vte_risks,
    detect_renal_risks,
    calculate_comprehensive_risk_score
)
from .equity_checker import EquityChecker
from .comprehension_analyzer import ComprehensionAnalyzer
from ..core.security import deidentify_patient_data

logger = logging.getLogger(__name__)

# Define the state of our clinical workflow
class ClinicalState(TypedDict):
    patient: PatientRecord
    deidentified_patient: Union[Dict, None]
    protocols: List[ClinicalProtocol]
    clinical_alerts: List[str]
    risk_factors: Dict[str, List[Dict]]
    analysis: Union[AnalysisResponse, None]
    validation_status: Dict[str, Union[bool, str]]
    error: Union[str, None]
    metadata: Dict[str, str]


class ClinicalOrchestrator:
    """
    Orchestrates the RAG workflow for clinical safety with comprehensive risk stratification.
    Uses LangGraph to define a robust, state-based execution.
    """
    
    def __init__(self, retriever: ClinicalRetriever, llm_client: LLMClient):
        self.retriever = retriever
        self.llm_client = llm_client
        self.equity_checker = EquityChecker()
        self.comprehension_analyzer = ComprehensionAnalyzer()
        self.workflow = self._build_workflow()

    def _build_workflow(self) -> StateGraph:
        """Constructs the LangGraph state machine with enhanced risk stratification."""
        workflow = StateGraph(ClinicalState)

        # Define nodes
        workflow.add_node("deidentify_data", self._deidentify_node)
        workflow.add_node("risk_stratification", self._risk_stratification_node)
        workflow.add_node("check_safety_logic", self._safety_logic_node)
        workflow.add_node("retrieve_protocols", self._retrieve_protocols_node)
        workflow.add_node("analyze_safety", self._analyze_safety_node)
        workflow.add_node("validate_output", self._validate_output_node)
        
        # Define wiring
        workflow.set_entry_point("deidentify_data")
        workflow.add_edge("deidentify_data", "risk_stratification")
        workflow.add_edge("risk_stratification", "check_safety_logic")
        workflow.add_edge("check_safety_logic", "retrieve_protocols")
        workflow.add_edge("retrieve_protocols", "analyze_safety")
        workflow.add_edge("analyze_safety", "validate_output")
        workflow.add_edge("validate_output", "__end__")

        return workflow.compile()

    # --- Node Implementations ---

    async def _deidentify_node(self, state: ClinicalState) -> Dict:
        """Step 1: Scrub PII from patient data before LLM sees it."""
        patient_dict = state["patient"].dict()
        deidentified = deidentify_patient_data(patient_dict)
        logger.info("✅ PII de-identification complete")
        return {"deidentified_patient": deidentified}

    async def _risk_stratification_node(self, state: ClinicalState) -> Dict:
        """Step 2: Comprehensive risk stratification using deterministic logic."""
        patient = state["patient"]
        
        # Detect various risk categories
        anticoag_risks = detect_anticoagulation_risks(patient)
        vte_risks = detect_vte_risks(patient)
        renal_risks = detect_renal_risks(patient)
        
        risk_factors = {
            "anticoagulation": anticoag_risks,
            "thromboembolism": vte_risks,
            "renal": renal_risks
        }
        
        # Calculate comprehensive risk score
        risk_category, risk_score, reasoning = calculate_comprehensive_risk_score(patient)
        
        logger.info(f"🎯 Risk Stratification: {risk_category.value} (Score: {risk_score})")
        logger.info(f"   - Anticoagulation risks: {len(anticoag_risks)}")
        logger.info(f"   - VTE risks: {len(vte_risks)}")
        logger.info(f"   - Renal risks: {len(renal_risks)}")
        
        return {
            "risk_factors": risk_factors,
            "metadata": {
                "risk_category": risk_category.value,
                "risk_score": str(risk_score),
                "risk_reasoning": reasoning
            }
        }

    async def _safety_logic_node(self, state: ClinicalState) -> Dict:
        """Step 3: Run deterministic clinical logic (NEWS2, drug interactions, etc.)."""
        patient = state["patient"]
        alerts = []
        
        # Sepsis risk alert
        sepsis_alert = check_sepsis_risk(patient)
        if sepsis_alert:
            alerts.append(sepsis_alert)
            logger.warning(f"⚠️ {sepsis_alert}")
        
        # Add detailed risk information from stratification
        for risk_type, risks in state.get("risk_factors", {}).items():
            for risk in risks:
                alert_msg = f"[{risk['type']}] {risk['condition']}: {risk['implication']}"
                alerts.append(alert_msg)
                if risk['type'] in ['CRITICAL', 'HIGH']:
                    logger.warning(f"🔴 {alert_msg}")
        
        logger.info(f"Generated {len(alerts)} clinical alerts")
        return {"clinical_alerts": alerts}

    async def _retrieve_protocols_node(self, state: ClinicalState) -> Dict:
        """Step 4: Retrieve relevant clinical guidelines based on patient factors."""
        patient = state["patient"]
        
        # Build comprehensive search query
        search_terms = [m.name for m in patient.medications]
        search_terms.extend(patient.active_problems)
        
        # Add terms from detected risk factors
        for risk_type, risks in state.get("risk_factors", {}).items():
            for risk in risks:
                search_terms.append(risk["condition"])
        
        query = " ".join(search_terms)
        logger.info(f"🔍 Searching for guidelines: {query[:100]}...")
        
        protocols = await self.retriever.search(query)
        logger.info(f"✅ Retrieved {len(protocols)} protocols")
        
        return {"protocols": protocols}

    async def _analyze_safety_node(self, state: ClinicalState) -> Dict:
        """Step 5: Generate comprehensive safety analysis with equity checks."""
        patient = state["patient"]
        patient_data = state["deidentified_patient"]
        protocols = state["protocols"]
        alerts = "\n".join(state["clinical_alerts"]) if state["clinical_alerts"] else "No immediate automated alerts."
        
        # Format for LLM context - use JSON instead of str()
        import json
        patient_str = json.dumps(patient_data, indent=2, default=str) if patient_data else "No patient data available"
        protocol_str = await self.retriever.get_all_context_string(protocols) if protocols else "No protocols retrieved"
        
        # Include risk stratification in LLM context
        risk_context = (
            f"\n\nRISK STRATIFICATION CONTEXT:\n"
            f"Overall Risk Category: {state['metadata'].get('risk_category', 'Unknown')}\n"
            f"Risk Score: {state['metadata'].get('risk_score', 'N/A')}/100\n"
            f"Clinical Reasoning: {state['metadata'].get('risk_reasoning', 'N/A')}\n"
        )
        
        alerts_with_context = alerts + risk_context
        
        logger.info(f"📊 Calling AI analysis with:")
        logger.info(f"   - Patient data: {len(patient_str)} chars")
        logger.info(f"   - Protocols: {len(protocol_str)} chars")
        logger.info(f"   - Alerts/Context: {len(alerts_with_context)} chars")
        
        try:
            # Run AI safety analysis
            analysis = await self.llm_client.analyze_safety(patient_str, protocol_str, alerts_with_context)
            logger.info(f"✅ AI Analysis complete. Risk: {analysis.risk_stratification.overall_risk}")
            
            # Add equity awareness flags
            equity_flags = self.equity_checker.check_equity_considerations(patient)
            analysis.equity_flags = equity_flags
            logger.info(f"✅ Added {len(equity_flags)} equity flags")
            
            return {"analysis": analysis}
        except Exception as e:
            logger.error(f"❌ Analysis failed: {str(e)}")
            return {"error": f"Clinical Safety Analysis Error: {str(e)}"}

    async def _validate_output_node(self, state: ClinicalState) -> Dict:
        """Step 6: Safety Guardrail - check for citations, quality, and consistency."""
        analysis = state["analysis"]
        if not analysis:
            return {"validation_status": {"passed": False, "reason": "No analysis produced"}}
            
        # Check if at least one citation exists
        has_citations = len(analysis.relevant_protocols) > 0 or any(len(f.citations) > 0 for f in analysis.flags)
        
        # Check for high-risk flags
        high_risk_flags = [f for f in analysis.flags if f.severity.value == "Red"]
        
        if not has_citations:
            logger.warning("⚠️  Guardrail: AI response missing citations")
        
        logger.info(f"✅ Validation: {len(high_risk_flags)} RED flags, {len(analysis.flags)} total flags")
        
        return {"validation_status": {"passed": True, "high_risk_count": len(high_risk_flags)}}

    # --- Public API methods ---

    async def run_analysis(self, patient: PatientRecord) -> AnalysisResponse:
        """Execute the primary safety analysis workflow."""
        initial_state: ClinicalState = {
            "patient": patient,
            "deidentified_patient": None,
            "protocols": [],
            "clinical_alerts": [],
            "risk_factors": {},
            "analysis": None,
            "validation_status": {},
            "error": None,
            "metadata": {"timestamp": datetime.now().isoformat()}
        }
        
        final_state = await self.workflow.ainvoke(initial_state)
        
        if final_state.get("error"):
            raise Exception(final_state["error"])
            
        return final_state["analysis"]

    async def run_discharge_draft(self, patient: PatientRecord, analysis: AnalysisResponse) -> DischargeInstructions:
        """Executes discharge drafting with risk-stratified, personalized instructions."""
        protocol_str = await self.retriever.get_all_context_string(analysis.relevant_protocols)
        
        # Add risk level to context for discharge generation
        risk_context = (
            f"\n\nPATIENT RISK PROFILE:\n"
            f"Risk Category: {analysis.risk_stratification.overall_risk}\n"
            f"Risk Score: {analysis.risk_stratification.risk_score}\n"
            f"Critical Issues: {analysis.risk_stratification.critical_count}\n"
            f"High Issues: {analysis.risk_stratification.high_count}\n"
        )
        
        try:
            # Generate discharge instructions
            discharge = await self.llm_client.generate_discharge(
                patient.json(),
                analysis.json() + risk_context,
                protocol_str
            )
            
            # Analyze patient-facing text for comprehension
            comprehension_result = await self.comprehension_analyzer.analyze_and_improve(
                discharge.patient_facing
            )
            
            # Add comprehension analysis to discharge
            from ..models.responses import ComprehensionScore
            discharge.comprehension_analysis = ComprehensionScore(
                score=comprehension_result["score"],
                reading_level=comprehension_result["reading_level"],
                interpretation=comprehension_result["interpretation"],
                jargon_detected=comprehension_result["jargon_detected"],
                simplified_version=comprehension_result["simplified_version"],
                language=comprehension_result["language"],
                needs_improvement=comprehension_result["needs_improvement"]
            )
            
            logger.info(f"✅ Discharge drafted. Comprehension: {discharge.comprehension_analysis.score}/100")
            return discharge
        except Exception as e:
            logger.error(f"❌ Discharge drafting failed: {str(e)}")
            raise Exception(f"Clinical Discharge Error: {str(e)}")



    async def _retrieve_protocols_node(self, state: ClinicalState) -> Dict:
        """Step 3: Retrieve relevant clinical guidelines."""
        patient = state["patient"]
        
        search_terms = [m.name for m in patient.medications]
        search_terms.extend(patient.active_problems)
        
        query = " ".join(search_terms)
        protocols = await self.retriever.search(query)
        
        return {"protocols": protocols}

    async def _analyze_safety_node(self, state: ClinicalState) -> Dict:
        """Step 4: Generate safety analysis using AI + equity checks."""
        patient = state["patient"]
        patient_data = state["deidentified_patient"]
        protocols = state["protocols"]
        alerts = "\n".join(state["clinical_alerts"]) if state["clinical_alerts"] else "No immediate automated alerts."
        
        # Format for LLM context - use JSON instead of str()
        import json
        patient_str = json.dumps(patient_data, indent=2, default=str) if patient_data else "No patient data available"
        protocol_str = await self.retriever.get_all_context_string(protocols) if protocols else "No protocols retrieved"
        
        # Debug logging
        logger.info(f"Patient data length: {len(patient_str)}")
        logger.info(f"Protocols length: {len(protocol_str)}")
        logger.info(f"Alerts: {alerts}")
        logger.info(f"Patient data preview: {patient_str[:200]}...")
        
        try:
            # Run AI safety analysis
            analysis = await self.llm_client.analyze_safety(patient_str, protocol_str, alerts)
            
            # Add equity awareness flags
            equity_flags = self.equity_checker.check_equity_considerations(patient)
            analysis.equity_flags = equity_flags
            
            return {"analysis": analysis}
        except Exception as e:
            logger.error(f"Analysis failed: {str(e)}")
            return {"error": f"Clinical Safety Analysis Error: {str(e)}"}

    async def _validate_output_node(self, state: ClinicalState) -> Dict:
        """Step 5: Safety Guardrail - check for citations and quality."""
        analysis = state["analysis"]
        if not analysis:
            return {"validation_status": {"passed": False, "reason": "No analysis produced"}}
            
        # Check if at least one citation exists
        has_citations = len(analysis.relevant_protocols) > 0 or any(len(f.citations) > 0 for f in analysis.flags)
        
        if not has_citations:
            logger.warning("Guardrail Triggered: AI response missing citations.")
            # In Phase 2, we mark it but still return, potentially flagging for human review
            return {"validation_status": {"passed": False, "reason": "Missing citations in clinical output"}}
            
        return {"validation_status": {"passed": True}}

    # --- Public API methods ---

    async def run_analysis(self, patient: PatientRecord) -> AnalysisResponse:
        """Execute the primary safety analysis workflow."""
        initial_state: ClinicalState = {
            "patient": patient,
            "deidentified_patient": None,
            "protocols": [],
            "clinical_alerts": [],
            "analysis": None,
            "validation_status": {},
            "error": None,
            "metadata": {"timestamp": datetime.now().isoformat()}
        }
        
        final_state = await self.workflow.ainvoke(initial_state)
        
        if final_state.get("error"):
            raise Exception(final_state["error"])
            
        # Inject validation warnings into summary if any
        if final_state["validation_status"].get("passed") is False:
            final_state["analysis"].summary = f"[FLAGGED FOR REVIEW: {final_state['validation_status']['reason']}] " + final_state["analysis"].summary
            
        return final_state["analysis"]

    async def run_discharge_draft(self, patient: PatientRecord, analysis: AnalysisResponse) -> DischargeInstructions:
        """Executes a discharge drafting step with comprehension analysis."""
        protocol_str = await self.retriever.get_all_context_string(
            [ClinicalProtocol(title=p.title, summary=p.summary, source=p.source) for p in analysis.relevant_protocols]
        )
        
        try:
            # Generate discharge instructions
            discharge = await self.llm_client.generate_discharge(
                patient.json(),
                analysis.json(),
                protocol_str
            )
            
            # Analyze patient-facing text for comprehension
            comprehension_result = await self.comprehension_analyzer.analyze_and_improve(
                discharge.patient_facing
            )
            
            # Add comprehension analysis to discharge
            from ..models.responses import ComprehensionScore
            discharge.comprehension_analysis = ComprehensionScore(
                score=comprehension_result["score"],
                reading_level=comprehension_result["reading_level"],
                interpretation=comprehension_result["interpretation"],
                jargon_detected=comprehension_result["jargon_detected"],
                simplified_version=comprehension_result["simplified_version"],
                language=comprehension_result["language"],
                needs_improvement=comprehension_result["needs_improvement"]
            )
            
            return discharge
        except Exception as e:
            logger.error(f"Discharge drafting failed: {str(e)}")
            raise Exception(f"Clinical Discharge Error: {str(e)}")
