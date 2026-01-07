"""
Simple test upload to diagnose the issue
"""

import os
from datetime import datetime, timezone
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from dotenv import load_dotenv

load_dotenv()

endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
api_key = os.getenv("AZURE_SEARCH_API_KEY")
index_name = os.getenv("AZURE_SEARCH_INDEX", "clinical-guidelines")

credential = AzureKeyCredential(api_key)
search_client = SearchClient(endpoint=endpoint, index_name=index_name, credential=credential)

# Create a simple test document WITHOUT keywords
test_doc = {
    "id": "test_doc_1",
    "title": "Test Warfarin Guideline",
    "content": "Warfarin requires INR monitoring. Target INR for atrial fibrillation is 2.0-3.0.",
    "source": "Test Source",
    "category": "Anticoagulant Guidelines",
    "medication_name": "Warfarin",
    "page_number": 1,
    "upload_date": datetime.now(timezone.utc).isoformat()
    # Removed keywords to test
}

print("Testing upload of single document (without keywords)...")
print(f"Document: {test_doc}")

try:
    result = search_client.upload_documents(documents=[test_doc])
    print(f"✅ Upload successful!")
    for r in result:
        print(f"   Status: {r.succeeded}, Key: {r.key}")
except Exception as e:
    print(f"❌ Upload failed: {str(e)}")
    import traceback
    traceback.print_exc()
