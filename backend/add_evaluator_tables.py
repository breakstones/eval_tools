"""Database migration script to add evaluator tables.

Run this script to create the evaluators and task_evaluators tables.
"""

import asyncio
import sys
import os

# Add parent directory to path to import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.database import engine


async def create_evaluators_table():
    """Create the evaluators table."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS evaluators (
                id VARCHAR(36) PRIMARY KEY,
                name VARCHAR(100) UNIQUE NOT NULL,
                description TEXT,
                type VARCHAR(20) NOT NULL CHECK(type IN ('llm_judge', 'code')),
                config TEXT NOT NULL DEFAULT '{}',
                is_system INTEGER NOT NULL DEFAULT 0,
                created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """))
        print("Created evaluators table")


async def create_task_evaluators_table():
    """Create the task_evaluators association table."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS task_evaluators (
                id VARCHAR(36) PRIMARY KEY,
                task_id VARCHAR(36) NOT NULL,
                evaluator_id VARCHAR(36) NOT NULL,
                order_index INTEGER NOT NULL DEFAULT 0,
                FOREIGN KEY (task_id) REFERENCES eval_tasks(id) ON DELETE CASCADE,
                FOREIGN KEY (evaluator_id) REFERENCES evaluators(id) ON DELETE CASCADE,
                UNIQUE(task_id, evaluator_id)
            )
        """))
        print("Created task_evaluators table")


async def create_indexes():
    """Create indexes for performance."""
    async with engine.begin() as conn:
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_task_evaluators_task_id
            ON task_evaluators(task_id)
        """))
        await conn.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_task_evaluators_evaluator_id
            ON task_evaluators(evaluator_id)
        """))
        print("Created indexes")


async def insert_system_evaluators():
    """Insert system built-in evaluators."""
    import uuid
    import json
    from datetime import datetime

    async with engine.begin() as conn:
        # Check if evaluators already exist
        result = await conn.execute(text("SELECT COUNT(*) FROM evaluators WHERE is_system = 1"))
        count = result.scalar()

        if count > 0:
            print("System evaluators already exist, skipping insertion")
            return

        # Insert Exact Match evaluator
        exact_match_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO evaluators (id, name, description, type, config, is_system, created_at, updated_at)
            VALUES (:id, :name, :description, :type, :config, :is_system, :created_at, :updated_at)
        """), {
            "id": exact_match_id,
            "name": "exact_match",
            "description": "精确字符串匹配评估器，自动归一化空白字符",
            "type": "code",
            "config": json.dumps({
                "code": '''
def evaluate(expected: str, actual: str) -> dict:
    """Evaluate if expected matches actual after normalizing whitespace."""
    import json

    # Normalize whitespace
    def normalize(s: str) -> str:
        return " ".join(s.split())

    expected_normalized = normalize(expected)
    actual_normalized = normalize(actual)

    if expected_normalized == actual_normalized:
        return {"result": "passed", "reason": "输出完全匹配"}
    else:
        return {
            "result": "failed",
            "reason": f"输出不匹配\\n预期: {expected_normalized[:100]}\\n实际: {actual_normalized[:100]}"
        }
'''
            }),
            "is_system": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        print(f"Created exact_match evaluator with id: {exact_match_id}")

        # Insert JSON Compare evaluator
        json_compare_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO evaluators (id, name, description, type, config, is_system, created_at, updated_at)
            VALUES (:id, :name, :description, :type, :config, :is_system, :created_at, :updated_at)
        """), {
            "id": json_compare_id,
            "name": "json_compare",
            "description": "JSON结构深度比较评估器，支持自动修复畸形JSON",
            "type": "code",
            "config": json.dumps({
                "code": '''
def evaluate(expected: str, actual: str) -> dict:
    """Evaluate JSON structures by deep comparison."""
    import json
    from app.utils.json_repair import repair_json

    def parse_json(s: str) -> object:
        """Parse JSON with repair fallback."""
        try:
            return json.loads(s)
        except json.JSONDecodeError:
            try:
                repaired = repair_json(s)
                return json.loads(repaired)
            except Exception:
                return s

    expected_obj = parse_json(expected)
    actual_obj = parse_json(actual)

    if expected_obj == actual_obj:
        return {"result": "passed", "reason": "JSON结构完全匹配"}
    else:
        return {
            "result": "failed",
            "reason": f"JSON结构不匹配\\n预期: {json.dumps(expected_obj, ensure_ascii=False)[:200]}\\n实际: {json.dumps(actual_obj, ensure_ascii=False)[:200]}"
        }
'''
            }),
            "is_system": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        print(f"Created json_compare evaluator with id: {json_compare_id}")

        # Insert LLM Judge evaluator as system evaluator
        llm_judge_id = str(uuid.uuid4())
        await conn.execute(text("""
            INSERT INTO evaluators (id, name, description, type, config, is_system, created_at, updated_at)
            VALUES (:id, :name, :description, :type, :config, :is_system, :created_at, :updated_at)
        """), {
            "id": llm_judge_id,
            "name": "llm_judge",
            "description": "LLM评估器，使用大语言模型进行语义评估",
            "type": "llm_judge",
            "config": json.dumps({
                "prompt_template": """你是一个专业的评估助手。请评估以下LLM的输出是否符合预期。

预期输出:
{expected}

实际输出:
{actual}

请根据以下标准进行评估:
1. 语义是否一致
2. 关键信息是否完整
3. 格式是否正确

请以JSON格式返回评估结果:
{
  "result": "passed" | "failed",
  "reason": "判断原因说明"
}"""
            }),
            "is_system": 1,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        })
        print(f"Created llm_judge evaluator with id: {llm_judge_id}")


async def main():
    """Run all migration steps."""
    print("Starting database migration...")
    print("=" * 50)

    await create_evaluators_table()
    await create_task_evaluators_table()
    await create_indexes()
    await insert_system_evaluators()

    print("=" * 50)
    print("Migration completed successfully!")


if __name__ == "__main__":
    asyncio.run(main())
