#!/usr/bin/env python3
"""
Settings Configuration Module
Loads environment variables using pydantic and python-dotenv
"""

from typing import Optional
from functools import lru_cache
from pathlib import Path

# Try importing pydantic v2, fallback to v1
try:
    from pydantic_settings import BaseSettings
    from pydantic import Field
    PYDANTIC_V2 = True
except ImportError:
    try:
        from pydantic import BaseSettings, Field
        PYDANTIC_V2 = False
    except ImportError:
        raise ImportError(
            "pydantic is required. Install with: pip install pydantic pydantic-settings"
        )

# Load environment variables
try:
    from dotenv import load_dotenv
    # Load from project root .env file
    env_file = Path(__file__).parent.parent.parent / ".env"
    load_dotenv(env_file)
except ImportError:
    print("⚠️ python-dotenv not installed. Using system environment variables only.")


# ==============================================
# SETTINGS CLASS
# ==============================================

if PYDANTIC_V2:
    class Settings(BaseSettings):
        """
        Application settings loaded from environment variables
        Uses pydantic v2 BaseSettings
        """
        
        # API Keys
        gemini_api_key: Optional[str] = Field(
            default=None,
            description="Google Gemini API key for AI analysis"
        )
        sendgrid_api_key: Optional[str] = Field(
            default=None,
            description="SendGrid API key for email notifications"
        )
        
        # Database
        database_url: str = Field(
            default="sqlite:///./violations.db",
            description="Database connection URL"
        )
        
        # Supabase (Optional Cloud Sync)
        supabase_url: Optional[str] = Field(
            default=None,
            description="Supabase project URL for cloud sync"
        )
        supabase_key: Optional[str] = Field(
            default=None,
            description="Supabase anon API key"
        )
        
        # Application Settings
        app_name: str = Field(
            default="Traffic Violation Detection",
            description="Application name"
        )
        app_version: str = Field(
            default="1.0.0",
            description="Application version"
        )
        debug: bool = Field(
            default=False,
            description="Debug mode (development)"
        )
        
        # API Server Settings
        api_host: str = Field(
            default="0.0.0.0",
            description="API server host"
        )
        api_port: int = Field(
            default=8000,
            description="API server port"
        )
        
        # ML Model Settings
        model_confidence_threshold: float = Field(
            default=0.75,
            description="Model confidence threshold for detections"
        )
        max_violations_to_store: int = Field(
            default=10000,
            description="Maximum violations to store in database"
        )
        
        # Notification Settings
        notification_email: Optional[str] = Field(
            default=None,
            description="Email to send violation alerts"
        )
        alert_on_violation: bool = Field(
            default=True,
            description="Send alerts when violations are detected"
        )
        
        class Config:
            env_file = ".env"
            case_sensitive = False

else:
    # Pydantic v1 fallback
    class Settings(BaseSettings):
        """
        Application settings loaded from environment variables
        Uses pydantic v1 BaseSettings
        """
        
        # API Keys
        gemini_api_key: Optional[str] = Field(
            None,
            description="Google Gemini API key for AI analysis"
        )
        sendgrid_api_key: Optional[str] = Field(
            None,
            description="SendGrid API key for email notifications"
        )
        
        # Database
        database_url: str = Field(
            "sqlite:///./violations.db",
            description="Database connection URL"
        )
        
        # Supabase (Optional Cloud Sync)
        supabase_url: Optional[str] = Field(
            None,
            description="Supabase project URL for cloud sync"
        )
        supabase_key: Optional[str] = Field(
            None,
            description="Supabase anon API key"
        )
        
        # Application Settings
        app_name: str = Field(
            "Traffic Violation Detection",
            description="Application name"
        )
        app_version: str = Field(
            "1.0.0",
            description="Application version"
        )
        debug: bool = Field(
            False,
            description="Debug mode (development)"
        )
        
        # API Server Settings
        api_host: str = Field(
            "0.0.0.0",
            description="API server host"
        )
        api_port: int = Field(
            8000,
            description="API server port"
        )
        
        # ML Model Settings
        model_confidence_threshold: float = Field(
            0.75,
            description="Model confidence threshold for detections"
        )
        max_violations_to_store: int = Field(
            10000,
            description="Maximum violations to store in database"
        )
        
        # Notification Settings
        notification_email: Optional[str] = Field(
            None,
            description="Email to send violation alerts"
        )
        alert_on_violation: bool = Field(
            True,
            description="Send alerts when violations are detected"
        )
        
        class Config:
            env_file = ".env"
            case_sensitive = False


# ==============================================
# SINGLETON PATTERN
# ==============================================

@lru_cache()
def get_settings() -> Settings:
    """
    Get settings instance (cached/singleton pattern)
    Returns the same instance for all calls
    
    Returns:
        Settings instance with loaded configuration
    """
    return Settings()


# ==============================================
# UTILITY FUNCTIONS
# ==============================================

def print_settings_summary():
    """Print configuration summary (excluding sensitive data)"""
    settings = get_settings()
    
    print("""
╔════════════════════════════════════════════════════╗
║          APPLICATION SETTINGS SUMMARY              ║
╚════════════════════════════════════════════════════╝
""")
    
    print(f"App Name:              {settings.app_name}")
    print(f"App Version:           {settings.app_version}")
    print(f"Debug Mode:            {settings.debug}")
    
    print("\n--- API Server ---")
    print(f"API Host:              {settings.api_host}")
    print(f"API Port:              {settings.api_port}")
    
    print("\n--- Database ---")
    db_url = settings.database_url
    # Hide sensitive data
    if "://" in db_url:
        parts = db_url.split("://")
        if "@" in parts[1]:
            db_url = f"{parts[0]}://***:***@..." + parts[1].split("@")[1][-20:]
    print(f"Database:              {db_url}")
    
    print("\n--- API Keys (Loaded) ---")
    print(f"Gemini API:            {'✅ YES' if settings.gemini_api_key else '❌ NO'}")
    print(f"SendGrid API:          {'✅ YES' if settings.sendgrid_api_key else '❌ NO'}")
    
    print("\n--- Cloud Sync (Optional) ---")
    print(f"Supabase:              {'✅ YES' if settings.supabase_url else '❌ NO'}")
    
    print("\n--- Model Settings ---")
    print(f"Confidence Threshold:  {settings.model_confidence_threshold}")
    print(f"Max Violations Store:  {settings.max_violations_to_store}")
    
    print("\n--- Notifications ---")
    print(f"Alert on Violation:    {settings.alert_on_violation}")
    notification_email = settings.notification_email
    if notification_email:
        # Hide email for privacy
        parts = notification_email.split("@")
        notification_email = f"{parts[0][:2]}***@{parts[1]}"
    print(f"Notification Email:    {notification_email or '❌ NOT SET'}")
    
    print("\n" + "=" * 50 + "\n")


# ==============================================
# VALIDATORS (Optional - for custom validation)
# ==============================================

def validate_settings():
    """
    Validate required settings and warn about missing optional ones
    """
    settings = get_settings()
    warnings = []
    
    # Optional but recommended
    if not settings.gemini_api_key:
        warnings.append("⚠️  GEMINI_API_KEY not set (optional)")
    
    if not settings.sendgrid_api_key:
        warnings.append("⚠️  SENDGRID_API_KEY not set (optional)")
    
    if not settings.notification_email and settings.alert_on_violation:
        warnings.append("⚠️  NOTIFICATION_EMAIL not set but ALERT_ON_VIOLATION=true")
    
    if warnings:
        print("Configuration Warnings:")
        for warning in warnings:
            print(f"  {warning}")
    
    return len(warnings) == 0


# ==============================================
# MAIN / TESTING
# ==============================================

if __name__ == "__main__":
    print("Loading settings from environment...\n")
    settings = get_settings()
    print_settings_summary()
    
    is_valid = validate_settings()
    if is_valid:
        print("✅ All settings valid and loaded!")
    else:
        print("⚠️  Some settings need attention")
