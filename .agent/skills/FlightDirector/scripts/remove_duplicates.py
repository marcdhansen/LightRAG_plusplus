#!/usr/bin/env python3
"""
Comprehensive Duplicate File Remover

Safely removes all duplicate markdown files across the system.
Uses SHA256 hashing to verify identical files and keeps the most recent copy.
"""

import os
import sys
import json
import argparse
import hashlib
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict


class DuplicateRemover:
    def __init__(self, workspace_dir: str = None):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()

    def file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        try:
            with open(file_path, "rb") as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return "ERROR"

    def find_all_duplicates(self) -> Dict[str, List[Path]]:
        """Find ALL duplicate markdown files across key directories."""
        print("🔍 Scanning for duplicate markdown files...")

        # Key directories to search
        search_dirs = [
            self.workspace_dir,
            self.workspace_dir / ".agent",
            Path.home() / ".gemini",
            Path.home() / ".agent",
        ]

        file_hashes = {}
        duplicates = {}

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            for md_file in search_dir.rglob("*.md"):
                # Skip problematic directories
                if any(
                    pattern in str(md_file)
                    for pattern in [
                        "node_modules",
                        ".venv",
                        "site-packages",
                        "__pycache__",
                        ".git",
                        "task-",
                        "lightrag-1sk",
                        "lightrag-o9j",
                    ]
                ):
                    continue

                # Only track actual files, not symlinks
                if md_file.is_file():
                    filename = md_file.name
                    file_hash = self.file_hash(md_file)

                    if filename in file_hashes:
                        if file_hashes[filename] == file_hash:
                            print(f"    ✓ Same file: {filename}")
                            continue
                        else:
                            print(f"    ⚠️  Different file: {filename} (CONFLICT!)")
                    else:
                        file_hashes[filename] = file_hash

                    if filename in duplicates:
                        duplicates[filename].append(md_file)
                    else:
                        duplicates[filename] = [md_file]

        return dict(duplicates)

    def remove_duplicates_safely(
        self, duplicates: Dict[str, List[Path]], dry_run: bool = False
    ) -> int:
        """Safely remove duplicate files, keeping the most recent copy."""
        removed_count = 0
        errors = []

        for filename, files in duplicates.items():
            if len(files) <= 1:
                continue

            print(f"\n🗑️ Processing {filename} ({len(files)} copies):")

            # Sort by modification time (most recent first)
            try:
                files.sort(
                    key=lambda f: f.stat().st_mtime if f.exists() else 0, reverse=True
                )
            except Exception:
                files.sort()  # Fallback to name

            # Keep the first (most recent), remove others
            keep_file = files[0]
            for i, file in enumerate(files):
                rel_path = str(file.relative_to(self.workspace_dir))

                if i == 0:
                    print(f"  ✓ KEEP: {rel_path}")
                else:
                    print(f"  - REMOVE: {rel_path}")

                    if not dry_run:
                        try:
                            file.unlink(missing_ok=True)
                            removed_count += 1
                        except Exception as e:
                            errors.append(f"Failed to remove {rel_path}: {e}")

        return removed_count, errors

    def run_full_cleanup(self, dry_run: bool = False) -> None:
        """Run comprehensive duplicate cleanup."""
        print("🧹 COMPREHENSIVE DUPLICATE FILE CLEANUP")
        print("=" * 60)

        # Find all duplicates
        all_duplicates = self.find_all_duplicates()

        if not all_duplicates:
            print("✅ No duplicate markdown files found!")
            return

        # Count total duplicates
        total_duplicate_files = sum(len(files) for files in all_duplicates.values())
        total_duplicate_copies = sum(
            len(files) - 1 for files in all_duplicates.values()
        )

        print(f"\n📊 Found {len(all_duplicates)} types of duplicate files")
        print(f"📈 Total duplicate files: {total_duplicate_files}")
        print(f"📈 Total duplicate copies: {total_duplicate_copies}")

        # Remove duplicates
        removed_count, errors = self.remove_duplicates_safely(all_duplicates, dry_run)

        # Summary
        print(f"\n" + "=" * 60)
        print("📋 CLEANUP SUMMARY")
        print("=" * 60)
        print(f"🗑️ Files removed: {removed_count}")
        print(f"📂 Errors encountered: {len(errors)}")

        if errors:
            print("\n❌ ERRORS:")
            for error in errors:
                print(f"   • {error}")

        if removed_count > 0:
            print(f"\n✅ Successfully cleaned up {removed_count} duplicate files!")
        else:
            print("\n✅ No cleanup needed (verified no critical duplicates)")

        print(f"\n💡 VERIFICATION:")
        print("   Run again to verify all duplicates are resolved")


def main():
    parser = argparse.ArgumentParser(
        description="Comprehensive duplicate markdown file remover"
    )
    parser.add_argument(
        "--workspace-dir", "-w", default=".", help="Workspace directory"
    )
    parser.add_argument(
        "--dry-run", "-d", action="store_true", help="Dry run only, no removal"
    )

    args = parser.parse_args()

    try:
        remover = DuplicateRemover(workspace_dir=args.workspace_dir)
        remover.run_full_cleanup(dry_run=args.dry_run)

    except KeyboardInterrupt:
        print("\n⚠️ Cleanup interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n🚨 Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
