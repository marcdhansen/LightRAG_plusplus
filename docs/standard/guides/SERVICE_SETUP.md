# 🔧 Service Setup Guide for LightRAG Agent Onboarding

This guide provides comprehensive setup and troubleshooting instructions for the critical services used in LightRAG agent onboarding.

## 📋 Quick Reference

| Service | Default Port | Health Endpoint | Authentication | Startup Command |
|---------|---------------|------------------|------------------|-----------------|
| Automem Flask API | 8001 | `GET /health` | `Authorization: Bearer test-token` | `make dev` |
| Automem FalkorDB | 6380 | N/A | N/A | Docker managed |
| Langfuse Web UI | 3000 | `GET /api/public/health` | Pre-configured keys | `docker-compose up -d` |
| Langfuse Redis | 6379 | N/A | N/A | Docker managed |

---

## 🧠 Automem Service Setup

### Prerequisites
```bash
# Required paths
export AUTOMEM_PATH="$HOME/GitHub/verygoodplugins/automem"
export AUTOMEM_API_TOKEN="test-token"
export ADMIN_API_TOKEN="test-admin-token"

# Optional: Local model configuration
export EMBEDDING_PROVIDER="auto"  # auto|openai|local|placeholder
export OPENAI_API_KEY="your-key-here"  # Optional, for OpenAI embeddings
```

### Startup Procedure
```bash
cd "$AUTOMEM_PATH"

# Start all services (FalkorDB + Qdrant + Flask API)
make dev

# Verify startup
curl -s http://localhost:8001/health | jq .

# Expected response:
{
  "status": "healthy",
  "falkordb": "connected",
  "qdrant": "connected",
  "memory_count": 0,
  "vector_count": 0,
  "sync_status": "synced",
  "enrichment": {
    "status": "running",
    "queue_depth": 0,
    "pending": 0,
    "inflight": 0,
    "processed": 0,
    "failed": 0
  },
  "timestamp": "2026-01-29T21:58:33.513260+00:00",
  "graph": "memories"
}
```

### Service Components
1. **FalkorDB** (Port 6380): Graph database for memory relationships
2. **Qdrant** (Port 6333): Vector database for semantic search
3. **Flask API** (Port 8001): REST API for memory operations
4. **Enrichment Pipeline**: Background processing for entity extraction
5. **Consolidation Scheduler**: Periodic memory maintenance

### Health Status Meanings
- **healthy**: All systems operational, data synchronized
- **degraded**: At least one system offline or data out of sync
- **falkordb**: Graph database connectivity status
- **qdrant**: Vector database connectivity status
- **sync_status**: Data consistency between graph and vector stores
  - `synced`: Memory and vector counts match
  - `drift_detected`: More memories than vectors
  - `orphaned_vectors`: More vectors than memories

### API Testing
```bash
# Store a memory
curl -X POST -H "Authorization: Bearer test-token" \
     -H "Content-Type: application/json" \
     -d '{"content": "Test memory", "tags": ["test"]}' \
     http://localhost:8001/memory

# Retrieve memories
curl -H "Authorization: Bearer test-token" \
     -G -d "query=test" \
     http://localhost:8001/recall

# Delete a memory (replace with actual ID)
curl -X DELETE -H "Authorization: Bearer test-token" \
     http://localhost:8001/memory/{memory_id}
```

### Troubleshooting
```bash
# Check service logs
cd "$AUTOMEM_PATH"
make logs

# Restart services
docker compose down
docker compose up --build

# Clear corrupted data (last resort)
docker compose down -v
docker compose up --build
```

---

## 🔭 Langfuse Service Setup

### Prerequisites
```bash
# Langfuse uses pre-configured Docker environment
cd "$PWD/langfuse_docker"  # or your Langfuse directory
```

### Startup Procedure
```bash
# Start all Langfuse services
docker-compose up -d

# Wait for initialization (up to 90 seconds)
# Web UI: http://localhost:3000
# Default credentials: pk-lf-lightrag / sk-lf-lightrag
```

### Service Components
1. **Web UI** (Port 3000): Main dashboard and visualization
2. **Worker** (Port 3030): Background job processing
3. **PostgreSQL** (Port 5432): Primary data storage
4. **ClickHouse** (Port 8123): Analytics and events storage
5. **Redis** (Port 6379): Job queue and caching
6. **MinIO** (Port 9090): Object storage for traces

### Health Check
```bash
# API health check
curl -s http://localhost:3000/api/public/health

# Expected response:
{
  "status": "OK",
  "version": "3.141.0"
}
```

### Web UI Access
- **URL**: http://localhost:3000
- **Public Key**: `pk-lf-lightrag`
- **Secret Key**: `sk-lf-lightrag`
- **Default Organization**: Default Org
- **Default Project**: LightRAG

### Troubleshooting
```bash
# Check service logs
docker-compose logs -f

# Check specific service
docker-compose logs langfuse-web
docker-compose logs langfuse-worker

# Restart services
docker-compose restart

# Full reset (last resort)
docker-compose down -v
docker-compose up -d
```

---

## 🚨 Common Issues & Solutions

### Port Conflicts
**Problem**: Services fail to start due to port conflicts
**Solution**: Identify conflicting processes and stop them
```bash
# Check port usage
lsof -i :8001  # Automem API
lsof -i :3000  # Langfuse Web UI
lsof -i :6379  # Langfuse Redis
lsof -i :6380  # Automem FalkorDB

# Kill conflicting processes
kill -9 $(lsof -ti:8001)
```

### Authentication Failures
**Problem**: API returns 401 Unauthorized
**Solution**: Verify tokens are correctly set
```bash
# Check Automem tokens
echo $AUTOMEM_API_TOKEN
echo $ADMIN_API_TOKEN

# Test with curl
curl -H "Authorization: Bearer test-token" http://localhost:8001/health
```

### Service Startup Timeout
**Problem**: Services take too long to initialize
**Solution**: Increase timeout or check resource constraints
```bash
# Check Docker resource usage
docker stats

# Check disk space
df -h

# Check memory usage
free -h
```

### Database Connection Issues
**Problem**: Services start but can't connect to databases
**Solution**: Verify database containers are healthy
```bash
# Check Automem databases
docker ps | grep automem
docker logs automem-flask-api-1

# Check Langfuse databases
docker ps | grep langfuse
docker logs langfuse_docker-postgres-1
```

### Data Synchronization Issues
**Problem**: Automem shows "drift_detected" status
**Solution**: Run manual sync or re-embed data
```bash
# Access Automem admin interface
curl -H "Authorization: Bearer test-admin-token" \
     -X POST \
     http://localhost:8001/admin/sync

# Re-embed all memories (if needed)
curl -H "Authorization: Bearer test-admin-token" \
     -X POST \
     http://localhost:8001/admin/reembed
```

---

## 🔧 Environment Configuration

### Required Environment Variables
```bash
# Automem Configuration
export AUTOMEM_PATH="$HOME/GitHub/verygoodplugins/automem"
export AUTOMEM_API_TOKEN="test-token"
export ADMIN_API_TOKEN="test-admin-token"

# Optional: OpenAI Integration
export OPENAI_API_KEY="your-openai-api-key"
export EMBEDDING_PROVIDER="auto"  # auto|openai|local|placeholder
export CLASSIFICATION_MODEL="gpt-4o-mini"

# Optional: Database Passwords
export FALKORDB_PASSWORD=""  # Default: empty
export QDRANT_API_KEY=""       # Default: empty
```

### Docker Configuration Files
- **Automem**: `$AUTOMEM_PATH/docker-compose.yml`
- **Langfuse**: `$PWD/langfuse_docker/docker-compose.yml`

### Service Dependencies
- Automem requires FalkorDB and Qdrant to be healthy before API starts
- Langfuse requires PostgreSQL, ClickHouse, Redis, and MinIO
- Both services can run independently of each other

---

## 🧪 Integration Testing

### Automem Smoke Test
```bash
#!/bin/bash
# Test complete Automem workflow

API_TOKEN="test-token"
BASE_URL="http://localhost:8001"

# 1. Store memory
MEMORY_RESPONSE=$(curl -s -X POST \
    -H "Authorization: Bearer $API_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"content": "Integration test memory", "tags": ["test"]}' \
    "$BASE_URL/memory")

echo "Store Response: $MEMORY_RESPONSE"

# 2. Recall memory
MEMORY_ID=$(echo "$MEMORY_RESPONSE" | grep -o '"id":\s*"[^"]*"' | cut -d'"' -f4)
RECALL_RESPONSE=$(curl -s -G \
    -H "Authorization: Bearer $API_TOKEN" \
    -d "query=integration test" \
    "$BASE_URL/recall")

echo "Recall Response: $RECALL_RESPONSE"

# 3. Cleanup
if [[ -n "$MEMORY_ID" ]]; then
    curl -s -X DELETE \
        -H "Authorization: Bearer $API_TOKEN" \
        "$BASE_URL/memory/$MEMORY_ID"
    echo "Test memory cleaned up"
fi
```

### Langfuse Smoke Test
```bash
#!/bin/bash
# Test Langfuse integration

# 1. Health check
curl -s http://localhost:3000/api/public/health

# 2. Web UI accessibility
curl -s -I http://localhost:3000 | head -1

# Expected: HTTP/1.1 200 OK
```

---

## 📞 Getting Help

### Log Locations
```bash
# Automem logs
cd "$AUTOMEM_PATH"
docker compose logs -f flask-api

# Langfuse logs
cd "$PWD/langfuse_docker"
docker-compose logs -f langfuse-web
```

### Community Support
- **LightRAG Repository**: Check issues and discussions
- **Automem Repository**: Service-specific issues
- **Langfuse Documentation**: https://docs.langfuse.com/

### Debug Mode
```bash
# Enable debug logging for Automem
export FLASK_DEBUG=1
export FLASK_ENV=development

# Restart Automem with debug mode
cd "$AUTOMEM_PATH"
docker compose down
docker compose up --build
```
