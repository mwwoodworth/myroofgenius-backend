"""
WeatherCraft ERP Backend Configuration
Centralized configuration management with environment variables
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    """Application settings loaded from environment variables"""

    model_config = SettingsConfigDict(
        extra="ignore",
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        populate_by_name=True,
    )

    # ============================================================================
    # DATABASE
    # ============================================================================
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")
    database_pool_size: int = Field(default=50, alias="DATABASE_POOL_SIZE")
    database_max_overflow: int = Field(default=100, alias="DATABASE_MAX_OVERFLOW")
    database_pool_recycle: int = Field(default=3600, alias="DATABASE_POOL_RECYCLE")

    supabase_project_ref: Optional[str] = Field(default=None, alias="SUPABASE_PROJECT_REF")
    supabase_anon_key: Optional[str] = Field(default=None, alias="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, alias="SUPABASE_SERVICE_ROLE_KEY")

    # ============================================================================
    # AI PROVIDERS
    # ============================================================================
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    perplexity_api_key: Optional[str] = Field(default=None, alias="PERPLEXITY_API_KEY")
    elevenlabs_api_key: Optional[str] = Field(default=None, alias="ELEVENLABS_API_KEY")

    # ============================================================================
    # AUTHENTICATION
    # ============================================================================
    jwt_secret_key: Optional[str] = Field(default=None, alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(default=24, alias="JWT_EXPIRATION_HOURS")

    # ============================================================================
    # STRIPE
    # ============================================================================
    stripe_secret_key: Optional[str] = Field(default=None, alias="STRIPE_SECRET_KEY")
    stripe_publishable_key: Optional[str] = Field(default=None, alias="STRIPE_PUBLISHABLE_KEY")
    stripe_webhook_secret: Optional[str] = Field(default=None, alias="STRIPE_WEBHOOK_SECRET")

    # ============================================================================
    # RENDER DEPLOYMENT
    # ============================================================================
    render_api_key: Optional[str] = Field(default=None, alias="RENDER_API_KEY")
    render_service_id: Optional[str] = Field(default=None, alias="RENDER_SERVICE_ID")
    render_deploy_hook: Optional[str] = Field(default=None, alias="RENDER_DEPLOY_HOOK")

    # ============================================================================
    # MONITORING
    # ============================================================================
    papertrail_host: str = Field(default="logs.papertrailapp.com", alias="PAPERTRAIL_HOST")
    papertrail_port: int = Field(default=34302, alias="PAPERTRAIL_PORT")
    sentry_dsn: Optional[str] = Field(default=None, alias="SENTRY_DSN")

    # ============================================================================
    # APPLICATION
    # ============================================================================
    environment: str = Field(default="development", alias="ENVIRONMENT")
    debug: bool = Field(default=True, alias="DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")
    backend_url: str = Field(default="http://localhost:8000", alias="BACKEND_URL")
    frontend_url: str = Field(default="http://localhost:3000", alias="FRONTEND_URL")

    # CORS
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:3001",
            "http://localhost:8000",
            "http://localhost:8002",
            "https://weathercraft-erp.vercel.app",
            "https://myroofgenius.com",
            "https://brainops-backend-prod.onrender.com"
        ],
        alias="CORS_ORIGINS"
    )

    # ============================================================================
    # REDIS CACHE
    # ============================================================================
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    # ============================================================================
    # EMAIL
    # ============================================================================
    smtp_host: str = Field(default="smtp.gmail.com", alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: str = Field(default="noreply@weathercraft.com", alias="SMTP_FROM_EMAIL")

    # ============================================================================
    # WEATHER API
    # ============================================================================
    weather_api_key: Optional[str] = Field(default=None, alias="WEATHER_API_KEY")
    weather_api_url: str = Field(default="https://api.openweathermap.org/data/2.5", alias="WEATHER_API_URL")

    # ============================================================================
    # DOCKER
    # ============================================================================
    docker_username: str = Field(default="mwwoodworth", alias="DOCKER_USERNAME")
    docker_pat: Optional[str] = Field(default=None, alias="DOCKER_PAT")

    # ============================================================================
    # FEATURE FLAGS
    # ============================================================================
    enable_ai_agents: bool = Field(default=True, alias="ENABLE_AI_AGENTS")
    enable_blog_system: bool = Field(default=True, alias="ENABLE_BLOG_SYSTEM")
    enable_realtime_sync: bool = Field(default=False, alias="ENABLE_REALTIME_SYNC")
    enable_advanced_analytics: bool = Field(default=True, alias="ENABLE_ADVANCED_ANALYTICS")
    enable_webhook_processing: bool = Field(default=True, alias="ENABLE_WEBHOOK_PROCESSING")

    # ============================================================================
    # RATE LIMITING
    # ============================================================================
    rate_limit_per_minute: int = Field(default=100, alias="RATE_LIMIT_PER_MINUTE")
    rate_limit_per_hour: int = Field(default=1000, alias="RATE_LIMIT_PER_HOUR")
    rate_limit_per_day: int = Field(default=1000000, alias="RATE_LIMIT_PER_DAY")  # 1M requests/day for production
    public_rate_limit_per_minute: int = Field(default=60, alias="PUBLIC_RATE_LIMIT_PER_MINUTE")
    public_rate_limit_per_hour: int = Field(default=600, alias="PUBLIC_RATE_LIMIT_PER_HOUR")
    webhook_rate_limit_per_minute: int = Field(default=300, alias="WEBHOOK_RATE_LIMIT_PER_MINUTE")
    webhook_rate_limit_per_hour: int = Field(default=4000, alias="WEBHOOK_RATE_LIMIT_PER_HOUR")

    # ============================================================================
    # API PAGINATION
    # ============================================================================
    api_default_limit: int = Field(default=1000, alias="API_DEFAULT_LIMIT")
    api_max_limit: int = Field(default=10000, alias="API_MAX_LIMIT")

# Create global settings instance
settings = Settings()

# Helper functions
def get_database_url() -> str:
    """Get database URL from environment configuration"""
    if settings.database_url:
        return settings.database_url

    host = os.getenv("DB_HOST") or os.getenv("SUPABASE_DB_HOST")
    port = os.getenv("DB_PORT") or os.getenv("SUPABASE_DB_PORT") or "6543"
    name = os.getenv("DB_NAME") or os.getenv("SUPABASE_DB_NAME")
    user = os.getenv("DB_USER") or os.getenv("SUPABASE_DB_USER")
    password = os.getenv("DB_PASSWORD") or os.getenv("SUPABASE_DB_PASSWORD")

    if all([host, port, name, user, password]):
        return f"postgresql://{user}:{password}@{host}:{port}/{name}?sslmode=require"

    raise RuntimeError(
        "DATABASE_URL is not configured. Set DATABASE_URL or DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD in the environment."
    )

def get_ai_provider_key(provider: str) -> Optional[str]:
    """Get API key for specified AI provider"""
    provider_keys = {
        "openai": settings.openai_api_key,
        "anthropic": settings.anthropic_api_key,
        "gemini": settings.gemini_api_key,
        "perplexity": settings.perplexity_api_key,
        "elevenlabs": settings.elevenlabs_api_key
    }
    return provider_keys.get(provider.lower())

def is_production() -> bool:
    """Check if running in production environment"""
    return settings.environment.lower() in ["production", "prod"]

def is_development() -> bool:
    """Check if running in development environment"""
    return settings.environment.lower() in ["development", "dev"]

# Export settings
__all__ = ["settings", "get_database_url", "get_ai_provider_key", "is_production", "is_development"]
