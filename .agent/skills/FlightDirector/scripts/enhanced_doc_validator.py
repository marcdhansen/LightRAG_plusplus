#!/usr/bin/env python3
"""
Enhanced Document Reachability Validator with Auto-Fix

Validates and fixes document reachability issues automatically.
"""

import os
import re
import sys
import json
import argparse
from pathlib import Path
from typing import Set, Dict, List, Tuple, Optional
from urllib.parse import urlparse
import time


class EnhancedDocumentValidator:
    def __init__(
        self,
        workspace_dir: str | None = None,
        verbose: bool = False,
        auto_fix: bool = False,
    ):
        self.workspace_dir = Path(workspace_dir) if workspace_dir else Path.cwd()
        self.verbose = verbose
        self.auto_fix = auto_fix
        self.broken_links = []
        self.suggested_fixes = []
        self.unreachable_files = []

    def _find_global_index(self) -> Path:
        """Find GLOBAL_INDEX.md file with proper hierarchy."""
        candidates = [
            self.workspace_dir / ".agent" / "docs" / "GLOBAL_INDEX.md",
            Path.home()
            / ".agent"
            / "docs"
            / "GLOBAL_INDEX.md",  # Single source of truth
            Path.home() / ".gemini" / ".agent" / "docs" / "GLOBAL_INDEX.md",
        ]

        for candidate in candidates:
            if candidate.exists():
                if self.verbose:
                    print(f"Found GLOBAL_INDEX.md at: {candidate}")
                return candidate

        raise FileNotFoundError(
            f"GLOBAL_INDEX.md not found in any of these locations: {candidates}"
        )

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

    def _resolve_path(self, link_target: str, source_file: Path) -> Optional[Path]:
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

    def _find_target_file(self, link_target: str) -> Optional[Path]:
        """Try to find a file matching the link target using various strategies."""
        # Extract filename from path
        filename = Path(link_target).name

        # Common directory names to search
        search_dirs = [
            self.workspace_dir,
            self.workspace_dir / ".agent" / "docs",
            self.workspace_dir / "docs",
            Path.home() / ".gemini" / ".agent" / "docs",
            Path.home() / ".agent" / "docs",
        ]

        # Search for the file in all reasonable locations
        found_files = []
        for search_dir in search_dirs:
            for candidate in search_dir.rglob(filename):
                if candidate.is_file() and candidate.suffix == ".md":
                    found_files.append(candidate)

        # Return the most likely candidate (prefer workspace files)
        if found_files:
            # Sort by preference: workspace > global > other
            def score_path(path: Path) -> int:
                score = 0
                if str(path).startswith(str(self.workspace_dir)):
                    score += 100  # Prefer workspace files
                if "docs" in str(path):
                    score += 10  # Prefer docs directories
                return score

            found_files.sort(key=score_path, reverse=True)
            return found_files[0]

        return None

    def _suggest_path_fix(
        self, source_file: Path, broken_link: str, resolved_path: Path
    ) -> Optional[str]:
        """Suggest a fix for a broken link."""
        # Try to find the actual file
        target_file = self._find_target_file(broken_link)

        if target_file:
            # Calculate correct relative path
            try:
                relative_path = os.path.relpath(target_file, source_file.parent)
                return relative_path
            except ValueError:
                # Different drives, can't make relative
                return str(target_file.resolve())

        return None

    def _validate_and_fix_links(self, file_path: Path) -> List[Dict]:
        """Validate links in a file and suggest fixes."""
        links = self._extract_links(file_path)
        issues = []

        for link_text, link_target in links:
            resolved = self._resolve_path(link_target, file_path)

            if resolved is None:
                continue  # External URL

            if not resolved.exists():
                # Try to suggest a fix
                suggested_fix = self._suggest_path_fix(file_path, link_target, resolved)

                issue = {
                    "source": str(file_path),
                    "target": link_target,
                    "resolved": str(resolved),
                    "suggested_fix": suggested_fix,
                    "link_text": link_text,
                }
                issues.append(issue)
                self.broken_links.append(issue)

        return issues

    def _fix_file_links(self, file_path: Path, issues: List[Dict]) -> bool:
        """Fix broken links in a file."""
        if not self.auto_fix:
            return False

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Apply fixes
            for issue in issues:
                if issue["suggested_fix"]:
                    old_pattern = f"[{issue['link_text']}]({issue['target']})"
                    new_pattern = f"[{issue['link_text']}]({issue['suggested_fix']})"
                    content = content.replace(old_pattern, new_pattern)

                    if self.verbose:
                        print(f"  Fixed: {issue['target']} → {issue['suggested_fix']}")

            # Write back the fixed content
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            return True

        except Exception as e:
            print(f"Error fixing {file_path}: {e}")
            return False

    def _check_duplicates(self) -> List[str]:
        """Check for duplicate GLOBAL_INDEX.md files."""
        search_paths = [
            str(Path.home() / ".agent"),
            str(Path.home() / ".gemini"),
            str(self.workspace_dir),
            str(self.workspace_dir / ".agent"),
        ]

        found_indices = []
        for search_path in search_paths:
            for md_file in Path(search_path).rglob("GLOBAL_INDEX.md"):
                if md_file.is_file():
                    found_indices.append(str(md_file))

        # Determine which should be kept
        main_index = Path.home() / ".agent" / "docs" / "GLOBAL_INDEX.md"
        duplicates = [f for f in found_indices if f != str(main_index)]

        return duplicates

    def validate(self) -> bool:
        """Run validation with optional auto-fix."""
        print("🔍 Enhanced Document Reachability Validation")
        print("=" * 50)

        try:
            # Step 1: Check for duplicates
            duplicates = self._check_duplicates()
            if duplicates:
                print(f"⚠️  Found {len(duplicates)} duplicate GLOBAL_INDEX.md files:")
                for dup in duplicates:
                    print(f"   {dup}")
                if self.auto_fix:
                    for dup in duplicates:
                        try:
                            os.remove(dup)
                            print(f"   ✅ Removed: {dup}")
                        except Exception as e:
                            print(f"   ❌ Could not remove {dup}: {e}")

            # Step 2: Find global index
            self.global_index_path = self._find_global_index()
            print(f"✅ Global index: {self.global_index_path}")

            # Step 3: Validate links in global index
            print("🔗 Validating links in GLOBAL_INDEX.md...")
            global_index_issues = self._validate_and_fix_links(self.global_index_path)

            if global_index_issues:
                print(
                    f"❌ Found {len(global_index_issues)} broken links in GLOBAL_INDEX.md"
                )

                if self.auto_fix:
                    if self._fix_file_links(
                        self.global_index_path, global_index_issues
                    ):
                        print("✅ Applied fixes to GLOBAL_INDEX.md")
                        # Re-validate to confirm fixes
                        global_index_issues = self._validate_and_fix_links(
                            self.global_index_path
                        )
                        if global_index_issues:
                            print(
                                f"⚠️  {len(global_index_issues)} issues remain after auto-fix"
                            )
                        else:
                            print("✅ All links in GLOBAL_INDEX.md are now working!")
                else:
                    print("\n💡 Suggested fixes for GLOBAL_INDEX.md:")
                    for issue in global_index_issues[:5]:  # Show first 5
                        if issue["suggested_fix"]:
                            print(f"   {issue['target']} → {issue['suggested_fix']}")
                    if len(global_index_issues) > 5:
                        print(f"   ... and {len(global_index_issues) - 5} more")
            else:
                print("✅ All links in GLOBAL_INDEX.md are working")

            # Step 4: Check overall document reachability (simplified)
            print("\n📚 Checking document reachability...")
            reachable_count = len(self._extract_links(self.global_index_path))
            broken_count = len(global_index_issues)

            print(f"✅ Links in GLOBAL_INDEX.md: {reachable_count}")
            print(f"❌ Broken links: {broken_count}")

            # Report results
            success = len(duplicates) == 0 and broken_count == 0

            if success:
                print("\n✅ All validations passed!")
            else:
                print(
                    f"\n❌ Validation failed - {len(duplicates)} duplicates, {broken_count} broken links"
                )

            return success

        except Exception as e:
            print(f"\n🚨 Validation error: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(
        description="Enhanced document reachability validator with auto-fix"
    )
    parser.add_argument("--workspace-dir", "-w", help="Workspace directory")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--auto-fix", action="store_true", help="Automatically fix found issues"
    )
    parser.add_argument(
        "--check-only", action="store_true", help="Only check, no fixes"
    )

    args = parser.parse_args()

    try:
        validator = EnhancedDocumentValidator(
            workspace_dir=args.workspace_dir,
            verbose=args.verbose,
            auto_fix=args.auto_fix,
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
