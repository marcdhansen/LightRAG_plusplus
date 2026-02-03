# OpenViking Agent Skill

## Overview

OpenViking is an enhanced agent system designed to replace the Standard Mission Protocol (SMP) with improved skill discovery, token efficiency, and conversation memory management.

## Quick Start for New Agents

### Prerequisites

- OpenAI API key required for OpenViking operations
- Docker environment with compose support
- Existing LightRAG project workspace

### Initialization

```bash
# 1. Set OpenAI API key
export OPENAI_API_KEY=your-openai-api-key-here

# 2. Start OpenViking services
./openviking/scripts/manage.sh start

# 3. Verify services are running
./openviking/scripts/manage.sh status

# 4. Test OpenViking functionality
curl -f http://localhost:8000/health
curl -f http://localhost:9622/health
```

## Key Differences from SMP

### Feature Comparison

| Feature | SMP | OpenViking |
| :--- | :--- | :--- |
| Skill Discovery | Manual file-based | Dynamic AI-powered |
| Token Efficiency | Standard (850 avg) | Optimized (≤680 target) |
| Conversation Memory | Limited | Enhanced multi-turn |
| Response Time | 2500ms avg | ≤1500ms target |
| Success Rate | 97% | ≥98% target |

### Architecture Differences

- **SMP**: File-based skill system in `.agent/skills/`
- **OpenViking**: AI-powered skill discovery with conversation memory
- **Port Mapping**: SMP uses :9621, OpenViking uses :9622 for LightRAG integration

### Slash Command Support

OpenViking now supports cross-agent slash commands from `~/.agent/commands/`:

```bash
# List all available commands
curl http://localhost:8000/commands

# Get a specific command by name
curl -X POST http://localhost:8000/commands/get \
  -H "Content-Type: application/json" \
  -d '{"name": "/rtb"}'

# Get command by path
curl http://localhost:8000/commands/rtb

# Search commands
curl http://localhost:8000/commands/search/beads
```

### Slash Command Synchronization

To use these commands directly in your agent terminal/chat (e.g., typing `/next`), they must be synchronized to the project's workflow directory:

```bash
# Manual synchronization
python3 openviking/commands.py --sync .agent/workflows/

# Automated synchronization
# Automatically handled by ./scripts/agent-init.sh and ./scripts/enhanced-agent-init.sh
```

**Available Endpoints:**

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/commands` | GET | List all slash commands |
| `/commands/get` | POST | Get command by name (body: `{"name": "/cmd"}`) |
| `/commands/{name}` | GET | Get command by path parameter |
| `/commands/search/{query}` | GET | Search commands by keyword |

## OpenViking-Specific Operations

### Session Management

```bash
# Check OpenViking session status
./scripts/agent-status.sh  # Shows both SMP and OpenViking sessions

# Start OpenViking-specific session
./scripts/agent-start.sh --task-id <id> --task-desc "OpenViking: <description>"

# End session (includes cleanup)
./scripts/agent-end.sh
```

### Performance Monitoring

```bash
# Run A/B comparison with SMP
./openviking/scripts/manage.sh compare

# Monitor OpenViking performance
watch -n 5 'curl -s -w "%{time_total}\n" -o /dev/null http://localhost:9622/api/chat -X POST -H "Content-Type: application/json" -d '"'"'{"query":"test"}'"'"''
```

### Data Migration (from SMP)

```bash
# Migrate existing SMP data to OpenViking
./openviking/scripts/manage.sh migrate

# Verify migration success
ls -la ./data/openviking/
curl -s http://localhost:8000/migration/status
```

## Integration Points

### With Existing LightRAG Workflow

1. **Bootstrap**: Enhanced `agent-init.sh` detects OpenViking availability
2. **Task Management**: Uses same `bd` system for issue tracking
3. **Quality Gates**: Identical testing and linting requirements
4. **Documentation**: Same RTB procedure with OpenViking-specific logs

### Service Architecture

```text
┌─────────────────┐    ┌─────────────────┐
│   OpenViking    │    │  LightRAG App   │
│   Agent Engine  │    │   (Client)      │
│   :8000         │    │   :9622         │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌─────────────────────┐
         │   OpenViking Redis   │
         │   :6379 (Memory)     │
         └─────────────────────┘
```

## OpenViking Configuration

### Environment Variables

```bash
OPENAI_API_KEY=your-openai-api-key-here    # Required
OPENVIKING_STORAGE_PATH=/data/openviking   # Data storage
LOG_LEVEL=INFO                             # Logging verbosity
```

### Service Ports

- **OpenViking API**: 8000 (main agent interface)
- **LightRAG Integration**: 9622 (OpenViking-powered LightRAG)
- **Redis Memory**: 6379 (conversation and session storage)
- **Health Checks**: `/health` endpoint on all services

## Troubleshooting OpenViking

### Common Issues

#### OpenViking fails to start

```bash
# Check API key
echo $OPENAI_API_KEY

# Verify Docker services
docker ps | grep openviking

# Check logs
docker logs lightrag-openviking
```

#### Performance degradation

```bash
# Run comparison test
./openviking/scripts/manage.sh compare

# Check resource usage
docker stats lightrag-openviking --no-stream

# Verify Redis memory
docker exec lightrag-openviking-redis redis-cli info memory
```

#### Session coordination issues

```bash
# Check session locks
ls -la .agent/session_locks/

# Clear stale sessions
./scripts/agent-status.sh  # Identifies stale locks

# Manual cleanup if needed
rm .agent/session_locks/stale_*.json
```

## Migration from SMP

### When to Use OpenViking

- **New projects**: Start with OpenViking for better performance
- **Token-sensitive applications**: Reduced token usage
- **Complex conversations**: Enhanced memory management
- **AI-powered workflows**: Dynamic skill discovery

### Migration Checklist

- [ ] Export existing SMP session data
- [ ] Set OpenAI API key
- [ ] Start OpenViking services
- [ ] Run data migration tool
- [ ] Verify functionality with comparison tests
- [ ] Update team documentation
- [ ] Train team on OpenViking operations

## Performance Expectations

### Target Metrics (vs SMP)

- **Response Time**: 40% faster (≤1500ms vs 2500ms)
- **Token Usage**: 20% reduction (≤680 vs 850)
- **Success Rate**: 1% improvement (≥98% vs 97%)
- **Memory Efficiency**: 20% reduction (≤120MB vs 150MB)

### Success Criteria

OpenViking is considered successful when:

1. All primary metrics meet minimum acceptable values
2. At least 3 of 4 secondary metrics meet targets
3. No critical bugs or stability issues
4. Team training completed

## Integration with Existing SOP

OpenViking integrates seamlessly with the existing LightRAG SOP:

1. **Bootstrap**: Enhanced `agent-init.sh` detects and configures OpenViking
2. **Session Management**: Same scripts with OpenViking-aware coordination
3. **Quality Gates**: Identical pytest, ruff, mypy requirements
4. **RTB Procedure**: Same git push workflow with OpenViking service verification
5. **Documentation**: Same `/reflect` skill with OpenViking session data

### Updated RTB for OpenViking

```bash
# Standard RTB steps (unchanged)
pytest && ruff check && ruff format
bd sync && git push

# OpenViking-specific additions
curl -f http://localhost:8000/health  # Verify OpenViking API
./openviking/scripts/manage.sh status  # Check OpenViking services

# Global memory push (unchanged)
cd ~/.gemini && git add -A && git commit -m "OpenViking session learnings" && git push
```

---

**Skill Version**: 1.0
**Last Updated**: 2026-02-03
**Compatible**: LightRAG v2.0+ with OpenViking integration
