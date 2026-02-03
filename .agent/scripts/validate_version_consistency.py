#!/usr/bin/env python3

"""
Version Consistency Validator
Ensures global and project versions stay aligned and detects drift
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class VersionConflict:
    """Represents a version conflict between sources"""

    file_path: str
    global_version: Optional[str]
    project_version: Optional[str]
    conflict_type: str  # 'missing', 'outdated', 'format_mismatch'
    severity: str  # 'high', 'medium', 'low'


class VersionValidator:
    """Validates version consistency across information sources"""

    def __init__(self):
        self.agent_global = Path.home() / ".agent"
        self.project_agent = Path(".agent")
        self.conflicts: List[VersionConflict] = []

    def validate_all(self) -> List[VersionConflict]:
        """Validate all version consistency checks"""
        print("🔍 Checking version consistency...")
        print("==================================")

        self.conflicts.clear()

        # Check key alignment files
        self._check_file_alignment("AGENTS.md")
        self._check_skill_versions()
        self._check_protocol_versions()
        self._check_documentation_sync()

        return self.conflicts

    def _check_file_alignment(self, filename: str):
        """Check if global and project versions are aligned"""
        global_file = self.agent_global / filename
        project_link = self.project_agent / "docs" / "sop" / "global-configs" / filename

        print(f"   📄 Checking {filename} alignment...")

        if not global_file.exists():
            self.conflicts.append(
                VersionConflict(
                    file_path=str(global_file),
                    global_version=None,
                    project_version=self._get_file_version(project_link),
                    conflict_type="missing",
                    severity="high",
                )
            )
            print(f"      ❌ Global {filename} missing")
            return

        if not project_link.exists():
            self.conflicts.append(
                VersionConflict(
                    file_path=str(project_link),
                    global_version=self._get_file_version(global_file),
                    project_version=None,
                    conflict_type="missing",
                    severity="medium",
                )
            )
            print(f"      ⚠️  Project link to {filename} missing")
            return

        # Compare versions if both exist
        global_version = self._get_file_version(global_file)
        project_version = self._get_file_version(project_link)

        if global_version != project_version:
            severity = (
                "high"
                if self._is_major_version_mismatch(global_version, project_version)
                else "medium"
            )
            self.conflicts.append(
                VersionConflict(
                    file_path=str(project_link),
                    global_version=global_version,
                    project_version=project_version,
                    conflict_type="outdated",
                    severity=severity,
                )
            )
            print(
                f"      ❌ Version mismatch: Global={global_version}, Project={project_version}"
            )
        else:
            print(f"      ✅ {filename} versions aligned")

    def _check_skill_versions(self):
        """Check skill version consistency"""
        print("   🛠️  Checking skill versions...")

        # Get skill registry
        try:
            result = subprocess.run(
                [
                    "python3",
                    ".agent/scripts/discover_skills.py",
                    "--discover",
                    "--generate-registry",
                    "/tmp/skill_registry.json",
                ],
                capture_output=True,
                text=True,
                cwd=".",
            )

            if result.returncode == 0:
                with open("/tmp/skill_registry.json", "r") as f:
                    registry = json.load(f)

                for name, skill in registry["skills"].items():
                    if skill["version"] == "unknown" or not skill["version"]:
                        self.conflicts.append(
                            VersionConflict(
                                file_path=skill["path"],
                                global_version=None,
                                project_version="unknown",
                                conflict_type="format_mismatch",
                                severity="medium",
                            )
                        )
                        print(f"      ⚠️  {name}: Missing version information")
            else:
                print("      ❌ Failed to generate skill registry")
        except Exception as e:
            print(f"      ❌ Error checking skill versions: {e}")

    def _check_protocol_versions(self):
        """Check protocol document versions"""
        print("   📋 Checking protocol versions...")

        # Check for version consistency in key protocol files
        protocol_files = [
            ("GLOBAL_PROTOCOL.md", "rules"),
            ("ROADMAP.md", "rules"),
            ("CROSS_COMPATIBILITY.md", "docs/sop/global-configs"),
        ]

        for filename, relative_dir in protocol_files:
            global_file = self.agent_global / relative_dir / filename
            project_file = self.project_agent / relative_dir / filename

            if global_file.exists() and project_file.exists():
                global_version = self._get_file_version(global_file)
                project_version = self._get_file_version(project_file)

                if global_version != project_version:
                    self.conflicts.append(
                        VersionConflict(
                            file_path=str(project_file),
                            global_version=global_version,
                            project_version=project_version,
                            conflict_type="outdated",
                            severity="high",
                        )
                    )
                    print(
                        f"      ❌ {filename}: Global={global_version}, Project={project_version}"
                    )
                else:
                    print(f"      ✅ {filename}: Versions aligned")

    def _check_documentation_sync(self):
        """Check if documentation references are up-to-date"""
        print("   🔗 Checking documentation references...")

        # This would check for broken internal links, version references, etc.
        # For now, just check if key docs exist
        key_docs = ["docs/GLOBAL_INDEX.md", "docs/sop/global-configs/AGENTS.md"]

        for doc in key_docs:
            doc_path = Path(doc)
            if not doc_path.exists():
                self.conflicts.append(
                    VersionConflict(
                        file_path=str(doc_path),
                        global_version="expected",
                        project_version="missing",
                        conflict_type="missing",
                        severity="medium",
                    )
                )
                print(f"      ⚠️  Missing documentation: {doc}")

def _get_file_version(self, file_path: Path) -> str:
        """Extract version from file (simple heuristics)"""
        if not file_path.exists():
            return ""

        try:
            with open(file_path, "r") as f:
                content = f.read()

            # Look for version in frontmatter or common patterns
            import re

            # YAML frontmatter version
            version_match = re.search(r'version[:\s*["\']([^"\']+)["\']', content)
            if version_match:
                return version_match.group(1).strip()

            # Common version patterns
            version_patterns = [
                r'version[:\s*([0-9]+\.[0-9]+)',
                r'v([0-9]+\.[0-9]+)',
                r'Updated:[\s*([0-9]+-[0-9]+-[0-9]+)',
                r'Last Updated:[\s*([0-9]+-[0-9]+-[0-9]+)'
            ]

            for pattern in version_patterns:
                match = re.search(pattern, content)
                if match:
                    return match.group(1).strip()

            return "unknown"
        except Exception:
            return "unknown"

    def _is_major_version_mismatch(self, v1: str, v2: str) -> bool:
        """Check if versions have major differences"""
        try:
            major1 = v1.split(".")[0] if "." in v1 else v1
            major2 = v2.split(".")[0] if "." in v2 else v2
            return major1 != major2
        except:
            return False

    def generate_report(self, output_path: Path):
        """Generate detailed consistency report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_conflicts": len(self.conflicts),
            "conflicts_by_severity": {},
            "conflicts_by_type": {},
            "conflicts": [],
        }

        for conflict in self.conflicts:
            severity_key = conflict.severity
            type_key = conflict.conflict_type

            if severity_key not in report["conflicts_by_severity"]:
                report["conflicts_by_severity"][severity_key] = 0
            if type_key not in report["conflicts_by_type"]:
                report["conflicts_by_type"][type_key] = 0

            report["conflicts_by_severity"][severity_key] += 1
            report["conflicts_by_type"][type_key] += 1
            report["conflicts"].append(
                {
                    "file_path": conflict.file_path,
                    "global_version": conflict.global_version,
                    "project_version": conflict.project_version,
                    "conflict_type": conflict.conflict_type,
                    "severity": conflict.severity,
                }
            )

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        print(f"📝 Version consistency report: {output_path}")

    def print_summary(self):
        """Print validation summary"""
        print(f"\n📊 Version Consistency Summary:")
        print("=" * 40)
        print(f"Total conflicts: {len(self.conflicts)}")

        if self.conflicts:
            severity_counts = {}
            for conflict in self.conflicts:
                severity_counts[conflict.severity] = (
                    severity_counts.get(conflict.severity, 0) + 1
                )

            for severity in ["high", "medium", "low"]:
                count = severity_counts.get(severity, 0)
                if count > 0:
                    print(f"   {severity.title()} severity: {count}")

            print(f"\n🔧 Suggested actions:")
            print("   1. Update project files to match global versions")
            print("   2. Use symlinks instead of copies")
            print("   3. Run regular consistency checks")
        else:
            print("✅ No version conflicts detected!")


def main():
    """Main CLI interface"""
    import argparse

    parser = argparse.ArgumentParser(description="Version Consistency Validator")
    parser.add_argument(
        "--validate", action="store_true", help="Validate all version consistency"
    )
    parser.add_argument("--report", help="Generate JSON report to file")
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix common issues"
    )
    parser.add_argument("--summary", action="store_true", help="Print summary only")

    args = parser.parse_args()

    validator = VersionValidator()

    if args.validate or args.report or args.fix:
        conflicts = validator.validate_all()

        if args.report:
            validator.generate_report(Path(args.report))

        if args.fix:
            print("🔧 Auto-fix not implemented yet")

        if args.summary or not args.report:
            validator.print_summary()

        return len(conflicts) > 0
    else:
        print("Use --validate to check consistency")
        return 0


if __name__ == "__main__":
    exit(main())
