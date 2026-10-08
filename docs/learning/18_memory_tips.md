# Memory Tips for Programmers Who Forget Code Easily

## The Golden Rule: YOU DON'T NEED TO MEMORIZE CODE
Professional developers Google things daily. What matters is understanding CONCEPTS and knowing WHERE to find the syntax.

## Concept vs Syntax
```
CONCEPT (remember this)          SYNTAX (look this up)
-----------------------          --------------------
"JWT has 3 parts"          -->   jwt.encode(payload, key, algorithm)
"bcrypt includes salt"     -->   pwd_context.hash(password)
"Use yield for cleanup"    -->   def get_db(): yield db
"Alembic tracks changes"   -->   alembic revision --autogenerate
```

## The 5-Second Recall Technique
When you forget something, ask yourself:
1. WHAT does it do? (concept)
2. WHERE have I seen it? (file/project)
3. WHO wrote a good example? (docs, Stack Overflow, your own old code)

## The "Teach It" Method
If you can't explain it simply, you don't understand it well enough. After learning something:
1. Write a blog post about it
2. Explain it to a rubber duck
3. Write it in your own words (not copy-paste)

## Spaced Repetition Schedule
```
Day 1:  Learn it
Day 3:  Review it
Day 7:  Review again
Day 14: Review again
Day 30: Review again
```
After 5 reviews, it sticks permanently.

## Common Things People Forget (And The Pattern Behind Them)

### 1. Import Statements
```
PATTERN: Most Python frameworks use similar import patterns
FastAPI:      from fastapi import Depends, HTTPException
SQLAlchemy:   from sqlalchemy import select, func
Pydantic:     from pydantic import BaseModel, Field
TIP: Your IDE (VS Code) auto-imports. Just start typing and press Ctrl+Space
```

### 2. Decorator Syntax
```
PATTERN: @decorator_name(optional_args)
@router.get("/path")
@router.get("/path", response_model=User)
@field_validator("email")
TIP: Decorators are just functions that wrap other functions.
     The syntax is ALWAYS @name(...)
```

### 3. Async vs Def
```
PATTERN: I/O bound = async def, CPU bound = def
Database (sync)     --> def
Database (async)    --> async def
API calls           --> async def
Calculations        --> def
TIP: If it waits for something external, use async.
     If it computes something, use def.
```

### 4. Dependency Injection
```
PATTERN: param: Type = Depends(function)
db: Session = Depends(get_db)
user: User = Depends(get_current_user)
TIP: Depends() means "FastAPI, run this function first and give me the result"
```

### 5. Try/Except Patterns
```
PATTERN: try the risky thing, catch the specific error
try:
    db.commit()
except IntegrityError:
    db.rollback()
    raise HTTPException(409, "Already exists")
TIP: Always rollback on database error. Always catch specific exceptions.
```
