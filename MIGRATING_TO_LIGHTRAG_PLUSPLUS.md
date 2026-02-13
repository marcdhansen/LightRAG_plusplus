# Migrating to LightRAG++

This guide helps you migrate from the old `lightrag-hku` package to the new `lightrag-plusplus` package and from `LightRAG_gemini` repository to `LightRAG++`.

## 🔄 What Changed?

### Repository Name
- **Old**: `LightRAG_gemini`
- **New**: `LightRAG++`

### Package Name
- **Old**: `lightrag-hku`
- **New**: `lightrag-plusplus`

### CLI Commands
- **Old**: `lightrag-server`
- **New**: `lightrag-plusplus-server` (with alias `lrag-plus-server`)

## 📦 Installation

### Old Installation
```bash
pip install lightrag-hku
```

### New Installation
```bash
pip install lightrag-plusplus
```

## 🐍 Python Imports

### Old Imports
```python
import lightrag
from lightrag import LightRAG, QueryParam
```

### New Imports
```python
import lightrag_plusplus as lightrag
# OR
from lightrag_plusplus import LightRAG, QueryParam

# For cleaner namespace
import lightrag_plusplus as lrag
from lrag import LightRAG, QueryParam
```

## 🔧 CLI Commands

### Old Commands
```bash
lightrag-server
lightrag-gunicorn
lightrag-download-cache
lightrag-clean-llmqc
```

### New Commands
```bash
# Full command names
lightrag-plusplus-server
lightrag-plusplus-gunicorn
lightrag-plusplus-download-cache
lightrag-plusplus-clean-llmqc

# Short aliases (recommended)
lrag-plus-server
lrag-plus-gunicorn
```

## 📚 Documentation

- **Old Repository**: https://github.com/marcdhansen/LightRAG_gemini
- **New Repository**: https://github.com/marcdhansen/LightRAG_plusplus

## 🔄 Migration Steps

### 1. Update Installation
```bash
# Uninstall old package
pip uninstall lightrag-hku

# Install new package
pip install lightrag-plusplus
```

### 2. Update Python Code
Replace imports in your Python files:

```python
# Replace this
import lightrag

# With this
import lightrag_plusplus as lightrag
```

### 3. Update Scripts
Replace any CLI commands in shell scripts:

```bash
# Replace this
lightrag-server

# With this
lrag-plus-server
```

### 4. Update Dependencies
If you have `lightrag-hku` in your `requirements.txt` or `pyproject.toml`:

```bash
# Old
lightrag-hku>=0.1.0

# New
lightrag-plusplus>=0.1.0
```

## ⚠️ Breaking Changes

### Package Structure
- All functionality remains the same
- Only package name and import paths have changed
- All APIs are fully compatible

### Configuration
- Environment variables remain the same
- Configuration file formats remain the same
- No changes required to existing LightRAG instances

## 🐛 Troubleshooting

### Import Errors
If you see "ModuleNotFoundError: No module named 'lightrag'", update your imports:

```python
import lightrag_plusplus as lightrag
```

### CLI Command Not Found
If CLI commands aren't found, reinstall the package:

```bash
pip install --force-reinstall lightrag-plusplus
```

### Documentation Links
Update any bookmarks to the new repository:
- Old: `https://github.com/marcdhansen/LightRAG_gemini`
- New: `https://github.com/marcdhansen/LightRAG_plusplus`

## 🆓 Version Compatibility

- `lightrag-plusplus` is fully backward compatible with `lightrag-hku`
- All existing LightRAG instances will work without changes
- Only the package installation and imports need updating

## 📞 Support

For migration issues:
1. Check the [Issues](https://github.com/marcdhansen/LightRAG_plusplus/issues) page
2. Open a new issue with the `migration` label
3. Join the [Discord Community](https://discord.gg/yF2MmDJyGJ)

---

**Note**: The migration is designed to be as seamless as possible. All functionality remains identical - only the package name and repository branding have changed.
