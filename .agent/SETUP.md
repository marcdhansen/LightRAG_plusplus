# 🚀 LightRAG One-Time Setup Guide

> **Purpose**: First-time environment setup for new agents/IDEs
> **Audience**: New agents setting up LightRAG for the first time
> **Frequency**: Perform **once** per new development environment
> **Prerequisites**: macOS/Linux system with admin access

---

## 🎯 Setup Overview

This guide walks you through the complete one-time setup process for LightRAG. After completion, you'll use `start-session.sh` for daily work sessions.

### ⏱️ Time Estimates
- **Global Tools**: 10-15 minutes
- **Project Setup**: 5-10 minutes
- **Service Initialization**: 5-10 minutes
- **Total**: 20-35 minutes

---

## 📋 Pre-Setup Checklist

Before starting, ensure you have:

- [ ] **Admin access** to install system software
- [ ] **Internet connection** for downloading tools
- [ ] **10GB free disk space** for Docker images and dependencies
- [ ] **Git access** to clone repositories

---

## 🔧 One-Time Setup Process

### Step 1: Run Automated Setup Script

```bash
# Clone LightRAG repository (if not already done)
git clone <LightRAG-URL>
cd LightRAG

# Execute one-time setup
./scripts/setup.sh
```

### Step 2: Manual Verification

After the automated script completes, verify setup:

```bash
# Check global tools
which docker uv git bd
docker --version && uv --version && bd --version

# Verify project structure
ls -la .env .venv/ .setup_complete

# Test Automem repository
ls -la $HOME/GitHub/verygoodplugins/automem/

# Verify service configuration
docker ps -a | grep -E "(automem|langfuse)"
```

---

## 🛠️ What the Setup Script Does

### Global Environment Setup
- ✅ **Docker Desktop**: Verifies installation or provides installation instructions
- ✅ **Package Managers**: Installs `uv` (Python), `bd` (Beads), verifies `git`
- ✅ **Global Memory**: Initializes Beads configuration (`bd init`)
- ✅ **Skills Installation**: Sets up FlightDirector and other global skills

### Project Environment Setup
- ✅ **Dependencies**: Installs Python packages with `uv sync`
- ✅ **Environment Files**: Creates `.env` from `.env.example` template
- ✅ **Virtual Environment**: Sets up Python virtual environment
- ✅ **Git Configuration**: Initializes repository tracking

### Service Repository Setup
- ✅ **Automem**: Clones and configures Automem repository
- ✅ **Service Config**: Creates initial environment files
- ✅ **Database Initialization**: Starts services once to create databases, then stops them

---

## 📁 File Structure After Setup

```
LightRAG/
├── .setup_complete          # Marker that setup was completed
├── .env                    # Project environment variables
├── .venv/                  # Python virtual environment
├── scripts/
│   ├── setup.sh             # One-time setup (this script)
│   ├── start-session.sh     # Daily session startup
│   ├── end-session.sh      # Session cleanup
│   └── test-services.sh     # Service testing
├── .agent/
│   ├── SETUP.md             # This guide
│   ├── SESSION.md           # Daily startup guide
│   └── TROUBLESHOOTING.md  # Issue resolution
└── langfuse_docker/         # Langfuse Docker configuration

~/.beads/                    # Beads configuration
~/.gemini/                    # Global agent memory
~/GitHub/verygoodplugins/automem/  # Automem repository
```

---

## ✅ Validation Checklist

After setup completion, verify:

### Global Tools
```bash
# Docker Desktop running
docker info

# Package managers available
uv --version
bd --version

# Beads initialized
ls ~/.beads/config.yaml
```

### Project Setup
```bash
# Virtual environment active
source .venv/bin/activate

# Dependencies installed
uv pip list | head -5

# Environment configured
cat .env
```

### Services Ready
```bash
# Automem repository exists
ls ~/GitHub/verygoodplugins/automem/

# Can start services (test)
./scripts/start-session.sh
```

---

## 🐛 Troubleshooting One-Time Setup

### Docker Issues
**Problem**: Docker not installed or not running
**Solution**:
```bash
# Install Docker Desktop (macOS)
brew install --cask docker

# Start Docker Desktop
open /Applications/Docker.app
```

### Permission Issues
**Problem**: Permission denied errors
**Solution**:
```bash
# Fix script permissions
chmod +x scripts/*.sh

# Fix Docker permissions (Linux)
sudo usermod -aG docker $USER
```

### Network Issues
**Problem**: Repository cloning fails
**Solution**:
```bash
# Check internet
ping google.com

# Use alternative URL or VPN
git clone https://mirror.com/LightRAG.git
```

### Disk Space Issues
**Problem**: Insufficient space for Docker images
**Solution**:
```bash
# Check disk space
df -h

# Clean Docker if needed
docker system prune -a
```

---

## 🎉 Setup Completion

When setup completes successfully:

1. **Setup Marker**: `.setup_complete` file created
2. **Environment Ready**: All tools installed and configured
3. **Services Prepared**: Docker images downloaded and initialized
4. **Documentation Available**: All guides ready for reference

### Next Steps

After one-time setup, use these commands for daily work:

```bash
# Start a new work session
./scripts/start-session.sh

# End a work session
./scripts/end-session.sh

# Test service health
./scripts/test-services.sh
```

---

## 📚 Additional Resources

- **Daily Startup**: See `SESSION.md`
- **Service Issues**: See `SERVICE_SETUP.md`
- **Project Status**: See `.agent/rules/ROADMAP.md`
- **Troubleshooting**: See `TROUBLESHOOTING.md`

---

## 🔄 Resetting One-Time Setup

If you need to re-run setup:

```bash
# Remove setup marker
rm .setup_complete

# Re-run setup
./scripts/setup.sh
```

*Note: This won't uninstall tools but will re-verify configuration.*

---

## 💡 Tips for Success

1. **Network Connection**: Ensure stable internet during setup
2. **System Resources**: Close resource-heavy applications during setup
3. **Follow Instructions**: Don't skip setup steps or use shortcuts
4. **Save Progress**: Setup script creates markers - don't delete them
5. **Document Issues**: If problems occur, note them for troubleshooting

---

*Last Updated: 2026-01-29*
*For issues or questions, check TROUBLESHOOTING.md*
