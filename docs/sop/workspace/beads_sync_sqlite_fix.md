# Beads Sync SQLite Backend Fix

## Issue Summary

The `bd sync` command was failing with the error:

```text
Import failed: import requires SQLite storage backend
```

## Root Cause

The issue was caused by a **prefix mismatch** between the SQLite database and the JSONL file:

- **Database**: Used `LightRAG-` prefix (capital L) for issue IDs
- **JSONL**: Had mixed prefixes - 15 issues with `LightRAG-` and 105 with `lightrag-` (lowercase)
- **Config**: Specified `issue-prefix: "lightrag"` (lowercase)

When `bd sync` attempted to import the merged JSONL back into the database, it detected the prefix mismatch and failed.

## Solution

Standardized all issue IDs to use lowercase `lightrag-` prefix to match the configuration:

### 1. Updated Database Configuration

```bash
sqlite3 .beads/beads.db "UPDATE config SET value = 'lightrag' WHERE key = 'issue_prefix';"
```

### 2. Updated Issue IDs in Database

```bash
sqlite3 .beads/beads.db "UPDATE issues SET id = REPLACE(id, 'LightRAG-', 'lightrag-') WHERE id LIKE 'LightRAG-%';"
```

### 3. Updated Dependencies Table

```bash
sqlite3 .beads/beads.db "UPDATE dependencies SET issue_id = REPLACE(issue_id, 'LightRAG-', 'lightrag-') WHERE issue_id LIKE 'LightRAG-%'; UPDATE dependencies SET depends_on_id = REPLACE(depends_on_id, 'LightRAG-', 'lightrag-') WHERE depends_on_id LIKE 'LightRAG-%';"
```

### 4. Updated JSONL File

```bash
sed -i.bak 's/"LightRAG-/"lightrag-/g' .beads/issues.jsonl
```

## Verification

After the fix:

```bash
$ bd sync
→ Loaded 120 local issues from database
→ Loading base state...
  Loaded 120 issues from base state
→ Pulling from remote...
  Loaded 120 remote issues from JSONL
→ Merging base, local, and remote issues (3-way)...
  Merged: 120 issues total
    Local wins: 0, Remote wins: 0, Same: 120, Conflicts (LWW): 0
→ Writing merged state to JSONL...
→ Importing merged state to database...
Import complete: 0 created, 0 updated, 104 unchanged, 16 skipped
→ Exporting from database to JSONL...
→ Committing changes...
→ Pushing to remote...
→ Updating base state...
  Saved 120 issues to base state

✓ Sync complete
```

## Prevention

To prevent this issue in the future:

1. **Always use lowercase** for the `issue-prefix` in `.beads/config.yaml`
2. **Avoid manual edits** to issue IDs that might introduce case inconsistencies
3. **Run `bd doctor --fix`** periodically to catch configuration mismatches early

## Related Issues

- Database version was also updated from `unknown` to `0.47.1` during the fix
- Repo fingerprint was updated to match current git remote

## Date Fixed

2026-01-30

## Fixed By

Automated diagnosis and repair using `bd doctor --fix` and manual SQL updates
