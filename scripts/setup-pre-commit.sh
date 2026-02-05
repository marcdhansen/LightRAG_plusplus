#!/bin/bash
# Setup pre-commit framework for LightRAG
# One-time setup for developers

set -e

echo "🚀 Setting up LightRAG Pre-commit Framework"
echo "=========================================="

# Check if pre-commit is installed
if ! command -v pre-commit >/dev/null 2>&1; then
    echo "❌ pre-commit not found"
    echo ""
    echo "📦 Installing pre-commit..."

    # Try pip first
    if command -v pip >/dev/null 2>&1; then
        pip install pre-commit
    elif command -v pip3 >/dev/null 2>&1; then
        pip3 install pre-commit
    else
        echo "❌ Cannot find pip. Please install pre-commit manually:"
        echo "   pip install pre-commit"
        exit 1
    fi
else
    echo "✅ pre-commit already installed"
fi

# Ensure hook scripts are executable
echo ""
echo "🔧 Setting up hook scripts..."
if [[ -f "scripts/hooks/tdd-compliance-check.sh" ]]; then
    chmod +x scripts/hooks/tdd-compliance-check.sh
    echo "✅ Made TDD compliance hook executable"
fi

if [[ -f "scripts/hooks/beads-sync-check.sh" ]]; then
    chmod +x scripts/hooks/beads-sync-check.sh
    echo "✅ Made beads sync hook executable"
fi

if [[ -f "scripts/dev-start-check.sh" ]]; then
    chmod +x scripts/dev-start-check.sh
    echo "✅ Made dev-start-check script executable"
fi

if [[ -f "scripts/create-tdd-artifacts.sh" ]]; then
    chmod +x scripts/create-tdd-artifacts.sh
    echo "✅ Made create-tdd-artifacts script executable"
fi

# Install pre-commit hooks
echo ""
echo "🪝 Installing pre-commit hooks..."
if [[ -f ".pre-commit-config.yaml" ]]; then
    pre-commit install
    echo "✅ Pre-commit hooks installed"
else
    echo "❌ .pre-commit-config.yaml not found"
    exit 1
fi

# Run initial validation
echo ""
echo "🧪 Running initial validation..."
if pre-commit run --all-files --verbose; then
    echo ""
    echo "🎉 Setup completed successfully!"
    echo ""
    echo "✅ Pre-commit hooks are now active and will run automatically before each commit."
    echo ""
    echo "📋 What happens now:"
    echo "• Each commit will automatically check for TDD artifacts on feature branches"
    echo "• Code quality checks will run (ruff, black, etc.)"
    echo "• Beads sync will be validated"
    echo "• Tests will be validated for new Python code"
    echo ""
    echo "🔧 Manual testing:"
    echo "  Test all hooks:  pre-commit run --all-files"
    echo "  Test specific hook: pre-commit run tdd-artifact-validation"
    echo "  Skip hooks (emergency): git commit --no-verify"
    echo ""
    echo "📚 For more info, see: docs/ci-cd-prevention-guide.md"
else
    echo ""
    echo "⚠️  Some checks failed during setup"
    echo "💡 Fix the issues above, then run: pre-commit run --all-files"
fi
