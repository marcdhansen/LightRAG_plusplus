# 🔄 LightRAG Session Startup Guide

> **Purpose**: Fast startup for returning agents (every work session)
> **Audience**: Returning agents starting new work sessions
> **Frequency**: Perform at start of **every** work session
> **Prerequisites**: One-time setup completed (`.setup_complete` exists)

---

## 🎯 Session Overview

This guide covers daily session startup for agents who have already completed one-time setup. The goal is to get you productive within 2-3 minutes.

### ⏱️ Time Estimates
- **Quick Start**: 2-3 minutes (if services already running)
- **Cold Start**: 5-8 minutes (need to start services)
- **With Issues**: 10-15 minutes (troubleshooting required)

---

## 🚀 Quick Session Start

### Step 1: Run Session Startup Script

```bash
# Navigate to LightRAG repository
cd /path/to/LightRAG

# Start session (automated)
./scripts/start-session.sh
```

### Step 2: Review Session Status

After startup completes, review the session status report:

```bash
# Check service status
curl -s http://localhost:8001/health | jq .status
curl -s http://localhost:3000/api/public/health | jq .status

# View available tasks
bd ready
```

---

## 📋 What the Session Script Does

### Environment Validation
- ✅ **Setup Check**: Verifies one-time setup was completed
- ✅ **Docker Status**: Ensures Docker Desktop is running
- ✅ **Path Validation**: Confirms required paths exist

### Service Startup
- ✅ **Automem Service**: Starts Flask API + databases
- ✅ **Langfuse Service**: Starts observability stack
- ✅ **Health Monitoring**: Waits for services to be ready
- ✅ **Error Recovery**: Attempts single restart if needed

### Project Context Loading
- ✅ **Pre-Flight Check**: Runs Flight Director verification
- ✅ **Task Discovery**: Shows current available tasks
- ✅ **Project Status**: Loads current ROADMAP and ImplementationPlan
- ✅ **Session Context**: Queries Automem for relevant memories

---

## 🛠️ Manual Session Startup (Fallback)

If the automated script fails, use this manual process:

### Step 1: Start Docker Desktop
```bash
# Check if running
docker info

# Start if needed (macOS)
open /Applications/Docker.app

# Wait for startup
while ! docker info >/dev/null 2>&1; do
    echo "Waiting for Docker..."
    sleep 2
done
```

### Step 2: Start Services

```bash
# Start Automem
cd ~/GitHub/verygoodplugins/automem
make dev

# Start Langfuse (in another terminal)
cd /path/to/LightRAG/langfuse_docker
docker-compose up -d
```

### Step 3: Verify Services

```bash
# Check Automem health
curl -s http://localhost:8001/health | jq .

# Check Langfuse health
curl -s http://localhost:3000/api/public/health | jq .

# Test Automem API
curl -H "Authorization: Bearer test-token" \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"content": "test", "tags": ["session-test"]}' \
     http://localhost:8001/memory
```

### Step 4: Load Project Context

```bash
# Run Pre-Flight Check
python ~/.gemini/antigravity/skills/flight-director/scripts/check_flight_readiness.py --pfc

# Discover available tasks
bd ready

# Load project status
cat .agent/rules/ROADMAP.md
cat .agent/rules/ImplementationPlan.md
```

---

## 📊 Session Status Dashboard

The session startup script provides a comprehensive status report:

```
📊 Session Status Report
  🕐 Session Start: 2026-01-29 14:30:15
  📁 Project Root: /Users/user/LightRAG
  🧠 Automem: healthy
  🔭 Langfuse: OK
  🐚 Ready Tasks: 3
```

### Status Indicators

| Service | Status | Meaning | Action |
|---------|--------|---------|--------|
| Automem: healthy | ✅ All systems operational | Continue |
| Automem: degraded | ⚠️ Some issues | Check logs |
| Langfuse: OK | ✅ Observability ready | Continue |
| Langfuse: error | ❌ Service down | Check Docker |

---

## 🚨 Common Session Startup Issues

### Docker Desktop Not Running
**Problem**: `docker info` fails
**Solution**:
```bash
# Start Docker Desktop
open /Applications/Docker.app

# Wait and verify
sleep 10 && docker info
```

### Port Conflicts
**Problem**: Services fail to start due to port conflicts
**Solution**:
```bash
# Find conflicting processes
lsof -i :8001  # Automem API
lsof -i :3000  # Langfuse Web UI

# Kill conflicting processes
kill -9 $(lsof -ti:8001)
kill -9 $(lsof -ti:3000)
```

### Service Health Failures
**Problem**: Health checks fail after startup
**Solution**:
```bash
# Check service logs
cd ~/GitHub/verygoodplugins/automem && make logs
cd /path/to/LightRAG/langfuse_docker && docker-compose logs

# Restart services
docker restart automem-flask-api-1
docker restart langfuse_docker-langfuse-web-1
```

### Authentication Issues
**Problem**: API returns 401 errors
**Solution**:
```bash
# Check environment variables
echo $AUTOMEM_API_TOKEN
echo $ADMIN_API_TOKEN

# Set default tokens if missing
export AUTOMEM_API_TOKEN=test-token
export ADMIN_API_TOKEN=test-admin-token
```

---

## 🔧 Service Health Commands

Keep these commands handy during your session:

### Quick Health Check
```bash
# Check both services
curl -s http://localhost:8001/health | jq '{status: .status, services: {automem: .status}}'
curl -s http://localhost:3000/api/public/health | jq '{status: .status, services: {langfuse: .status}}'
```

### Service Logs
```bash
# Automem logs
cd ~/GitHub/verygoodplugins/automem
make logs

# Langfuse logs
cd /path/to/LightRAG/langfuse_docker
docker-compose logs -f langfuse-web
```

### Service Restart
```bash
# Restart Automem
docker restart automem-flask-api-1

# Restart Langfuse
cd /path/to/LightRAG/langfuse_docker
docker-compose restart
```

---

## 🎯 Session Productivity Workflow

Once session startup completes:

1. **Check Tasks**: `bd ready` to see current work items
2. **Load Context**: Review ROADMAP.md for current project phase
3. **Start Working**: Pick a task and begin development
4. **Monitor Health**: Services should remain healthy throughout session
5. **Session End**: Use `./scripts/end-session.sh` for clean shutdown

---

## 📚 Related Documentation

- **🚀 One-Time Setup**: `SETUP.md` - For new environments
- **🔧 Service Details**: `SERVICE_SETUP.md` - Complete service documentation
- **🚨 Troubleshooting**: `TROUBLESHOOTING.md` - Common issues and solutions
- **📊 Project Status**: `.agent/rules/ROADMAP.md` - Current project state

---

## 💡 Session Tips

### For Fast Startup
1. **Keep Docker Running**: Don't close Docker Desktop between sessions
2. **Use Quick Start**: The automated script is faster than manual steps
3. **Monitor Health**: Check service status if things seem slow
4. **Bookmark Commands**: Keep health check commands handy

### For Productive Sessions
1. **Start with Tasks**: Use `bd ready` to choose work immediately
2. **Check Roadmap**: Understand current project phase and goals
3. **Monitor Services**: If errors occur, check health endpoints first
4. **End Cleanly**: Use `end-session.sh` to preserve work and status

---

## 🔄 Session Variations

### Quick Development Session
```bash
# For quick coding work
./scripts/start-session.sh
bd ready
# Start coding
```

### Testing Session
```bash
# For testing and validation
./scripts/start-session.sh
./scripts/test-services.sh
# Run tests
```

### Debugging Session
```bash
# For troubleshooting issues
./scripts/start-session.sh
# Monitor logs in separate terminals
make logs &
docker-compose logs -f &
```

---

## 📈 Session Success Metrics

### Successful Session Indicators
- ✅ All services start without errors
- ✅ Health checks pass within 2 minutes
- ✅ PFC completes successfully
- ✅ Tasks discovered and ready
- ✅ Session context loaded

### Performance Targets
- **Session Startup Time**: < 3 minutes (warm), < 8 minutes (cold)
- **Service Health Time**: < 2 minutes for both services
- **Task Discovery Time**: < 30 seconds
- **Error Rate**: < 5% of sessions require troubleshooting

---

*Last Updated: 2026-01-29*
*For complete service documentation, see SERVICE_SETUP.md*
