# OpenViking Integration Experiment Guide

## Executive Summary

This document provides a complete guide for executing the OpenViking integration experiment with LightRAG. The experiment evaluates OpenViking as a replacement for the SMP system to improve skill discovery and token efficiency.

## Quick Start

### Prerequisites
1. **Git checkpoint created**: `lightrag-0qp.0-pre-experiment` ✅
2. **Docker environment ready**: Complete with management scripts ✅
3. **Migration tooling built**: Comprehensive migration scripts ✅
4. **A/B testing framework**: Performance comparison system ✅
5. **Documentation complete**: Success criteria and rollback procedures ✅

### Environment Setup

```bash
# 1. Set OpenAI API key (required for OpenViking)
export OPENAI_API_KEY=your-openai-api-key-here

# 2. Start the experiment environment
./openviking/scripts/manage.sh start

# 3. Verify all services are running
./openviking/scripts/manage.sh status

# 4. Run A/B comparison tests
./openviking/scripts/manage.sh compare
```

## Experiment Architecture

### System Layout
```
┌─────────────────┐    ┌─────────────────┐
│   SMP System    │    │ OpenViking Sys  │
│   (Reference)   │    │ (Experimental)  │
│                 │    │                 │
│ lightrag-main   │    │ lightrag-       │
│ :9621           │    │ experimental    │
│                 │    │ :9622           │
└─────────────────┘    └─────────────────┘
         │                       │
         └───────────┬───────────┘
                     │
         ┌─────────────────────┐
         │ Performance Compare │
         │   Service           │
         └─────────────────────┘
```

### Data Flow
1. **Test scenarios** loaded from configuration
2. **Parallel queries** sent to both systems
3. **Metrics collected**: response time, tokens, success rate
4. **Analysis performed** with statistical validation
5. **Report generated** with recommendations

## Detailed Execution Plan

### Phase 1: Environment Preparation (Day 0)

#### 1.1 System Setup
```bash
# Create OpenViking data directory
mkdir -p ./data/openviking

# Set environment variables
export OPENAI_API_KEY=your-key-here
export LOG_LEVEL=INFO

# Start all services
./openviking/scripts/manage.sh start
```

#### 1.2 Validation
```bash
# Check service health
curl -f http://localhost:8000/health  # OpenViking API
curl -f http://localhost:9621/health   # SMP Reference
curl -f http://localhost:9622/health   # OpenViking LightRAG

# Verify agent coordination
./scripts/agent-status.sh
```

### Phase 2: Baseline Testing (Day 1)

#### 2.1 SMP Baseline
```bash
# Ensure SMP system is stable
docker-compose -f docker-compose.yml restart lightrag

# Run baseline tests
./scripts/performance-test.sh --system=smp --duration=3600
```

#### 2.2 OpenViking Baseline
```bash
# Verify OpenViking is stable
docker-compose -f docker-compose.openviking.yml restart openviking-server

# Run OpenViking tests
./scripts/performance-test.sh --system=openviking --duration=3600
```

### Phase 3: A/B Testing (Days 2-3)

#### 3.1 Execute Comparison
```bash
# Run full comparison suite
./openviking/scripts/manage.sh compare

# Monitor progress
./openviking/scripts/manage.sh logs performance-comparison
```

#### 3.2 Monitor Results
```bash
# Check results directory
ls -la /data/results/

# View preliminary results
cat /data/results/comparison_report_*.md
```

### Phase 4: Data Migration (Day 4) - Optional

If performance is promising, test data migration:

```bash
# Run migration test
./openviking/scripts/manage.sh migrate

# Monitor migration
./openviking/scripts/manage.sh logs openviking-migration
```

### Phase 5: Decision (Day 5)

#### 5.1 Review Results
```bash
# Generate final report
python -c "
import json
from pathlib import Path

# Load latest metrics
metrics_file = max(Path('/data/results').glob('raw_metrics_*.json'))
with open(metrics_file) as f:
    metrics = json.load(f)

# Analyze results (simplified)
smp_times = [m['response_time_ms'] for m in metrics if m['system'] == 'smp' and m['success']]
ov_times = [m['response_time_ms'] for m in metrics if m['system'] == 'openviking' and m['success']]

print(f'SMP avg response: {sum(smp_times)/len(smp_times):.1f}ms')
print(f'OpenViking avg response: {sum(ov_times)/len(ov_times):.1f}ms')
print(f'Improvement: {(sum(smp_times)/len(smp_times) - sum(ov_times)/len(ov_times))/sum(smp_times)*len(smp_times)*100:.1f}%')
"
```

#### 5.2 Make Decision

Based on success criteria in `openviking/docs/success_criteria.md`:

- **SUCCESS**: Deploy OpenViking permanently
- **CONDITIONAL**: Deploy with modifications
- **FAILURE**: Rollback to SMP

## Monitoring During Experiment

### Key Metrics to Watch

```bash
# Response times
watch -n 5 'curl -s -w "%{time_total}\n" -o /dev/null http://localhost:9621/api/chat -X POST -H "Content-Type: application/json" -d '"'"'{"query":"test"}'"'"''

# Error rates
watch -n 10 'docker logs lightrag-main --tail 50 | grep -i error | wc -l'

# Resource usage
watch -n 5 'docker stats --no-stream lightrag-main lightrag-experimental'

# Token usage (if available)
watch -n 30 'grep "tokens" /data/results/latest_metrics.json 2>/dev/null || echo "No token data yet"'
```

### Alert Thresholds

- **Response time**: >3x baseline for 5+ minutes
- **Error rate**: >5% sustained for 10+ minutes
- **Memory usage**: >500MB sustained
- **Container crashes**: Any container restart

## Success Evaluation

### Primary Metrics (All Required)

| Metric | SMP Baseline | OpenViking Target | Minimum Acceptable |
|--------|--------------|-------------------|-------------------|
| Response Time | 2500ms | ≤1500ms | ≤1750ms |
| Token Usage | 850 tokens | ≤680 tokens | ≤750 tokens |
| Success Rate | 97% | ≥98% | ≥97% |

### Secondary Metrics (Most Required)

| Metric | SMP Baseline | OpenViking Target |
|--------|--------------|-------------------|
| Response Quality | 3.8/5 | ≥4.0/5 |
| Context Memory | 85% | ≥90% |
| Resource Usage | 150MB RAM | ≤120MB RAM |

## Rollback Decision Tree

```
Is any primary metric failing?
├─ YES → Immediate rollback to SMP
└─ NO
   ├─ Are ≥3 secondary metrics failing?
   │  ├─ YES → Conditional rollback
   │  └─ NO → Continue evaluation
   ├─ Are there critical bugs?
   │  ├─ YES → Emergency rollback
   │  └─ NO → Deploy OpenViking
   └─ Is performance comparable?
      ├─ YES → Consider deployment
      └─ NO → Stick with SMP
```

## Communication Plan

### Daily Status Updates
- **Morning**: Previous day's results summary
- **Evening**: System health and progress report
- **Issues**: Immediate notification of any problems

### Stakeholder Reports
- **Day 0**: Experiment start notification
- **Day 3**: Interim results
- **Day 5**: Final recommendation

## Post-Experiment Activities

### If Successful
1. **Permanent deployment**: Replace SMP with OpenViking
2. **Migration**: Execute full data migration
3. **Documentation**: Update all system documentation
4. **Training**: Team training on OpenViking
5. **Monitoring**: Enhanced monitoring for production

### If Unsuccessful
1. **Rollback**: Execute rollback procedures
2. **Analysis**: Document root causes
3. **Learning**: Update experiment design
4. **Planning**: Future improvement opportunities
5. **Cleanup**: Remove OpenViking components

## Troubleshooting Guide

### Common Issues

#### OpenViking fails to start
```bash
# Check logs
docker logs lightrag-openviking

# Verify OpenAI API key
echo $OPENAI_API_KEY

# Restart services
./openviking/scripts/manage.sh stop
./openviking/scripts/manage.sh start
```

#### Performance comparison fails
```bash
# Verify both systems are healthy
curl -f http://localhost:9621/health
curl -f http://localhost:9622/health

# Check comparison logs
docker logs lightrag-performance-comparison

# Rebuild comparison service
docker-compose -f docker-compose.openviking.yml build --no-cache performance-comparison
```

#### Migration issues
```bash
# Verify OpenViking is running
curl -f http://localhost:8000/health

# Check migration logs
docker logs lightrag-openviking-migration

# Verify source data
ls -la ./.agent/skills/
ls -la ~/.gemini/
```

## Emergency Contacts

- **System Administrator**: 24/7 on-call for production issues
- **Development Team**: Available during business hours
- **Stakeholder Committee**: Decision approval and communication

---

**Experiment Duration**: 5 days
**Risk Level**: Medium (with rollback plan)
**Expected Outcome**: Data-driven decision on OpenViking adoption

**Document Version**: 1.0
**Last Updated**: 2026-02-03
