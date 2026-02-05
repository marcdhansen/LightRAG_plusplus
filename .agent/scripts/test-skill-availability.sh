#!/bin/bash
# test-skill-availability.sh - Test all skill availability before agent work

echo "🔍 Universal Skill Availability Test"
echo "================================="

# Test universal skill resolver
echo "🧪 Testing Universal Skill Resolver..."
if python lightrag/core/skill_resolver.py > /dev/null 2>&1; then
    echo "✅ Universal Skill Resolver: WORKING"
else
    echo "❌ Universal Skill Resolver: FAILED"
    exit 1
fi

# Test critical skill paths
echo ""
echo "📋 Testing Critical Skill Paths..."

# Test return-to-base
if [ -f "~/.gemini/antigravity/skills/return-to-base/scripts/return-to-base.sh" ] && [ -L ".agent/skills/return-to-base" ]; then
    echo "✅ return-to-base: AVAILABLE (local symlink)"
else
    echo "❌ return-to-base: NOT FOUND (local)"
fi

# Test local symlinks
if [ -L ".agent/skills/return-to-base/scripts/return-to-base.sh" ]; then
    echo "✅ return-to-base: AVAILABLE (local symlink)"
else
    echo "❌ return-to-base: NOT FOUND (local symlink)"
fi

# Test reflect
if [ -f "~/.gemini/antigravity/skills/reflect/enhanced_reflection_cli.py" ]; then
    echo "✅ reflect: AVAILABLE (global enhanced)"
else
    echo "❌ reflect: NOT FOUND (global enhanced)"
fi

# Test local symlinks
if [ -f "~/.gemini/antigravity/skills/reflect/enhanced_reflection_cli.py" ] && [ -L ".agent/skills/reflect" ]; then
    echo "✅ reflect: AVAILABLE (local symlink)"
else
    echo "❌ reflect: NOT FOUND (local)"
fi

# Test fallback scripts
if [ -f ".agent/skills/return-to-base/scripts/fallback:return-to-base.sh" ]; then
    echo "✅ fallback:return-to-base: AVAILABLE (local emergency)"
else
    echo "❌ fallback:return-to-base: NOT FOUND (local emergency)"
fi

if [ -f ".agent/skills/reflect/scripts/fallback:reflect.sh" ]; then
    echo "✅ fallback:reflect: AVAILABLE (local emergency)"
else
    echo "❌ fallback:reflect: NOT FOUND (local emergency)"
fi

echo ""
echo "🎯 Skill Availability Summary:"
echo "================================"
echo "Primary skills should be available from global location"
echo "Emergency fallbacks should be available from local location"
echo "All agents should verify skill availability before accepting tasks"

echo ""
echo "📋 Required Actions:"
echo "- Fix any missing critical skills"
echo "- Test skill resolver functionality"
echo "- Verify fallback mechanisms work"
echo "- Update agent training to include skill verification"

echo ""
echo "🛬 Skill Availability Test Complete"
