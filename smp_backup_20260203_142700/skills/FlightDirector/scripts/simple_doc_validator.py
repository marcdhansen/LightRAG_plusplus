#!/usr/bin/env python3
"""
Simplified Document Reachability Validator

Focused validation that avoids symlink loops by being more targeted.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Set, Dict, List, Tuple
from urllib.parse import urlparse
import time


class SimpleDocumentValidator:
    def __init__(self, workspace_dir: str | None = None, verbose: bool = False):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.verbose = verbose
        self.broken_links = []
        self.unreachable_files = []

    def _find_global_index(self) -> Path:
        """Find the GLOBAL_INDEX.md file."""
        candidates = [
            self.workspace_dir / ".agent" / "docs" / "GLOBAL_INDEX.md",
            Path.home() / ".gemini" / ".agent" / "docs" / "GLOBAL_INDEX.md",
            Path.home() / ".agent" / "docs" / "GLOBAL_INDEX.md",
        ]

        for candidate in candidates:
            if candidate.exists():
                if self.verbose:
                    print(f"Found GLOBAL_INDEX.md at: {candidate}")
                return candidate

        raise FileNotFoundError(f"GLOBAL_INDEX.md not found")

    def _extract_links(self, file_path: Path) -> List[Tuple[str, str]]:
        """Extract markdown links from a file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            print(f"Warning: Could not read {file_path}: {e}")
            return []

        # Simple regex for markdown links
        pattern = r"\[([^\]]+)\]\(([^)]+)\)"
        return re.findall(pattern, content)

    def _resolve_path(self, link_target: str, source_file: Path) -> Path | None:
        """Resolve a link target relative to source file."""
        # Skip external URLs
        if urlparse(link_target).scheme:
            return None

        # Remove anchors
        link_target = link_target.split("#")[0]

        # Handle absolute paths
        if link_target.startswith("/"):
            return Path(link_target)

        # Handle relative paths
        return (source_file.parent / link_target).resolve()

    def _check_file_reachable(
        self, file_path: Path, checked: Set[str] | None = None
    ) -> bool:
        """Check if a file is reachable from GLOBAL_INDEX."""
        if checked is None:
            checked = set()

        # Avoid infinite recursion
        file_key = str(file_path.resolve())
        if file_key in checked:
            return False
        checked.add(file_key)

        # Try to find file in the workspace
        try:
            # Check if file exists
            if not file_path.exists():
                return False

            # Extract links and check recursively
            links = self._extract_links(file_path)
            for _, link_target in links:
                resolved = self._resolve_path(link_target, file_path)
                if resolved and resolved.exists() and resolved.suffix == ".md":
                    if str(resolved.resolve()) == str(self.global_index_path.resolve()):
                        return True
                    # Don't recurse too deep to avoid performance issues
                    if len(checked) < 100:
                        if self._check_file_reachable(resolved, checked):
                            return True

            return False
        except Exception:
            return False

    def validate(self) -> bool:
        """Run the validation."""
        print("🔍 Simple Document Reachability Validation")
        print("=" * 50)

        try:
            # Find GLOBAL_INDEX.md
            self.global_index_path = self._find_global_index()
            print(f"✅ Global index: {self.global_index_path}")

            # Get all markdown files in specific directories (avoid symlink loops)
            markdown_files = set()

            # Search in specific safe directories
            search_dirs = [
                self.workspace_dir / ".agent" / "docs",
                self.workspace_dir / "docs",
                Path.home() / ".gemini" / ".agent" / "docs",
                Path.home() / ".agent" / "docs",
            ]

            for search_dir in search_dirs:
                if search_dir.exists():
                    try:
                        for md_file in search_dir.rglob("*.md"):
                            # Skip problematic paths
                            if any(
                                part
                                in ["skills", "node_modules", ".git", "__pycache__"]
                                for part in md_file.parts
                            ):
                                continue
                            if md_file.is_symlink():
                                try:
                                    real_path = md_file.resolve()
                                    if real_path.exists():
                                        markdown_files.add(real_path)
                                except:
                                    continue
                            else:
                                markdown_files.add(md_file)
                    except Exception as e:
                        if self.verbose:
                            print(f"Warning: Could not search {search_dir}: {e}")

            print(f"📚 Found {len(markdown_files)} markdown files")

            # Check reachability
            reachable_count = 0
            unreachable_count = 0

            for md_file in markdown_files:
                if self._check_file_reachable(md_file):
                    reachable_count += 1
                else:
                    unreachable_count += 1
                    try:
                        relative_path = md_file.relative_to(self.workspace_dir)
                    except ValueError:
                        relative_path = md_file.relative_to(Path.home())
                    self.unreachable_files.append(str(relative_path))

            # Check links in GLOBAL_INDEX.md for broken links
            global_links = self._extract_links(self.global_index_path)
            for link_text, link_target in global_links:
                resolved = self._resolve_path(link_target, self.global_index_path)
                if resolved and not resolved.exists():
                    self.broken_links.append(
                        {
                            "source": str(self.global_index_path),
                            "target": link_target,
                            "resolved": str(resolved),
                        }
                    )

            # Report results
            print(f"✅ Reachable: {reachable_count}")
            print(f"⚠️  Unreachable: {unreachable_count}")
            print(f"❌ Broken links: {len(self.broken_links)}")

            if self.unreachable_files:
                print("\n⚠️  Unreachable documents:")
                for file in sorted(self.unreachable_files)[:10]:  # Show first 10
                    print(f"   {file}")
                if len(self.unreachable_files) > 10:
                    print(f"   ... and {len(self.unreachable_files) - 10} more")

            if self.broken_links:
                print("\n❌ Broken links:")
                for link in self.broken_links:
                    print(f"   {link['source']}")
                    print(f"   → {link['target']}")

            success = len(self.unreachable_files) == 0 and len(self.broken_links) == 0

            if success:
                print("\n✅ All documents reachable and links working!")
            else:
                print(
                    "\n❌ Validation failed - unreachable documents or broken links found"
                )

            return success

        except Exception as e:
            print(f"\n🚨 Validation error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Simple document reachability validator"
    )
    parser.add_argument("--workspace-dir", "-w", help="Workspace directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")

    args = parser.parse_args()

    try:
        validator = SimpleDocumentValidator(
            workspace_dir=args.workspace_dir, verbose=args.verbose
        )

        success = validator.validate()
        sys.exit(0 if success else 2)

    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"🚨 Unexpected error: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
