# CI/CD Troubleshooting Guide

## 🚨 Common CI/CD Issues and Solutions

This guide covers common CI/CD problems and their solutions for the LightRAG project.

---

## 🔍 Quick Diagnostic Commands

### Local Testing
```bash
# Test pre-commit hooks locally
pre-commit run --all-files --show-diff-on-failure

# Test specific hook
pre-commit run tdd-artifact-validation

# Check Python environment
python --version
pip list | grep -E "(ruff|pytest|pre-commit)"

# Check Node.js/Bun for WebUI
node --version
bun --version
```

### CI Debugging
```bash
# Run CI setup locally (if you have GitHub Actions runner locally)
./.github/scripts/ci-debug.sh

# Check environment variables
env | grep -E "(CI|GITHUB)"
```

---

## 🛠️ Common Issues and Solutions

### 1. **Linting Workflow Fails**

**Symptoms:**
- `linting.yaml` workflow fails with exit code 1
- Ruff formatting errors
- Pre-commit hook failures

**Solutions:**

#### Fix Local Formatting Issues
```bash
# Fix ruff issues automatically
ruff check --fix .
ruff format .

# Run pre-commit to verify
pre-commit run --all-files
```

#### Check Python Version
```bash
# Ensure Python 3.12+
python --version  # Should be 3.12.x

# Install correct version if needed
pyenv install 3.12.0
pyenv local 3.12.0
```

#### Dependency Issues
```bash
# Reinstall dependencies
pip install --upgrade pip
pip install -e ".[api,test]"
pip install pre-commit ruff

# Clear pip cache if needed
pip cache purge
```

---

### 2. **TDD Validation Failures**

**Symptoms:**
- Missing TDD artifacts
- Test quality checks fail
- Feature branch validation errors

**Solutions:**

#### Auto-Generate Missing Artifacts
```bash
# Generate all TDD artifacts for your feature
FEATURE_NAME="your-feature-name"
./scripts/create-tdd-artifacts.sh $FEATURE_NAME

# Or manually:
# Create tests/your_feature_tdd.py
# Create tests/your_feature_functional.py
# Create docs/your_feature_analysis.md
```

#### Fix Test Quality Issues
```bash
# Ensure tests have proper structure
grep "def test_" tests/your_feature_tdd.py
grep "assert" tests/your_feature_tdd.py

# Run tests locally
pytest tests/your_feature_tdd.py -v
```

---

### 3. **WebUI Linting Failures**

**Symptoms:**
- Node.js/Bun not found errors
- WebUI dependency installation fails
- ESLint errors in TypeScript/JavaScript files

**Solutions:**

#### Install Required Tools
```bash
# Install Bun (recommended)
curl -fsSL https://bun.sh/install | bash

# Or install Node.js (fallback)
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt-get install -y nodejs
```

#### Install WebUI Dependencies
```bash
cd lightrag_webui
bun install  # Primary method
# or
npm install  # Fallback method
```

#### Fix Linting Errors
```bash
cd lightrag_webui
bun run lint:fix  # Auto-fix issues
# or
npm run lint:fix
```

---

### 4. **Beads Sync Issues**

**Symptoms:**
- Beads command not found
- Beads repository sync failures
- Pending beads changes not flushed

**Solutions:**

#### Install Beads
```bash
# Install beads globally
npm install -g @beadsdev/beads

# Verify installation
bd --version
```

#### Fix Sync Issues
```bash
# Check beads status
bd status

# Flush pending changes
bd flush

# Sync with remote
bd sync
```

#### In CI Environments
```bash
# Beads issues are non-blocking in CI
# The hooks have built-in CI bypass logic
```

---

### 5. **Pre-commit Hook Failures**

**Symptoms:**
- Pre-commit installation fails
- Hook execution errors
- Permission issues

**Solutions:**

#### Reinstall Pre-commit
```bash
# Clean pre-commit installation
pre-clean-local() {
    pre-commit clean
    pre-commit uninstall --all
    rm -rf ~/.cache/pre-commit
}

# Reinstall hooks
pre-commit install --hook-types pre-commit,pre-push,commit-msg
```

#### Fix Permissions
```bash
# Make scripts executable
chmod +x scripts/hooks/*.sh
chmod +x .agent/scripts/*.sh

# Fix git hooks directory
chmod +x .git/hooks/*
```

---

### 6. **CI Cache Issues**

**Symptoms:**
- Stale cache causing build failures
- Dependency installation takes too long
- Inconsistent CI behavior

**Solutions:**

#### Clear CI Cache
```bash
# In GitHub Actions UI:
# 1. Go to Actions → Your Workflow → Settings
# 2. Find "Caches" section
# 3. Delete problematic caches
```

#### Force Cache Refresh
```bash
# Update cache key by changing any of these files:
# - pyproject.toml
# - requirements*.txt
# - .pre-commit-config.yaml
```

---

## 🔧 Environment Setup

### Local Development Setup
```bash
# Complete local setup
./scripts/setup-dev.sh

# Manual setup
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -e ".[api,test]"
pip install pre-commit ruff
pre-commit install
```

### CI Environment Variables
```bash
# Common CI environment variables
export GITHUB_ACTIONS=true
export CI=true
export PYTHON_VERSION=3.12
```

---

## 📊 Performance Optimization

### Faster CI Runs
1. **Use Dependency Caching**: Configured in workflows
2. **Parallel Jobs**: Matrix strategy for testing
3. **Selective Hooks**: Only run relevant pre-commit hooks

### Local Performance
```bash
# Speed up pre-commit
pre-commit run --all-files --parallel

# Use faster ruff
ruff check --quiet .
ruff format --quiet .
```

---

## 🆘 Getting Help

### Debug Information Collection
```bash
# Create debug report
./scripts/collect-ci-debug-info.sh

# Manual debugging report
echo "=== Environment ===" > ci-debug.txt
python --version >> ci-debug.txt
pip list >> ci-debug.txt
node --version >> ci-debug.txt
bun --version >> ci-debug.txt
echo "" >> ci-debug.txt

echo "=== Pre-commit Status ===" >> ci-debug.txt
pre-commit --version >> ci-debug.txt
git status >> ci-debug.txt
echo "" >> ci-debug.txt

echo "=== Test Files ===" >> ci-debug.txt
find tests -name "*_tdd.py" | head -5 >> ci-debug.txt
find tests -name "*_functional.py" | head -5 >> ci-debug.txt
```

### Submitting Issues
Include in your issue:
1. Full error message and logs
2. `ci-debug.txt` output
3. Branch name and commit hash
4. Local vs CI environment
5. Steps to reproduce

---

## ✅ Success Criteria

Your CI/CD should pass when:
- [ ] Python 3.12+ is used
- [ ] All dependencies are installed correctly
- [ ] Pre-commit hooks pass locally
- [ ] TDD artifacts exist for feature branches
- [ ] WebUI dependencies are installed (if WebUI exists)
- [ ] Ruff formatting and linting pass
- [ ] Tests run successfully
- [ ] No blocking errors in any hooks

---

*Last updated: 2026-02-05*
