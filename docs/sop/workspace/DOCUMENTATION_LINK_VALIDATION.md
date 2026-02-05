# Documentation Link Validation and Path Resolution Guide

## 🚨 Problem Statement

The global documentation system suffers from broken relative links due to complex directory structures and inconsistent path resolution. This creates maintenance overhead and documentation drift.

## 🔍 Root Causes

1. **Cross-boundary relative paths**: Links that traverse multiple directory levels (e.g., from `~/.agent/docs/` to `~/antigravity_lightrag/LightRAG/.agent/rules/`)
2. **Multiple global indices**: Different global index files in different locations with different path contexts
3. **Inconsistent path resolution**: Some scripts use absolute paths, others use relative, causing confusion

## ✅ Solution Principles

### 1. Use Relative Paths Only
- **NEVER** use absolute paths in markdown links
- **ALWAYS** use paths relative to the containing document
- Example: From `~/.agent/docs/GLOBAL_INDEX.md` to `~/antigravity_lightrag/LightRAG/.agent/rules/ROADMAP.md`, use `../../antigravity_lightrag/LightRAG/.agent/rules/ROADMAP.md`

### 2. Path Resolution Strategy
When resolving links from a document:
```bash
# From document directory
cd /path/to/document/directory
# Test relative path
ls -la relative/path/to/target.md
```

### 3. Validation Tools

#### Global Agent Index Validator
```bash
python scripts/validate_global_agent_index_links.py
```
- Validates: `/Users/marchansen/.agent/docs/GLOBAL_INDEX.md`
- Base directory: `/Users/marchansen/.agent/docs/`
- Reports: Valid/broken links with relative paths

#### Project Global Index Validator  
```bash
python scripts/validate_global_index_links.py
```
- Validates: `.agent/GLOBAL/index/GLOBAL_INDEX.md`
- Base directory: `.agent/GLOBAL/index/`
- Reports: Valid/broken links with project-relative paths

#### Project Documentation Validator
```bash
python scripts/check_docs_coverage.py
```
- Validates: All project documentation
- Base directory: Project root
- Reports: Broken links, orphaned files, absolute path violations

## 🛠️ Maintenance Procedures

### When Adding New Links
1. **Determine source document location**
2. **Calculate relative path**: Use `realpath --relative-to=SOURCE_DIR TARGET_FILE` or Python's `Path.relative_to()`
3. **Test the link**: `cd SOURCE_DIR && ls -la RELATIVE_PATH`
4. **Run validator**: Execute appropriate validation script

### When Moving/Renaming Files
1. **Find all inbound links**: Use `grep -r "old/path/name.md" .`
2. **Update all references**: Change to new relative paths
3. **Validate**: Run comprehensive link validation

### When Directory Structure Changes
1. **Run all validators**: Identify all broken links
2. **Batch update**: Use `sed` or similar tools for systematic updates
3. **Test thoroughly**: Validate from multiple document contexts

## 📋 Common Path Patterns

### From Global Agent Index (`~/.agent/docs/`)
- To LightRAG project files: `../../antigravity_lightrag/LightRAG/path/to/file.md`
- To global standards: `sop/FILENAME.md`
- To skills: `skills/category/SKILL.md`

### From Project Global Index (`.agent/GLOBAL/index/`)
- To project files: `../../path/to/file.md` 
- To global standards: `../standards/FILENAME.md`

### From Project Documentation (`docs/`)
- To project files: `../path/to/file.md`
- To root files: `../FILENAME.md`
- To agent files: `../.agent/path/to/file.md`

## 🚀 Quick Reference Commands

```bash
# Calculate relative path (Python)
python3 -c "from pathlib import Path; print(Path('/absolute/target').relative_to(Path('/absolute/source')))"

# Test link resolution
cd /source/document/dir && ls -la relative/path/target.md

# Find all links in a file
grep -o '\[.*\]([^)]*' file.md | grep -v 'http'

# Validate all documentation
python scripts/check_docs_coverage.py && python scripts/validate_global_agent_index_links.py
```

## 🔄 Automated Integration

### Pre-commit Hook
Add to `.pre-commit-config.yaml`:
```yaml
- repo: local
  hooks:
    - id: validate-docs
      name: Validate documentation links
      entry: python scripts/check_docs_coverage.py
      language: system
      pass_filenames: false
    - id: validate-global-index
      name: Validate global index links  
      entry: python scripts/validate_global_agent_index_links.py
      language: system
      pass_filenames: false
```

### CI/CD Pipeline
```yaml
- name: Validate documentation
  run: |
    python scripts/check_docs_coverage.py
    python scripts/validate_global_agent_index_links.py
    python scripts/validate_global_index_links.py
```

## 📚 Resources

- **Python Pathlib**: <https://docs.python.org/3/library/pathlib.html>
- **Markdown Link Syntax**: <https://www.markdownguide.org/basic-syntax/#links>
- **Git Pre-commit Hooks**: <https://pre-commit.com/>

---

**Last Updated**: 2026-02-05  
**Maintained by**: Librarian Skill  
**Status**: Active