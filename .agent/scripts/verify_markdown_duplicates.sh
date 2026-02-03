#!/bin/bash

# Markdown Duplication Verification Script
# Uses hashes to detect and remove duplicate markdown files
# Compatible with bash 3.x+

echo "🔍 Markdown Duplication Verification"
echo "===================================="

# Function to calculate file hash
calculate_hash() {
    local file="$1"
    if command -v sha256sum &> /dev/null; then
        sha256sum "$file" | cut -d' ' -f1
    elif command -v shasum &> /dev/null; then
        shasum -a 256 "$file" | cut -d' ' -f1
    else
        md5sum "$file" | cut -d' ' -f1
    fi
}

# Find common document files for duplicate detection (simplified approach)
echo "📋 Scanning for duplicate files..."
temp_md_list="/tmp/md_files_$$.list"
temp_hashes="/tmp/md_hashes_$$.list"
temp_duplicates="/tmp/md_duplicates_$$.list"

find . -name "*.md" -o -name "*.txt" -o -name "*.pdf" | grep -v "/.git/" | grep -v "/node_modules/" | grep -v "/.venv/" | grep -v "/rag_storage" | grep -v "/test_ace" > "$temp_md_list"

if [ -s "$temp_md_list" ]; then
    # Calculate hashes for all files
    while IFS= read -r file; do
        if [ -f "$file" ]; then
            hash=$(calculate_hash "$file")
            echo "$hash|$file" >> "$temp_hashes"
        fi
    done < "$temp_md_list"

    # Find duplicate hashes
    cut -d'|' -f1 "$temp_hashes" | sort | uniq -d > "$temp_duplicates"

    duplicate_count=$(wc -l < "$temp_duplicates")

    if [ "$duplicate_count" -eq 0 ]; then
        md_count=$(wc -l < "$temp_md_list")
        echo "✅ No duplicate markdown files found"
        echo "📊 Total files: $md_count unique files"
    else
        echo "❌ $duplicate_count duplicate group(s) found"
        echo ""
        echo "🔍 Duplicate file groups:"
        while IFS= read -r duplicate_hash; do
            echo "  📄 Hash: $duplicate_hash"
            grep "^$duplicate_hash|" "$temp_hashes" | cut -d'|' -f2 | sed 's/^/    /'
        done < "$temp_duplicates"
        echo ""
        rm -f "$temp_md_list" "$temp_hashes" "$temp_duplicates"
        exit 1
    fi
else
    echo "✅ No markdown files found to check"
fi

# Cleanup
rm -f "$temp_md_list" "$temp_hashes" "$temp_duplicates"

echo "✅ Markdown verification complete"
