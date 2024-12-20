"""
Author: Imran Mughal
Email: imran@mughal.com
Date: December 19, 2024
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager
import aiosqlite

# Create async engine for SQLite
engine = create_async_engine(
    "sqlite+aiosqlite:///tasks.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True
)

# Create async session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency for FastAPI
async def get_db():
    session = AsyncSessionLocal()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()

# Function to get inspector
async def get_inspector(session):
    """Get SQLAlchemy inspector for the database."""
    def _get_inspector():
        from sqlalchemy import inspect
        return inspect(session.bind)
    return await session.run_sync(_get_inspector)

# Function to list tables
async def list_tables(session):
    """List all tables in the database with their schema."""
    inspector = await get_inspector(session)
    
    def get_table_info():
        tables = []
        for table_name in inspector.get_table_names():
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column.get("nullable", True)
                })
            tables.append({
                "name": table_name,
                "columns": columns
            })
        return tables
    
    return {"tables": await session.run_sync(lambda: get_table_info())}