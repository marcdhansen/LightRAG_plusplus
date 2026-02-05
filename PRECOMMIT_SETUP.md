# Pre-commit Setup Guide (Minimal Approach)

## Quick Setup for Developers

### One-time Setup
```bash
./scripts/setup-pre-commit.sh
```

### What It Does
- ✅ Automatically checks TDD artifacts on every commit
- ✅ Blocks commits if required files are missing
- ✅ Works with existing pre-commit framework
- ✅ Team consistency via Git

### Required Files for Feature Branches
For feature/agent/task branches, these files are required:
- `tests/{feature}_tdd.py` - Unit tests
- `tests/{feature}_functional.py` - Integration tests
- `docs/{feature}_analysis.md` - Technical analysis

### Emergency Bypass
```bash
git commit --no-verify -m "Emergency fix"
```

That's it! Simple, effective, team-based solution.
