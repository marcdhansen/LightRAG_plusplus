#!/bin/bash

# Directory Architecture Clarification and Fix
# Resolves the ~/.gemini vs ~/.agent confusion by establishing correct hierarchy

echo "🏗️ Analyzing directory architecture..."
echo "========================================="

# Check current state
echo "Current state:"
if [ -L ~/.gemini ]; then
    echo "  ~/.gemini -> $(readlink ~/.gemini)"
else
    echo "  ~/.gemini is a regular directory"
fi

if [ -L ~/.agent ]; then
    echo "  ~/.agent -> $(readlink ~/.agent)"
else
    echo "  ~/.agent is a regular directory"
fi

echo ""

# Determine true primary source
AGENT_CONTENT=$(ls ~/.agent/ | wc -l | awk '{print $1}')
GEMINI_CONTENT=$(if [ -L ~/.gemini ]; then ls $(readlink ~/.gemini) | wc -l | awk '{print $1}'; else ls ~/.gemini | wc -l | awk '{print $1}'; fi)

echo "Content comparison:"
echo "  ~/.agent/ contains: $AGENT_CONTENT items"
echo "  ~/.gemini/ contains: $GEMINI_CONTENT items"

# Determine fix action
if [ "$AGENT_CONTENT" -gt "$GEMINI_CONTENT" ]; then
    echo ""
    echo "✅ Recommended action: ~/.agent/ should remain primary source"
    echo "  (contains more recent and comprehensive content)"
    echo ""
    echo "🔧 Suggested fixes:"
    echo "  1. Update ~/.gemini symlink to point to ~/.agent"
    echo "  2. Update documentation to clarify ~/.agent/ as primary source"
    echo "  3. Migrate any unique content from ~/.gemini/ to ~/.agent/"
elif [ "$GEMINI_CONTENT" -gt "$AGENT_CONTENT" ]; then
    echo ""
    echo "✅ Recommended action: Migrate unique content to ~/.agent/"
    echo "  (both directories should be consolidated)"
    echo ""
    echo "🔧 Suggested fixes:"
    echo "  1. Move unique content from ~/.gemini/ to ~/.agent/"
    echo "  2. Update ~/.gemini symlink to point to ~/.agent" 
    echo "  3. Remove duplicate ~/.agent/ directory if it exists"
else
    echo ""
    echo "✅ Both directories have equal content"
    echo "  Recommended action: Consolidate to single directory with proper symlinks"
fi

echo ""
echo "📊 Architecture Decision:"
echo "The single source of truth should be the directory with the most"
echo "comprehensive and recent content. In this case: ~/.agent/"
echo ""

# Ask for action
echo ""
echo "Choose action:"
echo "1) Make ~/.agent/ primary (recommended)"
echo "2) Make ~/.gemini/ primary"
echo "3) Manual investigation"
echo ""
read -p "Enter choice [1-3]: " choice

case $choice in
    1)
        echo "🎯 Making ~/.agent/ the primary source..."
        if [ -L ~/.gemini ]; then
            echo "  Updating ~/.gemini symlink to point to ~/.agent"
            ln -sf ~/.agent ~/.gemini
        fi
        
        if [ -L ~/.agent ]; then
            echo "  Removing ~/.agent symlink to prevent loops"
            rm ~/.agent
        fi
        
        echo "  Creating ~/.agent symlink for convenience..."
        ln -sf ~/.agent ~/.agent
        echo "✅ ~/.agent/ is now the primary source of truth"
        ;;
        
    2)
        echo "🎯 Making ~/.gemini/ the primary source..."
        if [ -L ~/.agent ]; then
            echo "  Updating ~/.agent symlink to point to ~/.gemini"
            ln -sf ~/.gemini ~/.agent
        fi
        
        if [ -L ~/.gemini ]; then
            echo "  Removing ~/.gemini symlink to prevent loops"
            rm ~/.gemini
        fi
        
        echo "  Creating ~/.gemini symlink for convenience..."
        ln -sf ~/.gemini ~/.gemini
        echo "✅ ~/.gemini/ is now the primary source of truth"
        ;;
        
    3)
        echo "🔍 Manual investigation selected"
        echo "Please examine both directories to determine best approach"
        ;;
        
    *)
        echo "❌ Invalid choice"
        exit 1
        ;;
esac