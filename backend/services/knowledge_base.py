"""
Azure AI Search Knowledge Base service.
Retrieves clinical guidelines from Azure AI Search for RAG.
"""

import os
import logging
from typing import List
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from ..models.responses import ClinicalProtocol
from ..config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class ClinicalRetriever:
    """
    Production retriever using Azure AI Search for clinical guidelines.
    Supports semantic search and hybrid retrieval.
    """
    
    def __init__(self):
        """Initialize Azure AI Search client."""
        try:
            self.endpoint = settings.azure_search_endpoint
            self.api_key = settings.azure_search_api_key
            self.index_name = settings.azure_search_index
            
            if not self.endpoint or not self.api_key:
                logger.warning("Azure Search credentials not configured, using mock data")
                self.use_mock = True
                self._init_mock_data()
            else:
                self.credential = AzureKeyCredential(self.api_key)
                self.search_client = SearchClient(
                    endpoint=self.endpoint,
                    index_name=self.index_name,
                    credential=self.credential
                )
                self.use_mock = False
                logger.info(f"✅ Connected to Azure AI Search: {self.index_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize Azure Search: {str(e)}")
            logger.warning("Falling back to mock data")
            self.use_mock = True
            self._init_mock_data()
    
    def _init_mock_data(self):
        """Initialize mock guidelines for fallback."""
        self.guidelines = [
            {
                "topic": "Warfarin",
                "keywords": ["warfarin", "anticoagulant", "inr", "bleeding", "interaction"],
                "content": "NICE Guidelines [KTT21]: Warfarin management requires careful INR monitoring. Target INR for AF is 2.5. INR > 3.0 increases major bleeding risk. Significant interactions include Cranberry juice, NSAIDs, and certain antibiotics (e.g., Erythromycin). Avoid sudden dietary changes in Vitamin K intake.",
                "source": "NICE KTT21"
            },
            {
                "topic": "Sepsis",
                "keywords": ["sepsis", "red flag", "infection", "fever", "hypotension", "tachycardia"],
                "content": "NHS Sepsis Lead: Sepsis Red Flags include: Systolic BP < 90mmHg, Heart Rate > 130bpm, Resp Rate > 25/min, Lactate > 2mmol/L, New onset confusion, or Non-blanching rash. Sepsis is a medical emergency requiring 'Sepsis Six' within 1 hour.",
                "source": "NHS Sepsis Trust / NICE NG51"
            },
            {
                "topic": "NSAIDs",
                "keywords": ["nsaid", "ibuprofen", "naproxen", "bleeding", "gastric", "renal"],
                "content": "NICE NG6: Avoid NSAIDs in patients with history of GI bleeding or renal impairment. NSAIDs increase the risk of GI ulceration and can interact with anticoagulants like warfarin to significantly raise hemorrhage risk.",
                "source": "NICE NG6"
            }
        ]
    
    async def search(self, query: str, top_k: int = 5) -> List[ClinicalProtocol]:
        """
        Search for relevant clinical guidelines.
        Uses Azure AI Search if available, otherwise falls back to mock data.
        """
        logger.info(f"🔍 Searching for: {query}")
        
        if self.use_mock:
            return await self._search_mock(query, top_k)
        else:
            return await self._search_azure(query, top_k)
    
    async def _search_azure(self, query: str, top_k: int = 5) -> List[ClinicalProtocol]:
        """Search using Azure AI Search with semantic ranking."""
        try:
            # Perform hybrid search (keyword + semantic)
            results = self.search_client.search(
                search_text=query,
                top=top_k,
                select=["title", "content", "source", "medication_name", "category"],
                query_type="semantic",
                semantic_configuration_name="clinical-semantic-config"
            )
            
            protocols = []
            for result in results:
                protocol = ClinicalProtocol(
                    title=result.get("title", "Clinical Guideline"),
                    summary=result.get("content", ""),
                    source=result.get("source", "Azure AI Search")
                )
                protocols.append(protocol)
                logger.info(f"   ✅ Found: {protocol.title[:50]}...")
            
            if not protocols:
                logger.warning("No results found in Azure Search, using mock data")
                return await self._search_mock(query, top_k)
            
            logger.info(f"   📊 Retrieved {len(protocols)} guidelines from Azure AI Search")
            return protocols
            
        except Exception as e:
            logger.error(f"Azure Search error: {str(e)}")
            logger.warning("Falling back to mock data")
            return await self._search_mock(query, top_k)
    
    async def _search_mock(self, query: str, top_k: int = 5) -> List[ClinicalProtocol]:
        """Fallback mock search using keyword matching."""
        logger.info("   Using mock knowledge base")
        
        relevant = []
        query_lower = query.lower()
        
        for g in self.guidelines:
            # Check if any keyword or topic matches
            if g["topic"].lower() in query_lower or any(k in query_lower for k in g["keywords"]):
                relevant.append(
                    ClinicalProtocol(
                        title=g["topic"],
                        summary=g["content"],
                        source=g["source"]
                    )
                )
        
        logger.info(f"   📊 Retrieved {len(relevant)} guidelines from mock data")
        return relevant[:top_k]
    
    async def get_all_context_string(self, protocols: List[ClinicalProtocol]) -> str:
        """Format protocols for LLM context."""
        if not protocols:
            return "No relevant clinical guidelines found."
        
        context_parts = []
        for p in protocols:
            context_parts.append(f"SOURCE: {p.source}\nPROTOCOL: {p.title}\nCONTENT: {p.summary}")
        
        return "\n\n---\n\n".join(context_parts)
    
    def test_connection(self) -> bool:
        """Test Azure AI Search connection."""
        if self.use_mock:
            logger.info("⚠️  Using mock data (Azure Search not configured)")
            return False
        
        try:
            # Try a simple search
            results = self.search_client.search(search_text="test", top=1)
            list(results)  # Force execution
            logger.info("✅ Azure AI Search connection successful")
            return True
        except Exception as e:
            logger.error(f"❌ Azure AI Search connection failed: {str(e)}")
            return False
