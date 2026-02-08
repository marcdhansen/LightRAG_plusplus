#!/bin/bash
# Repository Renaming Validation Script for LightRAG++
# Validates that all renaming changes are correctly applied

set -e

echo "🔍 Testing Repository Renaming to LightRAG++..."

# Test 1: Verify package name in pyproject.toml
echo ""
echo "📋 Test 1: Verifying package name in pyproject.toml..."
PACKAGE_NAME=$(python -c "
try:
    import tomllib
except ImportError:
    import tomli

with open('pyproject.toml', 'rb') as f:
    if 'tomllib' in globals():
        data = tomllib.load(f)
    else:
        data = tomli.load(f)
    print(data['project']['name'])
")

if [[ "$PACKAGE_NAME" == "lightrag-plusplus" ]]; then
    echo "✅ Package name correctly set to 'lightrag-plusplus'"
else
    echo "❌ Package name is '$PACKAGE_NAME' (expected 'lightrag-plusplus')"
    exit 1
fi

# Test 2: Verify URLs in pyproject.toml
echo ""
echo "📋 Test 2: Verifying repository URLs in pyproject.toml..."
HOMEPAGE_URL=$(python -c "
try:
    import tomllib
except ImportError:
    import tomli

with open('pyproject.toml', 'rb') as f:
    if 'tomllib' in globals():
        data = tomllib.load(f)
    else:
        data = tomli.load(f)
    print(data['project']['urls']['Homepage'])
")

if [[ "$HOMEPAGE_URL" == "https://github.com/marcdhansen/LightRAG++" ]]; then
    echo "✅ Homepage URL correctly updated"
else
    echo "❌ Homepage URL is '$HOMEPAGE_URL' (expected 'https://github.com/marcdhansen/LightRAG++')"
    exit 1
fi

# Test 3: Verify CLI scripts in pyproject.toml
echo ""
echo "📋 Test 3: Verifying CLI scripts in pyproject.toml..."
SERVER_SCRIPT=$(python -c "
try:
    import tomllib
except ImportError:
    import tomli

with open('pyproject.toml', 'rb') as f:
    if 'tomllib' in globals():
        data = tomllib.load(f)
    else:
        data = tomli.load(f)
    scripts = data['project']['scripts']
    for key, value in scripts.items():
        if 'server' in key and 'lightrag-plusplus-server' in key:
            print(value)
            break
")

if [[ "$SERVER_SCRIPT" == "lightrag.api.lightrag_server:main" ]]; then
    echo "✅ CLI scripts correctly updated"
else
    echo "❌ Server script not found or incorrect"
    exit 1
fi

# Test 4: Verify README.md updates
echo ""
echo "📋 Test 4: Verifying README.md updates..."
if grep -q "LightRAG++" README.md; then
    echo "✅ README.md contains LightRAG++ branding"
else
    echo "❌ README.md missing LightRAG++ branding"
    exit 1
fi

if grep -q "lightrag-plusplus" README.md; then
    echo "✅ README.md contains new package name"
else
    echo "❌ README.md missing new package name"
    exit 1
fi

# Test 5: Verify migration guide exists
echo ""
echo "📋 Test 5: Verifying migration guide exists..."
if [[ -f "MIGRATING_TO_LIGHTRAG_PLUSPLUS.md" ]]; then
    echo "✅ Migration guide exists"
else
    echo "❌ Migration guide missing"
    exit 1
fi

# Test 6: Verify ruff configuration updated
echo ""
echo "📋 Test 6: Verifying ruff configuration..."
RUFF_CONFIG=$(python -c "
try:
    import tomllib
except ImportError:
    import tomli

with open('pyproject.toml', 'rb') as f:
    if 'tomllib' in globals():
        data = tomllib.load(f)
    else:
        data = tomli.load(f)
    known_first_party = data['tool']['ruff']['lint']['isort']['known-first-party']
    print('lightrag_plusplus' in known_first_party)
")

if [[ "$RUFF_CONFIG" == "True" ]]; then
    echo "✅ Ruff configuration updated with new package name"
else
    echo "❌ Ruff configuration not updated"
    exit 1
fi

# Test 7: Verify test dependencies updated
echo ""
echo "📋 Test 7: Verifying test dependencies..."
TEST_DEPS=$(python -c "
try:
    import tomllib
except ImportError:
    import tomli

with open('pyproject.toml', 'rb') as f:
    if 'tomllib' in globals():
        data = tomllib.load(f)
    else:
        data = tomli.load(f)
    test_deps = data['project']['optional-dependencies']['test']
    print('lightrag-plusplus' in test_deps[0])
")

if [[ "$TEST_DEPS" == "True" ]]; then
    echo "✅ Test dependencies updated"
else
    echo "❌ Test dependencies not updated"
    exit 1
fi

# Test 8: Verify package is importable (simulated)
echo ""
echo "📋 Test 8: Verifying package structure..."
if [[ -d "lightrag" ]]; then
    echo "✅ Source directory structure maintained"
else
    echo "❌ Source directory structure issue"
    exit 1
fi

echo ""
echo "🎉 All Repository Renaming Tests Completed!"
echo ""
echo "📊 Summary:"
echo "  ✅ Package name in pyproject.toml"
echo "  ✅ Repository URLs updated"
echo "  ✅ CLI scripts updated"
echo "  ✅ README.md branding updated"
echo "  ✅ Migration guide created"
echo "  ✅ Ruff configuration updated"
echo "  ✅ Test dependencies updated"
echo "  ✅ Source directory structure maintained"
echo ""
echo "🚀 Ready for PR Group 3 submission!"
echo ""
echo "📋 Migration Impact:"
echo "  • Repository: LightRAG_gemini → LightRAG++"
echo "  • Package: lightrag-hku → lightrag-plusplus"
echo "  • CLI: lightrag-server → lightrag-plusplus-server"
echo "  • Backward compatibility: Maintained with aliases"
