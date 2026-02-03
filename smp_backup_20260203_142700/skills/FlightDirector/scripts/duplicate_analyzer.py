#!/usr/bin/env python3
"""
Duplicate Markdown File Analyzer with Hash Verification

Identifies duplicate markdown files using SHA256 hashes and helps clean up safely.
"""

import os
import sys
import json
import argparse
import hashlib
import subprocess
from pathlib import Path
from typing import Dict, List, Set, Tuple
from collections import defaultdict

class DuplicateAnalyzer:
    def __init__(self, workspace_dir: str = None, dry_run: bool = False):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.dry_run = dry_run
        self.duplicates = defaultdict(list)
        self.file_hashes = {}  # filename -> hash

    def _get_file_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of a file."""
        try:
            with open(file_path, 'rb') as f:
                return hashlib.sha256(f.read()).hexdigest()
        except Exception:
            return "UNREADABLE"

    def find_duplicates(self) -> Dict[str, List[Path]]:
        """Find duplicate markdown files across key directories."""
        print("🔍 Scanning for duplicate markdown files...")

        # Key directories to search
        search_dirs = [
            self.workspace_dir,
            self.workspace_dir / ".agent",
            Path.home() / ".gemini",
            Path.home() / ".agent",
        ]

        file_map = defaultdict(list)
        file_hashes = {}

        for search_dir in search_dirs:
            if not search_dir.exists():
                continue

            for md_file in search_dir.rglob("*.md"):
                # Skip problematic directories
                if any(pattern in str(md_file) for pattern in [
                    "node_modules", ".venv", "site-packages", "__pycache__",
                    ".git", "task-", "lightrag-1sk", "lightrag-o9j"
                ]):
                    continue

                # Only track actual files, not symlinks
                if md_file.is_file():
                    filename = md_file.name
                    file_hash = self._get_file_hash(md_file)

                    # Store hash
                    if filename in file_hashes:
                        if file_hashes[filename] == file_hash:
                            print(f"    ℹ️  Same file {filename} (same content)")
                            continue
                        else:
                            print(f"    ⚠️  DIFFERENT file {filename} detected!")

                    file_hashes[filename] = file_hash
                    file_map[filename].append(md_file)

        # Identify duplicates by comparing hashes
        for filename, files in file_map.items():
            if len(files) > 1:
                self.duplicates[filename] = files

        return dict(self.duplicates)

    def _get_relative_path(self, file_path: Path) -> str:
        """Get a clean relative path from workspace."""
        try:
            return str(file_path.relative_to(self.workspace_dir))
        except ValueError:
            return str(file_path)

    def analyze_duplicates(self) -> None:
        """Analyze duplicates and make recommendations."""
        if not self.duplicates:
            print("✅ No duplicate markdown files found!")
            return

        print(f"\n📊 Found {len(self.duplicates)} types of duplicate files:")

        critical_duplicates = []
        significant_duplicates = []
        minor_duplicates = []

        for filename, files in self.duplicates.items():
            if len(files) > 1:
                print(f"\n📄 {filename} ({len(files)} copies):")

                for i, file in enumerate(files, 1):
                    rel_path = self._get_relative_path(file)
                    status = "⚠️  " if i > 1 else "✅ PRIMARY"
                    print(f"  {i}. {status} {rel_path}")

                    # Categorize duplicates
                    if i == 1:  # Primary file
                        if filename.startswith(("AGENTS", "GLOBAL_INDEX")):
                            critical_duplicates.append((filename, file))
                        elif filename in ["README.md", "KEYWORD_SEARCH_PERFORMANCE.md"]:
                            significant_duplicates.append((filename, file))
                        else:
                            minor_duplicates.append((filename, file))
                    else:
                        print(f"    ℹ️  Consider removing: {rel_path}")
                    else:
                        print(f"    💡  Keep this one: {rel_path}")

        # Summary and recommendations
        self._print_summary(critical_duplicates, significant_duplicates, minor_duplicates)

        if not self.dry_run:
            self._suggest_cleanup_commands(critical_duplicates, significant_duplicates, minor_duplicates)

    def _print_summary(self, critical: List, significant: List, minor: List) -> None:
        """Print summary of duplicate analysis."""
        print(f"\n" + "=" * 60)
        print("📋 DUPLICATE ANALYSIS SUMMARY")
        print("=" * 60)

        print(f"🚨 CRITICAL DUPLICATES: {len(critical)}")
        for filename, _ in critical:
            print(f"   • {filename} - Must be unique!")

        print(f"\n⚠️  SIGNIFICANT DUPLICATES: {len(significant)}")
        for filename, _ in significant:
            print(f"   • {filename} - Should be consolidated")

        print(f"\n📝 MINOR DUPLICATES: {len(minor)}")
        for filename, _ in minor:
            print(f"   • {filename} - Can be cleaned up")

        total_duplicates = len(critical) + len(significant) + len(minor)
        print(f"\n📈 TOTAL DUPLICATE FILES: {total_duplicates}")

    def _suggest_cleanup_commands(self, critical: List, significant: List, minor: List) -> None:
        """Suggest cleanup commands."""
        print(f"\n" + "=" * 60)
        print("🧹 SUGGESTED CLEANUP COMMANDS")
        print("=" * 60)

        # Critical duplicates - recommend manual review
        if critical:
            print("\n🚨 CRITICAL DUPLICATES - Manual review required:")
            for filename, file in critical:
                rel_path = self._get_relative_path(file)
                print(f"   # Review: {rel_path}")
            print("\n   ⚠️  These files must remain unique across the system!")

        # Significant duplicates - recommend keeping primary, removing others
        if significant:
            print("\n🔧 SIGNIFICANT DUPLICATES - Automated cleanup:")
            for filename, file in significant:
                rel_path = self._get_relative_path(file)
                print(f"   rm \"{rel_path}\"")

        # Minor duplicates - bulk cleanup
        if minor:
            print("\n🧹 MINOR DUPLICATES - Bulk cleanup:")
            print("   # Remove duplicates in problematic directories:")
            print("   find . -name \"*_README.md\" -not -path \"*/node_modules/*\" -not -path \"*/.venv/*\" -exec rm {{}} \\;")
            print("\n   # Or remove specific types:")
            print("   find . -name \"*_README.md\" -not -path \"*/node_modules/*\" -not -path \"*/.venv/*\" -exec rm {{}} \\;")

        if not (critical or significant or minor):
            print("\n✅ No cleanup needed!")
        else:
            print(f"\n💡 EXECUTE DRY RUN WITH: --execute to actually remove files")
            print(f"\n💡 REVIEW COMMANDS BEFORE RUNNING: Always test with --dry-run first!")

def main():
    parser = argparse.ArgumentParser(description='Duplicate markdown file analyzer with hash verification')
    parser.add_argument('--workspace-dir', '-w', help='Workspace directory to analyze')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Only analyze, dont actually remove files')
    parser.add_argument('--execute', action='store_true', help='Execute suggested cleanup commands')
    parser.add_argument('--json', '-j', action='store_true', help='Output in JSON format')

    args = parser.parse_args()

    # Validate arguments
    if args.execute and not args.dry_run:
        print("❌ ERROR: --execute requires --dry-run first for review")
        sys.exit(1)

    try:
        analyzer = DuplicateAnalyzer(
            workspace_dir=args.workspace_dir,
            dry_run=args.dry_run
        )

        duplicates = analyzer.find_duplicates()
        analyzer.analyze_duplicates()

        if args.json:
            # Export to JSON with hash info
            export_data = {}
            for filename, files in analyzer.duplicates.items():
                export_data[filename] = [{
                    'path': str(analyzer._get_relative_path(f)),
                    'hash': analyzer._get_file_hash(f) if len(files) > 0 else None
                } for f in files]

            print(json.dumps(export_data, indent=2))

    except KeyboardInterrupt:
        print("\n⚠️ Analysis interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"\n🚨 Analysis error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
