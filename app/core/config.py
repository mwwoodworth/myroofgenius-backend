"""
Production-grade configuration management with validation
"""

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from typing import List, Optional
import secrets

class Settings(BaseSettings):
    """Application settings with validation and defaults"""

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
        populate_by_name=True,
        extra="ignore",
    )
    
    # Application
    APP_NAME: str = "BrainOps AI Platform"
    VERSION: str = "12.0.0"
    ENVIRONMENT: str = Field(default="production", alias="ENVIRONMENT")
    DEBUG: bool = Field(default=False, alias="DEBUG")
    LOG_LEVEL: str = Field(default="INFO", alias="LOG_LEVEL")
    
    # API Configuration
    API_V1_STR: str = "/api/v1"
    BACKEND_CORS_ORIGINS: List[str] = Field(
        default=["https://myroofgenius.com", "https://weathercraft-erp.vercel.app"],
        alias="ALLOWED_ORIGINS"
    )
    
    # Security
    SECRET_KEY: str = Field(default_factory=lambda: secrets.token_urlsafe(32), alias="JWT_SECRET_KEY")
    ALGORITHM: str = Field(default="HS256", alias="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, alias="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=100, alias="API_RATE_LIMIT")
    RATE_LIMIT_PERIOD: int = Field(default=60, alias="API_RATE_PERIOD")
    
    # Database
    DATABASE_URL: str = Field(..., alias="DATABASE_URL")
    DB_POOL_SIZE: int = Field(default=20, alias="DB_POOL_SIZE")
    DB_MAX_OVERFLOW: int = Field(default=40, alias="DB_MAX_OVERFLOW")
    DB_POOL_TIMEOUT: int = Field(default=30, alias="DB_POOL_TIMEOUT")
    
    # Supabase
    SUPABASE_URL: str = Field(..., alias="SUPABASE_URL")
    SUPABASE_ANON_KEY: str = Field(..., alias="SUPABASE_ANON_KEY")
    SUPABASE_SERVICE_KEY: str = Field(..., alias="SUPABASE_SERVICE_KEY")
    
    # AI Providers
    OPENAI_API_KEY: Optional[str] = Field(None, alias="OPENAI_API_KEY")
    ANTHROPIC_API_KEY: Optional[str] = Field(None, alias="ANTHROPIC_API_KEY")
    GOOGLE_API_KEY: Optional[str] = Field(None, alias="GOOGLE_API_KEY")
    GROQ_API_KEY: Optional[str] = Field(None, alias="GROQ_API_KEY")
    PERPLEXITY_API_KEY: Optional[str] = Field(None, alias="PERPLEXITY_API_KEY")
    
    # Stripe
    STRIPE_SECRET_KEY: Optional[str] = Field(None, alias="STRIPE_SECRET_KEY")
    STRIPE_WEBHOOK_SECRET: Optional[str] = Field(None, alias="STRIPE_WEBHOOK_SECRET")
    
    # Redis
    REDIS_URL: str = Field(default="redis://localhost:6379", alias="REDIS_URL")
    
    # Monitoring
    SENTRY_DSN: Optional[str] = Field(None, alias="SENTRY_DSN")
    NEW_RELIC_LICENSE_KEY: Optional[str] = Field(None, alias="NEW_RELIC_LICENSE_KEY")
    
    # External Services
    SENDGRID_API_KEY: Optional[str] = Field(None, alias="SENDGRID_API_KEY")
    TWILIO_ACCOUNT_SID: Optional[str] = Field(None, alias="TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN: Optional[str] = Field(None, alias="TWILIO_AUTH_TOKEN")
    SLACK_WEBHOOK_URL: Optional[str] = Field(None, alias="SLACK_WEBHOOK_URL")
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            return [i.strip() for i in v.split(",")]
        return v
    
    @field_validator("DATABASE_URL", mode="before")
    def validate_database_url(cls, v):
        if not v or v == "postgresql://user:<DB_PASSWORD_REDACTED>@host:port/database":
            raise ValueError("DATABASE_URL must be configured with actual values")
        return v
    
    @field_validator("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY", "GROQ_API_KEY")
    def validate_ai_keys(cls, v, info):
        if v and (v.startswith("sk-...") or v.startswith("AI...")):
            raise ValueError(f"{info.field_name} contains placeholder value. Use actual API key.")
        return v
        
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
