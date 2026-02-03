# 🚀 LightRAG Quick Start

**Purpose**: Get up and running with LightRAG in 5 minutes.

## ⚡ Essential Commands

```bash
# Setup
pip install lightrag

# Basic usage
from lightrag import LightRAG
rag = LightRAG("path/to/data")
result = rag.query("your question")

# Web UI
cd lightrag_webui && npm install && npm run dev
```

## 🔧 Quick Setup

```bash
# Environment
export OPENAI_API_KEY="your-key"  # or OLLAMA_BASE_URL for local

# Database: SQLite (default), Neo4j, PostgreSQL
```

## 🤖 For Agents

```bash
cd .agent && ./scripts/agent-start.sh --task-id <id> --task-desc "description"
bd ready  # See available tasks
```

## 🆘 Need Help?

- [📚 Full Docs](../standard/) - Complete guides
- [🔧 Troubleshooting](../navigation/TROUBLESHOOTING_MAP.md) - Common issues
- [🗺️ Navigation](../navigation/QUICK_START.md) - Find anything

**💡 Tip**: Use standard docs for detailed setup instructions.
