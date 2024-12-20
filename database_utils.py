from sqlalchemy import inspect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, Any, List

async def list_tables(session: AsyncSession) -> Dict[str, List[Dict[str, Any]]]:
    """List all tables in the database with their schema."""
    tables = []
    inspector = inspect(session.bind)
    
    def get_table_info():
        table_list = []
        for table_name in inspector.get_table_names():
            columns = []
            for column in inspector.get_columns(table_name):
                columns.append({
                    "name": column["name"],
                    "type": str(column["type"]),
                    "nullable": column.get("nullable", True)
                })
            table_list.append({
                "name": table_name,
                "columns": columns
            })
        return table_list
    
    tables = await session.run_sync(lambda _: get_table_info())
    return {"tables": tables} 