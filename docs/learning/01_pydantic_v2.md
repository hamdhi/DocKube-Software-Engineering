# Pydantic v2 Complete Guide

## Overview
Pydantic v2 is a complete rewrite in Rust (via pydantic-core) offering 5-50x performance improvements over v1.

## Key Changes from v1
- Core rewritten in Rust - Massive speed improvements
- New validation API - @field_validator, @model_validator decorators
- V2 config - model_config = ConfigDict(...) instead of inner Config class
- Serialization - Built-in .model_dump(), .model_dump_json()
- Strict mode - StrictStr, StrictInt, etc. for exact type matching

## Basic Model Definition
```python
from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import Optional
from datetime import datetime
from uuid import UUID

class User(BaseModel):
    email: EmailStr
    name: str = Field(..., min_length=1, max_length=100)
    age: Optional[int] = Field(None, ge=0, le=150)
    website: Optional[HttpUrl] = None
    id: UUID = Field(default_factory=uuid4)
    created_at: datetime = Field(default_factory=datetime.utcnow)

    model_config = ConfigDict(
        str_strip_whitespace=True,
        validate_assignment=True,
        extra="forbid",
        use_enum_values=True,
        populate_by_name=True,
    )
```

## Field Validation (v2 Style)

### @field_validator - Single Field
```python
from pydantic import field_validator

class Product(BaseModel):
    name: str
    price: float
    discount: float = 0.0

    @field_validator("price")
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Price must be positive")
        return v
```

### @model_validator - Cross-Field Validation
```python
from pydantic import model_validator

class Event(BaseModel):
    start_date: datetime
    end_date: datetime
    timezone: str = "UTC"

    @model_validator(mode="after")
    def check_dates(self) -> "Event":
        if self.start_date >= self.end_date:
            raise ValueError("start_date must be before end_date")
        return self
```

## Serialization
```python
user = User(email="test@example.com", name="John")
user_dict = user.model_dump()
json_str = user.model_dump_json()
user_dict = user.model_dump(exclude_unset=True)
```

## Settings Management (pydantic-settings)
```python
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Union, List

class Settings(BaseSettings):
    app_name: str = "MyApp"
    debug: bool = False
    database_url: str
    secret_key: str
    allowed_hosts: Union[List[str], str] = ["localhost"]
    
    @field_validator("allowed_hosts", mode="before")
    @classmethod
    def parse_hosts(cls, v: Union[str, List[str]]) -> List[str]:
        if isinstance(v, str):
            return [h.strip() for h in v.split(",")]
        return v

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

settings = Settings()
```

## Discriminated Unions (Polymorphic Models)
```python
from pydantic import Field
from typing import Union, Literal

class Cat(BaseModel):
    pet_type: Literal["cat"]
    meows: int

class Dog(BaseModel):
    pet_type: Literal["dog"]
    barks: float

class Pet(BaseModel):
    pet: Union[Cat, Dog] = Field(discriminator="pet_type")
```

## Migration from v1 Checklist
- [ ] Change Config class to model_config = ConfigDict(...)
- [ ] Replace @validator with @field_validator / @model_validator
- [ ] Replace @root_validator with @model_validator(mode="before/after")
- [ ] Update orm_mode = True to from_attributes=True
- [ ] Change json_encoders to serialization methods
- [ ] Update allow_mutation to frozen / validate_assignment
