from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List
import json

class Settings(BaseSettings):
    PROJECT_NAME: str = "Aarogya Health Engine"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str
    
    # Database
    DATABASE_URL: str
    INSTANCE_CONNECTION_NAME: str = ""
    
    # CORS
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"
    
    # 3rd Party APIs
    GEMINI_API_KEY: str = ""
    SMTP_EMAIL: str = ""
    SMTP_PASSWORD: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""
    
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")
    
    @property
    def cors_origins(self) -> List[str]:
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]

settings = Settings()
