# lightrag-4vcp Dependency Cleanup Plan

## 🚨 Critical Issue Summary
**Issue**: P0 dependency conflicts blocking PR #49 merge (critical CI/CD infrastructure fixes)
**Root Cause**: Unneeded development packages causing version conflicts
**Status**: Investigation complete, ready for execution

---

## 🔍 Investigation Results

### Conflicts Identified:
1. **NumPy Version Conflict**: `mcp-agent 0.2.6` requires `numpy>=2.1.3`, current is `1.26.4`
2. **Missing Dependencies**: PySpark packages require `py4j`, `grpcio-status` (not installed)
3. **Package Environment**: 7 unneeded packages causing conflicts

### Key Finding: **No Actual Conflicts Needed**
- `mcp-agent 0.2.6` is **NOT required** for LightRAG
- `deepcode-hku` is from separate HKU research project
- PySpark packages are completely unused
- **Solution**: Remove unneeded packages, not upgrade numpy

---

## 📦 Packages to Remove

```bash
# MCP packages (source of numpy conflict)
deepcode-hku           1.0.8 (from /Users/marchansen/GitHub/DeepCode)
mcp-agent              0.2.6 (dependency of deepcode-hku)
mcp-server-git         2025.11.25 (dependency of deepcode-hku)
mcp                    1.24.0 (dependency of mcp-agent)

# PySpark packages (source of py4j/grpcio conflicts)
pyspark                4.0.1 (unused big data framework)
pyspark-client         4.0.1 (unused client)
pyspark-connect        4.0.1 (unused connector)
```

---

## 🎯 Execution Plan

### Phase 1: Environment Backup
```bash
pip freeze > requirements_backup_$(date +%Y%m%d_%H%M%S).txt
```

### Phase 2: Package Removal
```bash
# Remove MCP packages (eliminates numpy conflict)
pip uninstall deepcode-hku mcp-agent mcp-server-git mcp -y

# Remove PySpark packages (eliminates py4j/grpcio conflicts)
pip uninstall pyspark pyspark-client pyspark-connect -y
```

### Phase 3: Validation
```bash
# Verify no conflicts
pip check  # Should show "No broken requirements found"

# Verify removal
pip list | grep -E "(deepcode|mcp|spark)"  # Should return empty

# Test LightRAG functionality
pip install -e .
python -c "import lightrag; print('LightRAG imports working')"
python -c "from lightrag import LightRAG; print('Core LightRAG accessible')"
```

### Phase 4: CI/CD Testing
```bash
# Test critical workflows locally
ruff check .  # Linting
pytest tests/ -k "light" --maxfail=5  # Basic tests
python -m build  # Package build
```

---

## 📊 Expected Outcomes

✅ **NumPy conflict eliminated** - No need to upgrade numpy  
✅ **All pip check conflicts resolved** - Clean dependency state  
✅ **Faster CI/CD** - Fewer packages to install  
✅ **PR #49 unblocked** - Infrastructure fixes can proceed  
✅ **Cleaner environment** - Only required dependencies remain  

---

## 🔍 Risk Assessment

### Low Risk Factors:
- **Confirmed no usage** - Zero references in LightRAG codebase
- **Separate projects** - deepcode-hku from different repository  
- **Reversible** - Packages can be reinstalled if needed
- **Backup available** - Environment snapshot before changes

### Success Criteria:
- `pip check` shows no conflicts
- LightRAG imports and basic functionality work
- CI workflows (linting, basic tests) pass locally
- PR #49 merge checks pass

---

## 📋 Session Context

**Agent**: marchansen (unknown)  
**Session**: 1770565095  
**Mode**: Build (was Plan, executed after SOP compliance)  
**Friction Log**: `.agent/friction_log_20260208_lightrag-4vcp.md`

**SOP Compliance Status**: ✅ Complete
- Session lock created
- Pre-Flight Check completed  
- Friction logging established
- Documentation created

---

## 🔄 Next Steps After Fix

1. Update lightrag-4vcp beads issue with execution results
2. Test PR #49 CI/CD workflow success
3. Close issue as completed
4. Document lessons learned for future dependency management

---

## 📝 Beads Update Status
**Note**: Tried to update beads issue but vim editor failed in non-interactive mode. Status documented here for now.

### Investigation Update:
- **Session**: 1770565095 (SOP compliant)
- **Status**: Investigation complete, ready for execution
- **Key Finding**: mcp-agent and PySpark packages confirmed unneeded
- **Solution**: Remove packages, not upgrade numpy

---

*This document serves as both execution plan and continuity documentation for other agents.*