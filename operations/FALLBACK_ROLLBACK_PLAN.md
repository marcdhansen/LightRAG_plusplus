# OpenViking Fallback Procedures & Rollback Plan

## 🛡️ Fallback Strategy Overview

This document outlines comprehensive fallback procedures and rollback plans for OpenViking production deployment, ensuring system resilience and quick recovery from any issues.

---

## 🚨 Critical Failure Triggers

### Immediate Rollback Triggers
- **Health Check Failures**: >3 consecutive failed health checks
- **Response Time Degradation**: >5000ms average response time
- **Error Rate Spike**: >20% error rate across key endpoints
- **Memory/CPU Exhaustion**: >90% resource utilization for >5 minutes
- **Data Corruption**: Any database integrity issues detected

### Warning Triggers (Monitor Closely)
- **Performance Degradation**: 2-5x slower than baseline
- **Cache Inefficiency**: <50% cache hit rate
- **Session Failures**: >10% session creation failures

---

## 🔄 Fallback Procedures

### Level 1: Graceful Degradation (First 5 Minutes)

**Trigger**: Minor performance issues or temporary spikes

**Actions**:
```bash
# 1. Enable circuit breaker pattern
curl -X POST http://localhost:8002/admin/circuit-breaker/enable \
  -H "Content-Type: application/json" \
  -d '{"failure_threshold": 5, "recovery_timeout": 30}'

# 2. Increase cache sizes
curl -X POST http://localhost:8002/admin/cache/resize \
  -H "Content-Type: application/json" \
  -d '{"max_size": 2000}'

# 3. Enable request queuing
curl -X POST http://localhost:8002/admin/queue/enable \
  -H "Content-Type: application/json" \
  -d '{"max_queue_size": 1000, "timeout_ms": 30000}'
```

**Monitoring**: Continue with increased alerting frequency (every 30 seconds)

---

### Level 2: Service Isolation (5-15 Minutes)

**Trigger**: Persistent issues after Level 1 actions

**Actions**:
```bash
# 1. Route to SMP fallback
# Update load balancer configuration
# Example using nginx:
sudo sed -i 's/upstream openviking {/upstream openviking {\n    server localhost:8002 backup;/g' /etc/nginx/nginx.conf

# 2. Scale up OpenViking resources
docker-compose -f docker-compose.openviking.yml up -d --scale openviking-server=3

# 3. Enable aggressive caching
curl -X POST http://localhost:8002/admin/cache/aggressive \
  -H "Content-Type: application/json" \
  -d '{"cache_ttl_seconds": 3600, "force_cache": true}'
```

**Monitoring**: Every 15 seconds with alert thresholds lowered by 50%

---

### Level 3: Full Rollback (15+ Minutes)

**Trigger**: Critical failures or unresolved issues after Level 2

**Actions**:
```bash
#!/bin/bash
# emergency_rollback.sh

echo "🚨 EMERGENCY ROLLBACK INITIATED"

# 1. Stop OpenViking services
docker-compose -f docker-compose.openviking.yml down

# 2. Verify SMP is running and healthy
if ! curl -f http://localhost:9621/health; then
    echo "❌ SMP is not available - CRITICAL"
    exit 1
fi

# 3. Update routing to 100% SMP
sudo cp /etc/nginx/smp-only.conf /etc/nginx/nginx.conf
sudo nginx -s reload

# 4. Restart core monitoring
docker-compose -f docker-compose.yml up -d lightrag

# 5. Verify rollback success
sleep 10
if curl -f http://localhost/health; then
    echo "✅ ROLLBACK SUCCESSFUL"
    # Send alert
    curl -X POST https://alerts.company.com/webhook \
      -H "Content-Type: application/json" \
      -d '{"status": "rollback_complete", "timestamp": "'$(date -Iseconds)'"}'
else
    echo "❌ ROLLBACK FAILED - MANUAL INTERVENTION REQUIRED"
fi
```

---

## 📋 Step-by-Step Rollback Guide

### Phase 1: Assessment (First 2 Minutes)

1. **Check System Status**
   ```bash
   # OpenViking status
   curl -s http://localhost:8002/health | jq '.status'

   # Resource usage
   docker stats lightrag-openviking --no-stream

   # Error logs
   docker logs lightrag-openviking --tail 50
   ```

2. **Validate SMP Availability**
   ```bash
   # SMP health
   curl -s http://localhost:9621/health | jq '.status'

   # SMP response time
   time curl -s http://localhost:9621/status
   ```

3. **Determine Impact Scope**
   ```bash
   # Check recent errors
   grep -i error /var/log/openviking/*.log | tail -20

   # Check database integrity
   docker exec lightrag-openviking-redis redis-cli ping
   ```

### Phase 2: Containment (Next 3 Minutes)

1. **Isolate OpenViking from Production Traffic**
   ```bash
   # Update load balancer
   kubectl patch service openviking -p '{"spec":{"selector":{"version":"backup"}}}'

   # Or update nginx
   sudo sed -i 's/server localhost:8002/# server localhost:8002/g' /etc/nginx/nginx.conf
   sudo nginx -s reload
   ```

2. **Preserve Current State**
   ```bash
   # Create data snapshot
   docker exec lightrag-openviking-redis redis-cli BGSAVE

   # Export configurations
   docker-compose -f docker-compose.openviking.yml config > openviking_config_backup.yml

   # Archive logs
   tar -czf openviking_logs_$(date +%Y%m%d_%H%M%S).tar.gz /var/log/openviking/
   ```

### Phase 3: Recovery (Next 5 Minutes)

1. **Initiate SMP Primary Routing**
   ```bash
   # Ensure SMP is primary
   docker-compose -f docker-compose.yml up -d lightrag

   # Update DNS/load balancer
   kubectl patch service frontend -p '{"spec":{"externalIPs":["192.168.1.100"]}}'
   ```

2. **Scale SMP Resources**
   ```bash
   # Increase SMP capacity if needed
   docker-compose -f docker-compose.yml up -d --scale lightrag=3

   # Verify SMP performance
   python monitoring/smp_health_check.py
   ```

### Phase 4: Verification (Final 5 Minutes)

1. **End-to-End Testing**
   ```bash
   # Test core functionality
   python tests/smp_integration_test.py

   # Load testing
   python tests/smp_load_test.py --concurrent 100 --duration 60
   ```

2. **Monitor System Stability**
   ```bash
   # Watch for issues
   watch -n 5 'curl -s http://localhost:9621/health | jq .'

   # Check error rates
   tail -f /var/log/smp/application.log | grep ERROR
   ```

---

## 🔄 Recovery Procedures

### After Rollback - Root Cause Analysis

1. **Data Collection**
   ```bash
   # Collect diagnostic information
   ./scripts/collect_diagnostics.sh

   # Generate incident report
   python tools/generate_incident_report.py \
     --rollback-time "$(date -Iseconds)" \
     --trigger-level "critical"
   ```

2. **System Analysis**
   ```bash
   # Analyze performance data
   python tools/analyze_performance_degradation.py \
     --start-time "2026-02-03T14:00:00" \
     --end-time "2026-02-03T14:30:00"

   # Check for resource exhaustion
   docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}" > resource_usage.log
   ```

### Re-deployment Preparation

1. **Fix Implementation**
   - Address root cause issues
   - Implement additional monitoring
   - Update fallback configurations

2. **Staged Re-deployment**
   ```bash
   # Deploy to staging first
   docker-compose -f docker-compose.staging.yml up -d

   # Run comprehensive tests
   python tests/full_regression_suite.py

   # Gradual production rollout
   kubectl patch deployment openviking -p '{"spec":{"replicas":1}}'
   sleep 300
   kubectl patch deployment openviking -p '{"spec":{"replicas":2}}'
   sleep 300
   kubectl patch deployment openviking -p '{"spec":{"replicas":3}}'
   ```

---

## 📞 Escalation Contacts

### Primary Response Team
- **DevOps Lead**: devops@company.com (Page: 555-0101)
- **Engineering Manager**: eng-manager@company.com (Page: 555-0102)
- **Site Reliability**: sre@company.com (Slack: #sre-oncall)

### Escalation Chain
1. **Level 1**: DevOps Team (0-15 minutes)
2. **Level 2**: Engineering Director (15-30 minutes)
3. **Level 3**: CTO (30+ minutes)

---

## 🧪 Testing Fallback Procedures

### Regular Drills (Monthly)

```bash
# Automated fallback drill
./scripts/fallback_drill.sh --scenario=performance_degradation --duration=300

# Manual rollback drill
./scripts/manual_rollback_drill.sh --simulate_failure=true

# Recovery time measurement
python scripts/measure_recovery_time.py --baseline=180 --target=300
```

### Quarterly Full-Scale Test

1. **Simulate production outage**
2. **Execute full rollback procedure**
3. **Measure recovery metrics**
4. **Update procedures based on lessons learned**

---

## 📊 Success Metrics

### Rollback Success Criteria
- **Recovery Time**: < 5 minutes to full SMP functionality
- **Data Loss**: < 1% of recent session data
- **Service Downtime**: < 30 seconds for end users
- **No Manual Intervention**: Automated rollback completes successfully

### Fallback Performance
- **Detection Time**: < 30 seconds to detect failures
- **Containment Time**: < 2 minutes to isolate issues
- **Recovery Time**: < 10 minutes to restore service

---

## 📝 Checklist Templates

### Emergency Rollback Checklist
```
[ ] System status assessed
[ ] SMP availability confirmed
[ ] OpenViking traffic isolated
[ ] Current state preserved
[ ] SMP routing activated
[ ] End-to-end testing completed
[ ] Monitoring re-enabled
[ ] Incident report initiated
[ ] Stakeholders notified
[ ] Root cause analysis started
```

### Post-Rollback Review Checklist
```
[ ] Timeline documented
[ ] Root cause identified
[ ] Fixes implemented
[ ] Monitoring improved
[ ] Procedures updated
[ ] Team debrief completed
[ ] Lessons learned captured
[ ] Re-deployment plan approved
[ ] Schedule for re-deployment set
[ ] Success criteria defined
```

---

*Last Updated: 2026-02-03*
*Version: 1.0*
*Next Review: 2026-03-03*
