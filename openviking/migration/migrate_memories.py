#!/usr/bin/env python3
"""
Migrate file-based memories from ~/.agent/memory/learnings/ to OpenViking.
"""

import asyncio
import json
import logging
from pathlib import Path

import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

# Constants
LEARNINGS_DIR = Path.home() / ".agent" / "memory" / "learnings"
OPENVIKING_URL = "http://localhost:8000"


async def migrate_file(file_path: Path, resource_type: str):
    """Migrate a single JSON file of learnings to OpenViking."""
    if not file_path.exists():
        logger.warning(f"File not found: {file_path}")
        return 0

    try:
        data = json.loads(file_path.read_text())
        if not isinstance(data, list):
            # If it's a single object, wrap it in a list
            data = [data]

        success_count = 0
        async with httpx.AsyncClient() as client:
            for item in data:
                # Use a unique target_uri based on the item id if available
                item_id = (
                    item.get("id")
                    or item.get("timestamp")
                    or f"{file_path.stem}_{success_count}"
                )
                target_uri = f"memory:{resource_type}:{item_id}"

                response = await client.post(
                    f"{OPENVIKING_URL}/resources",
                    json={
                        "content": json.dumps(item),
                        "target_uri": target_uri,
                        "resource_type": resource_type,
                    },
                    timeout=10.0,
                )

                if response.status_code == 200:
                    success_count += 1
                else:
                    logger.error(f"Failed to migrate item {item_id}: {response.text}")

        logger.info(
            f"Successfully migrated {success_count}/{len(data)} items from {file_path.name}"
        )
        return success_count

    except Exception as e:
        logger.error(f"Error migrating {file_path}: {e}")
        return 0


async def main():
    logger.info("🚀 Starting Memory Migration to OpenViking...")

    # Check if OpenViking is running
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{OPENVIKING_URL}/health")
            if resp.status_code != 200:
                logger.error("OpenViking health check failed. Is the server running?")
                return
    except Exception as e:
        logger.error(f"Could not connect to OpenViking: {e}")
        return

    files_to_migrate = [
        ("pending_learnings.json", "pending_learning"),
        ("applied_learnings.json", "applied_learning"),
        ("proactive_suggestions.json", "proactive_suggestion"),
        ("skill_versions.json", "skill_version"),
    ]

    total_migrated = 0
    for filename, res_type in files_to_migrate:
        count = await migrate_file(LEARNINGS_DIR / filename, res_type)
        total_migrated += count

    logger.info(f"✨ Migration complete! Total items migrated: {total_migrated}")


if __name__ == "__main__":
    asyncio.run(main())
