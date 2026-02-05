#!/usr/bin/env python3
"""
Global Agent Index Link Validator

Validates links in the global agent index at /Users/marchansen/.agent/docs/GLOBAL_INDEX.md
"""

import re
import sys
from pathlib import Path

# Configuration
GLOBAL_INDEX_PATH = Path("/Users/marchansen/.agent/docs/GLOBAL_INDEX.md")
USER_HOME = Path("/Users/marchansen")


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


def resolve_global_agent_index_link(target_link: str) -> Path:
    """
    Resolves a relative link from GLOBAL_INDEX.md to an absolute path.
    GLOBAL_INDEX.md is located at /Users/marchansen/.agent/docs/GLOBAL_INDEX.md
    """
    global_index_dir = GLOBAL_INDEX_PATH.parent
    return (global_index_dir / target_link).resolve()


def check_global_agent_index_links():
    """Check links in the global agent index GLOBAL_INDEX.md"""

    if not GLOBAL_INDEX_PATH.exists():
        print(f"❌ Global agent index not found: {GLOBAL_INDEX_PATH}")
        sys.exit(1)

    print("🔍 Checking links in Global Agent Index...")
    print(f"📍 Global Index: {GLOBAL_INDEX_PATH}")
    print(f"🏠 User Home: {USER_HOME}")

    links = extract_links(GLOBAL_INDEX_PATH)
    broken_links = []
    valid_links = 0

    for link in sorted(links):
        # Skip external URLs and anchors
        if link.startswith("http") or link.startswith("#"):
            continue

        resolved_path = resolve_global_agent_index_link(link)

        if not resolved_path.exists():
            broken_links.append(
                {"link": link, "resolved": resolved_path, "exists": False}
            )
        else:
            valid_links += 1
            try:
                rel_path = resolved_path.relative_to(USER_HOME)
                print(f"  ✅ {link} -> ~/{rel_path}")
            except ValueError:
                print(f"  ✅ {link} -> {resolved_path}")

    # Report results
    print("\n--- Results ---")
    print(f"📊 Total links checked: {len(links)}")
    print(f"✅ Valid links: {valid_links}")
    print(f"❌ Broken links: {len(broken_links)}")

    if broken_links:
        print("\n❌ Broken links found:")
        for bl in broken_links:
            try:
                rel_path = bl["resolved"].relative_to(USER_HOME)
                print(f"  - {bl['link']} -> ~/{rel_path} (NOT FOUND)")
            except ValueError:
                print(f"  - {bl['link']} -> {bl['resolved']} (NOT FOUND)")
        return False
    else:
        print("\n🎉 All links in Global Agent Index are valid!")
        return True


if __name__ == "__main__":
    success = check_global_agent_index_links()
    sys.exit(0 if success else 1)
