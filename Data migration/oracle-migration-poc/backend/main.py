"""
FastAPI Main Application
Oracle Database Migration POC with Agentic AI
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import logging
import structlog
from dotenv import load_dotenv
import os

# Load environment variables early so imported modules can read them
load_dotenv()

# Import routers
from api import migration, schema, validation, discovery

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
structlog.configure(
    wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
)

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    logger.info("Starting Oracle Migration POC API")
    logger.info(f"Mock Mode: {os.getenv('ENABLE_MOCK_MODE', 'false')}")
    yield
    # Shutdown
    logger.info("Shutting down Oracle Migration POC API")


# Create FastAPI application
app = FastAPI(
    title="Oracle Database Migration API",
    description="Agentic AI-powered Oracle Database Migration Platform",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Oracle Database Migration API",
        "version": "1.0.0",
        "status": "active",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "azure_openai_configured": bool(os.getenv("AZURE_OPENAI_API_KEY")),
        "mock_mode": os.getenv("ENABLE_MOCK_MODE", "false").lower() == "true"
    }


# Include routers
app.include_router(migration.router, prefix="/api/migration", tags=["Migration"])
app.include_router(schema.router, prefix="/api/schema", tags=["Schema"])
app.include_router(validation.router, prefix="/api/validation", tags=["Validation"])
app.include_router(discovery.router, prefix="/api/discovery", tags=["Discovery"])


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("LOG_LEVEL") == "DEBUG" else "An error occurred"
        }
    )


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("BACKEND_PORT", 8000))
    uvicorn.run(
        "main:app",
        host=os.getenv("BACKEND_HOST", "0.0.0.0"),
        port=port,
        reload=True
    )
