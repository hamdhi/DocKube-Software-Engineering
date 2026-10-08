# Pydantic Settings Complete Guide

## What is pydantic-settings?
It extends Pydantic v2 to read configuration from environment variables, .env files, and other sources with full validation.

## Installation
```bash
pip install pydantic-settings
```

## Basic Usage
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, SecretStr, field_validator
from typing import Union, List
import json

class Settings(BaseSettings):
    PROJECT_NAME: str = "MyApp"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    ALLOWED_ORIGINS: Union[List[str], str] = ["http://localhost:3000"]
    DATABASE_URL: str = Field(default=...)
    GEMINI_API_KEY: SecretStr = Field(default=...)

    @field_validator("ALLOWED_ORIGINS", mode="before")
    @classmethod
    def assemble_list_fields(cls, value: Union[str, List[str]]) -> List[str]:
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        if isinstance(value, str):
            cleaned = value.strip()
            if cleaned.startswith("[") and cleaned.endswith("]"):
                try:
                    parsed = json.loads(cleaned)
                    if isinstance(parsed, list):
                        return [str(item).strip() for item in parsed if str(item).strip()]
                except json.JSONDecodeError:
                    pass
            return [item.strip() for item in cleaned.split(",") if item.strip()]
        return []

    @field_validator("DATABASE_URL")
    @classmethod
    def validate_database_url(cls, value: str) -> str:
        cleaned = value.strip()
        if cleaned.startswith("postgres://"):
            cleaned = cleaned.replace("postgres://", "postgresql://", 1)
        valid_prefixes = ("postgresql://", "postgresql+psycopg2://", "postgresql+asyncpg://")
        if not cleaned.startswith(valid_prefixes):
            raise ValueError(f"DATABASE_URL must start with one of: {valid_prefixes}")
        return cleaned

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

from functools import lru_cache

@lru_cache
def get_settings() -> Settings:
    return Settings()

settings = get_settings()
```

## .env File Format
```env
PROJECT_NAME=Hospital Management System
ENVIRONMENT=development
DEBUG=true
ALLOWED_ORIGINS=http://localhost:3000,https://hms.yourdomain.com
ALLOWED_HOSTS=localhost,127.0.0.1,hms.yourdomain.com
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
GEMINI_API_KEY=AIzaSy...
```

## Why lru_cache on get_settings()?
Without caching, Settings() reads the .env file from disk on EVERY call. With @lru_cache, it reads once and caches in memory. This is critical for performance.
