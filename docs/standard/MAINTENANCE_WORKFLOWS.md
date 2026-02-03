# 🔧 Documentation Maintenance Workflows

**Purpose**: Systematic procedures for maintaining organized, accessible, and effective documentation.

## 📅 Maintenance Schedule

### **🗓️ Daily (5 minutes)**
**Quick Triage:**
```bash
# Check for new files in root directory
find . -maxdepth 1 -name "*.md" -o -name "*.txt" -o -name "*.json" -newer yesterday

# Move any misplaced files to appropriate locations
# Update relevant index files
```

### **🗓️ Weekly (30 minutes)**
**Documentation Health Check:**
```bash
#!/bin/bash
# weekly_maintenance.sh

echo "📚 Weekly Documentation Maintenance"

# 1. Check progressive disclosure compliance
echo "🔍 Checking file size limits..."
find docs/quick/ -name "*.md" -exec wc -l {} \; | awk '$1 > 50 {print "❌ Quick doc too long:", $2}'
find docs/standard/ -name "*.md" -exec wc -l {} \; | awk '$1 > 500 {print "❌ Standard doc too long:", $2}'

# 2. Check for broken links
echo "🔗 Checking cross-references..."
grep -r "](\.\./" docs/ --include="*.md" | while read line; do
  # Validate link targets exist
  link=$(echo "$line" | sed 's/.*](\.\.\/\([^)]*\)).*/\1/')
  if [[ ! -f "docs/$link" ]] && [[ ! -d "docs/$link" ]]; then
    echo "❌ Broken link: $link"
  fi
done

# 3. Archive outdated content
echo "🗃️ Archiving outdated content..."
# Move files not modified in >6 months to archive
find . -maxdepth 1 -name "*.md" -mtime +180 -exec echo "Consider archiving: {}" \;

echo "✅ Weekly maintenance complete"
```

### **🗓️ Monthly (2 hours)**
**Comprehensive Review:**
```bash
#!/bin/bash
# monthly_maintenance.sh

echo "📊 Monthly Documentation Review"

# 1. Content audit
echo "📋 Content inventory..."
echo "Quick docs: $(find docs/quick/ -name "*.md" | wc -l) files"
echo "Standard docs: $(find docs/standard/ -name "*.md" | wc -l) files"
echo "Detailed docs: $(find docs/detailed/ -name "*.md" | wc -l) files"
echo "Archived docs: $(find archive/ -name "*.md" | wc -l) files"

# 2. Usage analysis
echo "📈 Usage patterns..."
# Check which quick docs are referenced most
grep -r "docs/quick/" . --include="*.md" | sort | uniq -c | sort -nr | head -10

# 3. Archive optimization
echo "🗂️ Archive organization..."
# Check for duplicates in archive
find archive/ -name "*.md" -exec basename {} \; | sort | uniq -d

echo "✅ Monthly review complete"
```

### **🗓️ Quarterly (4 hours)**
**Strategic Optimization:**
- Review progressive disclosure effectiveness
- Update documentation templates and standards
- Analyze agent feedback on documentation usability
- Plan documentation structure improvements
- Update automation scripts and tools

## 🛠️ Maintenance Tools

### **Automated Validation Scripts**

**Progressive Disclosure Validator** (`scripts/validate_progressive_disclosure.sh`):
```bash
#!/bin/bash
# Validates compliance with progressive disclosure standards

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

# Check cross-references
echo "🔗 Checking cross-references..."
grep -r "](\.\.\/" docs/ --include="*.md" | while read line; do
  if [[ ! -f "docs/${line#*../}" ]] && [[ ! -d "docs/${line#*../}" ]]; then
    echo "❌ Broken cross-reference found"
    FAILED=1
  fi
done

if [[ $FAILED -eq 0 ]]; then
  echo "✅ All progressive disclosure standards met"
else
  echo "❌ Progressive disclosure standards violated"
  exit 1
fi
```

**Link Checker** (`scripts/check_links.sh`):
```bash
#!/bin/bash
# Checks for broken internal links

echo "🔗 Checking documentation links..."

# Check markdown links within docs
find docs/ -name "*.md" -exec grep -H "\[.*\](" {} \; | while read line; do
  # Extract link targets and validate
  if [[ "$line" =~ \]\(([^)]+)\) ]]; then
    target="${BASH_REMATCH[1]}"
    if [[ "$target" == ../* ]]; then
      full_path="docs/${target#../}"
      if [[ ! -f "$full_path" ]] && [[ ! -d "$full_path" ]]; then
        echo "❌ Broken link: $target in $line"
      fi
    fi
  fi
done

echo "✅ Link check complete"
```

**Archive Organizer** (`scripts/organize_archive.sh`):
```bash
#!/bin/bash
# Organizes archive by date and category

echo "🗂️ Archive Organization"

# Create date-based subdirectories
current_year=$(date +%Y)
current_month=$(date +%m)

mkdir -p "archive/benchmarks/$current_year/$current_month"
mkdir -p "archive/audits/$current_year/$current_month"
mkdir -p "archive/profiling/$current_year/$current_month"

# Move files from root to appropriate archive categories
for file in *.md *.json *.txt; do
  if [[ -f "$file" ]]; then
    case "$file" in
      *benchmark*|*performance*)
        mv "$file" "archive/benchmarks/$current_year/$current_month/"
        echo "📊 Moved benchmark: $file"
        ;;
      *audit*|*quality*)
        mv "$file" "archive/audits/$current_year/$current_month/"
        echo "🔍 Moved audit: $file"
        ;;
      *profiling*|*model*)
        mv "$file" "archive/profiling/$current_year/$current_month/"
        echo "🧠 Moved profiling: $file"
        ;;
      *)
        mv "$file" "archive/legacy/"
        echo "🗃️ Moved to legacy: $file"
        ;;
    esac
  fi
done

echo "✅ Archive organization complete"
```

### **Git Hooks Integration**

**Pre-commit Hook** (`.git/hooks/pre-commit`):
```bash
#!/bin/bash
# Pre-commit check for documentation standards

# Check if any docs were modified
if git diff --cached --name-only | grep -E "^docs/|\.md$"; then
  echo "📚 Running documentation pre-commit checks..."

  # Validate progressive disclosure
  if ! bash scripts/validate_progressive_disclosure.sh; then
    echo "❌ Progressive disclosure validation failed"
    exit 1
  fi

  # Check links
  if ! bash scripts/check_links.sh; then
    echo "❌ Link validation failed"
    exit 1
  fi

  echo "✅ Documentation pre-commit checks passed"
fi

exit 0
```

## 📋 Quality Assurance Checklists

### **New Documentation Creation**
- [ ] Created in appropriate layer (quick/standard/detailed)
- [ ] Follows file naming conventions
- [ ] Under size limits for that layer
- [ ] Includes cross-references to other layers
- [ ] Added to relevant index files
- [ ] Tested progressive disclosure workflow

### **Documentation Updates**
- [ ] Updated all related layers consistently
- [ ] Verified cross-references still work
- [ ] Checked size limits after changes
- [ ] Updated index files if needed
- [ ] Tested with validation scripts

### **Archive Migration**
- [ ] File moved to appropriate archive category
- [ ] Updated archive INDEX.md
- [ ] Updated any references in active docs
- [ ] Created redirect if necessary
- [ ] Updated main documentation index

## 🎯 Maintenance Success Metrics

### **Quantitative**
- Root directory markdown files: maintain < 5 total
- Progressive disclosure compliance: 95%+
- Broken links: 0% tolerance
- Average context load: < 60% of previous levels

### **Qualitative**
- Agents find information within 2 clicks
- New documentation follows progressive disclosure
- Archive remains organized and findable
- Cross-references are accurate and helpful

---

**💡 Key Principle**: Consistent maintenance prevents documentation decay and ensures the progressive disclosure system continues to serve its purpose of optimizing agent context and reducing cognitive load.
