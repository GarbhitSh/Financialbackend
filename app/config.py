from pydantic_settings import BaseSettings
from typing import List, Optional
import os
from dotenv import load_dotenv
import secrets
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

class Settings(BaseSettings):
    # Application settings
    APP_NAME: str = "Financial Screener"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Database settings
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./financial_screener.db"
    )
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", "5"))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", "10"))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", "30"))
    DB_POOL_RECYCLE: int = int(os.getenv("DB_POOL_RECYCLE", "1800"))
    
    # Security settings
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        secrets.token_urlsafe(32)  # Generate a secure random key if not provided
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
    )
    
    # Password policy
    MIN_PASSWORD_LENGTH: int = 8
    REQUIRE_SPECIAL_CHAR: bool = True
    REQUIRE_NUMBER: bool = True
    REQUIRE_UPPERCASE: bool = True
    REQUIRE_LOWERCASE: bool = True
    
    # CORS settings
    CORS_ORIGINS: List[str] = [
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,https://localhost:3000"
        ).split(",")
    ]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # API documentation
    API_V1_PREFIX: str = "/api/v1"
    DOCS_URL: Optional[str] = "/docs"
    REDOC_URL: Optional[str] = "/redoc"
    OPENAPI_URL: Optional[str] = "/openapi.json"
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Validate configuration
        self._validate_settings()
    
    def _validate_settings(self):
        """Validate critical configuration settings"""
        try:
            # Check if SECRET_KEY is secure enough
            if len(self.SECRET_KEY) < 32:
                logger.warning("SECRET_KEY is too short. Generating a new one...")
                self.SECRET_KEY = secrets.token_urlsafe(32)
            
            # Validate database URL
            if not self.DATABASE_URL:
                raise ValueError("DATABASE_URL must be set")
            
            # Validate CORS origins
            if not self.CORS_ORIGINS:
                logger.warning("No CORS origins specified. API may be inaccessible from frontend applications.")
            
            logger.info("Configuration validated successfully")
            
        except Exception as e:
            logger.error(f"Configuration validation error: {str(e)}")
            raise

settings = Settings()

# Log non-sensitive configuration details
logger.info(f"Application Name: {settings.APP_NAME}")
logger.info(f"Version: {settings.APP_VERSION}")
logger.info(f"Debug Mode: {settings.DEBUG}")
logger.info(f"API Prefix: {settings.API_V1_PREFIX}")
logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
