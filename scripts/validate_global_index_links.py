#!/usr/bin/env python3
"""
Global Index Link Validator

Validates links in the GLOBAL_INDEX.md file, handling the complex relative path structure.
"""

import re
import sys
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
GLOBAL_INDEX_PATH = PROJECT_ROOT / ".agent" / "GLOBAL" / "index" / "GLOBAL_INDEX.md"


def extract_links(file_path: Path) -> set[str]:
    """
    Extracts all local markdown links from a file.
    """
    if not file_path.exists():
        return set()

    content = file_path.read_text(errors="ignore")
    # Matches [Label](path/to/file.md) or [Label](file.md)
    # Also matches [Label](path/to/file.md#anchor)
    links = re.findall(r"\[.*?\]\(([\w\-\./]+\.md)(?:#.*)?\)", content)
    return set(links)


def resolve_global_index_link(target_link: str) -> Path:
    """
    Resolves a relative link from GLOBAL_INDEX.md to an absolute path.
    GLOBAL_INDEX.md is located at .agent/GLOBAL/index/GLOBAL_INDEX.md
    """
    global_index_dir = GLOBAL_INDEX_PATH.parent
    return (global_index_dir / target_link).resolve()


def check_global_index_links():
    """Check links in GLOBAL_INDEX.md"""

    if not GLOBAL_INDEX_PATH.exists():
        print(f"❌ Global index not found: {GLOBAL_INDEX_PATH}")
        sys.exit(1)

    print("🔍 Checking links in GLOBAL_INDEX.md...")
    print(f"📍 Global Index: {GLOBAL_INDEX_PATH}")
    print(f"📂 Project Root: {PROJECT_ROOT}")

    links = extract_links(GLOBAL_INDEX_PATH)
    broken_links = []

    for link in links:
        # Skip external URLs and anchors
        if link.startswith("http") or link.startswith("#"):
            continue

        resolved_path = resolve_global_index_link(link)

        if not resolved_path.exists():
            broken_links.append(
                {"link": link, "resolved": resolved_path, "exists": False}
            )
        else:
            try:
                rel_path = resolved_path.relative_to(PROJECT_ROOT)
                print(f"  ✅ {link} -> {rel_path}")
            except ValueError:
                print(f"  ✅ {link} -> {resolved_path}")

    # Report results
    print("\n--- Results ---")

    if broken_links:
        print(f"❌ Found {len(broken_links)} broken links in GLOBAL_INDEX.md:")
        for bl in broken_links:
            rel_path = (
                bl["resolved"].relative_to(PROJECT_ROOT)
                if PROJECT_ROOT in bl["resolved"].parents
                else bl["resolved"]
            )
            print(f"  - {bl['link']} -> {rel_path} (NOT FOUND)")
        return False
    else:
        print(f"✅ All {len(links)} links in GLOBAL_INDEX.md are valid!")
        return True


if __name__ == "__main__":
    success = check_global_index_links()
    sys.exit(0 if success else 1)
