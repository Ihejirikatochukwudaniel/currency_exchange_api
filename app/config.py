# app/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, AnyUrl


class DatabaseUrl(AnyUrl):
    allowed_schemes = ["mysql+aiomysql"]  # ✅ restrict to async MySQL driver
    user_required = True


class Settings(BaseSettings):
    # ✅ Environment variables
    database_url: DatabaseUrl = Field(..., env="DATABASE_URL")
    port: int = Field(default=8000, env="PORT")
    debug: bool = Field(default=False, env="DEBUG")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# ✅ Singleton settings instance
settings = Settings()
