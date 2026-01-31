"""Migration script to add concurrency column to eval_tasks table."""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.database import engine


async def add_concurrency_column():
    """Add concurrency column to eval_tasks table if it doesn't exist."""

    async with engine.begin() as conn:
        # Check if column already exists
        result = await conn.execute(text("""
            SELECT COUNT(*) as count
            FROM pragma_table_info('eval_tasks')
            WHERE name = 'concurrency'
        """))
        row = result.fetchone()

        if row and row[0] > 0:
            print("Column 'concurrency' already exists in eval_tasks table.")
            return

        # Add the column
        await conn.execute(text("""
            ALTER TABLE eval_tasks
            ADD COLUMN concurrency INTEGER NOT NULL DEFAULT 1
        """))
        print("Added 'concurrency' column to eval_tasks table.")


if __name__ == "__main__":
    asyncio.run(add_concurrency_column())
