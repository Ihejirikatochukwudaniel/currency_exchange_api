# app/config.py

from pydantic_settings import BaseSettings  # ✅ new import
from pydantic import Field

class Settings(BaseSettings):
    database_url: str = Field(..., env="DATABASE_URL")
    port: int = Field(8000, env="PORT")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
