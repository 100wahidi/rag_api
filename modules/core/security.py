from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

class Settings(BaseSettings):
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ALGORITHM: str = os.getenv("ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    PG_DB_URL: str = os.getenv("PG_DB_URL")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY")
    ORIGINS: str = os.getenv("ORIGINS")

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8"
    )