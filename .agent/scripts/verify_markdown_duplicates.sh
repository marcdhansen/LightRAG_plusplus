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
find . -name "*.md" -o -name "*.txt" -o -name "*.pdf" | grep -v "/.git/" | grep -v "/node_modules/" | grep -v "/.venv/" | grep -v "/rag_storage" | grep -v "/test_ace" > "$temp_md_list"

    while IFS= read -r file; do
        if [ -f "$file" ]; then
            hash=$(calculate_hash "$file")
            echo "$hash|$file" >> "$temp_final_hashes"
        fi
    done < "$temp_md_list"

    cut -d'|' -f1 "$temp_final_hashes" | sort | uniq -d > "$temp_final_duplicates"

    final_duplicate_count=$(wc -l < "$temp_final_duplicates")

    if [ "$final_duplicate_count" -eq 0 ]; then
        final_md_count=$(wc -l < "$temp_md_list")
        echo "✅ All duplicate files resolved successfully"
        echo "📊 Final count: $final_md_count unique files"
    else
        echo "❌ $final_duplicate_count duplicate group(s) still remain"
        rm -f "$temp_md_list" "$temp_hashes" "$temp_duplicates" "$temp_final_hashes" "$temp_final_duplicates"
        exit 1
    fi

    rm -f "$temp_final_hashes" "$temp_final_duplicates"
fi

# Cleanup
rm -f "$temp_md_list" "$temp_hashes" "$temp_duplicates"

echo "✅ Markdown verification complete"
