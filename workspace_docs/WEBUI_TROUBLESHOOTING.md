# Web UI Troubleshooting & FAQ

This document tracks recurring issues with the LightRAG Web UI and provides consistent fixes to avoid mission downtime.

## Build Failures

### 1. Inconsistent Badge Import

**Problem**: Build fails with `error during build: src/components/retrieval/ReferenceList.tsx (3:9): "Badge" is not exported by "src/components/ui/Badge.tsx"`.
**Cause**: `Badge.tsx` uses `export default Badge`, but `ReferenceList.tsx` attempts a named import `import { Badge }`.
**Fix**: Ensure `ReferenceList.tsx` (and any other consumer) uses the default import:

```tsx
import Badge from '@/components/ui/Badge'
```

### 2. Dependency Issues

**Problem**: UI components fail to load or build after updating dependencies.
**Fix**: Clear `node_modules` and reinstall using `bun`:

```bash
cd LightRAG/lightrag_webui
rm -rf node_modules bun.lock
bun install
```

## Runtime Issues

### 1. Graph Not Rendering

**Problem**: The knowledge graph remains empty even after document ingestion.
**Cause**: The API server might not be running or the connection to Memgraph/Neo4j is down.
**Fix**:

1. Verify the API server is alive: `curl http://localhost:9621/health`
2. Check API logs for database connection errors.
3. Refresh the Web UI.

## Verification Checklist (Mandatory before RTB)

- [ ] Build passes: `bun run build` in `lightrag_webui`.
- [ ] Knowledge Graph loads and displays entities.
- [ ] Retrieval interface works with test queries.
