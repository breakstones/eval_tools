"""Migration script to add execution_error column to eval_results table."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.database import engine


async def add_execution_error_column():
    """Add execution_error column to eval_results table if it doesn't exist."""

    async with engine.begin() as conn:
        # Check if column already exists
        result = await conn.execute(text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('eval_results')
            WHERE name = 'execution_error'
        """))
        row = result.fetchone()

        if row and row[0] > 0:
            print("Column 'execution_error' already exists in eval_results table.")
            return

        # Add the column
        await conn.execute(text("""
            ALTER TABLE eval_results
            ADD COLUMN execution_error TEXT
        """))
        print("Added 'execution_error' column to eval_results table.")


if __name__ == "__main__":
    asyncio.run(add_execution_error_column())
