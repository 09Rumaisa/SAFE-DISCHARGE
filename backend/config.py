"""
Configuration settings for the AI Safety Copilot.
Uses Pydantic settings for environment variable management.
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from functools import lru_cache


class Settings(BaseSettings):
    """Application configuration with environment variable support."""
    
    # API Settings
    app_name: str = "AI Safety Copilot"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, description="Enable debug mode")
    
    # OpenAI Configuration (Deprecated - use Azure OpenAI instead)
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key (leave empty if using Azure OpenAI)"
    )
    openai_model: str = Field(
        default="gpt-4",
        description="OpenAI model name (e.g., gpt-4, gpt-3.5-turbo)"
    )
    
    # Azure OpenAI Configuration
    use_azure_openai: bool = Field(
        default=True,
        description="Use Azure OpenAI instead of regular OpenAI"
    )
    azure_openai_endpoint: str = Field(
        default="https://your-resource.openai.azure.com/",
        description="Azure OpenAI endpoint URL"
    )
    azure_openai_api_key: str = Field(
        default="your-azure-openai-key",
        description="Azure OpenAI API key"
    )
    azure_openai_deployment: str = Field(
        default="gpt-4",
        description="Azure OpenAI deployment name (e.g., gpt-4, gpt-4-turbo)"
    )
    azure_openai_api_version: str = Field(
        default="2024-02-15-preview",
        description="Azure OpenAI API version"
    )
    
    # Azure AI Search Configuration (for future integration)
    azure_search_endpoint: str = Field(
        default="https://your-search.search.windows.net",
        description="Azure AI Search endpoint"
    )
    azure_search_api_key: str = Field(
        default="your-search-key",
        description="Azure AI Search API key"
    )
    azure_search_index: str = Field(
        default="clinical-guidelines",
        description="Azure AI Search index name"
    )
    
    # RAG Configuration
    max_context_tokens: int = Field(
        default=4000,
        description="Maximum tokens for context window"
    )
    top_k_results: int = Field(
        default=5,
        description="Number of top results to retrieve"
    )
    similarity_threshold: float = Field(
        default=0.7,
        description="Minimum similarity score for retrieval"
    )
    
    # Clinical Safety Configuration
    enable_audit_logging: bool = Field(
        default=True,
        description="Enable audit logging for clinical decisions"
    )
    require_citations: bool = Field(
        default=True,
        description="Require citations for all recommendations"
    )
    
    # Database Configuration
    database_url: str = Field(
        default="sqlite://db.sqlite3",
        description="Database connection URL (PostgreSQL or SQLite)"
    )
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
