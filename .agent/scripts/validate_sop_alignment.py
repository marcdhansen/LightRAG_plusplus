#!/usr/bin/env python3
"""
SOP Alignment Validation Script

Validates that local SOP documentation properly extends global SOP standards
while maintaining correct hierarchy and symlink integrity.

Usage:
    python .agent/scripts/validate_sop_alignment.py [--verbose] [--fix]
"""

import argparse
import sys
from pathlib import Path


class SOPAlignmentValidator:
    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.agent_dir = self.project_root / ".agent"
        self.sop_dir = self.agent_dir / "docs" / "sop"
        self.global_sop_dir = Path.home() / ".agent" / "docs" / "sop"
        self.global_docs_dir = Path.home() / ".gemini" / "antigravity" / "docs"

        self.errors = []
        self.warnings = []
        self.fixes_applied = []

    def log_error(self, message):
        self.errors.append(message)

    def log_warning(self, message):
        self.warnings.append(message)

    def log_fix(self, message):
        self.fixes_applied.append(message)

    def validate_global_symlinks(self):
        """Validate that required global symlinks exist and resolve correctly."""
        required_global_files = [
            "AGENT_ONBOARDING.md",
            "COLLABORATION.md",
            "GEMINI.md",
            "tdd-workflow.md",
        ]

        global_configs_dir = self.sop_dir / "global-configs"

        for filename in required_global_files:
            symlink_path = global_configs_dir / filename

            if not symlink_path.exists():
                self.log_error(f"Missing required global symlink: {symlink_path}")
                continue

            if not symlink_path.is_symlink():
                self.log_error(f"Required global file is not a symlink: {symlink_path}")
                continue

            target = symlink_path.resolve()
            expected_global = self.global_sop_dir / filename

            if target != expected_global:
                self.log_error(
                    f"Symlink {symlink_path} points to {target}, expected {expected_global}"
                )

    def validate_ecosystem_symlinks(self):
        """Validate that ecosystem documentation symlinks are correct."""
        ecosystem_files = [
            "SKILLS_ECOSYSTEM.md",
            "COMMANDS_ECOSYSTEM.md",
            "COMPLETE_SYMLINK_ECOSYSTEM.md",
        ]

        for filename in ecosystem_files:
            local_path = self.sop_dir / filename

            if not local_path.exists():
                self.log_error(f"Missing ecosystem documentation: {local_path}")
                continue

            if not local_path.is_symlink():
                self.log_error(f"Ecosystem file is not a symlink: {local_path}")
                continue

            target = local_path.resolve()
            expected_global = self.global_docs_dir / filename

            if target != expected_global:
                self.log_error(
                    f"Ecosystem symlink {local_path} points to {target}, expected {expected_global}"
                )

    def validate_local_extensions(self):
        """Validate that local extensions are properly identified and accessible."""
        local_extensions = ["TDD_MANDATORY_GATE.md", "MULTI_PHASE_HANDOFF_PROTOCOL.md"]

        for filename in local_extensions:
            local_path = self.sop_dir / filename

            if not local_path.exists():
                self.log_error(f"Missing required local extension: {local_path}")
                continue

            if local_path.is_symlink():
                self.log_error(f"Local extension should not be a symlink: {local_path}")
                continue

            # Check that file contains proper extension markers
            content = local_path.read_text(errors="ignore")
            if "🚫 MANDATORY" not in content and "MANDATORY GATE" not in content:
                self.log_warning(
                    f"Local extension {filename} should contain mandatory requirement markers"
                )

    def validate_readme_hierarchy(self):
        """Validate that README properly documents hierarchy and references global SOP."""
        readme_path = self.sop_dir / "README.md"

        if not readme_path.exists():
            self.log_error(f"SOP README not found: {readme_path}")
            return

        content = readme_path.read_text(errors="ignore")

        # Check for global SOP references
        if "Global SOP" not in content:
            self.log_error("SOP README should reference Global SOP as base standards")

        if "~/.agent/docs/sop/" not in content:
            self.log_error("SOP README should reference global SOP location")

        # Check for hierarchy documentation
        if "hierarchy" not in content.lower():
            self.log_warning("SOP README should document protocol hierarchy")

        # Check for local extensions documentation
        if "TDD Mandatory Gate" not in content:
            self.log_error("SOP README should reference TDD Mandatory Gate extension")

    def validate_integration_guide(self):
        """Validate that integration guide exists and is comprehensive."""
        guide_path = self.sop_dir / "SOP_INTEGRATION_GUIDE.md"

        if not guide_path.exists():
            self.log_error("SOP Integration Guide not found")
            return

        content = guide_path.read_text(errors="ignore")

        # Check for key sections
        required_sections = [
            "Quick Decision Tree",
            "Protocol Usage Matrix",
            "Conflict Resolution",
            "Workflow Integration",
        ]

        for section in required_sections:
            if section not in content:
                self.log_warning(f"Integration guide missing section: {section}")

    def check_broken_symlinks(self):
        """Check for any broken symlinks in the SOP directory."""
        for item in self.sop_dir.rglob("*"):
            if item.is_symlink():
                if not item.exists():
                    self.log_error(f"Broken symlink found: {item} -> {item.readlink()}")

    def attempt_fixes(self):
        """Attempt to fix common alignment issues automatically."""
        if not hasattr(self, "args") or not self.args.fix:
            return

        # Fix missing global symlinks
        required_global_files = [
            "AGENT_ONBOARDING.md",
            "COLLABORATION.md",
            "GEMINI.md",
            "tdd-workflow.md",
        ]

        global_configs_dir = self.sop_dir / "global-configs"
        global_configs_dir.mkdir(parents=True, exist_ok=True)

        for filename in required_global_files:
            symlink_path = global_configs_dir / filename
            target_path = self.global_sop_dir / filename

            if not symlink_path.exists() and target_path.exists():
                try:
                    symlink_path.symlink_to(target_path)
                    self.log_fix(
                        f"Created missing symlink: {symlink_path} -> {target_path}"
                    )
                except OSError as e:
                    self.log_error(f"Failed to create symlink {symlink_path}: {e}")

        # Fix missing ecosystem symlinks
        ecosystem_files = [
            "SKILLS_ECOSYSTEM.md",
            "COMMANDS_ECOSYSTEM.md",
            "COMPLETE_SYMLINK_ECOSYSTEM.md",
        ]

        for filename in ecosystem_files:
            local_path = self.sop_dir / filename
            target_path = self.global_docs_dir / filename

            if not local_path.exists() and target_path.exists():
                try:
                    local_path.symlink_to(target_path)
                    self.log_fix(
                        f"Created missing ecosystem symlink: {local_path} -> {target_path}"
                    )
                except OSError as e:
                    self.log_error(
                        f"Failed to create ecosystem symlink {local_path}: {e}"
                    )

    def run_validation(self):
        """Run all validation checks."""
        print("🔍 Validating SOP Alignment...")
        print(f"Project Root: {self.project_root}")
        print(f"Local SOP: {self.sop_dir}")
        print(f"Global SOP: {self.global_sop_dir}")
        print(f"Global Docs: {self.global_docs_dir}")
        print("-" * 50)

        # Run all validation checks
        self.validate_global_symlinks()
        self.validate_ecosystem_symlinks()
        self.validate_local_extensions()
        self.validate_readme_hierarchy()
        self.validate_integration_guide()
        self.check_broken_symlinks()

        # Attempt fixes if requested
        self.attempt_fixes()

        # Report results
        self.print_results()

        return len(self.errors) == 0

    def print_results(self):
        """Print validation results."""
        if self.fixes_applied:
            print("🔧 Fixes Applied:")
            for fix in self.fixes_applied:
                print(f"  ✅ {fix}")
            print()

        if self.warnings:
            print("⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  ⚠️  {warning}")
            print()

        if self.errors:
            print("❌ Errors:")
            for error in self.errors:
                print(f"  ❌ {error}")
            print()

        if not self.errors and not self.warnings:
            print("✅ SOP Alignment: All checks passed!")
        elif not self.errors:
            print("✅ SOP Alignment: Passed with warnings")
        else:
            print("❌ SOP Alignment: Failed - please address errors")

        print(
            f"\nSummary: {len(self.errors)} errors, {len(self.warnings)} warnings, {len(self.fixes_applied)} fixes applied"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Validate SOP alignment between local and global standards"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--fix", action="store_true", help="Attempt to fix common issues automatically"
    )
    parser.add_argument(
        "--project-root", help="Project root directory (default: current directory)"
    )

    args = parser.parse_args()

    validator = SOPAlignmentValidator(args.project_root)
    validator.args = args  # Store args for fix method access

    success = validator.run_validation()

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
