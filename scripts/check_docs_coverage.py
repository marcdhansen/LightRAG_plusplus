#!/usr/bin/env python3
import re
import sys
from pathlib import Path

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DOCS_DIR = PROJECT_ROOT / "docs"

# Source files that should reference other documentation
PRIMARY_SOURCES = [
    PROJECT_ROOT / "README.md",
    PROJECT_ROOT / "docs" / "ARCHITECTURE.md",
    PROJECT_ROOT / ".agent" / "rules" / "ROADMAP.md",
    PROJECT_ROOT / ".agent" / "rules" / "ImplementationPlan.md",
]

# Files to ignore in orphaned check
IGNORE_FILES = {
    "TEMPLATE.md",
    "index.md",
}


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


def resolve_link(source_file: Path, target_link: str) -> Path:
    """
    Resolves a relative link to an absolute path.
    """
    if target_link.startswith("/"):
        return (PROJECT_ROOT / target_link.lstrip("/")).resolve()
    return (source_file.parent / target_link).resolve()


def safe_exists(path: Path) -> bool:
    try:
        return path.exists()
    except (PermissionError, OSError):
        return False


def check_coverage():
    print("🔍 Librarian: Starting Automated Cross-Reference Check...")
    print(f"📂 Project Root: {PROJECT_ROOT}")

    # 1. Collect all MD files in docs/ and .agent/rules/
    all_md_files = set(PROJECT_ROOT.glob("docs/**/*.md"))
    all_md_files.update(PROJECT_ROOT.glob(".agent/rules/*.md"))
    # Add root README
    all_md_files.add(PROJECT_ROOT / "README.md")

    # Filter ignored files
    all_md_files = {f for f in all_md_files if f.name not in IGNORE_FILES}

    print(f"📊 Total documentation files found: {len(all_md_files)}")

    # 2. Extract all links from ALL files to find cross-references
    linked_files: set[Path] = set()
    broken_links: list[dict] = []
    absolute_links: list[dict] = []

    for md_file in all_md_files:
        links = extract_links(md_file)
        for link in links:
            if "global_docs" in link:
                continue

            # Check for absolute path violations
            # - Starts with '/' (project or system absolute)
            # - Starts with drive letter 'C:\' etc.
            if link.startswith("/") or re.match(r"^[a-zA-Z]:\\", link):
                absolute_links.append(
                    {"source": md_file.relative_to(PROJECT_ROOT), "target": link}
                )

            target_path = resolve_link(md_file, link)
            if safe_exists(target_path):
                linked_files.add(target_path)
            else:
                broken_links.append(
                    {
                        "source": md_file.relative_to(PROJECT_ROOT),
                        "target": link,
                        "resolved": target_path,
                    }
                )

    # 3. Identify Orphaned Files
    # An orphaned file is a file in docs/ that is NOT linked by ANY other file
    # EXCEPT for ARCHITECTURE.md and README.md which are entry points.

    # Actually, let's be stricter: Any file in docs/ should be linked by README or ARCHITECTURE
    # OR by another file that is itself linked.

    referenced_from_primary = set()
    for source in PRIMARY_SOURCES:
        if source.exists():
            links = extract_links(source)
            for link in links:
                target_path = resolve_link(source, link)
                if safe_exists(target_path):
                    referenced_from_primary.add(target_path)

    # Breadth-First Search to find all reachable files from primary sources
    reachable = set(PRIMARY_SOURCES)
    queue = list(PRIMARY_SOURCES)

    while queue:
        current = queue.pop(0)
        links = extract_links(current)
        for link in links:
            target_path = resolve_link(current, link)
            if safe_exists(target_path) and target_path not in reachable:
                # Only follow markdown files within the project
                if target_path.suffix == ".md" and PROJECT_ROOT in target_path.parents:
                    reachable.add(target_path)
                    queue.append(target_path)

    orphaned = all_md_files - reachable

    # 4. Filter orphaned to only include files in docs/ (root README is primary source)
    orphaned_in_docs = {f for f in orphaned if DOCS_DIR in f.parents}

    # 5. Output Results
    print("\n--- Results ---")

    if broken_links:
        print(f"❌ Found {len(broken_links)} broken links:")
        for bl in broken_links:
            print(
                f"  - In {bl['source']}: '{bl['target']}' (Resolves to missing: {bl['resolved']})"
            )
    else:
        print("✅ No broken links found.")

    if absolute_links:
        print(f"❌ Found {len(absolute_links)} non-portable absolute links (Must be relative):")
        for al in absolute_links:
            print(f"  - In {al['source']}: '{al['target']}'")
    else:
        print("✅ All links use portable relative paths.")

    if orphaned_in_docs:
        print(
            f"⚠️ Found {len(orphaned_in_docs)} orphaned documentation files (not reachable from README or ARCHITECTURE):"
        )
        for orphan in sorted(orphaned_in_docs):
            print(f"  - {orphan.relative_to(PROJECT_ROOT)}")
    else:
        print("✅ No orphaned documentation files found.")

    # Failure condition
    if broken_links or absolute_links:
        print("\n💥 Documentation check FAILED (violations found).")
        sys.exit(1)

    # We might not want to fail on orphans yet, but we should report them.
    if orphaned_in_docs:
        print("\nℹ️ Documentation check finished with warnings (orphaned files).")
        # sys.exit(1) # Uncomment to enforce no-orphans policy
        sys.exit(0)

    print("\n🎉 Documentation check PASSED!")
    sys.exit(0)


if __name__ == "__main__":
    check_coverage()
