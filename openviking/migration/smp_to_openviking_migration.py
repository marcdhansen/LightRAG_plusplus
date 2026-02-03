#!/usr/bin/env python3
"""
SMP to OpenViking Migration Script
Migrates conversation data, embeddings, and skills from SMP to OpenViking
"""

import asyncio
import json
import shutil
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx


class SMPToOpenVikingMigrator:
    def __init__(
        self, smp_source_path: str, openviking_url: str = "http://localhost:8002"
    ):
        self.smp_source_path = Path(smp_source_path)
        self.openviking_url = openviking_url
        self.migration_log = []
        self.start_time = datetime.now()

    def log_migration(self, level: str, message: str, details: dict = None):
        """Log migration events"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "details": details or {},
        }
        self.migration_log.append(entry)

        level_emoji = {"info": "ℹ️", "success": "✅", "warning": "⚠️", "error": "❌"}
        print(f"{level_emoji.get(level, '📋')} {message}")
        if details:
            for key, value in details.items():
                print(f"   {key}: {value}")

    def scan_smp_data(self) -> dict[str, Any]:
        """Scan SMP data directory for migrable content"""
        self.log_migration("info", "Scanning SMP data directory...")

        smp_data = {
            "conversations": [],
            "embeddings": [],
            "skills": [],
            "sessions": [],
            "resources": [],
            "metadata": {},
        }

        if not self.smp_source_path.exists():
            self.log_migration(
                "error", f"SMP source path does not exist: {self.smp_source_path}"
            )
            return smp_data

        # Scan for JSON files that might contain SMP data
        for json_file in self.smp_source_path.rglob("*.json"):
            try:
                with open(json_file) as f:
                    data = json.load(f)

                # Categorize based on content patterns
                file_data = {
                    "path": str(json_file),
                    "size": json_file.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        json_file.stat().st_mtime
                    ).isoformat(),
                    "data": data,
                }

                # Simple heuristic categorization
                content = json.dumps(data).lower()

                if any(
                    keyword in content
                    for keyword in ["conversation", "session", "chat", "dialogue"]
                ):
                    smp_data["conversations"].append(file_data)
                elif any(
                    keyword in content
                    for keyword in ["embedding", "vector", "embedding_"]
                ):
                    smp_data["embeddings"].append(file_data)
                elif any(
                    keyword in content for keyword in ["skill", "agent", "capability"]
                ):
                    smp_data["skills"].append(file_data)
                elif any(
                    keyword in content for keyword in ["session", "user_id", "context"]
                ):
                    smp_data["sessions"].append(file_data)
                else:
                    smp_data["resources"].append(file_data)

            except Exception as e:
                self.log_migration("warning", f"Could not parse {json_file}: {e}")

        self.log_migration(
            "info",
            "SMP data scan complete",
            {
                "conversations": len(smp_data["conversations"]),
                "embeddings": len(smp_data["embeddings"]),
                "skills": len(smp_data["skills"]),
                "sessions": len(smp_data["sessions"]),
                "resources": len(smp_data["resources"]),
            },
        )

        return smp_data

    async def migrate_conversation_data(
        self, conversations: list[dict]
    ) -> dict[str, Any]:
        """Migrate conversation data to OpenViking"""
        self.log_migration("info", "Migrating conversation data...")

        migration_results = {
            "total": len(conversations),
            "migrated": 0,
            "failed": 0,
            "sessions_created": 0,
        }

        async with httpx.AsyncClient() as client:
            for conv_data in conversations:
                try:
                    data = conv_data.get("data", {})

                    # Extract conversation messages
                    messages = []
                    if isinstance(data, dict):
                        if "messages" in data:
                            messages = data["messages"]
                        elif "conversation" in data:
                            messages = data["conversation"]
                        elif "history" in data:
                            messages = data["history"]

                    if not messages:
                        self.log_migration(
                            "warning", "No messages found in conversation data"
                        )
                        continue

                    # Create a new session in OpenViking
                    session_id = f"migrated-{int(time.time())}-{len(messages)}"

                    # Migrate each message
                    for message in messages:
                        if isinstance(message, dict):
                            role = message.get("role", "user")
                            content = message.get("content", message.get("message", ""))

                            if content:
                                try:
                                    response = await client.post(
                                        f"{self.openviking_url}/conversation",
                                        json={
                                            "session_id": session_id,
                                            "message": content,
                                            "role": role,
                                        },
                                        timeout=30.0,
                                    )

                                    if response.status_code == 200:
                                        migration_results["migrated"] += 1
                                    else:
                                        migration_results["failed"] += 1
                                        self.log_migration(
                                            "warning",
                                            f"Failed to migrate message: {response.status_code}",
                                        )

                                except Exception as e:
                                    migration_results["failed"] += 1
                                    self.log_migration(
                                        "error", f"Error migrating message: {e}"
                                    )

                    migration_results["sessions_created"] += 1

                except Exception as e:
                    migration_results["failed"] += 1
                    self.log_migration(
                        "error",
                        f"Failed to migrate conversation file {conv_data.get('path')}: {e}",
                    )

        self.log_migration(
            "success", "Conversation migration complete", migration_results
        )
        return migration_results

    async def migrate_skills_data(self, skills: list[dict]) -> dict[str, Any]:
        """Migrate skills data to OpenViking"""
        self.log_migration("info", "Migrating skills data...")

        migration_results = {"total": len(skills), "migrated": 0, "failed": 0}

        # For skills, we can't directly migrate to OpenViking as they're hardcoded
        # but we can create a summary for manual integration
        skills_summary = []

        for skill_data in skills:
            try:
                data = skill_data.get("data", {})

                # Extract skill information
                skill_info = {
                    "source_file": skill_data.get("path"),
                    "name": data.get("name", "Unknown Skill"),
                    "description": data.get("description", ""),
                    "category": data.get("category", "general"),
                    "examples": data.get("examples", []),
                    "metadata": data,
                }
                skills_summary.append(skill_info)
                migration_results["migrated"] += 1

            except Exception as e:
                migration_results["failed"] += 1
                self.log_migration(
                    "error",
                    f"Failed to process skill file {skill_data.get('path')}: {e}",
                )

        # Save skills summary for manual review
        if skills_summary:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            with open(f"migrated_skills_summary_{timestamp}.json", "w") as f:
                json.dump(skills_summary, f, indent=2)

            self.log_migration(
                "success",
                f"Skills summary saved: migrated_skills_summary_{timestamp}.json",
            )

        self.log_migration("success", "Skills migration complete", migration_results)
        return migration_results

    async def migrate_embeddings_data(self, embeddings: list[dict]) -> dict[str, Any]:
        """Migrate embeddings data to OpenViking"""
        self.log_migration("info", "Migrating embeddings data...")

        migration_results = {"total": len(embeddings), "migrated": 0, "failed": 0}

        async with httpx.AsyncClient() as client:
            for embed_data in embeddings:
                try:
                    data = embed_data.get("data", {})

                    # Extract text content to generate new embeddings
                    text_content = ""
                    if isinstance(data, dict):
                        if "text" in data:
                            text_content = data["text"]
                        elif "content" in data:
                            text_content = data["content"]
                        elif "query" in data:
                            text_content = data["query"]
                        else:
                            # Try to find any string field
                            for key, value in data.items():
                                if isinstance(value, str) and len(value) > 10:
                                    text_content = value
                                    break

                    if not text_content:
                        self.log_migration(
                            "warning", "No text content found in embedding data"
                        )
                        continue

                    # Generate new embedding in OpenViking
                    try:
                        response = await client.post(
                            f"{self.openviking_url}/embeddings",
                            json={"text": text_content},
                            timeout=30.0,
                        )

                        if response.status_code == 200:
                            migration_results["migrated"] += 1
                        else:
                            migration_results["failed"] += 1
                            self.log_migration(
                                "warning",
                                f"Failed to generate embedding: {response.status_code}",
                            )

                    except Exception as e:
                        migration_results["failed"] += 1
                        self.log_migration("error", f"Error generating embedding: {e}")

                except Exception as e:
                    migration_results["failed"] += 1
                    self.log_migration(
                        "error",
                        f"Failed to process embedding file {embed_data.get('path')}: {e}",
                    )

        self.log_migration(
            "success", "Embeddings migration complete", migration_results
        )
        return migration_results

    def create_migration_backup(self) -> str:
        """Create backup of SMP data before migration"""
        self.log_migration("info", "Creating migration backup...")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(f"smp_backup_{timestamp}")

        try:
            if self.smp_source_path.exists():
                shutil.copytree(self.smp_source_path, backup_path)
                self.log_migration("success", f"Backup created: {backup_path}")
                return str(backup_path)
            else:
                self.log_migration("warning", "No SMP data to backup")
                return ""
        except Exception as e:
            self.log_migration("error", f"Failed to create backup: {e}")
            return ""

    def generate_migration_report(self, results: dict[str, Any]) -> dict[str, Any]:
        """Generate comprehensive migration report"""
        end_time = datetime.now()
        duration = end_time - self.start_time

        report = {
            "migration_info": {
                "start_time": self.start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration.total_seconds(),
                "smp_source": str(self.smp_source_path),
                "openviking_url": self.openviking_url,
            },
            "results": results,
            "log_entries": self.migration_log,
            "summary": {
                "total_items_migrated": sum(
                    r.get("migrated", 0) for r in results.values()
                ),
                "total_items_failed": sum(r.get("failed", 0) for r in results.values()),
                "success_rate": 0,
            },
        }

        total_items = (
            report["summary"]["total_items_migrated"]
            + report["summary"]["total_items_failed"]
        )
        if total_items > 0:
            report["summary"]["success_rate"] = (
                report["summary"]["total_items_migrated"] / total_items
            ) * 100

        return report

    async def run_migration(self) -> dict[str, Any]:
        """Run complete migration process"""
        self.log_migration("info", "Starting SMP to OpenViking migration...")

        # Create backup
        backup_path = self.create_migration_backup()

        # Scan SMP data
        smp_data = self.scan_smp_data()

        # Run migrations
        results = {}

        if smp_data["conversations"]:
            results["conversations"] = await self.migrate_conversation_data(
                smp_data["conversations"]
            )

        if smp_data["skills"]:
            results["skills"] = await self.migrate_skills_data(smp_data["skills"])

        if smp_data["embeddings"]:
            results["embeddings"] = await self.migrate_embeddings_data(
                smp_data["embeddings"]
            )

        # Generate report
        report = self.generate_migration_report(results)

        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = f"smp_to_openviking_migration_report_{timestamp}.json"

        with open(report_path, "w") as f:
            json.dump(report, f, indent=2)

        self.log_migration(
            "success", f"Migration complete! Report saved: {report_path}"
        )

        if backup_path:
            self.log_migration("info", f"Backup available at: {backup_path}")

        return report


async def main():
    """Main migration entry point"""
    import sys

    # Default SMP source path
    smp_source = ".agent"  # Current SMP directory

    if len(sys.argv) > 1:
        smp_source = sys.argv[1]

    print("🚀 SMP to OpenViking Migration Tool")
    print("=" * 50)
    print(f"SMP Source: {smp_source}")
    print("OpenViking Target: http://localhost:8002")
    print()

    migrator = SMPToOpenVikingMigrator(smp_source)

    try:
        report = await migrator.run_migration()

        print("\n📊 Migration Summary:")
        summary = report["summary"]
        print(f"   Total Items Migrated: {summary['total_items_migrated']}")
        print(f"   Total Items Failed: {summary['total_items_failed']}")
        print(f"   Success Rate: {summary['success_rate']:.1f}%")
        print(f"   Duration: {report['migration_info']['duration_seconds']:.1f}s")

        return 0 if summary["success_rate"] > 50 else 1

    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(asyncio.run(main()))
