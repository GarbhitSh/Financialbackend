from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from sqlalchemy import text
import uvicorn
import logging
import time
from typing import Callable

from app.database import get_db, create_tables
from app.routers import screens, auth, stocks
from app.config import settings
from app.tasks.stock_sync import start_stock_sync

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=True
)

app = FastAPI(
    title=settings.APP_NAME,
    description="API for creating and executing financial screening criteria",
    version=settings.APP_VERSION,
    docs_url=settings.DOCS_URL,
    redoc_url=settings.REDOC_URL,
    openapi_url=settings.OPENAPI_URL,
)

# Middleware for request timing
@app.middleware("http")
async def add_process_time_header(request: Request, call_next: Callable):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception handler caught: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "Internal server error"}
    )

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=settings.CORS_ALLOW_METHODS,
    allow_headers=settings.CORS_ALLOW_HEADERS,
)

# Add trusted host middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]  # Configure this based on your deployment environment
)

# Include routers with versioned prefix
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)
app.include_router(
    screens.router,
    prefix=f"{settings.API_V1_PREFIX}/screens",
    tags=["Screens"]
)
app.include_router(
    stocks.router,
    prefix=f"{settings.API_V1_PREFIX}/stocks",
    tags=["Stocks"]
)

@app.on_event("startup")
async def startup_event():
    """
    Initialize application on startup
    """
    try:
        logger.info("Initializing application...")
        create_tables()
        logger.info("Database tables created successfully")
        logger.info("Starting stock sync tasks...")
        start_stock_sync()
        logger.info("Stock sync tasks started successfully")
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}")
        raise

@app.on_event("shutdown")
async def shutdown_event():
    """
    Cleanup on application shutdown
    """
    logger.info("Shutting down application...")

@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint with database connection test
    """
    try:
        # Test database connection
        db: Session = next(get_db())
        db.execute(text("SELECT 1"))
        db.commit()
        
        return {
            "status": "healthy",
            "version": settings.APP_VERSION,
            "database": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        workers=1,
        log_level="info"
    )
