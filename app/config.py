# app/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn
from typing import Optional

class Settings(BaseSettings):
    # ✅ PostgreSQL database URL (not MySQL!)
    database_url: str = Field(..., env="DATABASE_URL")
    
    # ✅ Other environment variables
    port: int = Field(default=8080, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# ✅ Singleton settings instance
settings = Settings()
