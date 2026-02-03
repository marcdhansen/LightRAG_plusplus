#!/usr/bin/env python3

"""
Cross-Reference Integrity Checker
Validates internal documentation references and links
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass
from datetime import datetime


@dataclass
class ReferenceIssue:
    """Represents a documentation reference issue"""

    file_path: str
    line_number: int
    issue_type: str  # 'broken_link', 'circular_reference', 'missing_target', 'dead_end'
    description: str
    severity: str  # 'high', 'medium', 'low'
    context: str


class ReferenceChecker:
    """Cross-reference integrity validation system"""

    def __init__(self):
        self.agent_global = Path.home() / ".agent"
        self.project_agent = Path(".agent")
        self.issues: List[ReferenceIssue] = []

        # Common patterns for different issue types
        self.link_pattern = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")
        self.url_pattern = re.compile(r"https?://[^\s\)]+")

    def check_all_references(self) -> List[ReferenceIssue]:
        """Check all documentation references"""
        print("🔗 Checking cross-reference integrity...")
        print("====================================")

        self.issues.clear()

        # Get all markdown files
        md_files = self._find_markdown_files()

        for md_file in md_files:
            self._check_file_references(md_file)

        print(f"📊 Found {len(self.issues)} reference issues")
        return self.issues

    def _find_markdown_files(self) -> List[Path]:
        """Find all markdown files in project"""
        md_files = []

        # Search in both global and project locations
        for base_path in [self.agent_global, self.project_agent]:
            for md_file in base_path.rglob("**/*.md"):
                md_files.append(md_file)

        return md_files

    def _check_file_references(self, file_path: Path):
        """Check references in a single file"""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                lines = content.split("\n")

            for line_num, line in enumerate(lines, 1):
                self._check_line_references(file_path, line_num, line)

        except Exception as e:
            self.issues.append(
                ReferenceIssue(
                    file_path=str(file_path),
                    line_number=0,
                    issue_type="file_access",
                    description=f"Cannot read file: {e}",
                    severity="high",
                    context="file_error",
                )
            )

    def _check_line_references(self, file_path: Path, line_num: int, line: str):
        """Check references in a single line"""

        # Check for markdown links
        for match in self.link_pattern.finditer(line):
            link_text = match.group(1)
            link_target = match.group(2)

            # Check if reference is resolvable
            issue = self._check_reference(
                file_path, link_text, link_target, line_num, line
            )
            if issue:
                self.issues.append(issue)

        # Check for circular references
        self._check_circular_references(file_path, line_num, line)

    def _check_reference(
        self,
        file_path: Path,
        link_text: str,
        link_target: str,
        line_num: int,
        line: str,
    ) -> ReferenceIssue:
        """Check if a reference is valid"""

        # Skip external URLs
        if self.url_pattern.match(link_target):
            return None

        # Check for relative path resolution
        target_path = self._resolve_target_path(file_path, link_target)

        if not target_path.exists():
            severity = "high" if link_text.endswith(".md") else "medium"
            return ReferenceIssue(
                file_path=str(file_path),
                line_number=line_num,
                issue_type="missing_target",
                description=f"Target not found: {link_target} -> {target_path}",
                severity=severity,
                context=line.strip(),
            )

        # Check for circular references
        if target_path.resolve() == file_path.resolve():
            return ReferenceIssue(
                file_path=str(file_path),
                line_number=line_num,
                issue_type="circular_reference",
                description=f"Circular reference: {link_text} points to self",
                severity="high",
                context=line.strip(),
            )

        return None

    def _resolve_target_path(self, source_file: Path, target: str) -> Path:
        """Resolve target path relative to source file"""
        target_path = Path(target)

        # Handle absolute paths
        if target_path.is_absolute():
            return target_path

        # Resolve relative to source file
        return (source_file.parent / target_path).resolve()

    def _check_circular_references(self, file_path: Path, line_num: int, line: str):
        """Check for circular references in documentation"""
        # Simple heuristic: look for self-referencing patterns
        if "points to self" in line.lower() or "circular" in line.lower():
            self.issues.append(
                ReferenceIssue(
                    file_path=str(file_path),
                    line_number=line_num,
                    issue_type="circular_reference",
                    description="Potential circular reference detected",
                    severity="medium",
                    context=line.strip(),
                )
            )

    def generate_report(self, output_path: Path):
        """Generate detailed integrity report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_issues": len(self.issues),
            "issues_by_severity": {},
            "issues_by_type": {},
            "issues": [],
        }

        for issue in self.issues:
            severity_key = issue.severity
            type_key = issue.issue_type

            if severity_key not in report["issues_by_severity"]:
                report["issues_by_severity"][severity_key] = 0
            if type_key not in report["issues_by_type"]:
                report["issues_by_type"][type_key] = 0

            report["issues_by_severity"][severity_key] += 1
            report["issues_by_type"][type_key] += 1
            report["issues"].append(
                {
                    "file_path": issue.file_path,
                    "line_number": issue.line_number,
                    "issue_type": issue.issue_type,
                    "description": issue.description,
                    "severity": issue.severity,
                    "context": issue.context,
                }
            )

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📝 Reference integrity report: {output_path}")

    def print_summary(self):
        """Print validation summary"""
        print(f"\n📋 Reference Integrity Summary:")
        print("=" * 50)
        print(f"Total issues: {len(self.issues)}")

        if self.issues:
            severity_counts = {}
            type_counts = {}

            for issue in self.issues:
                severity_counts[issue.severity] = (
                    severity_counts.get(issue.severity, 0) + 1
                )
                type_counts[issue.issue_type] = type_counts.get(issue.issue_type, 0) + 1

            print(f"\n🚨 Issues by Severity:")
            for severity in ["high", "medium", "low"]:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    print(f"   {severity.title()}: {count}")

            print(f"\n📋 Issues by Type:")
            for issue_type in type_counts:
                count = type_counts[issue_type]
                if count > 0:
                    print(f"   {issue_type}: {count}")

            print(f"\n🔧 Suggested fixes:")
            print("   1. Update broken links with correct targets")
            print("   2. Remove circular references")
            print("   3. Use relative paths for internal references")
            print("   4. Validate links before committing")
        else:
            print("✅ No reference issues detected!")

    def auto_fix_simple_issues(self) -> int:
        """Attempt to fix simple issues automatically"""
        print("🔧 Attempting automatic fixes...")

        fixed_count = 0
        for issue in self.issues[:]:  # Copy to avoid modification during iteration
            if issue.issue_type == "missing_target":
                # Try to create missing directories
                target_path = Path(issue.description.split(" -> ")[1])
                if not target_path.exists() and "." in str(target_path):
                    try:
                        target_path.parent.mkdir(parents=True, exist_ok=True)
                        if target_path.suffix == ".md":
                            target_path.write_text(
                                "# Placeholder for "
                                + target_path.name
                                + "\n\nThis file was referenced but missing."
                            )
                            fixed_count += 1
                            print(f"   ✅ Created missing file: {target_path}")
                    except Exception as e:
                        print(f"   ❌ Failed to create {target_path}: {e}")

        return fixed_count


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Cross-Reference Integrity Checker")
    parser.add_argument(
        "--check", action="store_true", help="Check all reference integrity"
    )
    parser.add_argument("--report", help="Generate JSON report to file")
    parser.add_argument(
        "--auto-fix", action="store_true", help="Attempt automatic fixes"
    )
    parser.add_argument("--summary", action="store_true", help="Print summary only")

    args = parser.parse_args()

    checker = ReferenceChecker()

    if args.check or args.report or args.auto_fix:
        issues = checker.check_all_references()

        if args.report:
            checker.generate_report(Path(args.report))

        if args.auto_fix:
            fixed = checker.auto_fix_simple_issues()
            print(f"\n🔧 Auto-fixed {fixed_count} issues")

        if args.summary or not args.report:
            checker.print_summary()

        return len(issues) > 0
    else:
        parser.print_help()


if __name__ == "__main__":
    exit(main())
