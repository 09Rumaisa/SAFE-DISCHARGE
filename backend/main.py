"""
Main Entry Point for the AI Safety Copilot API.
"""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .api.endpoints import router as clinical_router
from .api.db_endpoints import router as db_router
from .config import get_settings
from .database import register_db_events

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Backend for AI Safety Copilot - Clinical RAG system",
    docs_url="/docs"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register database events
register_db_events(app)

# Register routers
app.include_router(clinical_router)
app.include_router(db_router)

@app.get("/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "version": settings.app_version,
        "clinical_engine": "active",
        "database": "connected"
    }

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
