"""
Author: Imran Mughal
Email: imran@mughal.com
Date: December 19, 2024
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from sqlalchemy import inspect
from typing import Dict, Any, List
import aiosqlite

# Create async engine
engine = create_async_engine(
    "sqlite+aiosqlite:///tasks.db",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=True
)

# Create session factory
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_session():
    """Get a database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def get_tables(session: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
    """Get all tables and their schema."""
    def get_schema():
        inspector = inspect(session.bind)
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
    
    tables = await session.run_sync(lambda: get_schema())
    return {"tables": tables} 