# Alembic Database Migrations Complete Guide

## Overview
Alembic is the migration tool for SQLAlchemy. It tracks schema changes over time.

## Setup
```bash
pip install alembic
cd your_project
alembic init alembic
```

## Configure env.py
```python
# alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

from myapp.core.database import Base
from myapp.models.user import User
from myapp.models.order import Order

target_metadata = Base.metadata
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

## Generate Migration
```bash
alembic revision --autogenerate -m "create users table"
alembic revision -m "seed admin user"
```

## Migration File Example (Schema)
```python
# alembic/versions/001_create_users_table.py
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID
import uuid

def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String(255), unique=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("role", sa.String(50), nullable=False, server_default="USER"),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])

def downgrade() -> None:
    op.drop_index("ix_users_email")
    op.drop_table("users")
```

## Data Seeding in Migration
```python
# alembic/versions/002_seed_admin.py
from alembic import op
import sqlalchemy as sa
import uuid
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def upgrade() -> None:
    users_table = sa.table(
        "users",
        sa.column("id", sa.UUID),
        sa.column("email", sa.String),
        sa.column("hashed_password", sa.String),
        sa.column("role", sa.String),
    )
    op.bulk_insert(users_table, [
        {
            "id": str(uuid.uuid4()),
            "email": "admin@example.com",
            "hashed_password": pwd_context.hash("admin123"),
            "role": "SUPER_ADMIN",
        }
    ])

def downgrade() -> None:
    op.execute("DELETE FROM users WHERE email = 'admin@example.com'")
```

## Apply Migrations
```bash
alembic upgrade head
alembic upgrade +1
alembic downgrade -1
alembic current
alembic history
alembic upgrade head --sql
```
