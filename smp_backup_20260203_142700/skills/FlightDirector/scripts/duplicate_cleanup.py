#!/usr/bin/env python3
"""
Duplicate File Cleanup Tool

Safely removes duplicate markdown files, especially critical ones like GLOBAL_INDEX.md and AGENTS.md.
"""

import argparse
import hashlib
from pathlib import Path


def file_hash(filepath: Path) -> str:
    """Calculate SHA256 hash of a file."""
    try:
        with open(filepath, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except Exception:
        return "ERROR"


def find_critical_duplicates(workspace_dir: Path) -> dict[str, list[Path]]:
    """Find critical duplicate files."""
    critical_files = ["GLOBAL_INDEX.md", "AGENTS.md"]
    duplicates = {}

    # Search all key directories
    search_dirs = [
        workspace_dir,
        workspace_dir / ".agent",
        Path.home() / ".gemini",
        Path.home() / ".agent",
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for md_file in search_dir.rglob("*.md"):
            if md_file.name in critical_files and md_file.is_file():
                file_hash_val = file_hash(md_file)
                if md_file.name in duplicates:
                    if duplicates[md_file.name][1] == file_hash_val:
                        print(f"    ✓ Same content for {md_file.name}")
                        continue

                duplicates[md_file.name] = duplicates.get(md_file.name, []) + [md_file]
                print(f"    Found: {md_file}")

    return duplicates


def main():
    parser = argparse.ArgumentParser(description="Critical duplicate file cleanup tool")
    parser.add_argument(
        "--workspace-dir", "-w", default=".", help="Workspace directory"
    )
    parser.add_argument("--dry-run", "-d", action="store_true", help="Dry run only")
    parser.add_argument("--execute", action="store_true", help="Execute cleanup")

    args = parser.parse_args()

    workspace_dir = Path(args.workspace_dir)

    # Find critical duplicates
    critical_duplicates = find_critical_duplicates(workspace_dir)

    if not critical_duplicates:
        print("✅ No critical duplicate files found!")
        return

    print("\n🔍 Critical Duplicate Analysis:")
    for filename, files in critical_duplicates.items():
        if len(files) > 1:
            print(f"⚠️  {filename}: {len(files)} copies found!")

            for i, file in enumerate(files, 1):
                rel_path = file.relative_to(workspace_dir)
                print(f"  {i}: {rel_path}")

                print(f"  Keeping: {files[0].relative_to(workspace_dir)}")
                for extra_file in files[1:]:
                    print(f"  Remove: {extra_file.relative_to(workspace_dir)}")

    if not args.dry_run and critical_duplicates:
        print("\n🧹 Safe cleanup commands for critical files:")

        for filename, files in critical_duplicates.items():
            if len(files) > 1:
                # Keep the first one (presumably in workspace)
                primary_file = files[0]
                print(f"  # Keep: {primary_file.relative_to(workspace_dir)}")

                # Remove the rest
                for extra_file in files[1:]:
                    remove_path = extra_file.relative_to(workspace_dir)
                    print(f'  rm "{remove_path}"')

                    if args.execute:
                        try:
                            extra_file.unlink(missing_ok=True)
                            print(f"    ✓ Removed: {remove_path}")
                        except Exception as e:
                            print(f"    ❌ Failed to remove: {remove_path}: {e}")

    print("\n✅ Cleanup complete!")


if __name__ == "__main__":
    main()
