# OpenViking Rollback Procedures

## Overview

This document outlines the rollback procedures for the OpenViking integration experiment. The rollback plan ensures we can quickly and safely revert to the SMP system if the experiment fails or issues arise.

## Rollback Triggers

### Immediate Rollback Triggers (Stop Experiment Immediately)
- **System instability**: Crashes, memory leaks, deadlocks
- **Critical functionality loss**: Cannot find basic skills or respond to queries
- **Security vulnerabilities**: Any identified security issues
- **Data corruption**: SMP or OpenViking data integrity compromised
- **Performance degradation**: >5x response time increase
- **Error rate**: >20% sustained failure rate

### Conditional Rollback Triggers (Evaluate Within 24 Hours)
- **Primary metric failure**: Any primary success metric not met
- **Resource overconsumption**: >2x memory or CPU usage vs SMP
- **User complaints**: Significant user feedback about degradation
- **Integration issues**: Problems with existing workflows

## Rollback Procedure

### Phase 1: Immediate Response (0-15 minutes)

#### 1. Stop OpenViking Services
```bash
# Stop all OpenViking-related containers
docker-compose -f docker-compose.openviking.yml down

# Verify OpenViking services are stopped
docker-compose -f docker-compose.openviking.yml ps
```

#### 2. Isolate Problem
```bash
# Check system status
docker-compose ps
./scripts/agent-status.sh

# Preserve logs for analysis
docker logs lightrag-openviking > /tmp/openviking_failure.log 2>&1
docker logs lightrag-experimental > /tmp/experimental_failure.log 2>&1
```

#### 3. Verify SMP System
```bash
# Ensure main SMP system is running
docker-compose -f docker-compose.yml ps
docker-compose -f docker-compose.yml start lightrag

# Verify SMP functionality
curl -f http://localhost:9621/health
```

### Phase 2: Data Recovery (15-60 minutes)

#### 1. Data Integrity Check
```bash
# Verify SMP data integrity
ls -la ./.agent/
ls -la ~/.gemini/

# Check for any data modifications
git status
git diff HEAD~1 ./.agent/ ~/.gemini/
```

#### 2. Restore from Git Checkpoint (if needed)
```bash
# Return to pre-experiment checkpoint
git checkout lightrag-0qp.0-pre-experiment

# Verify clean state
git status
docker-compose -f docker-compose.yml down
docker-compose -f docker-compose.yml up -d
```

#### 3. Verify Data Migration Reversal
```bash
# If migration was partially applied, verify SMP data is intact
find ./.agent/ -name "*.backup" -type f

# Restore from backups if they exist
for backup in $(find ./.agent/ -name "*.backup"); do
    original="${backup%.backup}"
    mv "$backup" "$original"
done
```

### Phase 3: System Validation (60-120 minutes)

#### 1. SMP System Health Check
```bash
# Test basic SMP functionality
curl -X POST http://localhost:9621/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "stream": false}'

# Verify skill discovery
curl -X POST http://localhost:9621/api/skills/list \
  -H "Content-Type: application/json"

# Check agent coordination
./scripts/agent-status.sh
```

#### 2. Performance Validation
```bash
# Run basic performance tests
./scripts/performance-test.sh --baseline

# Verify response times are within expected ranges
./scripts/monitor-performance.sh --duration 300 # 5 minutes
```

#### 3. Data Consistency Check
```bash
# Verify all expected skills are present
./scripts/validate-skills.sh

# Check memory and resource usage
docker stats lightrag --no-stream
```

### Phase 4: Documentation & Learning (120+ minutes)

#### 1. Incident Report
Create incident report including:
- Root cause analysis
- Timeline of events
- Impact assessment
- Lessons learned

#### 2. Data Preservation
```bash
# Archive OpenViking data for analysis
mkdir -p /tmp/openviking_rollback_$(date +%Y%m%d_%H%M%S)
cp -r /tmp/openviking_failure.log /tmp/experimental_failure.log /tmp/openviking_rollback_$(date +%Y%m%d_%H%M%S)/

# Archive test results
tar -czf /tmp/comparison_results_$(date +%Y%m%d_%H%M%S).tar.gz /data/results/
```

#### 3. Update Documentation
- Update experiment results
- Document rollback success/failure
- Record lessons learned for future experiments

## Rollback Validation Checklist

### System Health
- [ ] SMP container running and healthy
- [ ] Agent coordination system functional
- [ ] All expected skills discoverable
- [ ] Response times within normal range
- [ ] No error spikes in logs

### Data Integrity
- [ ] All SMP data present and unchanged
- [ ] No data corruption detected
- [ ] Backups verified (if created)
- [ ] Git repository in clean state

### Performance
- [ ] Response times ≤ baseline +10%
- [ ] Memory usage ≤ baseline +20%
- [ ] CPU usage ≤ baseline +20%
- [ ] Error rate ≤ baseline

### User Experience
- [ ] Basic queries working correctly
- [ ] Complex multi-skill queries functional
- [ ] Agent coordination operational
- [ ] No user-facing errors

## Emergency Rollback (Critical Issues)

For critical security issues or system-wide failures:

```bash
# EMERGENCY ROLLBACK - Execute immediately
#!/bin/bash

# 1. Stop everything
docker-compose -f docker-compose.yml down
docker-compose -f docker-compose.openviking.yml down

# 2. Force restore to known good state
git reset --hard lightrag-0qp.0-pre-experiment
git clean -fd

# 3. Restart only SMP
docker-compose -f docker-compose.yml up -d

# 4. Verify basic functionality
sleep 30
curl -f http://localhost:9621/health || echo "ROLLBACK FAILED - CONTACT SUPPORT"

echo "Emergency rollback completed at $(date)"
```

## Partial Rollback Scenarios

### Scenario 1: OpenViking API Issues
- Keep SMP system running
- Disable OpenViking integration
- Route all traffic to SMP
- Fix OpenViking issues separately

### Scenario 2: Performance Issues Only
- Implement rate limiting
- Reduce OpenViking load
- Keep both systems running with monitoring
- Optimize before full rollback

### Scenario 3: Data Migration Issues
- Rollback data changes only
- Keep OpenViking running with original data
- Re-run migration with fixes

## Rollback Time Targets

| Scenario | Target Time | Maximum Time |
|----------|-------------|--------------|
| Emergency rollback | 5 minutes | 15 minutes |
| Service disruption | 15 minutes | 60 minutes |
| Performance issues | 30 minutes | 120 minutes |
| Data corruption | 60 minutes | 240 minutes |

## Post-Rollback Activities

### Immediate (0-24 hours)
- Monitor system stability
- Verify all functionality working
- Communicate status to stakeholders

### Short-term (1-7 days)
- Analyze root causes
- Document lessons learned
- Plan improvements

### Long-term (1+ weeks)
- Consider future experiments
- Implement improvements
- Update procedures based on learnings

## Contacts and Escalation

### Primary Contacts
- **System Administrator**: Available 24/7 for emergency rollbacks
- **Development Team**: Available during business hours for analysis
- **Stakeholders**: To be informed of any production impact

### Escalation Paths
1. **Level 1**: On-call system administrator
2. **Level 2**: Development team lead
3. **Level 3**: Project stakeholder committee

---

**Document Version**: 1.0
**Last Updated**: 2026-02-03
**Next Review**: After any rollback execution
