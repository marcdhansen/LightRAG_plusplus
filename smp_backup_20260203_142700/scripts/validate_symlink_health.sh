#!/bin/bash

# Symlink Health Monitor - Validates symlink integrity for cross-agent compatibility
# Validates that symbolic links in .agent/ point to correct global targets

echo "🔍 Running symlink health validation..."
echo "=================================="

# Configuration
AGENT_GLOBAL="$HOME/.agent"
PROJECT_AGENT=".agent"
VALIDATION_LOG=".agent/logs/symlink_validation.log"

# Create log directory
mkdir -p "$(dirname "$VALIDATION_LOG")"

# Initialize results
ISSUES_FOUND=0
TOTAL_CHECKS=0

# Function to check symlink
check_symlink() {
    local link_path="$1"
    local expected_target="$2"
    local description="$3"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo "   🔗 Checking: $description"
    
    if [ -L "$link_path" ]; then
        local actual_target=$(readlink "$link_path")
        if [ "$actual_target" = "$expected_target" ]; then
            echo "   ✅ $description: Correct symlink"
            return 0
        else
            echo "   ❌ $description: WRONG target"
            echo "      Expected: $expected_target"
            echo "      Actual:   $actual_target"
            ISSUES_FOUND=$((ISSUES_FOUND + 1))
            return 1
        fi
    elif [ -f "$link_path" ]; then
        echo "   ⚠️  $description: File instead of symlink (potential copy)"
        echo "      Consider replacing with symlink to: $expected_target"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        return 1
    else
        echo "   ❌ $description: Missing"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        return 1
    fi
}

# Function to check if global source exists
check_global_source() {
    local source_path="$1"
    local description="$2"
    
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    
    echo "   📁 Checking: $description"
    
    if [ -e "$source_path" ]; then
        echo "   ✅ $description: Source exists"
        return 0
    else
        echo "   ❌ $description: Missing source"
        ISSUES_FOUND=$((ISSUES_FOUND + 1))
        return 1
    fi
}

echo "🔗 Checking symbolic links..."
echo

# Check key symlinks
check_symlink ".agent/docs/sop/global-configs/AGENTS.md" "$AGENT_GLOBAL/AGENTS.md" "AGENTS.md symlink"
check_symlink ".agent/docs/sop/global-configs/SKILLS_INDEX.md" "$AGENT_GLOBAL/skills/README.md" "Skills index symlink"

echo ""
echo "📁 Checking global sources..."
echo

# Check global source files exist
check_global_source "$AGENT_GLOBAL/AGENTS.md" "Global AGENTS.md"
check_global_source "$AGENT_GLOBAL/skills/README.md" "Skills README"
check_global_source "$AGENT_GLOBAL/rules/ROADMAP.md" "Global ROADMAP.md"

echo ""
echo "📊 Summary:"
echo "============"
echo "Total checks: $TOTAL_CHECKS"
echo "Issues found: $ISSUES_FOUND"

if [ $ISSUES_FOUND -eq 0 ]; then
    echo "✅ All symlink validations passed!"
    echo "🎯 Cross-agent structure is healthy"
    
    # Log successful validation
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Symlink validation: PASSED (0 issues)" >> "$VALIDATION_LOG"
    exit 0
else
    echo "❌ Symlink validation failed!"
    echo "💡 Suggested actions:"
    echo "   1. Fix broken symlinks: ln -s <target> <link_path>"
    echo "   2. Replace copies with symlinks"
    echo "   3. Run 'ln -sf ~/.agent/AGENTS.md .agent/docs/sop/global-configs/AGENTS.md'"
    
    # Log failed validation
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Symlink validation: FAILED ($ISSUES_FOUND issues)" >> "$VALIDATION_LOG"
    exit 1
fi