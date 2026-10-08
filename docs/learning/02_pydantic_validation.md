# Pydantic v2 Validation Complete Reference

## Field Constraints
```python
from pydantic import BaseModel, Field
from typing import Annotated
from annotated_types import Gt, Lt, Ge, Le, Len, Pattern

class Product(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0, le=10000)
    quantity: int = Field(ge=0, default=0)
    rating: float = Field(ge=0.0, le=5.0, default=0.0)
    tags: list[str] = Field(default_factory=list, max_length=10)
    code: Annotated[str, Len(3, 10)]
    score: Annotated[int, Gt(0), Le(100)]
    email: Annotated[str, Pattern(r"^[a-z]+@[a-z]+\.[a-z]+$")]
```

## @field_validator Options
```python
from pydantic import field_validator

class User(BaseModel):
    email: str
    username: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        if "@" not in v:
            raise ValueError("Invalid email")
        return v.lower()

    @field_validator("username", "password")
    @classmethod
    def no_whitespace(cls, v: str) -> str:
        if " " in v:
            raise ValueError("No whitespace allowed")
        return v

    @field_validator("password", mode="after")
    @classmethod
    def check_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain a digit")
        return v
```

## Computed Fields (v2 Feature)
```python
from pydantic import computed_field

class Rectangle(BaseModel):
    width: float
    height: float

    @computed_field
    @property
    def area(self) -> float:
        return self.width * self.height
```

## Strict Types
```python
from pydantic import StrictStr, StrictInt, StrictFloat, StrictBool

class StrictModel(BaseModel):
    name: StrictStr
    count: StrictInt
    active: StrictBool
```

## Error Handling
```python
from pydantic import ValidationError

try:
    user = User(email="invalid", name="", age=-5)
except ValidationError as e:
    for error in e.errors():
        print(f"Field: {error['loc']}")
        print(f"Error: {error['msg']}")
        print(f"Type: {error['type']}")
```
