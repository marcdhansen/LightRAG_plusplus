#!/usr/bin/env python3
import re
import sys
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DOCS_DIR = PROJECT_ROOT / "docs"
ARCH_FILE = DOCS_DIR / "ARCHITECTURE.md"


def check_link_target(source_file: Path, link_target: str) -> bool:
    """
    Checks if a link target exists relative to the source file.
    """
    if link_target.startswith("http") or link_target.startswith("#"):
        return True

    # Handle absolute paths (rare in this repo, but possible)
    if link_target.startswith("/"):
        # Assuming relative to project root for simplicity, or just fail
        target_path = PROJECT_ROOT / link_target.lstrip("/")
    else:
        target_path = (source_file.parent / link_target).resolve()

    if not target_path.exists():
        print(
            f"  ❌ Broken link in {source_file.name}: {link_target} -> {target_path} (NOT FOUND)"
        )
        return False
    return True


def validate_subsystems():
    print(f"🔍 Validating Architecture Subsystems defined in {ARCH_FILE.name}...")

    if not ARCH_FILE.exists():
        print(f"🔥 Critical: {ARCH_FILE} does not exist!")
        sys.exit(1)

    content = ARCH_FILE.read_text()

    # Regex to find links to subsystems/
    # Matches: [Label](subsystems/FileName.md)
    subsystem_links = re.findall(r"\[.*?\]\((subsystems/[a-zA-Z0-9_]+\.md)\)", content)

    if not subsystem_links:
        print(
            "⚠️ No subsystems found in ARCHITECTURE.md using pattern 'subsystems/*.md'"
        )
        sys.exit(0)

    print(f"✅ Found {len(subsystem_links)} registered subsystems.")

    all_passed = True

    for relative_path in subsystem_links:
        full_path = DOCS_DIR / relative_path

        if not full_path.exists():
            print(f"❌ Subsystem missing: {relative_path}")
            all_passed = False
            continue

        print(f"  Existing: {relative_path}")

        # Now validate links INSIDE this subsystem file
        sub_content = full_path.read_text()
        links = re.findall(r"\[.*?\]\((.*?)\)", sub_content)

        temp_passed = True
        for link in links:
            if not check_link_target(full_path, link):
                temp_passed = False

        if not temp_passed:
            print(f"    ⚠️ Internal link errors in {relative_path}")
            all_passed = False

    if all_passed:
        print("\n🎉 All subsystems validated successfully!")
        sys.exit(0)
    else:
        print("\n💥 Documentation validation failed.")
        sys.exit(1)


if __name__ == "__main__":
    validate_subsystems()
