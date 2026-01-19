# Detailed Agent Instructions for LightRAG Development

**For project overview and quick start, see [AGENTS.md](AGENTS.md)**

This document contains detailed operational instructions for AI agents working on LightRAG development, testing, and deployment.

## Development Guidelines

### Code Standards

- **Python version**: 3.10+
- **Package manager**: `uv` (for dependency management)
- **Linting**: `ruff check .` and `ruff format .`
- **Testing**: `pytest tests/` for unit tests
- **Type hints**: Use type hints for all public functions

### File Organization

```
LightRAG/
├── lightrag/
│   ├── api/               # FastAPI server and endpoints
│   ├── evaluation/        # RAGAS evaluation framework
│   ├── llm/               # LLM provider integrations
│   ├── kg/                # Knowledge graph operations
│   └── storage/           # Storage backends
├── tests/                 # Test suite
├── examples/              # Usage examples
├── docs/                  # Documentation
└── *.md                   # Root documentation
```

### Testing Workflow

**IMPORTANT:** Always run tests before committing changes.

**For local testing:**

```bash
# Sync dependencies
cd /Users/marchansen/claude_test/LightRAG
uv sync --extra api

# Run unit tests
uv run pytest tests/ -v

# Run specific test
uv run pytest tests/test_ollama_timeout.py -v
```

**For integration testing with server:**

```python
# Start the LightRAG server
import asyncio
from lightrag import LightRAG

async def test_rag():
    rag = LightRAG(working_dir="./test_storage")
    await rag.initialize_storages()
    
    # Insert test document
    await rag.ainsert("Test document content...")
    
    # Query
    result = await rag.aquery("What is in the test document?")
    print(result)

asyncio.run(test_rag())
```

### Before Committing

1. **Run tests**: `uv run pytest tests/ -v`
2. **Run linter**: `ruff check . && ruff format .`
3. **Update docs**: If you changed behavior, update README.md or other docs
4. **Update beads**: Close finished issues, update status
5. **Sync and push**: `bd sync && git push`

### Commit Message Convention

Include the beads issue ID in parentheses at the end:

```bash
git commit -m "Fix timeout handling in Ollama client (lightrag-abc)"
git commit -m "Add RAGAS evaluation baseline (lightrag-xyz)"
```

## LightRAG Server

### Starting the Server

```bash
# From project root
cd /Users/marchansen/claude_test/LightRAG

# Build WebUI (if needed)
cd lightrag_webui && bun run build && cd ..

# Sync dependencies and start
uv sync --extra api
uv run lightrag-server
```

Server runs at `http://localhost:9621`

### Key Environment Variables

Located in `.env`:

```bash
# LLM Configuration
LLM_BINDING=ollama
LLM_MODEL=llama3.2:3b
LLM_BINDING_HOST=http://localhost:11434
LLM_TIMEOUT=9000  # 2.5 hours for large PDFs

# Embedding Configuration
EMBEDDING_BINDING=ollama
EMBEDDING_MODEL=nomic-embed-text:v1.5
EMBEDDING_DIM=768

# Storage Configuration
LIGHTRAG_KV_STORAGE=JsonKVStorage
LIGHTRAG_DOC_STATUS_STORAGE=JsonDocStatusStorage
LIGHTRAG_GRAPH_STORAGE=NetworkXStorage
LIGHTRAG_VECTOR_STORAGE=NanoVectorDBStorage
```

### API Examples

```python
import httpx

# Upload a document
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:9621/documents",
        files={"file": open("document.pdf", "rb")}
    )

# Query the knowledge graph
async with httpx.AsyncClient() as client:
    response = await client.post(
        "http://localhost:9621/query",
        json={"query": "What are the main findings?", "mode": "hybrid"}
    )
    print(response.json())
```

## Evaluation Framework

### RAGAS Integration

Already available in `lightrag/evaluation/`:

```bash
# Install evaluation dependencies
pip install -e ".[evaluation]"

# Run RAGAS evaluation
python lightrag/evaluation/eval_rag_quality.py --dataset sample_dataset.json
```

### Custom Test Dataset

Create a JSON file with test cases:

```python
{
    "test_cases": [
        {
            "question": "Your question here",
            "ground_truth": "Expected answer from your data",
            "project": "evaluation_project_name"
        }
    ]
}
```

### Langfuse Tracing (Self-Hosted)

Configure in `.env`:

```bash
LANGFUSE_SECRET_KEY="<your-key>"
LANGFUSE_PUBLIC_KEY="<your-key>"
LANGFUSE_HOST="http://localhost:3000"  # Self-hosted
LANGFUSE_ENABLE_TRACE=true
```

## Landing the Plane

**When the user says "let's land the plane"**, you MUST complete ALL steps below.

**MANDATORY WORKFLOW:**

1. **File beads issues for any remaining work**
2. **Run quality gates** (if code changes were made):
   ```bash
   ruff check .
   uv run pytest tests/ -v
   ```
3. **Update beads issues** - close finished work, update status
4. **PUSH TO REMOTE - NON-NEGOTIABLE**:
   ```bash
   git pull --rebase
   bd sync
   git push
   git status  # MUST show "up to date with origin"
   ```
5. **Verify** - All changes committed AND pushed
6. **Hand off** - Provide context for next session

**CRITICAL:**
- Work is NOT complete until `git push` succeeds
- NEVER stop before pushing
- NEVER say "ready to push when you are" - YOU must push

## Agent Session Workflow

**WARNING: DO NOT use `bd edit`** - it opens an interactive editor. Use `bd update` with flags instead:

```bash
bd update <id> --description "new description"
bd update <id> --title "new title"
bd update <id> --status in_progress
```

**Always run at session end:**

```bash
bd sync  # Immediate flush/commit/push
```

## Common Development Tasks

### Adding a New API Endpoint

1. Create route in `lightrag/api/`
2. Add request/response models with Pydantic
3. Implement business logic
4. Add tests in `tests/`
5. Document in API README

### Adding Storage Features

1. Implement interface in `lightrag/storage/`
2. Add configuration in `.env.example`
3. Add tests
4. Update documentation

### Running Profiling

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Your code here
await rag.aquery("test query")

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

## Building and Testing

```bash
# Install dependencies
uv sync --extra api

# Run tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=lightrag --cov-report=html

# Start server
uv run lightrag-server
```

## Questions?

- Check existing issues: `bd list`
- Look at recent commits: `git log --oneline -20`
- Read the docs: README.md, docs/
- Create an issue if unsure: `bd create "Question: ..." --description "..."`

## Important Files

- **README.md** - Main documentation
- **.env** - Environment configuration
- **AGENTS.md** - Quick reference for agents
- **TODO.md** - Project roadmap and tasks
- **lightrag/evaluation/README_EVALUASTION_RAGAS.md** - Evaluation guide
