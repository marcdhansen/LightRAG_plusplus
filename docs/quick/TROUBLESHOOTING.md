# 🔥 Common Issues Quick Fix

**Purpose**: Fast solutions to frequent LightRAG problems.

## 🚀 Setup Issues

**Python:**
```bash
pip install uv && uv sync  # Faster than pip
```

**Models:**
```bash
export OLLAMA_BASE_URL="http://localhost:11434"  # Local
export OPENAI_API_KEY="your-key"  # Cloud
```

## ⚡ Performance Issues

**Hanging queries:**
```bash
grep -r timeout . --include="*.py"  # Check timeouts
```

**Slow extraction:**
```bash
cat docs/standard/guides/model_routing.md  # Check routing
```

## 🔧 Configuration

**Database:**
```bash
ls lightrag/ && cat your_config.json | grep database
```

**Web UI:**
```bash
cd lightrag_webui && npm install && npm run dev
lsof -i :3000  # Check port conflicts
```

## 🆘 More Help

- [🗺️ Detailed Map](../navigation/TROUBLESHOOTING_MAP.md)
- [📚 Full Docs](../standard/)
- [🤝 Coordination](../../.agent/)

**💡 Tip**: Check environment variables first - most issues are configuration-related.
