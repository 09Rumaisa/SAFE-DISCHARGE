"""
Quick script to delete existing index and recreate with new schema.
Run this if you need to change the index structure.
"""

import os
from azure.core.credentials import AzureKeyCredential
from azure.search.documents.indexes import SearchIndexClient
from dotenv import load_dotenv

load_dotenv()

def delete_and_recreate_index():
    endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
    api_key = os.getenv("AZURE_SEARCH_API_KEY")
    index_name = os.getenv("AZURE_SEARCH_INDEX", "clinical-guidelines")
    
    credential = AzureKeyCredential(api_key)
    index_client = SearchIndexClient(endpoint=endpoint, credential=credential)
    
    print(f"🗑️  Deleting existing index: {index_name}")
    
    try:
        index_client.delete_index(index_name)
        print(f"✅ Index '{index_name}' deleted successfully")
        print("\n✨ Now run the upload script again to create the new index!")
        print("   python backend\\scripts\\upload_to_azure_search.py")
    except Exception as e:
        if "not found" in str(e).lower():
            print(f"ℹ️  Index '{index_name}' doesn't exist (nothing to delete)")
        else:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    delete_and_recreate_index()
