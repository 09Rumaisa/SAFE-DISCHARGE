"""
Test script to verify Azure AI Search integration is working.
Run this to confirm Azure Search is being used actively.
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add backend directory to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path.parent))
sys.path.insert(0, str(backend_path))

# Configure logging
logging.basicConfig(level=logging.INFO)

# Now import after path is set
try:
    from backend.config import get_settings
    from backend.services.knowledge_base import ClinicalRetriever
except ImportError:
    # Fallback if running from different location
    from config import get_settings
    from services.knowledge_base import ClinicalRetriever


async def test_azure_search():
    """Test Azure AI Search connectivity and retrieval."""
    
    print("=" * 60)
    print("AZURE AI SEARCH INTEGRATION TEST")
    print("=" * 60)
    
    # Load configuration
    settings = get_settings()
    print("\n1. Configuration Check:")
    print(f"   - Azure Search Endpoint: {settings.azure_search_endpoint}")
    print(f"   - Azure Search Index: {settings.azure_search_index}")
    print(f"   - API Key configured: {'✓' if settings.azure_search_api_key else '✗'}")
    
    # Initialize retriever
    print("\n2. Initializing ClinicalRetriever...")
    retriever = ClinicalRetriever()
    
    if retriever.use_mock:
        print("   ⚠️  WARNING: Using MOCK data (Azure Search not connected)")
        print("   Possible reasons:")
        print("   - Azure credentials not configured")
        print("   - Azure Search service not reachable")
        print("   - Invalid endpoint or API key")
    else:
        print("   ✓ Successfully connected to Azure AI Search")
    
    # Test retrieval
    print("\n3. Testing Clinical Guideline Retrieval...")
    test_queries = [
        "anticoagulation INR warfarin",
        "thromboembolism VTE prevention",
        "patient discharge instructions"
    ]
    
    for query in test_queries:
        print(f"\n   Query: '{query}'")
        try:
            results = await retriever.search(query)
            print(f"   Results found: {len(results)}")
            if results:
                for i, result in enumerate(results[:2], 1):
                    print(f"     {i}. {result.title}")
                    if hasattr(result, 'source'):
                        print(f"        Source: {result.source}")
        except Exception as e:
            print(f"   ✗ Error: {str(e)}")
    
    # Verify active usage
    print("\n4. Verification Summary:")
    print(f"   Azure Search Mode: {'Active' if not retriever.use_mock else 'Mock/Fallback'}")
    print(f"   Source: {'Azure AI Search' if not retriever.use_mock else 'Local Mock Data'}")
    
    if not retriever.use_mock:
        print("\n✅ RESULT: Azure AI Search is ACTIVELY being used")
        print("\nAzure AI Search is being used for:")
        print("- Retrieving clinical guidelines and protocols")
        print("- Supporting RAG (Retrieval Augmented Generation)")
        print("- Providing evidence-based recommendations in analysis")
    else:
        print("\n❌ RESULT: Azure AI Search is NOT connected")
        print("\nTo activate Azure AI Search:")
        print("1. Set environment variables:")
        print("   - AZURE_SEARCH_ENDPOINT")
        print("   - AZURE_SEARCH_API_KEY")
        print("   - AZURE_SEARCH_INDEX")
        print("\n2. Or update .env file with your Azure Search credentials")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_azure_search())
