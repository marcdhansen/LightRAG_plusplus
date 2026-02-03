# 🔍 Troubleshooting Decision Map

**Purpose**: Navigate from symptoms to solutions using a decision-tree approach.

## 🚀 Quick Diagnosis Flow

### **Start here**: What's your primary issue?

**A. Setup/Installation Problems** → [Section A](#a-setupinstallation-problems)
**B. Runtime Errors** → [Section B](#b-runtime-errors)
**C. Performance Issues** → [Section C](#c-performance-issues)
**D. UI/Web Interface Issues** → [Section D](#d-uiweb-interface-issues)
**E. Database/Graph Issues** → [Section E](#edatabasegraph-issues)
**F. Agent Coordination Issues** → [Section F](#f-agent-coordination-issues)

---

## A. Setup/Installation Problems

### Python Environment Issues?
```bash
# Check Python version
python --version  # Should be 3.8+

# Check UV (recommended)
uv --version

# Install UV if missing
pip install uv
```

**Still issues?** → [Full Setup Guide](../standard/guides/) or use **[Process Skill](../../.agent/skills/process/SKILL.md)**

### Dependency Conflicts?
```bash
# Check current environment
uv pip list
uv pip check

# Clean start
rm -rf venv/ .venv/
uv sync
```

**Still issues?** → Check [archive/config/](../../archive/config/) for requirement files

### Model Configuration Problems?
```bash
# Check environment variables
env | grep -E "(LLM|API|KEY|URL)"

# Test model connection
python -c "from lightrag import LightRAG; print('Models working')"
```

**Still issues?** → [Model Routing Guide](../standard/guides/model_routing.md)

---

## B. Runtime Errors

### Extraction Fails?
**Symptom**: `Entity extraction failed` or hanging extraction
```bash
# Check model routing
cat docs/standard/guides/model_routing.md

# Test with smaller document
echo "test document" | python lightrag/scripts/extract.py
```

**Solutions**:
- Use **[Graph Skill](../../.agent/skills/graph/SKILL.md)** for extraction issues
- Check timeout settings: `grep -r timeout . --include="*.py"`
- Try different model in routing configuration

### Query Returns Nothing?
**Symptom**: Empty results or `No relevant information found`
```bash
# Check data was processed
ls lightrag/data/
cat lightrag/data/*.jsonl | head -5

# Test simple query
python -c "from lightrag import LightRAG; rag=LightRAG('.'); print(rag.query('test'))"
```

**Solutions**:
- Check vector database connection
- Verify data ingestion completed
- Use **[Testing Skill](../../.agent/skills/testing/SKILL.md)** for debugging

### Import Errors?
**Symptom**: `ModuleNotFoundError` or import failures
```bash
# Check installation
python -c "import lightrag; print('Import OK')"

# Check Python path
python -c "import sys; print(sys.path)"
```

**Solutions**:
- Reinstall with `uv sync`
- Check Python path configuration
- Use **[QualityAnalyst](~/.gemini/antigravity/skills/QualityAnalyst/SKILL.md)** for code quality

---

## C. Performance Issues

### Slow Queries?
**Symptom**: Queries taking > 30 seconds
```bash
# Check model performance
python -c "import time; start=time.time(); from lightrag import LightRAG; print(f'Load time: {time.time()-start}s')"

# Monitor resources
top -p $(pgrep python)
```

**Solutions**:
- Check [Model Profiling Results](../../archive/profiling/MODEL_PROFILING_RESULTS.md)
- Use **[Evaluation Skill](../../.agent/skills/evaluation/SKILL.md)** for performance analysis
- Consider model routing optimization

### Memory Issues?
**Symptom**: Out of memory errors or excessive RAM usage
```bash
# Monitor memory
python -c "import psutil; print(f'Memory: {psutil.virtual_memory().percent}%')"

# Check cache size
du -sh ~/.cache/lightrag/ 2>/dev/null || echo "No cache found"
```

**Solutions**:
- Clear LLM cache: `rm -rf ~/.cache/lightrag/`
- Check database configuration
- Use **[Process Skill](../../.agent/skills/process/SKILL.md)** for optimization

---

## D. UI/Web Interface Issues

### WebUI Won't Start?
**Symptom**: `npm run dev` fails or connection refused
```bash
cd lightrag_webui
npm install
npm run dev
# Check port conflicts
lsof -i :3000
```

**Solutions**:
- Use **[UI Skill](../../.agent/skills/ui/SKILL.md)** for frontend issues
- Check Node.js version: `node --version` (should be 16+)
- Verify API server is running

### Frontend Build Fails?
**Symptom**: Build errors during compilation
```bash
# Check dependencies
npm ls
npm audit fix

# Clean build
rm -rf node_modules package-lock.json
npm install
npm run build
```

**Solutions**:
- Use **[JavaScript Skill](~/.gemini/antigravity/skills/JavaScript/SKILL.md)** for JavaScript issues
- Check [Frontend Build Guide](../../docs/project/FrontendBuildGuide.md)
- Verify environment variables

---

## E. Database/Graph Issues

### Database Connection Fails?
**Symptom**: Connection refused or authentication errors
```bash
# Test database connection
sqlite3 lightrag/data.db ".tables"  # For SQLite
# or
curl -I neo4j:7474  # For Neo4j
```

**Solutions**:
- Use **[Graph Skill](../../.agent/skills/graph/SKILL.md)** for database issues
- Check database configuration in config files
- Verify database service is running

### Graph Queries Fail?
**Symptom**: Empty graph results or query errors
```bash
# Check graph data
python -c "from lightrag import LightRAG; rag=LightRAG('.'); print(rag.graph.query('MATCH (n) RETURN count(n)'))"
```

**Solutions**:
- Verify graph data was imported
- Check graph database configuration
- Use **[Testing Skill](../../.agent/skills/testing/SKILL.md)** for query debugging

---

## F. Agent Coordination Issues

### Session Lock Problems?
**Symptom**: "Agent already working" or stale lock errors
```bash
# Check agent status
cd .agent && ./scripts/agent-status.sh

# Clean stale locks (if >10 minutes old)
find .agent/session_locks -name '*.json' -mtime +1 -delete
```

**Solutions**:
- Use **[FlightDirector](~/.gemini/antigravity/skills/FlightDirector/SKILL.md)** for coordination
- Follow [Agent Coordination Guide](../../.agent/README.md#-multi-agent-coordination)

### Task Management Issues?
**Symptom**: `bd` command failures or sync problems
```bash
# Check beads status
bd status
bd sync

# Use sandbox mode if disk I/O errors
bd --sandbox <command>
```

**Solutions**:
- Check [Beads Usage Guide](../../.agent/GLOBAL/standards/HOW_TO_USE_BEADS.md)
- Use **[Process Skill](../../.agent/skills/process/SKILL.md)** for workflow issues
- See [Troubleshooting Guide](../../.agent/docs/troubleshooting/beads_sync_issues.md)

---

## 🆘 Emergency Procedures

### **Nothing Above Worked?**

1. **Use Global Skills**:
   - `/librarian` for knowledge organization
   - `/flight-director` for complex coordination
   - `/quality-analyst` for systematic debugging

2. **Check Historical Issues**:
   - Search [archive/audits/](../../archive/audits/) for similar problems
   - Check git history: `git log --oneline --grep="your-issue"`

3. **Get Human Help**:
   - Document what you've tried
   - Include error messages and logs
   - Reference this troubleshooting map

### **Prevent Future Issues**

- Use progressive disclosure: start with quick docs, then detailed
- Follow session management protocols
- Keep documentation updated with new issues and solutions
- Regular maintenance: `bd sync`, cache cleanup, log rotation

---

**💡 Navigation Tip**: Each section references the most relevant skill for that type of problem. When in doubt, start with the skill mentioned in your problem section.
