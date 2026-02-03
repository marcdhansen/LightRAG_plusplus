# Self-Evolution Tracker

This document tracks ideas for continuous improvement of both the AI agent capabilities and the LightRAG system. Ideas are prioritized and regularly reassessed.

## Active Improvement Areas

### Agent Workflow Improvements

| Idea | Priority | Status | Notes |
|------|----------|--------|-------|
| Update memory.md with learnings after each session | p0 | `lightrag-xxx` | Capture patterns, preferences, discoveries |
| Proactively suggest improvements after tasks | p0 | Active | Built into workflow |

### System Improvements

| Idea | Priority | Status | Notes |
|------|----------|--------|-------|
| ACE framework integration | p1 | ✓ Done | Core GRC loop implemented |
| Semantic Highlighting | p1 | ✓ Backend | Zilliz model integrated |
| RAGAS evaluation baseline | p1 | ✓ Done | Baseline scores generated |
| Pytest for Manual Testing | p0 | Active | Framework established with `--run-manual` |

---

## QA Protocols [NEW]

### Pre-Commit Code Quality

- [Rule] **Always** run `pre-commit run --all-files` before pushing to ensure linting and formatting are correct.
- [Rule] Check `ruff` output and fix manual errors (like `E741` ambiguous variable names) immediately.

### CI/CD Test Isolation

- [Rule] When adding new test directories (especially those requiring external dependencies like `playwright` or `docker`), **verify** they are excluded from the `offline` test suite.
  - Check `.github/workflows/tests.yml`: The `pytest -m offline` command should explicitly ignore online folders if the marker isn't sufficient (e.g., `--ignore=tests/ui`).
  - Check `pyproject.toml` or `pytest.ini` for marker configurations.

---

## Learning Resources

### ACE Framework (Agentic Context Engineering)

- [ACE GitHub Repo](https://github.com/ace-agent/ace)
- Core concept: Evolve context through Generator → Reflector → Curator cycle
- Key insight: Incremental delta updates prevent context collapse
- Application: Use for improving agent memory and playbook

### MemEvolve

- [MemEvolve GitHub Repo](https://github.com/bingreeky/MemEvolve)
- Focus: Meta-evolution of agent memory systems.

### Beads Best Practices

- Always add descriptions to issues
- Close with detailed reasons for future reference
- Keep planning docs and issues in sync

### Operational Learnings

- **Git Repository Location**: The git root is nested in `LightRAG/`. ALWAYS run git commands from `/Users/marchansen/antigravity_lightrag/LightRAG`. The workspace root is NOT a git repository.
- **Workspace Pattern**: Maintain the distinction between `Workspace` (Experiment/Lab) and `Project` (Git Repo). Always check if the current directory is a wrapper before initializing git or moving files.
- **Strict Mission Protocol**: Any structural change or code modification MUST have a Beads issue. Run `bd create` upon task definition, not after execution.

### Model Selection Criteria

When evaluating LLM models, consider these tradeoffs:

| Criterion | Question | Priority |
|-----------|----------|----------|
| **Speed** | What are the fastest models? | High for iteration |
| **Quality** | Does output meet requirements? | High for production |
| **No-code-change** | Can swap via .env only? | High for flexibility |
| **Context window** | Fits our document sizes? | Required |
| **Cost** | Token/API costs acceptable? | Varies |

**Current findings (2026-01-19):**

- `llama3.2:3b`: Best balance (12.65 t/s, good entity extraction)
- `qwen2.5-coder:1.5b`: Fastest (35 t/s) but poor quality for RAG tasks
- `mistral-nemo`: Good quality but slow (3.14 t/s)
- Embedding: `nomic-embed-text:v1.5` (only dedicated option)

---

## Improvement Backlog

### High Priority (p0/p1)

- [ ] Establish feedback loop for capturing user preferences
- [ ] Create templates for common task types
- [ ] Define metrics for measuring improvement
- [ ] Automate `pre-commit` in a local hook (if not already strictly enforced).
- [ ] Create a `verify_ci_config` script/skill to check for new directories not covered by exclusions.

### Medium Priority (p2)

- [ ] Experiment with different prompt structures
- [ ] Analyze which beads patterns work best
- [ ] Document anti-patterns to avoid

### Ideas to Explore

- How can the Reflector component critique completed work?
- What metadata should be captured per interaction?
- How to measure "improvement" quantitatively?
- **Prompt Tracking**: What is a solution that will track agent prompts and responses? (Investigate Langfuse/Custom logging)
- **MemGPT/Letta**: Investigate adding MemGPT (open source version of Letta) to the observability section.
- **Agentic RAG**: What additional functionality should the agent have?
  - Pick retrieval method(s)?
  - Pick LLM for a given task?
  - Pick chunking method/size/overlap?

---

## Technical Experiments Backlog

### RAG Modes Evaluation

Compare performance and quality across:

- [ ] Naive RAG
- [ ] Local RAG
- [ ] Global RAG
- [ ] Hybrid RAG
- [ ] Mix (Graph + Vector)

### Graph Storage & Hierarchy

- [ ] Framework for testing different strategies (e.g., contextual chunking, late chunking).
- [ ] Support for cold graph storage (Neo4j for demos).
- [ ] Support for temporal graphs (How to test?).
- [ ] Self-healing capabilities like Greptile.
- [ ] Review [n8n harness video](https://youtu.be/RQq3aMV7a5g?si=qfsbiuSGN33DVMrZ) for additional ideas.

---

## Review Log

| Date | Reviewer | Changes Made |
|------|----------|--------------|
| 2026-01-19 | Initial | Created document |
| 2026-01-23 | Antigravity | Standardized Pytest for manual testing; Updated priorities. |
| 2026-01-26 | Antigravity | Merged offline version; Added QA Protocols |

---

## Principles

1. **Proactive improvement**: Don't wait for problems; actively seek better approaches
2. **Learn from feedback**: Capture what works, discard what doesn't
3. **Incremental evolution**: Small, focused improvements compound over time
4. **Sync with beads**: Every improvement idea should become a trackable issue
5. **Reassess regularly**: Priorities shift; re-evaluate periodically
