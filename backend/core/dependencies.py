"""
Dependency injection for FastAPI.
"""

from functools import lru_cache
from ..services.knowledge_base import ClinicalRetriever
from ..services.llm_client import LLMClient
from ..services.orchestrator import ClinicalOrchestrator

@lru_cache()
def get_retriever() -> ClinicalRetriever:
    return ClinicalRetriever()

@lru_cache()
def get_llm_client() -> LLMClient:
    return LLMClient()

def get_orchestrator() -> ClinicalOrchestrator:
    # We don't cache orchestrator to ensure fresh state if needed,
    # though with LangGraph the graph itself is static.
    return ClinicalOrchestrator(
        retriever=get_retriever(),
        llm_client=get_llm_client()
    )
