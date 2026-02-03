#!/usr/bin/env python3
"""
Document Reachability Validator

Validates that all documents are reachable from GLOBAL_INDEX.md and that all links are working.
This is a critical safety gate for the Flight Director RTB process.

Usage:
    python validate_document_reachability.py [--workspace-dir PATH] [--verbose] [--fix]
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


class DocumentReachabilityValidator:
    def __init__(self, workspace_dir: str | None = None, verbose: bool = False):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.verbose = verbose
        self.issues = []
        self.warnings = []
        self.reachable_docs = set()
        self.all_docs = set()
        self.broken_links = []

        # Find global index file
        self.global_index_path = self._find_global_index()

    def _find_global_index(self) -> Path:
        """Find the GLOBAL_INDEX.md file following the hierarchy."""
        # Check multiple possible locations
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

        raise FileNotFoundError(
            f"GLOBAL_INDEX.md not found in any of these locations: {candidates}"
        )

    def _extract_markdown_links(self, file_path: Path) -> List[Tuple[str, str]]:
        """Extract all markdown links from a file.

        Returns:
            List of tuples (link_text, link_target)
        """
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception as e:
            self.issues.append(f"Failed to read {file_path}: {e}")
            return []

        # Regex patterns for different types of links
        patterns = [
            r"\[([^\]]+)\]\(([^)]+)\)",  # [text](link)
            r"\[([^\]]+)\]:\s*([^\s]+)",  # [text]: link
        ]

        links = []
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                link_text, link_target = match
                links.append((link_text, link_target))

        return links

    def _resolve_link_path(self, link_target: str, source_file: Path) -> Path | None:
        """Resolve a link target relative to the source file."""
        # Handle URL schemes (http, https, etc.)
        if urlparse(link_target).scheme:
            return None  # External URL, skip validation

        # Handle anchor links
        if link_target.startswith("#"):
            return source_file  # Same file anchor

        # Remove fragment identifiers
        link_target = link_target.split("#")[0]

        # Handle absolute paths
        if link_target.startswith("/"):
            return Path(link_target)

        # Handle relative paths
        return (source_file.parent / link_target).resolve()

    def _discover_all_markdown_files(self, start_dir: Path) -> Set[Path]:
        """Discover all markdown files in the workspace."""
        markdown_files = set()
        visited_dirs = set()

        # Define relevant directories to search - be more selective to avoid symlink loops
        search_dirs = [
            self.workspace_dir,
            self.workspace_dir / ".agent" / "docs",
            self.workspace_dir / ".agent" / "rules",
            Path.home() / ".gemini" / ".agent" / "docs",
        ]

        def safe_walk(directory: Path):
            """Safely walk directory tree avoiding symlink loops."""
            try:
                real_dir = directory.resolve()
                if real_dir in visited_dirs:
                    if self.verbose:
                        print(f"   Already visited directory: {real_dir}")
                    return
                visited_dirs.add(real_dir)

                for item in directory.iterdir():
                    if item.is_symlink():
                        try:
                            real_item = item.resolve()
                            if real_item.is_dir():
                                # Recursively walk symlinked directory
                                safe_walk(real_item)
                            elif real_item.suffix == ".md":
                                markdown_files.add(real_item)
                        except (OSError, RuntimeError):
                            # Skip problematic symlinks
                            continue
                    elif item.is_dir():
                        # Skip problematic directories
                        if any(
                            part
                            in [
                                "node_modules",
                                ".git",
                                ".venv",
                                "__pycache__",
                                "skills",
                            ]
                            for part in item.parts
                        ):
                            continue
                        safe_walk(item)
                    elif item.suffix == ".md":
                        markdown_files.add(
                            item.resolve() if item.is_symlink() else item
                        )
            except (OSError, RuntimeError) as e:
                if self.verbose:
                    print(f"   Warning: Could not walk {directory}: {e}")
                return

        for search_dir in search_dirs:
            if search_dir.exists():
                safe_walk(search_dir)

        return markdown_files

    def _crawl_reachable_documents(
        self, start_path: Path, visited: Set[Path] | None = None, depth: int = 0
    ) -> Set[Path]:
        """Recursively crawl all documents reachable from the starting document."""
        if visited is None:
            visited = set()

        # Prevent infinite recursion with depth limit
        if depth > 50:
            if self.verbose:
                print(f"   Max depth reached at: {start_path}")
            return visited

        # Handle symlinks safely
        try:
            real_path = start_path.resolve()
        except (OSError, RuntimeError):
            # Skip broken symlinks
            self.broken_links.append(
                {
                    "source": str(start_path),
                    "target": "symlink",
                    "resolved": str(start_path),
                    "error": "Broken or circular symlink",
                }
            )
            return visited

        if real_path in visited or not real_path.exists():
            return visited

        visited.add(real_path)

        if self.verbose:
            print(f"Crawling (depth {depth}): {real_path}")

        links = self._extract_markdown_links(real_path)

        for link_text, link_target in links:
            resolved_path = self._resolve_link_path(link_target, real_path)

            if resolved_path is None:
                continue  # External URL

            # Check if the file exists
            if not resolved_path.exists():
                self.broken_links.append(
                    {
                        "source": str(real_path),
                        "target": link_target,
                        "resolved": str(resolved_path),
                        "error": "File not found",
                    }
                )
                continue

            # Only crawl markdown files
            if resolved_path.suffix == ".md":
                # Skip problematic paths that might cause symlink loops
                # Skills directories are particularly problematic due to circular symlinks
                problematic_parts = [
                    "skills",
                    "node_modules",
                    ".git",
                    "__pycache__",
                    "antigravity",
                    "task-",
                ]
                if any(
                    problematic in str(part).lower()
                    for part in resolved_path.parts
                    for problematic in problematic_parts
                ):
                    if self.verbose:
                        print(f"   Skipping problematic path: {resolved_path}")
                    continue
                self._crawl_reachable_documents(resolved_path, visited, depth + 1)

        return visited

    def validate(self) -> bool:
        """Perform the complete validation."""
        print("🔍 Document Reachability Validation")
        print("=" * 50)

        try:
            # Step 1: Discover all markdown files
            print("📚 Discovering all markdown files...")
            self.all_docs = self._discover_all_markdown_files(self.workspace_dir)
            print(f"   Found {len(self.all_docs)} markdown files")

            # Step 2: Crawl reachable documents from GLOBAL_INDEX.md
            print("🔗 Crawling reachable documents from GLOBAL_INDEX.md...")
            self.reachable_docs = self._crawl_reachable_documents(
                self.global_index_path
            )
            print(f"   Found {len(self.reachable_docs)} reachable documents")

            # Step 3: Find unreachable documents
            unreachable_docs = self.all_docs - self.reachable_docs

            # Step 4: Report results
            success = True

            if self.broken_links:
                print("\n❌ BROKEN LINKS:")
                for link in self.broken_links:
                    print(f"   {link['source']}")
                    print(f"   → {link['target']} ({link['error']})")
                    print()
                success = False

            if unreachable_docs:
                print("\n⚠️  UNREACHABLE DOCUMENTS:")
                for doc in sorted(unreachable_docs):
                    try:
                        relative_path = doc.relative_to(self.workspace_dir)
                    except ValueError:
                        # If not relative to workspace, use absolute path
                        relative_path = doc
                    print(f"   {relative_path}")
                print(f"\n   Total: {len(unreachable_docs)} unreachable documents")
                success = False

            if success:
                print("\n✅ All documents reachable and links working!")

            return success

        except Exception as e:
            print(f"\n🚨 VALIDATION ERROR: {e}")
            self.issues.append(f"Validation failed: {e}")
            return False

    def generate_report(self) -> Dict:
        """Generate a detailed validation report."""
        unreachable_docs = self.all_docs - self.reachable_docs

        return {
            "timestamp": time.time(),
            "workspace_dir": str(self.workspace_dir),
            "global_index_path": str(self.global_index_path),
            "total_documents": len(self.all_docs),
            "reachable_documents": len(self.reachable_docs),
            "unreachable_documents": len(unreachable_docs),
            "broken_links": len(self.broken_links),
            "unreachable_document_list": [
                str(d.relative_to(self.workspace_dir))
                if str(d).startswith(str(self.workspace_dir))
                else str(d)
                for d in sorted(unreachable_docs)
            ],
            "broken_link_list": self.broken_links,
            "success": len(unreachable_docs) == 0 and len(self.broken_links) == 0,
        }


def main():
    parser = argparse.ArgumentParser(
        description="Validate document reachability from GLOBAL_INDEX.md"
    )
    parser.add_argument("--workspace-dir", "-w", help="Workspace directory to validate")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix issues (future feature)"
    )
    parser.add_argument("--output", "-o", help="Output report to JSON file")

    args = parser.parse_args()

    try:
        validator = DocumentReachabilityValidator(
            workspace_dir=args.workspace_dir, verbose=args.verbose
        )

        success = validator.validate()

        if args.output:
            report = validator.generate_report()
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"\n📄 Report saved to: {args.output}")

        # Exit codes: 0 = success, 1 = warnings, 2 = errors
        if not success:
            sys.exit(2)  # Block RTB completion
        else:
            sys.exit(0)  # Success

    except FileNotFoundError as e:
        print(f"🚨 CRITICAL ERROR: {e}")
        sys.exit(2)
    except KeyboardInterrupt:
        print("\n⚠️ Validation interrupted")
        sys.exit(130)
    except Exception as e:
        print(f"🚨 UNEXPECTED ERROR: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()
