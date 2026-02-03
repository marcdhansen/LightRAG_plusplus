# 📚 Documentation Skill

**Purpose**: Manages project documentation, ensuring comprehensive and up-to-date coverage across all LightRAG components.

## 🎯 Mission
- Maintain comprehensive documentation standards
- Generate and update documentation automatically
- Ensure documentation coverage for all components
- Manage API docs, READMEs, and guides

## 🛠️ Tools & Scripts

### Documentation Coverage Checker
```bash
# Run comprehensive documentation coverage analysis
python3 scripts/check_docs_coverage.py
```

### Documentation Generator
```bash
# Generate API documentation from source
python3 scripts/generate_docs.py --api

# Generate component documentation
python3 scripts/generate_docs.py --components
```

### Standards Validator
```bash
# Validate documentation against project standards
python3 scripts/validate_docs.py
```

## 📋 Usage Examples

### Basic Documentation Management
```bash
# Check current documentation coverage
/docs --check-coverage

# Generate missing documentation
/docs --generate-missing

# Validate documentation standards
/docs --validate
```

### API Documentation
```bash
# Update API documentation after code changes
/docs --update-api --component lightrag

# Generate documentation for new endpoints
/docs --new-endpoint --module extraction
```

## 🔗 Integration Points
- **CI/CD**: Automatic documentation generation on code changes
- **Quality Gates**: Documentation coverage validation before releases
- **WebUI**: Documentation viewer and editor interface
- **Beads**: Track documentation tasks and issues

## 📊 Metrics Tracked
- Documentation coverage percentage
- API documentation completeness
- Guide and tutorial accuracy
- Documentation maintenance backlog

## 🎯 Key Files
- `.agent/docs/` - Project documentation structure
- `scripts/check_docs_coverage.py` - Coverage validation script
- `docs/` - Generated documentation output
- `README.md` and API documentation files
