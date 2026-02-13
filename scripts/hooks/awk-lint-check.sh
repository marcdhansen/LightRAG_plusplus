#!/usr/bin/env bash
# Validate AWK scripts in YAML workflow files using gawk --lint

ERRORS=0

echo "🔍 Checking AWK scripts in workflow files..."

for file in "$@"; do
    if [[ "$file" == *.yml ]] || [[ "$file" == *.yaml ]]; then
        echo "Checking: $file"
        
        if [[ -f "$file" ]]; then
            # Check if the file contains awk scripts
            if grep -q "^[[:space:]]*awk " "$file"; then
                # Check if gawk is available
                if command -v gawk &> /dev/null; then
                    # Extract awk scripts and validate with gawk --lint
                    TEMP_AWK=$(mktemp /tmp/awk_script_XXXXXX.awk)
                    
                    # Use python to properly extract awk scripts from YAML
                    python3 -c "
import re
import sys

with open('$file', 'r') as f:
    content = f.read()

# Find awk script blocks between 'awk \"' and the closing '\"'
# This handles the double-quoted multi-line awk scripts
pattern = r'awk\s+\"([\s\S]*?)\"(?:\s+CHANGELOG|$)'
matches = re.findall(pattern, content)

for i, match in enumerate(matches):
    # Unescape the script
    script = match.replace('\\n', '\n').replace('\\\"', '\"')
    # Write to temp file
    with open('$TEMP_AWK', 'w') as out:
        out.write(script)
    print('Found awk script', file=sys.stderr)
" 2>/dev/null
                    
                    if [[ -f "$TEMP_AWK" && -s "$TEMP_AWK" ]]; then
                        # Run gawk --lint on the extracted script
                        LINT_OUTPUT=$(gawk --lint-no-ext -f "$TEMP_AWK" /dev/null 2>&1)
                        
                        if echo "$LINT_OUTPUT" | grep -qi "error"; then
                            echo "  ❌ $file: AWK syntax errors:"
                            echo "$LINT_OUTPUT" | head -3 | sed 's/^/      /'
                            ERRORS=$((ERRORS + 1))
                        elif echo "$LINT_OUTPUT" | grep -qi "warning"; then
                            echo "  ⚠️ $file: AWK portability warnings:"
                            echo "$LINT_OUTPUT" | head -3 | sed 's/^/      /'
                        else
                            echo "  ✅ $file: AWK syntax valid"
                        fi
                    else
                        echo "  ⏭️  $file: Could not extract awk scripts"
                    fi
                    
                    rm -f "$TEMP_AWK"
                else
                    echo "  ⚠️ gawk not installed, skipping lint"
                    ERRORS=$((ERRORS + 1))
                fi
            else
                echo "  ⏭️  $file: No awk scripts found, skipping"
            fi
        fi
    fi
done

echo ""
if [[ $ERRORS -gt 0 ]]; then
    echo "⚠️ AWK validation complete with errors"
    exit 1
else
    echo "✅ AWK validation complete"
    exit 0
fi
