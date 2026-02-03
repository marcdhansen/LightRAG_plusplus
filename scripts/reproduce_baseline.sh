#!/bin/bash
# Reproduce SMP Baseline Metrics
# This script ensures the SMP baseline is measured consistently.

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "🏁 Starting SMP Baseline Reproduction..."

# Ensure environment isolation
if [ ! -f .env.smp ]; then
    echo "⚠️  .env.smp not found. Creating from .env..."
    cp .env .env.smp
fi

# Run Benchmark
echo "📊 Running Benchmarks (5 cases per dataset)..."
python compare_benchmarks.py --cases 5 --output audit_results/smp_baseline_report_$(date +%Y%m%d_%H%M%S).md

echo "✅ Baseline reproduction complete."
