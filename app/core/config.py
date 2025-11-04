"""
Production-grade configuration management with validation
"""

from pydantic_settings import BaseSettings
from pydantic import Field, validator
from typing import List, Optional
import secrets
import os

class Settings(BaseSettings):
    """Application settings with validation and defaults"""
    
    # Application
    APP_NAME: str = "BrainOps AI Platform"
    VERSION: str = "12.0.0"
    ENVIRONMENT: str = Field(default="production", env="ENVIRONMENT")
    DEBUG: bool = Field(default=False, env="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["https://myroofgenius.com", "https://weathercraft-erp.vercel.app"],
        env="ALLOWED_ORIGINS"
    )
    
    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), env="JWT_SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, env="API_RATE_LIMIT")
    RATE_LIMIT_PERIOD: int = Field(default=60, env="API_RATE_PERIOD")
    
    # Database
    DATABASE_URL: str = Field(..., env="DATABASE_URL")
    DB_POOL_SIZE: int = Field(default=20, env="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=40, env="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # Supabase
    SUPABASE_URL: str = Field(..., env="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(..., env="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: str = Field(..., env="SUPABASE_SERVICE_KEY")
    
    # AI Providers
    OPENAI_API_KEY: Optional[str] = Field(None, env="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = Field(None, env="GOOGLE_API_KEY")
    GROQ_API_KEY: Optional[str] = Field(None, env="GROQ_API_KEY")
    PERPLEXITY_API_KEY: Optional[str] = Field(None, env="PERPLEXITY_API_KEY")
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = Field(None, env="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(None, env="STRIPE_WEBHOOK_SECRET")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", env="REDIS_URL")
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(None, env="SENTRY_DSN")
    NEW_RELIC_LICENSE_KEY: Optional[str] = Field(None, env="NEW_RELIC_LICENSE_KEY")
    
    # External Services
    SENDGRID_API_KEY: Optional[str] = Field(None, env="SENDGRID_API_KEY")
    TWILIO_ACCOUNT_SID: Optional[str] = Field(None, env="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(None, env="TWILIO_AUTH_TOKEN")
    SLACK_WEBHOOK_URL: Optional[str] = Field(None, env="SLACK_WEBHOOK_URL")
    
    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @validator("DATABASE_URL", pre=True)
    def validate_database_url(cls, v):
        if not v or v == "postgresql://user:password@host:port/database":
            raise ValueError("DATABASE_URL must be configured with actual values")
        return v
    
    @validator("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY")
    def validate_ai_keys(cls, v, field):
        if v and (v.startswith("sk-...") or v.startswith("AI...")):
            raise ValueError(f"{field.name} contains placeholder value. Use actual API key.")
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = True
        
    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"
    
    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"
    
    @property
    def has_ai_providers(self) -> bool:
        return any([
            self.OPENAI_API_KEY,
            self.ANTHROPIC_API_KEY,
            self.GOOGLE_API_KEY,
            self.GROQ_API_KEY
        ])
    
    def get_active_ai_providers(self) -> List[str]:
        providers = []
        if self.OPENAI_API_KEY:
            providers.append("openai")
        if self.ANTHROPIC_API_KEY:
            providers.append("anthropic")
        if self.GOOGLE_API_KEY:
            providers.append("google")
        if self.GROQ_API_KEY:
            providers.append("groq")
        if self.PERPLEXITY_API_KEY:
            providers.append("perplexity")
        return providers

# Singleton instance
settings = Settings()