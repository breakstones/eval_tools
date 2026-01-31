"""Add name column to eval_tasks table.

Run this script to add the name column to existing eval_tasks table.
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import text
from app.database import engine


async def add_name_column():
    """Add name column to eval_tasks table."""
    async with engine.begin() as conn:
        # Check if column already exists
        result = await conn.execute(text(
            "SELECT COUNT(*) FROM pragma_table_info('eval_tasks') WHERE name='name'"
        ))
        column_exists = result.scalar() > 0

        if column_exists:
            print("Column 'name' already exists in eval_tasks table.")
            return

        # Add the name column
        await conn.execute(text(
            "ALTER TABLE eval_tasks ADD COLUMN name VARCHAR(255)"
        ))
        print("Successfully added 'name' column to eval_tasks table.")


if __name__ == "__main__":
    asyncio.run(add_name_column())
