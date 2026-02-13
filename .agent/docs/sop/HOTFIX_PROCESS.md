# Hotfix Process

> **⚠️ IMPORTANT**: Direct pushes to `main` are now **blocked**. All changes must go through PR or use the hotfix workflow.

## Overview

The hotfix workflow provides a fast-track path for urgent fixes that need to bypass the standard PR review process. Hotfixes are intended for:

- Production bugs requiring immediate attention
- Critical security fixes
- CI/CD pipeline failures blocking all development

## When to Use Hotfix

| Scenario | Use Hotfix? |
|----------|-------------|
| Production down | ✅ Yes |
| CI blocked for everyone | ✅ Yes |
| New feature | ❌ No - use standard PR |
| Non-critical bug | ❌ No - use standard PR |
| Documentation fix | ❌ No - use standard PR |

## Hotfix Workflow

### Step 1: Create Hotfix Branch

```bash
# Create and switch to hotfix branch
git checkout -b hotfix/description-of-fix

# Make your changes
# ...

# Commit with hotfix ID in message
git commit -m "hotfix: fix critical issue

Fixes #issue-number"
```

### Step 2: Push and Auto-merge

```bash
# Push the hotfix branch - this triggers the Hotfix Pipeline
git push origin hotfix/description-of-fix
```

### What Happens Automatically

1. **Hotfix Pipeline** runs:
   - Detects hotfix ID from branch name or commit message
   - Runs full test suite (unit + integration)
   - Creates PR for merge
   - Auto-merges if tests pass

2. **Post-merge**:
   - Branch is merged to `main`
   - Notification posted

### Step 3: Post-Merge Review

⚠️ **Required within 24 hours**:

1. Review the merged changes
2. If issues found: create follow-up issue
3. Close the hotfix tracking issue

## Branch Naming Convention

```
hotfix/<description>
hotfix/<issue-id>
hotfix/<date>-<description>
```

Examples:
- `hotfix/cicd-cache-key-fix`
- `hotfix/lightrag-s85f`
- `hotfix/2026-02-13-security-patch`

## Creating Hotfix via GitHub

You can also trigger a hotfix manually via GitHub:

1. Go to **Actions** → **Hotfix Pipeline**
2. Click **Run workflow**
3. Enter hotfix ID (optional)
4. Click **Run workflow**

## Pipeline Status Checks

The hotfix pipeline runs:

| Job | Timeout | Required |
|-----|---------|----------|
| Unit Tests | ~10 min | ✅ Yes |
| Integration Tests | ~10 min | ✅ Yes |
| Auto-merge | ~1 min | Auto |

## Troubleshooting

### Tests Fail

- Fix the test failures in your hotfix branch
- Push again to re-run pipeline

### Auto-merge Fails

- The PR will still be created
- Merge manually or enable auto-merge in PR settings

### Need to Cancel Hotfix

- Close the PR created by the pipeline
- Delete the hotfix branch

## Emergency Access

If the hotfix pipeline itself is broken:

1. **Temporary**: Disable branch protection temporarily
2. **Long-term**: Fix the pipeline in a separate branch

> ⚠️ Document any emergency bypasses in follow-up

## Related

- [Branch Protection Settings](https://github.com/marcdhansen/LightRAG_gemini/settings/branches)
- [CI/CD Pipeline](./ci-pipeline.md)
- [Standard PR Process](./pull-request-process.md)
