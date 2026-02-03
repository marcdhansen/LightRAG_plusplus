#!/bin/bash
# Progressive Disclosure Compliance Validator
# Validates documentation meets progressive disclosure standards

FAILED=0

echo "🔍 Progressive Disclosure Compliance Check"

# Check quick docs
echo "📄 Checking quick reference docs..."
for file in docs/quick/*.md; do
  if [[ -f "$file" ]]; then
    lines=$(wc -l < "$file")
    if [[ $lines -gt 50 ]]; then
      echo "❌ Quick doc too long: $file ($lines lines, max 50)"
      FAILED=1
    else
      echo "✅ Quick doc OK: $file ($lines lines)"
    fi
  fi
done

# Check standard docs
echo "📚 Checking standard docs..."
for file in docs/standard/**/*.md; do
  if [[ -f "$file" ]]; then
    lines=$(wc -l < "$file")
    if [[ $lines -gt 500 ]]; then
      echo "❌ Standard doc too long: $file ($lines lines, max 500)"
      FAILED=1
    else
      echo "✅ Standard doc OK: $file ($lines lines)"
    fi
  fi
done

echo "✅ Progressive disclosure validation complete"

if [[ $FAILED -eq 0 ]]; then
  echo "✅ All progressive disclosure standards met"
  exit 0
else
  echo "❌ Progressive disclosure standards violated"
  exit 1
fi
