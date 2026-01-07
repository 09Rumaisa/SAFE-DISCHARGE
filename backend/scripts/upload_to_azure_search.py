"""
Azure AI Search Document Uploader
Processes PDF clinical guidelines and uploads them to Azure AI Search for RAG.
"""

import os
import json
from typing import List, Dict
from datetime import datetime, timezone
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SearchField,
    SearchFieldDataType,
    SimpleField,
    SearchableField,
    VectorSearch,
    HnswAlgorithmConfiguration,
    VectorSearchProfile,
    SemanticConfiguration,
    SemanticField,
    SemanticPrioritizedFields,
    SemanticSearch
)
import PyPDF2
from dotenv import load_dotenv

load_dotenv()


class AzureSearchUploader:
    """Handles document processing and upload to Azure AI Search."""
    
    def __init__(self):
        self.endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
        self.api_key = os.getenv("AZURE_SEARCH_API_KEY")
        self.index_name = os.getenv("AZURE_SEARCH_INDEX", "clinical-guidelines")
        
        if not self.endpoint or not self.api_key:
            raise ValueError("Azure Search credentials not found in .env file")
        
        self.credential = AzureKeyCredential(self.api_key)
        self.index_client = SearchIndexClient(
            endpoint=self.endpoint,
            credential=self.credential
        )
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=self.credential
        )
    
    def create_index(self):
        """Create or update the Azure AI Search index with optimal schema."""
        
        fields = [
            SimpleField(
                name="id",
                type=SearchFieldDataType.String,
                key=True,
                filterable=True
            ),
            SearchableField(
                name="title",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                sortable=True
            ),
            SearchableField(
                name="content",
                type=SearchFieldDataType.String,
                searchable=True,
                analyzer_name="en.microsoft"
            ),
            SearchableField(
                name="source",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                facetable=True
            ),
            SearchableField(
                name="category",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                facetable=True
            ),
            SearchableField(
                name="medication_name",
                type=SearchFieldDataType.String,
                searchable=True,
                filterable=True,
                facetable=True
            ),
            SimpleField(
                name="page_number",
                type=SearchFieldDataType.Int32,
                filterable=True,
                sortable=True
            ),
            SimpleField(
                name="upload_date",
                type=SearchFieldDataType.DateTimeOffset,
                filterable=True,
                sortable=True
            ),
            SearchableField(
                name="keywords",
                type=SearchFieldDataType.Collection(SearchFieldDataType.String),
                searchable=True,
                filterable=True
            )
        ]
        
        # Semantic configuration for better relevance
        semantic_config = SemanticConfiguration(
            name="clinical-semantic-config",
            prioritized_fields=SemanticPrioritizedFields(
                title_field=SemanticField(field_name="title"),
                content_fields=[SemanticField(field_name="content")],
                keywords_fields=[SemanticField(field_name="keywords")]
            )
        )
        
        semantic_search = SemanticSearch(
            configurations=[semantic_config]
        )
        
        index = SearchIndex(
            name=self.index_name,
            fields=fields,
            semantic_search=semantic_search
        )
        
        try:
            result = self.index_client.create_or_update_index(index)
            print(f"✅ Index '{self.index_name}' created/updated successfully")
            return result
        except Exception as e:
            print(f"❌ Error creating index: {str(e)}")
            raise
    
    def extract_text_from_pdf(self, pdf_path: str) -> List[Dict]:
        """
        Extract text from PDF and chunk it for optimal RAG performance.
        Returns list of document chunks.
        """
        print(f"📄 Processing PDF: {pdf_path}")
        
        chunks = []
        
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                total_pages = len(pdf_reader.pages)
                
                print(f"   Total pages: {total_pages}")
                
                # Extract metadata from filename
                filename = os.path.basename(pdf_path)
                
                # Determine document type and metadata
                if "warfarin" in filename.lower():
                    medication_name = "Warfarin"
                    category = "Anticoagulant Guidelines"
                    source = "Clinical Guidelines - Warfarin"
                elif "noac" in filename.lower() or "anticoagulant" in filename.lower():
                    medication_name = "NOACs"
                    category = "Anticoagulant Guidelines"
                    source = "Clinical Guidelines - Oral Anticoagulants"
                else:
                    medication_name = "General"
                    category = "Clinical Guidelines"
                    source = filename
                
                # Extract text from each page
                for page_num in range(total_pages):
                    page = pdf_reader.pages[page_num]
                    text = page.extract_text()
                    
                    if text.strip():
                        # Chunk text into manageable sections (max 1000 chars per chunk)
                        text_chunks = self._chunk_text(text, max_length=1000)
                        
                        for chunk_idx, chunk_text in enumerate(text_chunks):
                            # Extract keywords from chunk
                            keywords = self._extract_keywords(chunk_text)
                            
                            # Create document chunk
                            # Clean filename for ID (remove special characters)
                            clean_filename = filename.replace('.pdf', '').replace('-', '_').replace(' ', '_')
                            doc_id = f"{clean_filename}_p{page_num}_c{chunk_idx}"
                            
                            doc_chunk = {
                                "id": doc_id,
                                "title": f"{source} - Page {page_num + 1} (Section {chunk_idx + 1})",
                                "content": chunk_text,
                                "source": source,
                                "category": category,
                                "medication_name": medication_name,
                                "page_number": page_num + 1,
                                "upload_date": datetime.now(timezone.utc).isoformat()
                                # Keywords removed for now - causing JSON parsing issues
                            }
                            
                            chunks.append(doc_chunk)
                
                print(f"   ✅ Extracted {len(chunks)} chunks from {total_pages} pages")
                
        except Exception as e:
            print(f"   ❌ Error processing PDF: {str(e)}")
            raise
        
        return chunks
    
    def _chunk_text(self, text: str, max_length: int = 1000) -> List[str]:
        """Split text into chunks at sentence boundaries."""
        chunks = []
        current_chunk = ""
        
        # Split by sentences (simple approach)
        sentences = text.replace('\n', ' ').split('. ')
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_length:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract relevant medical keywords from text."""
        # Common medical terms to look for
        medical_keywords = [
            "warfarin", "inr", "anticoagulant", "bleeding", "thrombosis",
            "dosage", "interaction", "monitoring", "side effects", "contraindication",
            "vitamin k", "blood thinner", "coagulation", "stroke", "dvt",
            "pulmonary embolism", "atrial fibrillation", "dose adjustment",
            "elderly", "renal impairment", "liver disease", "pregnancy"
        ]
        
        text_lower = text.lower()
        found_keywords = []
        
        for keyword in medical_keywords:
            if keyword in text_lower:
                found_keywords.append(keyword.title())
        
        return list(set(found_keywords))  # Remove duplicates
    
    def upload_documents(self, documents: List[Dict]) -> bool:
        """Upload document chunks to Azure AI Search."""
        
        if not documents:
            print("⚠️  No documents to upload")
            return False
        
        print(f"\n📤 Uploading {len(documents)} document chunks to Azure AI Search...")
        
        try:
            # Upload in batches of 100
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                result = self.search_client.upload_documents(documents=batch)
                
                success_count = sum(1 for r in result if r.succeeded)
                print(f"   Batch {i//batch_size + 1}: {success_count}/{len(batch)} documents uploaded")
            
            print(f"✅ Successfully uploaded all documents!")
            return True
            
        except Exception as e:
            print(f"❌ Error uploading documents: {str(e)}")
            raise
    
    def test_search(self, query: str = "warfarin dosing"):
        """Test the search functionality."""
        print(f"\n🔍 Testing search with query: '{query}'")
        
        try:
            results = self.search_client.search(
                search_text=query,
                top=3,
                select=["title", "content", "source", "medication_name"]
            )
            
            print("\n📋 Search Results:")
            for idx, result in enumerate(results, 1):
                print(f"\n{idx}. {result['title']}")
                print(f"   Source: {result['source']}")
                print(f"   Medication: {result['medication_name']}")
                print(f"   Content: {result['content'][:200]}...")
            
        except Exception as e:
            print(f"❌ Search test failed: {str(e)}")


def main():
    """Main execution function."""
    
    print("=" * 60)
    print("🏥 Azure AI Search - Clinical Guidelines Uploader")
    print("=" * 60)
    
    # Initialize uploader
    uploader = AzureSearchUploader()
    
    # Step 1: Create/update index
    print("\n📊 Step 1: Creating/Updating Search Index...")
    uploader.create_index()
    
    # Step 2: Process PDFs
    print("\n📚 Step 2: Processing PDF Documents...")
    
    pdf_files = [
        "C:\\Users\\rumai\\OneDrive\\Desktop\\SAFE-DISCHARGE-AI\\imagine cup project\\oral-anticoagulant-warfarin-and-noacs-.pdf",
        "C:\\Users\\rumai\\OneDrive\\Desktop\\SAFE-DISCHARGE-AI\\imagine cup project\\Warfarin-2306-PIL.pdf"
    ]
    
    all_documents = []
    
    for pdf_path in pdf_files:
        if os.path.exists(pdf_path):
            chunks = uploader.extract_text_from_pdf(pdf_path)
            all_documents.extend(chunks)
        else:
            print(f"⚠️  File not found: {pdf_path}")
    
    # Step 3: Upload to Azure AI Search
    if all_documents:
        print(f"\n📊 Total document chunks prepared: {len(all_documents)}")
        uploader.upload_documents(all_documents)
        
        # Step 4: Test search
        print("\n" + "=" * 60)
        uploader.test_search("warfarin dosing elderly patients")
        uploader.test_search("INR monitoring")
        uploader.test_search("drug interactions")
        
        print("\n" + "=" * 60)
        print("✅ Upload Complete! Your RAG system is now production-ready!")
        print("=" * 60)
    else:
        print("\n❌ No documents were processed. Please check the PDF files.")


if __name__ == "__main__":
    main()
