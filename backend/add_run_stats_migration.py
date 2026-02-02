"""Add statistics columns to eval_runs table."""

import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "llm_eval.db")

def migrate():
    """Add new columns to eval_runs table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get existing columns
    cursor.execute("PRAGMA table_info(eval_runs)")
    existing_columns = {row[1] for row in cursor.fetchall()}

    # Columns to add
    new_columns = {
        "total_duration_ms": "INTEGER",
        "total_skill_tokens": "INTEGER",
        "total_evaluator_tokens": "INTEGER",
    }

    for column_name, column_type in new_columns.items():
        if column_name not in existing_columns:
            print(f"Adding column: {column_name}")
            cursor.execute(
                f"ALTER TABLE eval_runs ADD COLUMN {column_name} {column_type}"
            )
        else:
            print(f"Column already exists: {column_name}")

    conn.commit()
    conn.close()
    print("Migration completed!")

if __name__ == "__main__":
    migrate()
