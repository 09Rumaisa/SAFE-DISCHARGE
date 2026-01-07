"""
Database configuration and initialization for Tortoise ORM.
"""

from tortoise import Tortoise
from fastapi import FastAPI
import logging
from .config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Get database URL from settings
DATABASE_URL = settings.database_url

# Database configuration
TORTOISE_ORM = {
    "connections": {
        "default": DATABASE_URL
    },
    "apps": {
        "models": {
            "models": ["backend.models.database", "aerich.models"],
            "default_connection": "default",
        }
    },
}


async def init_db(app: FastAPI) -> None:
    """Initialize database connection."""
    try:
        await Tortoise.init(
            db_url=DATABASE_URL,
            modules={"models": ["backend.models.database"]}
        )
        await Tortoise.generate_schemas()
        
        db_type = "PostgreSQL" if "postgres" in DATABASE_URL else "SQLite"
        logger.info(f"✅ Database initialized successfully ({db_type})")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {str(e)}")
        raise


async def close_db() -> None:
    """Close database connections."""
    await Tortoise.close_connections()
    logger.info("Database connections closed")


def register_db_events(app: FastAPI) -> None:
    """Register database startup and shutdown events."""
    
    @app.on_event("startup")
    async def startup_event():
        await init_db(app)
    
    @app.on_event("shutdown")
    async def shutdown_event():
        await close_db()
