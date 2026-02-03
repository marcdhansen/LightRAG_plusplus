# ⚙️ Process Skill

**Purpose**: Manages development processes, CI/CD pipelines, release procedures, and quality gates for LightRAG development workflow.

## 🎯 Mission
- Automate CI/CD pipeline management
- Coordinate release procedures
- Manage quality gates and standards enforcement
- Optimize development workflows

## 🛠️ Tools & Scripts

### CI/CD Management
```bash
# Run full CI pipeline
python3 scripts/run_ci.py --full-pipeline

# Trigger specific stage
python3 scripts/run_ci.py --stage tests
```

### Release Management
```bash
# Prepare release candidate
python3 scripts/prepare_release.py --version 1.2.3

# Deploy to staging/production
python3 scripts/deploy.py --environment staging
```

### Quality Gates
```bash
# Run all quality gates
python3 scripts/quality_gates.py --all

# Check specific gate
python3 scripts/quality_gates.py --gate linting
```

### Workflow Optimization
```bash
# Analyze workflow efficiency
python3 scripts/analyze_workflow.py --detailed

# Suggest improvements
python3 scripts/optimize_workflow.py
```

## 📋 Usage Examples

### Basic Process Management
```bash
# Run complete CI/CD pipeline
/process --run-pipeline

# Check current release status
/process --release-status

# Validate quality gates
/process --quality-check
```

### Release Operations
```bash
# Create new release
/process --release --version 1.2.3 --auto-tag

# Rollback release
/process --rollback --version 1.2.2 --reason "critical_bug"

# Deploy to specific environment
/process --deploy --env production --confirm
```

### Quality Management
```bash
# Run all quality checks
/process --quality-all

# Bypass specific gate (emergency only)
/process --bypass-gate --security-check --reason "hotfix"
```

## 🔗 Integration Points
- **Testing Skill**: Coordinate test execution in pipeline
- **Evaluation Skill**: Run evaluations as quality gates
- **Documentation Skill**: Generate docs in release pipeline
- **Beads**: Track process tasks and improvements

## 📊 Metrics Tracked
- CI/CD pipeline duration and success rates
- Quality gate pass/fail statistics
- Release frequency and rollback rates
- Development cycle time

## 🎯 Key Files
- `.github/workflows/` - CI/CD pipeline definitions
- `scripts/run_ci.py` - Main CI orchestration
- `release/` - Release artifacts and notes
- `quality_gates/` - Quality gate configurations
